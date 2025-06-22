from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class GroupCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, description="组的唯一名称")
    description: str = Field("", description="组的可选描述")


class WebpagesAddRequest(BaseModel):
    urls: List[str] = Field(..., description="要添加到组的URL列表")


class FilesDeleteRequest(BaseModel):
    file_ids: List[str] = Field(..., description="要删除的文件的ID列表")


class WebpagesDeleteRequest(BaseModel):
    webpage_ids: List[str] = Field(..., description="要删除的网页的ID列表")


class QueryRequest(BaseModel):
    query: str = Field(..., description="用户提出的查询问题")
    group_ids: List[str] = Field(..., description="要在其中搜索的组ID列表")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatMessageRequest(BaseModel):
    message: str
    history: List[ChatMessage]
    group_ids: Optional[List[str]] = None


class FileMetadataModel(BaseModel):
    id: str
    name: str
    path: str
    creation_time: str
    size: int
    status: str


class WebpageMetadataModel(BaseModel):
    id: str
    url: str
    creation_time: str
    status: str


class SourceNodeModel(BaseModel):
    """用于API响应的源节点模型"""

    score: float
    group_id: str
    file_name: str
    page_label: str
    text_snippet: str

    @classmethod
    def from_source_node(cls, source_node):
        metadata = source_node.node.metadata
        return cls(
            score=source_node.score,
            group_id=metadata.get("group_id", "N/A"),
            file_name=metadata.get("file_name", "N/A"),
            page_label=metadata.get("page_label", "N/A"),
            text_snippet=source_node.node.get_text()[:250].strip() + "...",
        )


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceNodeModel]


class WebImportRequest(BaseModel):
    url: str
    group_id: Optional[str] = None  # 允许客户端指定组，否则使用默认组


class AskRequest(BaseModel):
    question: str
    # 兼容旧的 ask，可能没有 group_ids
    group_ids: Optional[List[str]] = None


class SourcesDeleteRequest(BaseModel):
    sources: List[str] = Field(
        ...,
        min_length=1,
        description="A list of source names (filenames or URLs) to delete.",
    )


class ChatMessageRequest(BaseModel):
    query_text: str = Field(..., min_length=1)
    group_ids: Optional[List[str]] = None


class GroupResponse(BaseModel):
    id: str
    name: str
    description: str
    files: List[FileMetadataModel]
    webpages: List[WebpageMetadataModel]


class ConversationCreationRequest(BaseModel):
    group_ids: Optional[List[str]] = Field(None, description="要关联的知识库组ID列表")


class MessagePostRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户发送的消息内容")
