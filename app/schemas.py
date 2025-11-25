"""Pydantic schemas for the FastAPI service."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class RetrievedDocument(BaseModel):
    """Document returned by the RAG retriever."""

    id: Optional[str] = Field(default=None, description="Identifier of the document in the index")
    title: Optional[str] = Field(default=None, description="Optional title of the document")
    content: str = Field(..., description="Content snippet for grounding the answer", min_length=1)
    score: Optional[float] = Field(default=None, description="Similarity score from the retriever")
    chunk_id: Optional[str] = Field(default=None, description="Unique chunk identifier")
    chunk_type: Optional[str] = Field(default=None, description="Section label (描述/原料/做法等)")
    origin_id: Optional[str] = Field(default=None, description="Source record identifier")
    source_text: Optional[str] = Field(
        default=None,
        description="Human-readable reconstruction of the source recipe",
    )
    source: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Raw recipe payload for downstream inspection",
    )


class ChatRequest(BaseModel):
    """Incoming chat completion request from the client."""

    query: str = Field(..., min_length=1, description="End-user query text")
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=50,
        description="Override number of documents to retrieve (defaults to config)",
    )
    stream: bool = Field(
        default=False,
        description="When true, return Server-Sent Events for incremental output",
    )
    use_rerank: Optional[bool] = Field(
        default=None,
        description="Override config to enable/disable retriever rerank",
    )
    rerank_mode: Optional[Literal["cross", "bi"]] = Field(
        default=None,
        description="Override rerank mode when use_rerank is true",
    )
    rerank_top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=50,
        description="Override how many docs to keep after rerank",
    )


class Usage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class ChatResponse(BaseModel):
    """Normalized response returned to the caller."""

    answer: str = Field(..., description="Model generated answer")
    model: str = Field(..., description="Model identifier used to produce the answer")
    usage: Optional[Usage] = Field(default=None, description="Token usage stats returned by SiliconFlow")
    raw_response: Optional[Dict[str, Any]] = Field(
        default=None, description="Raw response payload for debugging purposes"
    )
    documents: List[RetrievedDocument] = Field(
        default_factory=list, description="Documents that grounded the final answer"
    )
