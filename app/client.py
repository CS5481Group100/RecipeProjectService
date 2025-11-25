"""HTTP clients for SiliconFlow completion API and the RAG retriever service."""

import json
import logging
import time
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from .config import Settings
from .prompt import build_rewriter_messages
from .schemas import RetrievedDocument


logger = logging.getLogger(__name__)


class SiliconFlowClient:
    """Thin async HTTP client for the SiliconFlow chat completion API."""

    def __init__(self, settings: Settings):
        self._settings = settings

    async def chat(
        self, messages: List[Dict[str, str]], *, stream: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Send a chat completion request and return the JSON response."""
        stream_flag = self._settings.model.stream if stream is None else stream
        payload: Dict[str, Any] = {
            "model": self._settings.model.model_name,
            "messages": messages,
            "temperature": self._settings.model.temperature,
            "top_p": self._settings.model.top_p,
            "max_tokens": self._settings.model.max_tokens,
            "stream": stream_flag,
        }
        headers = {
            "Authorization": f"Bearer {self._settings.require_api_key()}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=self._settings.timeout) as client:
            response = await client.post(
                self._settings.base_url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def rewrite_query(self, query: str) -> str:
        """Rewrite a user query using the configured rewriter settings."""
        cfg = self._settings.rewriter
        if not cfg.enabled:
            return query

        messages = build_rewriter_messages(query)
        payload: Dict[str, Any] = {
            "model": cfg.model_name,
            "messages": messages,
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
            "max_tokens": cfg.max_tokens,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self._settings.require_api_key()}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self._settings.timeout) as client:
            response = await client.post(
                self._settings.base_url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        choices = data.get("choices") or []
        if not choices:
            logger.warning("Query rewrite returned no choices; fallback to original query")
            return query
        message = choices[0].get("message") or {}
        content = (message.get("content") or "").strip()
        if not content:
            logger.warning("Query rewrite choice missing content; fallback to original query")
            return query
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        logger.info("%s\n%s\n%s", timestamp, query, content)
        # Extract the rewritten query from the content
        print(f"Full rewrite response content:\n {content}")
        content = content.split("<rewrite>")[-1].rsplit("</rewrite>", 1)[0].strip()
        print(f"Extracted rewritten query:\n {content}")
        return content

    async def stream_chat(
        self, messages: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion deltas as plain text chunks."""
        payload: Dict[str, Any] = {
            "model": self._settings.model.model_name,
            "messages": messages,
            "temperature": self._settings.model.temperature,
            "top_p": self._settings.model.top_p,
            "max_tokens": self._settings.model.max_tokens,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self._settings.require_api_key()}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                self._settings.base_url,
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:"):].strip()
                    if not data or data == "[DONE]":
                        if data == "[DONE]":
                            break
                        continue
                    try:
                        payload = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choice = (payload.get("choices") or [{}])[0]
                    delta = choice.get("delta") or {}
                    content = delta.get("content")
                    if content:
                        yield content


class RetrievalClient:
    """Async client for the vector-store RAG service."""

    def __init__(self, settings: Settings):
        self._settings = settings

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        use_rerank: Optional[bool] = None,
        rerank_mode: Optional[str] = None,
        rerank_top_k: Optional[int] = None,
    ) -> List[RetrievedDocument]:
        if not self._settings.retrieval.url:
            raise RuntimeError("RAG_API_URL is not configured")
        effective_top_k = top_k or self._settings.retrieval.top_k
        effective_use_rerank = (
            self._settings.retrieval.use_rerank if use_rerank is None else use_rerank
        )
        effective_rerank_mode = (
            (rerank_mode or self._settings.retrieval.rerank_mode)
            if (rerank_mode or self._settings.retrieval.rerank_mode)
            else None
        )
        if effective_rerank_mode:
            effective_rerank_mode = effective_rerank_mode.lower()
        effective_rerank_top_k = (
            rerank_top_k
            or self._settings.retrieval.rerank_top_k
            or effective_top_k
        )
        payload: Dict[str, Any] = {
            "query": query,
            "k": effective_top_k,
            "use_rerank": effective_use_rerank,
            "rerank_mode": effective_rerank_mode,
        }
        if effective_use_rerank and effective_rerank_top_k:
            payload["rerank_top_k"] = effective_rerank_top_k

        logger.info(
            "Retrieval request -> %s | payload=%s",
            self._settings.retrieval.url,
            payload,
        )
        async with httpx.AsyncClient(timeout=self._settings.retrieval.timeout) as client:
            response = await client.post(self._settings.retrieval.url, json=payload)
            response.raise_for_status()
            data = response.json()
        logger.info(
            "Retrieval response <- %s | status=%s | body_type=%s",
            self._settings.retrieval.url,
            response.status_code,
            type(data).__name__,
        )

        docs_payload: List[Dict[str, Any]]
        if isinstance(data, list):
            docs_payload = data
        else:
            docs_payload = data.get("results") or []

        documents: List[RetrievedDocument] = []
        for item in docs_payload:
            content = (item.get("text") or item.get("name") or "").strip()
            if not content:
                continue
            source_text = item.get("source_text")
            documents.append(
                RetrievedDocument(
                    id=_maybe_str(item.get("id")),
                    title=_maybe_str(item.get("name")),
                    content=content,
                    score=_maybe_float(item.get("combined_score"))
                    or _maybe_float(item.get("rerank_score"))
                    or _maybe_float(item.get("score")),
                    chunk_id=_maybe_str(item.get("chunk_id")),
                    chunk_type=_maybe_str(item.get("type")),
                    origin_id=_maybe_str(item.get("origin_id")),
                    source=item.get("source"),
                    source_text=source_text.strip() if isinstance(source_text, str) else source_text,
                )
            )
        return documents


def _maybe_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _maybe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
