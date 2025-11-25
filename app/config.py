"""Configuration helpers for the FastAPI RAG service."""

from functools import lru_cache
from typing import Literal, Optional

from pydantic import BaseModel, Field, validator

DEFAULT_SILICONFLOW_API_KEY = "sk-wjrtizmtakyahakiovtuqynxrvzaafpcbrxddfdlutaglfhj"
DEFAULT_SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"
DEFAULT_SILICONFLOW_TIMEOUT = 30.0

DEFAULT_MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9
DEFAULT_MAX_TOKENS = 1024
DEFAULT_STREAM = False

DEFAULT_RAG_URL = "http://localhost:8000/search/docs"
DEFAULT_RAG_TIMEOUT = 15.0
DEFAULT_RAG_TOP_K = 5
DEFAULT_RAG_USE_RERANK = True
DEFAULT_RAG_RERANK_MODE = "cross"
DEFAULT_RAG_RERANK_TOP_K: Optional[int] = None

DEFAULT_REWRITER_ENABLED = True
DEFAULT_REWRITER_MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_REWRITER_TEMPERATURE = 0.1
DEFAULT_REWRITER_TOP_P = 0.9
DEFAULT_REWRITER_MAX_TOKENS = 128


class ModelConfig(BaseModel):
    """Model-specific generation parameters."""

    model_name: str = Field(default=DEFAULT_MODEL_NAME)
    temperature: float = Field(default=DEFAULT_TEMPERATURE, ge=0.0, le=2.0)
    top_p: float = Field(default=DEFAULT_TOP_P, gt=0.0, le=1.0)
    max_tokens: int = Field(default=DEFAULT_MAX_TOKENS, gt=0)
    stream: bool = Field(default=DEFAULT_STREAM)


class RetrievalConfig(BaseModel):
    """Settings for calling the external RAG retriever service."""

    url: str = Field(default=DEFAULT_RAG_URL)
    timeout: float = Field(default=DEFAULT_RAG_TIMEOUT, gt=0)
    top_k: int = Field(default=DEFAULT_RAG_TOP_K, ge=1, le=50)
    use_rerank: bool = Field(default=DEFAULT_RAG_USE_RERANK)
    rerank_mode: Literal["cross", "bi"] = Field(default=DEFAULT_RAG_RERANK_MODE)
    rerank_top_k: Optional[int] = Field(
        default=DEFAULT_RAG_RERANK_TOP_K,
        ge=1,
        le=50,
        description="Optional override for reranker output size",
    )


class RewriterConfig(BaseModel):
    """Settings for rewriting user queries before retrieval."""

    enabled: bool = Field(default=DEFAULT_REWRITER_ENABLED)
    model_name: str = Field(default=DEFAULT_REWRITER_MODEL_NAME)
    temperature: float = Field(default=DEFAULT_REWRITER_TEMPERATURE, ge=0.0, le=2.0)
    top_p: float = Field(default=DEFAULT_REWRITER_TOP_P, gt=0.0, le=1.0)
    max_tokens: int = Field(default=DEFAULT_REWRITER_MAX_TOKENS, gt=0)


class Settings(BaseModel):
    """Service-level configuration loaded from environment variables."""

    api_key: str = Field(default=DEFAULT_SILICONFLOW_API_KEY)
    base_url: str = Field(default=DEFAULT_SILICONFLOW_BASE_URL)
    timeout: float = Field(default=DEFAULT_SILICONFLOW_TIMEOUT, gt=0)
    model: ModelConfig = Field(default_factory=ModelConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    rewriter: RewriterConfig = Field(default_factory=RewriterConfig)

    @validator("api_key", pre=True, always=True)
    def strip_api_key(cls, value: str) -> str:  # pylint: disable=no-self-argument
        return (value or "").strip()

    def require_api_key(self) -> str:
        """Return the API key or raise if it's missing."""
        if not self.api_key:
            raise RuntimeError(
                "SILICONFLOW_API_KEY is not set. Export it before starting the service."
            )
        return self.api_key


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Provide a cached Settings instance."""
    return Settings()
