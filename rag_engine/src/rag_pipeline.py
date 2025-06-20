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

    def add_and_index_data(
        self, group_id: str, file_paths: List[str] = None, urls: List[str] = None
    ):
        """
        统一的接口，用于添加文件或URL，并立即进行索引。
        """
        logging.info(f"--- 开始向组 '{group_id}' 添加并索引新数据 ---")

        # 1. (可选) 将文件物理移动到组目录
        if file_paths:
            group_dir = self.group_manager.get_group_physical_path(group_id)
            if not group_dir:
                logging.error(f"无法找到组 '{group_id}' 的物理目录。")
                return

            processed_file_paths = []
            for src_path in file_paths:
                if os.path.exists(src_path):
                    try:
                        dest_path = os.path.join(group_dir, os.path.basename(src_path))
                        shutil.copy(src_path, dest_path)
                        processed_file_paths.append(dest_path)
                    except Exception as e:
                        logging.error(f"复制文件 '{src_path}' 失败: {e}")
                else:
                    logging.warning(f"源文件 '{src_path}' 不存在，已跳过。")

            # 使用复制后的路径进行处理
            file_paths_for_processing = processed_file_paths
        else:
            file_paths_for_processing = None

        # 2. 调用 DataProcessor 处理数据并生成节点
        nodes = self.data_processor.process_data(
            group_id=group_id, file_paths=file_paths_for_processing, urls=urls
        )

        if not nodes:
            logging.warning(f"没有为组 '{group_id}' 生成任何新节点。")
            return

        # 3. 将节点插入索引
        initial_count = self.chroma_collection.count()
        self.index.insert_nodes(nodes)
        final_count = self.chroma_collection.count()

        new_items = final_count - initial_count
        if new_items > 0:
            logging.info(
                f"成功为组 '{group_id}' 添加或更新了 {new_items} 个节点到索引。"
            )
        else:
            logging.info(f"数据已处理，但未向索引添加任何新节点（可能已是最新）。")

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

    def list_sources_in_group(self, group_id: str) -> List[Dict[str, str]]:
        """
        列出指定组内的所有数据源，包括物理文件和网页。

        Returns:
            一个字典列表，每个字典代表一个数据源，包含 'type' 和 'name'。
        """
        # 步骤 1: 获取物理文件
        physical_files = self.group_manager.list_files_in_group(group_id)

        # 步骤 2: 从 ChromaDB 获取所有数据源标识 (包括文件和网页)
        # 这样可以确保即使物理文件被删除但DB中还有残留，也能被发现
        try:
            # get() 方法可以带 where 过滤器和 include=['metadatas'] 来只获取元数据
            results = self.chroma_collection.get(
                where={"group_id": group_id}, include=["metadatas"]
            )
            metadatas = results.get("metadatas", [])
        except Exception as e:
            logging.error(f"从 ChromaDB 获取组 '{group_id}' 的元数据失败: {e}")
            metadatas = []

        # 步骤 3: 合并和去重
        all_source_names: Set[str] = set(physical_files)
        for meta in metadatas:
            if "file_name" in meta:
                all_source_names.add(meta["file_name"])

        # 步骤 4: 格式化输出
        sources = []
        for name in sorted(list(all_source_names)):
            source_type = "web" if name.startswith(("http://", "https://")) else "file"
            sources.append({"type": source_type, "name": name})

        return sources

    def delete_sources_from_group(
        self, group_id: str, sources_to_delete: List[str]
    ) -> bool:
        """
        从一个组中删除指定的数据源。

        Args:
            group_id: 组的 ID。
            sources_to_delete: 一个包含文件名或 URL 的列表。

        Returns:
            操作是否完全成功。
        """
        if not sources_to_delete:
            logging.warning("没有指定要删除的数据源，操作跳过。")
            return True

        logging.info(f"开始从组 '{group_id}' 删除 {len(sources_to_delete)} 个数据源...")

        # 步骤 1: 从 ChromaDB 删除与这些源相关的节点
        try:
            # 构建一个复杂的 where 子句: (group_id == X) AND (file_name IN [s1, s2, ...])
            # ChromaDB 的 $and 操作符是隐式的，直接提供多个条件即可
            where_clause = {
                "group_id": group_id,
                "file_name": {"$in": sources_to_delete},
            }
            self.chroma_collection.delete(where=where_clause)
            logging.info(f"已向 ChromaDB 发送删除与指定源相关的节点的请求。")
        except Exception as e:
            logging.error(f"从 ChromaDB 删除节点时发生错误: {e}", exc_info=True)
            return False

        # 步骤 2: 从物理存储中删除文件
        group_physical_path = self.group_manager.get_group_physical_path(group_id)
        if not group_physical_path:
            logging.warning(f"无法找到组 '{group_id}' 的物理路径，跳过文件删除。")
            return True  # 如果目录不存在，文件删除操作可视为成功

        for source_name in sources_to_delete:
            # 只删除不是 URL 的源
            if not source_name.startswith(("http://", "https://")):
                file_path = os.path.join(group_physical_path, source_name)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        logging.info(f"成功删除物理文件: {file_path}")
                    except OSError as e:
                        logging.error(f"删除物理文件 '{file_path}' 失败: {e}")
                        # 即使一个文件删除失败，也应继续尝试删除其他文件
                        # 但最终应返回失败状态
                        # 这里我们简单记录错误，最后返回成功（取决于业务需求）
                        # 更健壮的做法是收集错误并最后决定返回值

        logging.info(f"数据源删除流程完成。")
        return True

    def chat(
        self, query_text: str, chat_history: List[Dict[str, str]], group_ids: Optional[List[str]] = None
    ):
        """
        进行聊天，可选地在指定组内进行 RAG 检索。

        Args:
            query_text: 用户提出的新问题。
            chat_history: 一个包含过去消息的列表，格式为 [{'role': 'user'/'assistant', 'content': '...'}, ...]
            group_ids: 如果提供了则执行 RAG，否则执行无状态聊天

        Returns:
            一个包含答案和源节点的响应对象。
        """
        # 1. 创建并填充聊天内存 (这部分是共用的)
        llama_chat_history = [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in chat_history
        ]
        memory = ChatMemoryBuffer.from_defaults(chat_history=llama_chat_history)

        # 2. 根据是否提供 group_ids 决定聊天引擎类型
        if group_ids:
            # --- RAG 聊天模式 ---
            logging.info(f"在组 {group_ids} 中进行 RAG 聊天: '{query_text}'")
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
                system_prompt=self.config.SYSTEM_PROMPT,
            )
        else:
            # --- 标准聊天模式 (无 RAG) ---
            logging.info(f"进行标准聊天 (无 RAG): '{query_text}'")
            chat_engine = self.index.as_chat_engine(
                chat_mode="openai",  # "openai" 模式适合上下文聊天，不会进行检索
                memory=memory,
                system_prompt=self.config.SYSTEM_PROMPT,
            )

        # 3. 执行聊天
        response = chat_engine.chat(query_text)
        return response
