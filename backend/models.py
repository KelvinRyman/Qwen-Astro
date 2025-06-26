from pydantic import BaseModel, Field
from typing import Optional, List
import logging

# 获取 logger
logger = logging.getLogger(__name__)


class GroupCreateRequest(BaseModel):
    """创建知识库组的请求模型"""
    name: str = Field(..., min_length=1, description="组的唯一名称")
    description: str = Field("", description="组的可选描述")


class WebpagesAddRequest(BaseModel):
    """向知识库组添加网页的请求模型"""
    urls: List[str] = Field(..., description="要添加到组的URL列表")


class FilesDeleteRequest(BaseModel):
    """从知识库组删除文件的请求模型"""
    file_ids: List[str] = Field(..., description="要删除的文件的ID列表")


class WebpagesDeleteRequest(BaseModel):
    """从知识库组删除网页的请求模型"""
    webpage_ids: List[str] = Field(..., description="要删除的网页的ID列表")


class QueryRequest(BaseModel):
    """在知识库组中执行查询的请求模型"""
    query: str = Field(..., description="用户提出的查询问题")
    group_ids: List[str] = Field(..., description="要在其中搜索的组ID列表")


class ChatMessage(BaseModel):
    """聊天消息模型，用于表示用户或助手的单条消息"""
    role: str
    content: str


class LegacyChatMessageRequest(BaseModel):
    """旧版聊天消息请求模型，用于兼容旧版API"""
    message: str
    history: List[ChatMessage]
    group_ids: Optional[List[str]] = None


class FileMetadataModel(BaseModel):
    """文件元数据模型，用于API响应"""
    id: str
    name: str
    path: str
    creation_time: str
    size: int
    status: str


class WebpageMetadataModel(BaseModel):
    """网页元数据模型，用于API响应"""
    id: str
    url: str
    creation_time: str
    status: str


class SourceNodeModel(BaseModel):
    """用于API响应的源节点模型，表示检索到的知识片段"""
    id: str
    score: float
    group_id: str
    file_name: str
    page_label: str
    text_snippet: str
    source_type: str  # 新增：来源类型 ('file' | 'webpage')
    source_url: Optional[str] = None  # 新增：网页URL（仅网页类型）

    @classmethod
    def from_source_node(cls, source_node):
        # 获取节点对象，可能是不同类型的节点
        node = source_node.node

        # 获取元数据，确保即使没有元数据也能正常工作
        metadata = getattr(node, 'metadata', {}) or {}

        # 生成一个唯一ID，如果节点没有id属性，则使用hash值
        node_id = getattr(node, 'id', None)
        if node_id is None:
            # 使用节点内容的哈希作为ID
            node_id = f"text_node_{hash(node.get_text()[:100])}"

        # 安全地获取文本内容
        try:
            text_snippet = node.get_text()[:250].strip() + "..."
        except (AttributeError, Exception) as e:
            text_snippet = "无法提取文本内容"
            logger.warning(f"提取节点文本时出错: {e}")

        # 确定来源类型和URL - 基于metadata结构直接判断
        source_type = "file"  # 默认为文件类型
        source_url = None

        try:
            # 添加调试日志
            logger.info(f"开始类型识别，node_id: {node_id}")
            logger.info(f"metadata: {metadata}")

            # 方法1：检查source_url字段（网页类型的直接标识）
            source_url = metadata.get("source_url")
            if source_url:
                source_type = "webpage"
                logger.info(f"✅ 通过source_url识别为网页类型，URL: {source_url}")

            # 方法2：检查webpage_id字段（网页类型的备用标识）
            elif "webpage_id" in metadata:
                source_type = "webpage"
                # 尝试从file_name获取URL（网页的file_name通常是URL）
                file_name = metadata.get("file_name", "")
                if file_name.startswith(("http://", "https://")):
                    source_url = file_name
                logger.info(f"✅ 通过webpage_id识别为网页类型，URL: {source_url}")

            # 方法3：检查file_id字段或默认为文件类型
            elif "file_id" in metadata:
                source_type = "file"
                logger.info(f"✅ 通过file_id识别为文件类型")

            else:
                # 默认为文件类型
                source_type = "file"
                logger.info(f"✅ 默认识别为文件类型")

            logger.info(f"最终确定类型: {source_type}, URL: {source_url}")

        except Exception as e:
            logger.error(f"类型识别时出错: {e}")
            # 回退逻辑：检查metadata中的url字段
            source_url = metadata.get("url")
            source_type = "webpage" if source_url else "file"
            logger.info(f"回退到默认逻辑，类型: {source_type}, URL: {source_url}")

        return cls(
            id=node_id,
            score=source_node.score,
            group_id=metadata.get("group_id", "N/A"),
            file_name=metadata.get("file_name", "N/A"),
            page_label=metadata.get("page_label", "N/A"),
            text_snippet=text_snippet,
            source_type=source_type,
            source_url=source_url,
        )


class QueryResponse(BaseModel):
    """查询响应模型，包含回答和来源"""
    answer: str
    sources: List[SourceNodeModel]


class WebImportRequest(BaseModel):
    """导入网页到知识库的请求模型"""
    url: str
    group_id: Optional[str] = None  # 允许客户端指定组，否则使用默认组


class AskRequest(BaseModel):
    """旧版提问请求模型，用于兼容旧版API"""
    question: str
    # 兼容旧的 ask，可能没有 group_ids
    group_ids: Optional[List[str]] = None


class SourcesDeleteRequest(BaseModel):
    """删除知识源的请求模型"""
    sources: List[str] = Field(
        ...,
        min_length=1,
        description="A list of source names (filenames or URLs) to delete.",
    )


class ChatMessageRequest(BaseModel):
    """聊天消息请求模型，用于发送消息到会话"""
    query_text: str = Field(..., min_length=1, description="用户发送的消息内容")
    group_ids: Optional[List[str]] = None  # 如果提供，则使用RAG；否则使用普通聊天


class GroupResponse(BaseModel):
    """知识库组响应模型，包含组的详细信息"""
    id: str
    name: str
    description: str
    files: List[FileMetadataModel]
    webpages: List[WebpageMetadataModel]


class ConversationCreationRequest(BaseModel):
    """创建会话的请求模型"""
    group_ids: Optional[List[str]] = Field(None, description="要关联的知识库组ID列表")
    agent_id: Optional[str] = Field(None, description="要使用的Agent ID")


class MessagePostRequest(BaseModel):
    """发送消息到会话的请求模型"""
    message: str = Field(..., min_length=1, description="用户发送的消息内容")
    group_ids: Optional[List[str]] = None  # 如果提供，则使用RAG；否则使用普通聊天
    enable_deep_thinking: bool = Field(False, description="是否启用深度思考功能")
    enable_web_search: bool = Field(False, description="是否启用网页搜索功能")
    images: Optional[List[str]] = Field(None, description="图片base64数据列表（不包含data:前缀）")


class ConversationRenameRequest(BaseModel):
    """重命名会话的请求模型"""
    title: str = Field(..., description="对话的新标题")


class ConversationGroupsUpdateRequest(BaseModel):
    """更新会话关联的知识库组的请求模型"""
    group_ids: List[str] = Field(..., description="要关联的知识库组ID列表")


class AgentCreateRequest(BaseModel):
    """创建Agent的请求模型"""
    name: str = Field(..., min_length=1, description="Agent的名称")
    system_prompt: str = Field(..., min_length=1, description="Agent的系统提示词")
    description: Optional[str] = Field("", description="Agent的描述")
    enable_MCP: Optional[bool] = Field(False, description="是否启用MCP")
    tools: Optional[str] = Field("", description="Agent的工具配置")


class AgentUpdateRequest(BaseModel):
    """更新Agent的请求模型"""
    name: Optional[str] = Field(None, min_length=1, description="Agent的名称")
    system_prompt: Optional[str] = Field(None, min_length=1, description="Agent的系统提示词")
    description: Optional[str] = Field(None, description="Agent的描述")
    enable_MCP: Optional[bool] = Field(None, description="是否启用MCP")
    tools: Optional[str] = Field(None, description="Agent的工具配置")


class AgentResponse(BaseModel):
    """Agent响应模型"""
    id: str
    name: str
    system_prompt: str
    description: str
    enable_MCP: bool
    tools: str
    created_at: str


class MessagesDeleteRequest(BaseModel):
    """从会话中删除消息的请求模型"""
    from_index: int = Field(..., description="要删除的消息的起始索引（包含该索引）", ge=0)


class MessageRegenerateRequest(BaseModel):
    """重新生成会话中消息的请求模型"""
    from_message_index: int = Field(
        ...,
        description="要重新生成的助手消息的索引。将基于此消息之前的用户消息进行重新生成。",
        ge=1
    )
