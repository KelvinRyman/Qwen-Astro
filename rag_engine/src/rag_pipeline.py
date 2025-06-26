import os
import shutil
import logging
from typing import Dict, List, Optional, Set
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.vector_stores import (
    MetadataFilters,
    ExactMatchFilter,
    FilterCondition,
)
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.llms import ChatMessage

from .config import RAGConfig
from .components import create_vector_store, setup_global_settings
from .group_manager import GroupManager
from .data_processor import DataProcessor
from .conversation_manager import ConversationManager
from .agent_manager import AgentManager
from .smart_chat import SmartChatEngine


class RAGPipeline:
    """
    一个支持资源分组的 RAG 系统管道。
    """

    def __init__(self, config: RAGConfig):
        self.config = config
        self.index: VectorStoreIndex | None = None

        setup_global_settings(config)
        self.vector_store, self.chroma_collection = create_vector_store(config)

        self.group_manager = GroupManager(config)
        self.data_processor = DataProcessor(config)
        self.conversation_manager = ConversationManager()
        self.agent_manager = AgentManager(config)
        self.smart_chat_engine = SmartChatEngine(config)

    def initialize(self):
        """
        初始化管道，主要是从现有的向量存储中加载索引。
        这个方法取代了旧的 build_index，因为它不再主动扫描文件。
        """
        logging.info("\n--- 初始化 RAG 管道 ---")
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        self.index = VectorStoreIndex.from_vector_store(
            self.vector_store, storage_context=storage_context
        )
        logging.info(
            f"已从向量数据库加载索引。数据库中现有 {self.chroma_collection.count()} 个项目。"
        )
        logging.info("--- RAG 管道已准备就绪 ---")

    def add_files_to_group(
        self, group_id: str, source_file_paths: List[str]
    ) -> List[Dict]:
        """
        向指定组中添加多个文件，处理物理存储、元数据和向量索引。
        """
        group_meta = self.group_manager.get_group_by_id(group_id)
        if not group_meta:
            logging.error(f"添加文件失败：找不到组 (ID: {group_id})。")
            return []

        group_dir = self.group_manager.get_group_physical_path(group_id)
        if not group_dir:
            logging.error(f"无法找到组 '{group_id}' 的物理目录，无法添加文件。")
            return []

        added_files_meta = []
        for src_path in source_file_paths:
            if not os.path.exists(src_path):
                logging.warning(f"源文件 '{src_path}' 不存在，已跳过。")
                continue

            file_name = os.path.basename(src_path)
            # 1. 检查元数据中文件名是否重复
            if self.group_manager.get_file_by_name(group_id, file_name):
                logging.warning(f"文件名 '{file_name}' 已存在于组中，已跳过。")
                continue

            # 2. 复制物理文件
            dest_path = os.path.join(group_dir, file_name)
            try:
                shutil.copy(src_path, dest_path)
                file_size = os.path.getsize(dest_path)
            except (IOError, OSError) as e:
                logging.error(f"复制文件 '{src_path}' 到组目录失败: {e}")
                continue  # 继续处理下一个文件

            # 3. 添加文件元数据
            file_meta = self.group_manager.add_file_meta(
                group_id, file_name, file_size
            )
            if file_meta:
                # 为下一步处理添加物理路径
                file_meta["physical_path"] = dest_path
                added_files_meta.append(file_meta)

        if not added_files_meta:
            logging.info("没有新文件被添加到组中。")
            return []

        # 4. 为新添加的文件创建并插入向量
        logging.info(f"开始为 {len(added_files_meta)} 个新文件创建索引...")
        nodes = self.data_processor.process_data(
            group_id=group_id, files_meta=added_files_meta
        )
        if nodes:
            self.index.insert_nodes(nodes)
            logging.info(f"成功为 {len(added_files_meta)} 个新文件创建并插入了向量。")

        return added_files_meta

    def add_urls_to_group(self, group_id: str, urls: List[str]) -> List[Dict]:
        """
        向指定组中添加多个URL，处理元数据和向量索引。
        """
        group_meta = self.group_manager.get_group_by_id(group_id)
        if not group_meta:
            logging.error(f"添加URL失败：找不到组 (ID: {group_id})。")
            return []

        added_webpages_meta = []
        for url in urls:
            # 1. 检查元数据中URL是否重复
            if self.group_manager.get_webpage_by_url(group_id, url):
                logging.warning(f"URL '{url}' 已存在于组中，已跳过。")
                continue

            # 2. 添加网页元数据
            webpage_meta = self.group_manager.add_webpage_meta(group_id, url)
            if webpage_meta:
                added_webpages_meta.append(webpage_meta)

        if not added_webpages_meta:
            logging.info("没有新URL被添加到组中。")
            return []

        # 3. 为新添加的URL创建并插入向量
        logging.info(f"开始为 {len(added_webpages_meta)} 个新URL创建索引...")
        nodes = self.data_processor.process_data(
            group_id=group_id, webpages_meta=added_webpages_meta
        )
        if nodes:
            self.index.insert_nodes(nodes)
            logging.info(f"成功为 {len(added_webpages_meta)} 个新URL创建并插入了向量。")

        return added_webpages_meta

    def list_all_groups(self) -> List[Dict]:
        """
        代理 GroupManager 的方法，列出所有组。
        """
        return self.group_manager.get_all_groups()

    def query_in_groups(self, query_text: str, group_ids: List[str]):
        """
        在指定的一个或多个组内执行查询。

        Args:
            query_text: 用户提出的问题。
            group_ids: 一个包含要搜索的组ID的列表。

        Returns:
            一个包含答案和源节点的响应对象。
        """
        if not self.index:
            raise RuntimeError("索引尚未初始化。请先调用 initialize()。")
        if not group_ids:
            raise ValueError("必须至少提供一个 group_id 进行查询。")

        logging.info(f"在组 {group_ids} 中查询: '{query_text}'")

        # 核心：创建元数据过滤器
        filters = MetadataFilters(
            filters=[ExactMatchFilter(key="group_id", value=gid) for gid in group_ids],
            condition=FilterCondition.OR,  # 如果文档匹配任何一个组ID，就包含它
        )

        # 为本次查询创建一个临时的、带过滤器的查询引擎
        # 这是最佳实践，因为它无状态且线程安全
        query_engine = self.index.as_query_engine(
            filters=filters, similarity_top_k=self.config.SIMILARITY_TOP_K
        )

        return query_engine.query(query_text)

    def delete_group(self, group_id: str) -> bool:
        """
        彻底从向量数据库中删除一个组，包括其在向量数据库中的所有节点、元数据和物理存储内容。

        这是一个原子化操作，**请务必遵循以下顺序**：
        1. 从 ChromaDB 中删除所有相关节点。
        2. 从 GroupManager 中删除组的元数据和物理目录内容。

        Keyword arguments:
        group_id -- 组的唯一标识符
        Return: 返回是否成功删除组
        """
        logging.info(f"--- 开始删除组 (ID: {group_id}) ---")

        # 步骤 0: 验证组是否存在
        group_meta = self.group_manager.get_group_by_id(group_id)
        if not group_meta:
            logging.warning(
                f"尝试删除一个不存在的组 (ID: {group_id})。操作视为成功（幂等性）。"
            )
            return True

        group_name = group_meta.get("name", "Unknown")
        logging.info(f"正在删除组 '{group_name}'...")

        # 步骤 1: 从 ChromaDB 删除所有属于该组的节点
        try:
            # ChromaDB 的 `delete` 方法接受一个 `where` 子句来指定要删除的文档
            self.chroma_collection.delete(where={"group_id": group_id})
            logging.info(f"已向 ChromaDB 发送删除组 '{group_name}' 所有节点的请求。")
            # 注意: ChromaDB 的删除可能是异步的，但API调用是同步的。
            # 验证删除是否成功是可选的，但对于关键操作是好的实践。
            count_after = len(
                self.chroma_collection.get(where={"group_id": group_id})["ids"]
            )
            if count_after == 0:
                logging.info("验证成功：ChromaDB 中不再有该组的节点。")
            else:
                logging.error("验证失败：ChromaDB 中仍存在该组的节点！")
                return False
        except Exception as e:
            logging.error(
                f"从 ChromaDB 删除组 '{group_name}' 的节点时发生错误: {e}",
                exc_info=True,
            )
            # 如果数据库操作失败，中止整个流程，避免数据不一致
            return False

        # 步骤 2: 删除元数据和物理存储
        # 这一步现在被封装在 GroupManager 中
        success = self.group_manager.delete_group_metadata_and_storage(group_id)
        if success:
            logging.info(f"--- 组 '{group_name}' (ID: {group_id}) 已被彻底删除。 ---")
        else:
            logging.error(
                f"在删除组 '{group_name}' 的元数据或物理文件时发生错误。系统可能处于不一致状态！"
            )

        return success

    def list_sources_in_group(self, group_id: str) -> Dict[str, List[Dict]]:
        """
        列出指定组内的所有数据源，包括文件和网页。
        数据直接来自作为唯一可信源的元数据文件。
        """
        files = self.group_manager.list_files_metadata(group_id)
        webpages = self.group_manager.list_webpages_metadata(group_id)
        return {"files": files, "webpages": webpages}

    def delete_files_from_group(self, group_id: str, file_ids: List[str]) -> bool:
        """
        从一个组中彻底删除指定的文件。
        顺序: 向量数据库 -> 物理文件 -> 元数据
        """
        if not file_ids:
            return True

        logging.info(f"准备从组 '{group_id}' 删除 {len(file_ids)} 个文件...")
        all_success = True

        for file_id in file_ids:
            file_meta = self.group_manager.get_file_by_id(group_id, file_id)
            if not file_meta:
                logging.warning(f"找不到文件ID '{file_id}'，跳过删除。")
                continue

            file_name = file_meta['name']
            logging.info(f"正在删除文件 '{file_name}' (ID: {file_id})...")

            try:
                # 1. 从ChromaDB删除节点
                self.chroma_collection.delete(where={"file_id": file_id})
                logging.info(f"  - 已从向量数据库删除 '{file_name}' 的节点。")

                # 2. 删除物理文件
                group_physical_path = self.group_manager.get_group_physical_path(group_id)
                if group_physical_path:
                    file_to_delete = os.path.join(group_physical_path, file_meta['path'])
                    if os.path.exists(file_to_delete):
                        os.remove(file_to_delete)
                        logging.info(f"  - 已删除物理文件: {file_to_delete}")

                # 3. 从元数据文件删除记录
                if self.group_manager.remove_file_meta(group_id, file_id):
                    logging.info(f"  - 已从元数据中删除 '{file_name}'。")

            except Exception as e:
                logging.error(f"删除文件 '{file_name}' (ID: {file_id}) 时发生严重错误: {e}", exc_info=True)
                all_success = False

        return all_success

    def delete_webpages_from_group(self, group_id: str, webpage_ids: List[str]) -> bool:
        """
        从一个组中彻底删除指定的网页。
        顺序: 向量数据库 -> 元数据
        """
        if not webpage_ids:
            return True

        logging.info(f"准备从组 '{group_id}' 删除 {len(webpage_ids)} 个网页...")
        all_success = True

        for page_id in webpage_ids:
            logging.info(f"正在删除网页 (ID: {page_id})...")
            try:
                # 1. 从ChromaDB删除节点
                self.chroma_collection.delete(where={"webpage_id": page_id})
                logging.info(f"  - 已从向量数据库删除网页 (ID: {page_id}) 的节点。")

                # 2. 从元数据文件删除记录
                if self.group_manager.remove_webpage_meta(group_id, page_id):
                    logging.info(f"  - 已从元数据中删除网页 (ID: {page_id})。")

            except Exception as e:
                logging.error(f"删除网页 (ID: {page_id}) 时发生严重错误: {e}", exc_info=True)
                all_success = False

        return all_success

    def chat(
        self, query_text: str, chat_history: List[Dict[str, str]], group_ids: Optional[List[str]] = None,
        agent_id: Optional[str] = None, enable_deep_thinking: bool = False, enable_web_search: bool = False,
        images: Optional[List[str]] = None, stream: bool = False
    ):
        """
        智能聊天，支持三种互斥的对话模式。

        Args:
            query_text: 用户提出的新问题。
            chat_history: 一个包含过去消息的列表，格式为 [{'role': 'user'/'assistant', 'content': '...'}, ...]
            group_ids: 如果提供了则执行 RAG模式
            agent_id: 如果提供了则使用Agent的system prompt
            enable_deep_thinking: 是否启用深度思考功能
            enable_web_search: 是否启用网页搜索功能
            images: 图片base64数据列表（不包含data:前缀）
            stream: 是否启用流式响应

        Returns:
            一个包含答案和源节点的响应对象，或者流式生成器（如果stream=True）。
        """
        # 智能路由逻辑：三种互斥的对话模式

        # 如果启用流式，调用流式版本
        if stream:
            return self._chat_stream(
                query_text=query_text,
                chat_history=chat_history,
                group_ids=group_ids,
                agent_id=agent_id,
                enable_deep_thinking=enable_deep_thinking,
                enable_web_search=enable_web_search,
                images=images
            )

        # 模式1：联网搜索模式（优先级最高，因为前端已确保互斥）
        if enable_web_search:
            logging.info(f"使用联网搜索模式: '{query_text}'")
            try:
                answer = self.smart_chat_engine.chat_web_search_mode(
                    query_text=query_text,
                    chat_history=chat_history,
                    enable_deep_thinking=enable_deep_thinking,
                    agent_id=agent_id,
                    agent_manager=self.agent_manager,
                    images=images
                )
                # 创建一个简单的响应对象，模拟LlamaIndex的响应格式
                class SimpleResponse:
                    def __init__(self, answer):
                        self.response = answer
                        self.source_nodes = []  # 联网模式暂时不返回source_nodes

                    def __str__(self):
                        return self.response

                return SimpleResponse(answer)
            except Exception as e:
                logging.error(f"联网搜索模式失败，回退到普通模式: {e}")
                # 回退到普通模式
                answer = self.smart_chat_engine.chat_normal_mode(
                    query_text=query_text,
                    chat_history=chat_history,
                    enable_deep_thinking=enable_deep_thinking,
                    agent_id=agent_id,
                    agent_manager=self.agent_manager,
                    images=images
                )
                class SimpleResponse:
                    def __init__(self, answer):
                        self.response = answer
                        self.source_nodes = []

                    def __str__(self):
                        return self.response

                return SimpleResponse(answer)

        # 模式2：RAG模式
        elif group_ids and len(group_ids) > 0:
            logging.info(f"使用RAG模式，组: {group_ids}, 查询: '{query_text}'")
            # 使用原有的RAG逻辑
            system_prompt = self._get_system_prompt(agent_id, group_ids)

            llama_chat_history = [
                ChatMessage(role=msg["role"], content=msg["content"])
                for msg in chat_history
            ]
            memory = ChatMemoryBuffer.from_defaults(chat_history=llama_chat_history)

            filters = MetadataFilters(
                filters=[
                    ExactMatchFilter(key="group_id", value=gid) for gid in group_ids
                ],
                condition=FilterCondition.OR,
            )
            chat_engine = self.index.as_chat_engine(
                chat_mode="context",
                memory=memory,
                retriever_kwargs={
                    "filters": filters,
                    "similarity_top_k": self.config.SIMILARITY_TOP_K,
                },
                system_prompt=system_prompt,
            )
            response = chat_engine.chat(query_text)
            return response

        # 模式3：普通模式（默认）
        else:
            logging.info(f"使用普通模式: '{query_text}'")
            answer = self.smart_chat_engine.chat_normal_mode(
                query_text=query_text,
                chat_history=chat_history,
                enable_deep_thinking=enable_deep_thinking,
                agent_id=agent_id,
                agent_manager=self.agent_manager,
                images=images
            )

            class SimpleResponse:
                def __init__(self, answer):
                    self.response = answer
                    self.source_nodes = []

                def __str__(self):
                    return self.response

            return SimpleResponse(answer)
        return response

    def _chat_stream(
        self, query_text: str, chat_history: List[Dict[str, str]], group_ids: Optional[List[str]] = None,
        agent_id: Optional[str] = None, enable_deep_thinking: bool = False, enable_web_search: bool = False,
        images: Optional[List[str]] = None
    ):
        """
        流式聊天实现，支持三种互斥的对话模式。

        Args:
            query_text: 用户提出的新问题。
            chat_history: 聊天历史
            group_ids: 知识库组ID列表
            agent_id: Agent ID
            enable_deep_thinking: 是否启用深度思考功能
            enable_web_search: 是否启用网页搜索功能

        Yields:
            流式响应数据
        """
        # 模式1：联网搜索模式（优先级最高）
        if enable_web_search:
            logging.info(f"使用联网搜索模式（流式）: '{query_text}'")
            try:
                for chunk in self.smart_chat_engine.chat_web_search_mode_stream(
                    query_text=query_text,
                    chat_history=chat_history,
                    enable_deep_thinking=enable_deep_thinking,
                    agent_id=agent_id,
                    agent_manager=self.agent_manager,
                    images=images
                ):
                    yield chunk
                return
            except Exception as e:
                logging.error(f"联网搜索模式流式失败，回退到普通模式: {e}")
                # 回退到普通模式流式
                for chunk in self.smart_chat_engine.chat_normal_mode_stream(
                    query_text=query_text,
                    chat_history=chat_history,
                    enable_deep_thinking=enable_deep_thinking,
                    agent_id=agent_id,
                    agent_manager=self.agent_manager,
                    images=images
                ):
                    yield chunk
                return

        # 模式2：RAG模式
        elif group_ids and len(group_ids) > 0:
            logging.info(f"使用RAG模式（流式），组: {group_ids}, 查询: '{query_text}'")
            # 对于RAG模式，llama-index可能不支持流式，我们使用模拟流式
            # 先获取完整响应，然后模拟流式输出
            try:
                system_prompt = self._get_system_prompt(agent_id, group_ids)

                from llama_index.core.memory import ChatMemoryBuffer
                from llama_index.core.llms import ChatMessage
                from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter, FilterCondition

                llama_chat_history = [
                    ChatMessage(role=msg["role"], content=msg["content"])
                    for msg in chat_history
                ]
                memory = ChatMemoryBuffer.from_defaults(chat_history=llama_chat_history)

                filters = MetadataFilters(
                    filters=[
                        ExactMatchFilter(key="group_id", value=gid) for gid in group_ids
                    ],
                    condition=FilterCondition.OR,
                )

                # 尝试使用流式chat_engine
                chat_engine = self.index.as_chat_engine(
                    chat_mode="context",
                    memory=memory,
                    retriever_kwargs={
                        "filters": filters,
                        "similarity_top_k": self.config.SIMILARITY_TOP_K,
                    },
                    system_prompt=system_prompt,
                )

                # 对于RAG模式，我们先获取完整响应，然后模拟流式输出
                # 这样可以确保sources信息的正确性
                response = chat_engine.chat(query_text)
                answer = str(response)

                # 模拟流式输出：按词输出，提供更好的用户体验
                words = answer.split()
                for i, word in enumerate(words):
                    if i == 0:
                        yield word
                    else:
                        yield " " + word
                    # 适当的延迟，模拟真实的流式体验
                    import time
                    time.sleep(0.05)
                return

            except Exception as e:
                logging.error(f"RAG模式流式失败，回退到普通模式: {e}")
                # 回退到普通模式流式
                for chunk in self.smart_chat_engine.chat_normal_mode_stream(
                    query_text=query_text,
                    chat_history=chat_history,
                    enable_deep_thinking=enable_deep_thinking,
                    agent_id=agent_id,
                    agent_manager=self.agent_manager,
                    images=images
                ):
                    yield chunk
                return

        # 模式3：普通模式（默认）
        else:
            logging.info(f"使用普通模式（流式）: '{query_text}'")
            for chunk in self.smart_chat_engine.chat_normal_mode_stream(
                query_text=query_text,
                chat_history=chat_history,
                enable_deep_thinking=enable_deep_thinking,
                agent_id=agent_id,
                agent_manager=self.agent_manager,
                images=images
            ):
                yield chunk

    def _get_system_prompt(self, agent_id: Optional[str], group_ids: Optional[List[str]]) -> str:
        """
        根据Agent ID和知识库组ID确定要使用的system prompt。

        Args:
            agent_id: Agent ID
            group_ids: 知识库组ID列表

        Returns:
            要使用的system prompt字符串
        """
        # 如果有Agent，优先使用Agent的system prompt
        if agent_id:
            agent = self.agent_manager.get_agent_by_id(agent_id)
            if agent:
                return agent["system_prompt"]

        # 如果有知识库组，使用RAG的system prompt
        if group_ids:
            return self._get_rag_system_prompt(group_ids)

        # 否则使用默认的system prompt
        return self.config.SYSTEM_PROMPT

    def _get_rag_system_prompt(self, group_ids: List[str]) -> str:
        """
        为RAG生成专用的system prompt，包含知识库信息。

        Args:
            group_ids: 知识库组ID列表

        Returns:
            RAG专用的system prompt
        """
        # 收集知识库中的文档和网页信息
        documents = []
        webpages = []

        for group_id in group_ids:
            group = self.group_manager.get_group_by_id(group_id)
            if group:
                # 收集文档名称
                for file_meta in group.get("files", []):
                    if file_meta.get("status") == "completed":
                        documents.append(file_meta.get("name", "未知文档"))

                # 收集网页URL
                for webpage_meta in group.get("webpages", []):
                    if webpage_meta.get("status") == "completed":
                        webpages.append(webpage_meta.get("url", "未知网页"))

        # 构建RAG system prompt
        rag_prompt = "[知识库中的文档]: \n"
        if documents:
            rag_prompt += "\n".join(f"- {doc}" for doc in documents)
        else:
            rag_prompt += "无"

        rag_prompt += "\n---\n\n[知识库中的网页]:\n"
        if webpages:
            rag_prompt += "\n".join(f"- {url}" for url in webpages)
        else:
            rag_prompt += "无"

        rag_prompt += """
---

[指令]:

**角色与核心任务 / Role & Core Task:**
你是一个名为“Astro Qwen”的大语言模型。你由先进的Qwen 3模型微调而来，专门为解答天文学和航天领域的事实性问题而设计。你的核心使命是成为一个专业、准确且引人入胜的太空知识助手。\n
而且你目前是文档分析助手，一个严谨AI。你的唯一任务是严格、忠实地根据上方 `[文档]` 部分提供的文本内容来回答用户的问题。

**行为准则 / Rules of Conduct:**

1.  **严守信息边界 (Strict Information Boundary):** 绝对禁止使用 `[文档]` 之外的任何背景知识、个人经验或互联网信息。你的知识被严格限定在所提供的文本内。

2.  **答案必须基于原文 (Answers Must Be Grounded in the Source):** 你的回答必须完全基于 `[文档]` 中的事实和陈述。为确保准确性，在回答时应尽可能引用原文的关键短语或句子来支持你的论点。

3.  **处理信息不存在的情况 (Handling Non-Existent Information):** 如果 `[文档]` 中完全没有包含回答问题所需的信息，你必须且只能回复一个标准答案："根据提供的文档，无法回答此问题。" 不要尝试猜测、编造或提供任何形式的推断性回答。

4.  **处理信息不完整的情况 (Handling Incomplete Information):** 如果 `[文档]` 包含部分相关信息但不足以形成一个完整的答案，你应该首先清晰地陈述文档中已有的事实，然后明确指出"关于...的更多细节，文档中未提供。"

5.  **保持客观中立 (Maintain Objectivity and Neutrality):** 以客观、中立、专业的语气回答问题，避免任何个人观点、主观评价或情感色彩。

6.  **遵循提问语言 (Follow the Question's Language):** 除非特别指示，否则请使用与用户提问相同的语言（例如，中文问题用中文回答）进行回答。

7.  **不要输出Markdown**：在回答中不要使用Markdown格式，直接输出纯文本内容。通过空行的方式分隔不同段落。
---
现在，请严格遵循以上所有指令，对用户的下一个提问进行回答。
"""

        return rag_prompt
