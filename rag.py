import os
import chromadb

import logging
import sys
import hashlib

# 设置 LlamaIndex 和相关库的日志级别为 INFO
# 确保所有日志都输出到 stdout
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logging.info("日志系统已启动 (信息级别)。")

# 导入 LlamaIndex 核心模块和必要组件
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
)
from llama_index.core.node_parser import SimpleNodeParser

# 硅基流动嵌入模型
from llama_index.embeddings.openai_like import OpenAILikeEmbedding

# from llama_index.embeddings.dashscope import DashScopeEmbedding
# Gemini 大语言模型
from llama_index.llms.google_genai import GoogleGenAI

# from llama_index.llms.dashscope import DashScope
from llama_index.core.prompts import PromptTemplate
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.schema import Document

# 导入用于加载环境变量的库
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()
# --- ChromaDB 配置 ---
CHROMA_PERSIST_PATH = "./my_chroma_data"
collection_name = "my_rag_collection"
# --- API 配置 ---
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME")
EMBEDDING_API_BASE_URL = os.getenv("EMBEDDING_API_BASE_URL")


if not os.path.exists(CHROMA_PERSIST_PATH):
    os.makedirs(CHROMA_PERSIST_PATH)
    logging.info(f"已创建 ChromaDB 数据目录: {CHROMA_PERSIST_PATH}")
else:
    logging.info(f"ChromaDB 数据目录已存在: {CHROMA_PERSIST_PATH}")

chromadb_client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)

try:
    chroma_collection = chromadb_client.get_collection(collection_name)
    logging.info(f"已加载现有 ChromaDB 集合: '{collection_name}'。")
except chromadb.errors.NotFoundError:
    chroma_collection = chromadb_client.create_collection(collection_name)
    logging.info(f"已创建新的 ChromaDB 集合: '{collection_name}'。")

initial_chroma_count = chroma_collection.count()
logging.info(
    f"ChromaDB 集合 '{collection_name}' 初始包含项目数: {initial_chroma_count}"
)

vector_stores = ChromaVectorStore(chroma_collection)

# --- 配置 API 词嵌入模型 ---
embed_model = OpenAILikeEmbedding(
    model_name=EMBEDDING_MODEL_NAME,  # 从环境变量获取模型名称，提供默认值
    api_key=EMBEDDING_API_KEY,
    api_base=EMBEDDING_API_BASE_URL,  # 从环境变量获取 API 基础 URL
)
Settings.embed_model = embed_model
logging.info(f"词嵌入模型已配置: {Settings.embed_model.model_name}")

# --- 配置 API 大语言模型 ---
llm = GoogleGenAI(
    model=MODEL_NAME,  # 从环境变量获取模型名称，提供默认值
    api_key=API_KEY,
)
Settings.llm = llm
logging.info(f"大语言模型已配置: {Settings.llm.model}")

# --- 配置 LLM 的提示词 (Prompt Engineering) ---
Settings.llm.system_prompt = (
    "你是一个名为“Astro Qwen”的大语言模型。你由先进的Qwen 3模型微调而来，专门为解答天文学和航天领域的事实性问题而设计。你的核心使命是成为一个专业、准确且引人入胜的太空知识助手。\n"
    "你也是一个专业的智能问答助手，擅长从提供的文档中查找信息并简洁准确地回答问题。\n"
    "如果文档中没有相关信息，请明确告知你无法从提供的文档中找到答案。\n"
    "始终使用中文回答。建议使用Markdown格式来组织回答内容，以提高可读性：\n"
    "- 使用标题(#, ##, ###)来组织内容结构\n"
    "- 使用列表来展示要点或步骤\n"
    "- 使用**粗体**强调重要信息\n"
    "- 使用*斜体*表示术语或概念\n"
    "- 使用代码块```来展示代码或公式\n"
    "- 使用引用块>来引用文献或重要说明"
)
qa_tmpl_str = (
    "以下是上下文信息：\n"
    "------------\n"
    "{context_str}\n"
    "------------\n"
    "请根据以上上下文信息，简洁、准确地回答以下问题：\n"
    "{query_str}\n"
    "如果上下文信息不包含足够回答问题的内容，请说明你无法从提供的文档中找到相关信息。\n"
    "回答请以中文进行。"
)
qa_template = PromptTemplate(qa_tmpl_str)
Settings.text_qa_template = qa_template
logging.info("大语言模型系统提示和问答模板已配置。")

# --- 数据加载和索引创建 ---
logging.info("\n--- 文档处理与节点生成 ---")
logging.info("步骤 1: 正在从 'data' 目录加载原始文档...")
documents = SimpleDirectoryReader(r"data").load_data()
logging.info(f"已加载 {len(documents)} 份原始文档。")

# 定义要保留的稳定元数据键
STABLE_METADATA_KEYS = ["file_name", "page_label"]

processed_documents = []
for doc in documents:
    new_metadata = {}
    for key in STABLE_METADATA_KEYS:
        if key in doc.metadata:
            new_metadata[key] = doc.metadata[key]

    # 强制文本标准化
    normalized_text = doc.text.replace("\r\n", "\n").replace("\r", "\n")
    normalized_text = " ".join(normalized_text.split())

    processed_documents.append(Document(text=normalized_text, metadata=new_metadata))

logging.info(f"已清理文档元数据并标准化文本内容。")

# 确保文档处理顺序的稳定性
processed_documents.sort(
    key=lambda x: x.metadata.get("file_name", "")
    + str(x.metadata.get("page_label", ""))
)
logging.info("文档已根据文件名称和页码进行排序。")

# *** RAG 配置点 1: 节点解析 (Chunking) ***
logging.info("步骤 2: 正在将文档解析为节点 (分块)...")
node_parser = SimpleNodeParser.from_defaults(
    chunk_size=512,
    chunk_overlap=50,
)
base_nodes = node_parser.get_nodes_from_documents(
    processed_documents,
    include_metadata=True,
    include_prev_next_rel=False,  # 关闭节点间关系以增强ID稳定性
)

# --- 手动为每个节点生成确定性的 ID ---
stable_nodes_with_ids = []
for node in base_nodes:
    # 拼接文本和元数据，用于生成哈希
    metadata_str = ",".join(f'"{k}":"{v}"' for k, v in sorted(node.metadata.items()))
    content_for_hash = f"{node.text}|{metadata_str}"

    # 使用 SHA256 哈希确保确定性
    node.id_ = hashlib.sha256(content_for_hash.encode("utf-8")).hexdigest()
    stable_nodes_with_ids.append(node)
base = stable_nodes_with_ids

logging.info(f"文档已解析为 {len(base)} 个节点，并已生成稳定节点ID。")

logging.info("\n--- 向量存储索引管理 ---")
logging.info("步骤 3: 正在创建/加载向量存储索引...")

try:
    storage_context = StorageContext.from_defaults(vector_store=vector_stores)

    index = VectorStoreIndex(
        nodes=base, storage_context=storage_context, embed_model=Settings.embed_model
    )
    logging.info("向量存储索引创建/加载过程完成。")

    final_chroma_count = chroma_collection.count()
    logging.info(
        f"ChromaDB 集合 '{collection_name}' 最终包含项目数: {final_chroma_count}"
    )

    if final_chroma_count > initial_chroma_count:
        logging.info(
            f"--- 检测到新数据！ {final_chroma_count - initial_chroma_count} 个新节点已嵌入并添加到向量数据库中。 ---"
        )
        logging.info("这表示为新节点调用了DashScope嵌入API。")
    elif final_chroma_count == initial_chroma_count and initial_chroma_count > 0:
        logging.info("--- 未检测到新数据。索引已成功从现有向量数据库中加载。 ---")
        logging.info("现有节点未调用DashScope嵌入API。数据已从磁盘加载。")
    else:
        if len(base) > 0 and final_chroma_count == 0:
            logging.error(
                "尽管文档已解析为节点，但没有项目被添加到向量数据库中。这可能表示在嵌入或存储过程中发生静默失败。请检查日志获取详细错误信息。"
            )
            print(
                "\n--- 错误：索引创建失败，没有数据添加到向量数据库！请查看上方日志。 ---"
            )
            sys.exit(1)
        elif len(base) == 0 and initial_chroma_count == 0 and final_chroma_count == 0:
            logging.warning(
                "没有文档被处理或没有节点添加到向量数据库（可能'data'目录为空）。"
            )
        else:
            logging.info("--- 索引已加载，且没有新节点需要处理。 ---")

    logging.info("向量存储索引已准备就绪。")

except Exception as e:
    logging.error(f"在创建向量存储索引时发生意外错误: {e}", exc_info=True)
    print("\n--- 错误：向量存储索引创建失败！请检查日志获取详细信息。 ---")
    sys.exit(1)

logging.info("\n--- 查询引擎配置 ---")
query_engine = index.as_query_engine(
    similarity_top_k=3
    )
logging.info(
    f"查询引擎已配置为检索最相似的 {query_engine.retriever.similarity_top_k} 个节点。"
)


def run_local_query_loop():
    logging.info("\n进入本地调试模式。输入 'exit' 或 'quit' 退出。")
    while True:
        user_prompt = input("\n请输入你的问题 (或输入 'exit' 退出): ")
        if user_prompt.lower() in ["exit", "quit"]:
            logging.info("退出本地调试模式。")
            break

        logging.info(f"正在处理问题: {user_prompt}")
        response = query_engine.query(user_prompt)

        print("\n--- LLM 生成的答案 ---")
        print(str(response))

        if hasattr(response, "source_nodes") and response.source_nodes:
            print("\n--- RAG 检索到的相关文档片段 ---")
            for i, node_with_score in enumerate(response.source_nodes):
                print(f"片段 {i + 1} (分数: {node_with_score.score:.2f}):")
                file_name = node_with_score.node.metadata.get("file_name", "未知文件")
                page_label = node_with_score.node.metadata.get("page_label", "N/A")
                print(f"  来源: {file_name} (页码: {page_label})")
                print(f"  内容: {node_with_score.node.text[:200]}...")
                print("-" * 30)
            print("\n提示: 这是基于RAG模型生成的答案，并利用了以上片段。")
        else:
            print("\n提示: 未检索到直接相关的文档片段，答案可能基于模型自身的知识。")
        print("=" * 60)


if __name__ == "__main__":
    run_local_query_loop()
    # test_embedding_model(embed_model)
