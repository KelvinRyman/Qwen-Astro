from pydantic import BaseModel, Field
from typing import Optional, List


class GroupCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, description="The unique name of the group.")
    description: Optional[str] = Field(
        "", description="A brief description of the group."
    )


class QueryRequest(BaseModel):
    query_text: str = Field(..., min_length=1, description="The user's question.")
    group_ids: List[str] = Field(
        ..., min_length=1, description="A list of group IDs to search within."
    )


class SourceNodeModel(BaseModel):
    score: float
    group_id: str
    file_name: str
    page_label: str
    text_snippet: str


class QueryResponse(BaseModel):
    answer: str
    source_nodes: List[SourceNodeModel]


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
