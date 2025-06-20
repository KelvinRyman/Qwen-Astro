import logging
import chromadb
import chromadb.errors
from llama_index.core import Settings
from llama_index.core.prompts import PromptTemplate
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.embeddings.openai_like import OpenAILikeEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from .config import RAGConfig
from .utils import ensure_directory_exists


def setup_global_settings(config: RAGConfig):
    """配置 LlamaIndex 的全局设置"""
    # 1. 配置 LLM
    llm = GoogleGenAI(model=config.LLM_MODEL_NAME, api_key=config.LLM_API_KEY)
    Settings.llm = llm
    logging.info(f"大语言模型已配置: {Settings.llm.model}")

    # 2. 配置 Embedding Model
    embed_model = OpenAILikeEmbedding(
        model_name=config.EMBEDDING_MODEL_NAME,
        api_key=config.EMBEDDING_API_KEY,
        api_base=config.EMBEDDING_API_BASE_URL,
    )
    Settings.embed_model = embed_model
    logging.info(f"词嵌入模型已配置: {Settings.embed_model.model_name}")

    # 3. 配置 Prompts
    Settings.llm.system_prompt = config.SYSTEM_PROMPT
    Settings.text_qa_template = PromptTemplate(config.QA_TEMPLATE_STR)
    logging.info("大语言模型系统提示和问答模板已配置。")


def create_vector_store(
    config: RAGConfig,
) -> tuple[ChromaVectorStore, chromadb.Collection]:
    """创建并返回 ChromaDB 向量存储和集合"""
    ensure_directory_exists(config.CHROMA_PERSIST_PATH)

    db = chromadb.PersistentClient(path=config.CHROMA_PERSIST_PATH)

    try:
        chroma_collection = db.get_collection(config.CHROMA_COLLECTION_NAME)
        logging.info(f"已加载现有 ChromaDB 集合: '{config.CHROMA_COLLECTION_NAME}'")
    except chromadb.errors.NotFoundError:
        # chromadb 0.5.x use chromadb.errors.NotFoundError for not found
        chroma_collection = db.create_collection(config.CHROMA_COLLECTION_NAME)
        logging.info(f"已创建新的 ChromaDB 集合: '{config.CHROMA_COLLECTION_NAME}'")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    return vector_store, chroma_collection
