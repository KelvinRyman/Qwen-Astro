import os
from dataclasses import dataclass
from dotenv import load_dotenv

# 在模块加载时立即加载 .env 文件，确保环境变量可用
load_dotenv()


@dataclass(frozen=True)
class RAGConfig:
    """
    RAG 系统配置类。
    使用 dataclass 的 frozen=True 使配置对象不可变，防止在运行时意外修改。
    """

    # --- 路径配置 ---
    DATA_PATH: str = "data"
    CHROMA_PERSIST_PATH: str = "chroma_data"
    HISTORY_PATH: str = "history"
    HISTORY_COLLECTION_NAME: str = "rag_history_collection"

    # --- ChromaDB 配置 ---
    CHROMA_COLLECTION_NAME: str = "rag_collection"

    # --- 组管理配置 ---
    GROUP_META_FILE_PATH: str = os.path.join(DATA_PATH, "group_meta.json")

    # --- LLM 配置 ---
    LLM_API_KEY: str = os.getenv("API_KEY")
    LLM_MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-pro")

    # --- Embedding Model 配置 ---
    EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY")
    EMBEDDING_MODEL_NAME: str = os.getenv(
        "EMBEDDING_MODEL_NAME", "text-embedding-ada-002"
    )
    EMBEDDING_API_BASE_URL: str = os.getenv("EMBEDDING_API_BASE_URL")

    # --- 节点解析 (Chunking) 配置 ---
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50

    # --- 检索配置 ---
    SIMILARITY_TOP_K: int = 3

    # --- Prompt 模板 ---
    SYSTEM_PROMPT: str = (
        "你是一个专业的智能问答助手，擅长从提供的文档中查找信息并简洁准确地回答问题。\n"
        "如果文档中没有相关信息，请明确告知你无法从提供的文档中找到答案。\n"
        "始终使用中文回答。"
    )
    QA_TEMPLATE_STR: str = (
        "以下是上下文信息：\n"
        "------------\n"
        "{context_str}\n"
        "------------\n"
        "请根据以上上下文信息，简洁、准确地回答以下问题：\n"
        "{query_str}\n"
        "如果上下文信息不包含足够回答问题的内容，请说明你无法从提供的文档中找到相关信息。\n"
        "回答请以中文进行。"
    )


# 创建一个全局配置实例，方便其他模块导入和使用
config = RAGConfig()
