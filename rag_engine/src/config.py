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
    LLM_MODEL_NAME: str = os.getenv("MODEL_NAME")
    TEMPERATURE: float = 1.0

    # --- Embedding Model 配置 ---
    EMBEDDING_API_KEY: str = os.getenv("EMBEDDING_API_KEY")
    EMBEDDING_MODEL_NAME: str = os.getenv(
        "EMBEDDING_MODEL_NAME", "text-embedding-ada-002"
    )
    EMBEDDING_API_BASE_URL: str = os.getenv("EMBEDDING_API_BASE_URL")

    # --- 节点解析 (Chunking) 配置 ---
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50

    # --- 多格式文档解析配置 ---
    USE_ADVANCED_PARSERS: bool = True
    MIN_CHUNK_LENGTH: int = 50
    MAX_FILE_SIZE_MB: int = 100

    # PDF解析配置
    PDF_USE_PDFPLUMBER: bool = True
    PDF_MIN_PAGE_TEXT_LENGTH: int = 50

    # DOCX解析配置
    DOCX_EXTRACT_TABLES: bool = True
    DOCX_CHUNK_BY_HEADING: bool = True
    DOCX_MIN_PARAGRAPH_LENGTH: int = 10

    # Excel解析配置
    EXCEL_MAX_ROWS_PER_CHUNK: int = 100
    EXCEL_INCLUDE_HEADERS: bool = True

    # PPTX解析配置
    PPTX_EXTRACT_NOTES: bool = True
    PPTX_EXTRACT_SLIDE_TITLES: bool = True

    # EPUB解析配置
    EPUB_CHUNK_BY_CHAPTER: bool = True
    EPUB_MIN_CHAPTER_LENGTH: int = 100

    # HTML解析配置
    HTML_CHUNK_BY_SECTIONS: bool = True
    HTML_MIN_SECTION_LENGTH: int = 50

    # Markdown解析配置
    MARKDOWN_CHUNK_BY_HEADERS: bool = True
    MARKDOWN_EXTRACT_FRONTMATTER: bool = True

    # 文本解析配置
    TEXT_DETECT_ENCODING: bool = True

    # --- 检索配置 ---
    SIMILARITY_TOP_K: int = 3

    # --- Prompt 模板 ---
    SYSTEM_PROMPT: str = (
        "你是一个名为“Astro Qwen”的大语言模型。你由先进的Qwen 3模型微调而来，专门为解答天文学和航天领域的事实性问题而设计。你的核心使命是成为一个专业、准确且引人入胜的太空知识助手。\n"
        "你也是一个专业的智能问答助手，擅长从提供的文档中查找信息并简洁准确地回答问题。\n"
        "如果文档中没有相关信息，请明确告知你无法从提供的文档中找到答案。\n"
        "始终使用中文回答。建议使用Markdown格式来组织回答内容，以提高可读性：\n"
        "- 使用标题(#, ##, ###)来组织内容结构\n"
        "- 使用列表来展示要点或步骤\n"
        "- 使用**粗体**强调重要信息\n"
        "- 使用*斜体*表示术语或概念\n"
        "- 使用代码块```来展示代码或公式\n"
        "- 使用引用块>来引用文献或重要说明\n"
        "- 使用表格来展示数据对比"
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
