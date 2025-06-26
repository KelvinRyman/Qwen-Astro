import logging
import hashlib
from typing import List, Dict, Optional
from pathlib import Path
from llama_index.core.schema import Document, BaseNode
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core import SimpleDirectoryReader
from llama_index.readers.web import BeautifulSoupWebReader

from .config import RAGConfig
from .document_parsers import ParserFactory, FormatDetector
from .document_parsers.parser_factory import parser_factory


class DataProcessor:
    """负责加载、处理和将文档转换为节点的类"""

    STABLE_METADATA_KEYS = ["file_name", "page_label", "file_id", "webpage_id", "source_url"]

    def __init__(self, config: RAGConfig):
        self.config = config
        self.node_parser = SimpleNodeParser.from_defaults(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
        )
        # 多格式文档解析器配置
        self.use_advanced_parsers = getattr(config, 'USE_ADVANCED_PARSERS', True)
        self.parser_config = {
            'chunk_size': config.CHUNK_SIZE,
            'chunk_overlap': config.CHUNK_OVERLAP,
            'min_chunk_length': getattr(config, 'MIN_CHUNK_LENGTH', 50)
        }
        logging.info(
            f"节点解析器已初始化 (chunk_size={config.CHUNK_SIZE}, chunk_overlap={config.CHUNK_OVERLAP})"
        )
        if self.use_advanced_parsers:
            logging.info("启用多格式文档解析器支持")

    @staticmethod
    def _clean_and_normalize(documents: List[Document]) -> List[Document]:
        """
        清理文档元数据并标准化文本内容。
        现在 group_id 也会被保留。
        """
        processed_docs = []
        # 将 group_id 添加到稳定元数据键中，确保它被保留
        keys_to_keep = DataProcessor.STABLE_METADATA_KEYS + ["group_id"]

        for doc in documents:
            new_metadata = {
                key: doc.metadata[key] for key in keys_to_keep if key in doc.metadata
            }
            normalized_text = " ".join(
                doc.text.replace("\r\n", "\n").replace("\r", "\n").split()
            )
            processed_docs.append(Document(text=normalized_text, metadata=new_metadata))

        processed_docs.sort(
            key=lambda x: str(x.metadata.get("group_id", ""))
            + str(x.metadata.get("file_name", ""))
            + str(x.metadata.get("page_label", ""))
        )
        logging.info("文档已清理、标准化并排序。")
        return processed_docs

    @staticmethod
    def _generate_stable_node_ids(nodes: List[BaseNode]) -> List[BaseNode]:
        """为每个节点生成一个基于内容和元数据（包括group_id）的确定性ID。"""
        for node in nodes:
            metadata_str = ",".join(
                f'"{k}":"{v}"' for k, v in sorted(node.metadata.items())
            )
            content_for_hash = f"{node.text}|{metadata_str}"
            node.id_ = hashlib.sha256(content_for_hash.encode("utf-8")).hexdigest()
        logging.info(f"已为 {len(nodes)} 个节点生成稳定的哈希ID。")
        return nodes

    def _load_from_web(self, webpage_meta: Dict, group_id: str) -> List[Document]:
        """从网页加载文档并附加 group_id 和 webpage_id 元数据。
        """
        url = webpage_meta["url"]
        try:
            loader = BeautifulSoupWebReader()
            documents = loader.load_data(urls=[url])

            for doc in documents:
                doc.metadata["source_url"] = url
                doc.metadata["file_name"] = url  # 使用 URL 作为文件名以保持一致性
                doc.metadata["group_id"] = group_id
                doc.metadata["webpage_id"] = webpage_meta["id"]

            logging.info(
                f"成功从 URL '{url}' 为组 '{group_id}' 加载了 {len(documents)} 份文档。"
            )
            return documents
        except Exception as e:
            logging.error(f"从 URL '{url}' 加载失败: {e}")
            return []

    def process_data(
        self,
        group_id: str,
        files_meta: Optional[List[Dict]] = None,
        webpages_meta: Optional[List[Dict]] = None,
    ) -> List[BaseNode]:
        """
        统一处理来自文件或URL的数据源。
        现在它接收元数据字典列表，而不是简单的路径或URL列表。
        """
        documents_with_group = []
        if files_meta:
            # 从文件元数据中提取物理路径
            file_paths = [meta["physical_path"] for meta in files_meta]
            # 加载文档
            loaded_docs = self._load_from_directory_files(file_paths, group_id)
            # 将 file_id 回填到每个文档的元数据中
            for doc in loaded_docs:
                # 找到这个文档对应的原始元数据
                original_meta = next(
                    (
                        meta
                        for meta in files_meta
                        if meta["name"] == doc.metadata.get("file_name")
                    ),
                    None,
                )
                if original_meta:
                    doc.metadata["file_id"] = original_meta["id"]
            documents_with_group.extend(loaded_docs)

        if webpages_meta:
            for meta in webpages_meta:
                documents_with_group.extend(self._load_from_web(meta, group_id))

        if not documents_with_group:
            return []

        cleaned_documents = self._clean_and_normalize(documents_with_group)
        base_nodes = self.node_parser.get_nodes_from_documents(
            cleaned_documents, include_metadata=True, include_prev_next_rel=False
        )
        stable_nodes = self._generate_stable_node_ids(base_nodes)
        logging.info(
            f"为组 '{group_id}' 处理数据完成，共生成 {len(stable_nodes)} 个节点。"
        )
        return stable_nodes

    def _load_from_directory_files(
        self, file_paths: List[str], group_id: str
    ) -> List[Document]:
        """从指定的文件路径列表加载文档。"""
        logging.info(
            f"正在从 {len(file_paths)} 个指定文件为组 '{group_id}' 加载文档..."
        )

        documents = []

        for file_path in file_paths:
            try:
                # 尝试使用高级解析器
                if self.use_advanced_parsers:
                    file_documents = self._load_file_with_advanced_parser(file_path, group_id)
                    if file_documents:
                        documents.extend(file_documents)
                        continue

                # 回退到SimpleDirectoryReader
                logging.info(f"使用SimpleDirectoryReader处理文件: {file_path}")
                fallback_docs = SimpleDirectoryReader(input_files=[file_path]).load_data()
                for doc in fallback_docs:
                    doc.metadata["group_id"] = group_id
                documents.extend(fallback_docs)

            except Exception as e:
                logging.error(f"加载文件 {file_path} 失败: {e}")
                continue

        logging.info(f"成功加载 {len(documents)} 个文档")
        return documents

    def _load_file_with_advanced_parser(self, file_path: str, group_id: str) -> Optional[List[Document]]:
        """使用高级解析器加载单个文件"""
        try:
            # 检测文件格式
            format_type = FormatDetector.detect_format(file_path)
            if not format_type:
                logging.debug(f"无法检测文件格式，跳过高级解析: {file_path}")
                return None

            # 创建解析器
            parser = parser_factory.create_parser(file_path, self.parser_config)
            if not parser:
                logging.debug(f"无法创建解析器，跳过高级解析: {file_path}")
                return None

            # 验证文件
            is_valid, error_msg = parser.validate_file(file_path)
            if not is_valid:
                logging.warning(f"文件验证失败: {error_msg}")
                return None

            logging.info(f"使用 {parser.get_parser_name()} 解析文件: {file_path}")

            # 提取文档分块
            chunks = parser.extract_chunks(file_path)
            if not chunks:
                logging.warning(f"未能从文件提取分块: {file_path}")
                return None

            # 转换为LlamaIndex Document对象
            documents = []
            for chunk in chunks:
                # 确保元数据包含group_id
                chunk.metadata["group_id"] = group_id

                # 创建Document对象
                doc = Document(
                    text=chunk.text,
                    metadata=chunk.metadata
                )
                documents.append(doc)

            logging.info(f"成功从 {file_path} 提取 {len(documents)} 个文档分块")
            return documents

        except Exception as e:
            logging.error(f"高级解析器处理文件失败 {file_path}: {e}")
            return None
