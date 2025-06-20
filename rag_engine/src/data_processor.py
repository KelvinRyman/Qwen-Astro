import logging
import hashlib
from typing import List
from llama_index.core.schema import Document, BaseNode
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core import SimpleDirectoryReader
from llama_index.readers.web import BeautifulSoupWebReader

from .config import RAGConfig


class DataProcessor:
    """负责加载、处理和将文档转换为节点的类"""

    STABLE_METADATA_KEYS = ["file_name", "page_label"]

    def __init__(self, config: RAGConfig):
        self.config = config
        self.node_parser = SimpleNodeParser.from_defaults(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
        )
        logging.info(
            f"节点解析器已初始化 (chunk_size={config.CHUNK_SIZE}, chunk_overlap={config.CHUNK_OVERLAP})"
        )

    # def _load_from_directory(
    #     self, directory_path: str, group_id: str
    # ) -> List[Document]:
    #     """
    #     从指定的目录加载所有文档，并为每个文档附加 group_id 元数据。
    #     """
    #     if not os.path.isdir(directory_path):
    #         logging.warning(f"目录 '{directory_path}' 不存在，无法加载文档。")
    #         return []

    #     logging.info(f"正在从目录 '{directory_path}' 为组 '{group_id}' 加载文档...")
    #     documents = SimpleDirectoryReader(
    #         input_dir=directory_path, recursive=True
    #     ).load_data()

    #     for doc in documents:
    #         doc.metadata["group_id"] = group_id

    #     logging.info(f"已为 {len(documents)} 份文档分配 group_id: '{group_id}'。")
    #     return documents

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

    # def process_directory(self, directory_path: str, group_id: str) -> List[BaseNode]:
    #     """
    #     执行针对特定目录和组的完整数据处理流程。
    #     """
    #     documents_with_group = self._load_from_directory(directory_path, group_id)
    #     if not documents_with_group:
    #         return []

    #     cleaned_documents = self._clean_and_normalize(documents_with_group)

    #     base_nodes = self.node_parser.get_nodes_from_documents(
    #         cleaned_documents, include_metadata=True, include_prev_next_rel=False
    #     )

    #     stable_nodes = self._generate_stable_node_ids(base_nodes)
    #     logging.info(
    #         f"为组 '{group_id}' 从目录处理完成，共生成 {len(stable_nodes)} 个节点。"
    #     )
    #     return stable_nodes

    def _load_from_web(self, url: str, group_id: str) -> List[Document]:
        """从网页加载文档并附加 group_id 元数据。

        Keyword arguments:
        url -- 网页的 URL
        group_id -- 文档的组 ID
        Return: 包含网页内容的文档列表
        """
        try:
            loader = BeautifulSoupWebReader()
            documents = loader.load_data(urls=[url])

            for doc in documents:
                # LlamaIndex 加载器可能不提供有用的元数据，我们手动添加
                doc.metadata["source_url"] = url
                # 保持和文件处理的一致性，使用 URL 作为文件名
                doc.metadata["file_name"] = url  # 使用 URL 作为文件名以保持一致性
                doc.metadata["group_id"] = group_id

            logging.info(
                f"成功从 URL '{url}' 为组 '{group_id}' 加载了 {len(documents)} 份文档。"
            )
            return documents
        except Exception as e:
            logging.error(f"从 URL '{url}' 加载失败: {e}")
            return []

    def process_data(
        self, group_id: str, file_paths: List[str] = None, urls: List[str] = None
    ) -> List[BaseNode]:
        """
        统一处理来自文件或URL的数据源。
        """
        documents_with_group = []
        if file_paths:
            documents_with_group.extend(
                self._load_from_directory_files(file_paths, group_id)
            )
        if urls:
            for url in urls:
                documents_with_group.extend(self._load_from_web(url, group_id))

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
        # 原 DataProcessor.process_files 中的加载部分
        logging.info(
            f"正在从 {len(file_paths)} 个指定文件为组 '{group_id}' 加载文档..."
        )
        documents = SimpleDirectoryReader(input_files=file_paths).load_data()
        for doc in documents:
            doc.metadata["group_id"] = group_id
        return documents
