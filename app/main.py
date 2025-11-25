"""FastAPI entrypoint for the RAG-enabled chat service."""

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

from .client import RetrievalClient, SiliconFlowClient
from .config import get_settings
from .prompt import build_messages
from .ui import PLAYGROUND_HTML
from .schemas import ChatRequest, ChatResponse, RetrievedDocument, Usage


logger = logging.getLogger(__name__)

settings = get_settings()
client = SiliconFlowClient(settings)
retriever = RetrievalClient(settings)

app = FastAPI(
    title="RecipeProject RAG Service",
    version="0.1.0",
    description="RAG orchestration layer that forwards grounded prompts to SiliconFlow",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _trim_documents(
    documents: List[RetrievedDocument], limit: Optional[int] = None
) -> List[RetrievedDocument]:
    """Keep only the top-k documents as expected by downstream prompt builders."""
    max_docs = limit or settings.retrieval.top_k
    return documents[:max_docs]


@app.get("/health")
async def health() -> Dict[str, str]:
    """Simple readiness probe."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def playground() -> HTMLResponse:
    """Serve a lightweight UI for manual testing."""
    return HTMLResponse(content=PLAYGROUND_HTML)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Handle chat generation given a user query and retrieved documents."""
    logger.info(
        "Incoming /chat | query=%s | stream=%s | top_k=%s | use_rerank=%s | rerank_mode=%s",
        request.query,
        request.stream,
        request.top_k,
        request.use_rerank,
        request.rerank_mode,
    )

    rewritten_query = request.query
    if settings.rewriter.enabled:
        try:
            rewritten_query = await client.rewrite_query(request.query)
        except (RuntimeError, httpx.HTTPError) as exc:
            logger.warning("Query rewrite failed (%s); fallback to original", exc)
            rewritten_query = request.query

    if rewritten_query != request.query:
        logger.info("Using rewritten query for retrieval | original=%s | rewritten=%s", request.query, rewritten_query)

    try:
        retrieved_docs = await retriever.retrieve(
            rewritten_query,
            top_k=request.top_k,
            use_rerank=request.use_rerank,
            rerank_mode=request.rerank_mode,
            rerank_top_k=request.rerank_top_k,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text or exc.response.reason_phrase
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"Retriever error: {detail}",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Retriever request failed") from exc

    trimmed_docs = _trim_documents(retrieved_docs)
    logger.info("Retrieved %s documents after trimming", len(trimmed_docs))
    messages = build_messages(request.query, trimmed_docs)

    if request.stream:
        return StreamingResponse(
            _streaming_response(messages, trimmed_docs),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )

    try:
        logger.info("Calling SiliconFlow | model=%s | stream=%s", settings.model.model_name, request.stream)
        raw_response = await client.chat(messages)
    except RuntimeError as exc:  # Missing API key or similar misconfiguration
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text or exc.response.reason_phrase
        raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Upstream SiliconFlow request failed") from exc

    answer = _extract_answer(raw_response)
    usage = _extract_usage(raw_response)
    model_name = raw_response.get("model", settings.model.model_name)

    return ChatResponse(
        answer=answer,
        model=model_name,
        usage=usage,
        raw_response=raw_response,
        documents=trimmed_docs,
    )


def _extract_answer(raw_response: Dict[str, Any]) -> str:
    """Extract the assistant message text from the SiliconFlow payload."""
    choices = raw_response.get("choices") or []
    if not choices:
        raise HTTPException(status_code=502, detail="SiliconFlow returned no choices")

    message = choices[0].get("message") or {}
    content = (message.get("content") or "").strip()
    if not content:
        raise HTTPException(status_code=502, detail="Choice contained no message content")
    return content


def _extract_usage(raw_response: Dict[str, Any]) -> Optional[Usage]:
    """Normalize usage stats into the response schema."""
    usage_payload = raw_response.get("usage")
    if not usage_payload:
        return None
    return Usage(**usage_payload)


def _serialize_documents(documents: List[RetrievedDocument]) -> List[Dict[str, Any]]:
    return [doc.dict() for doc in documents]


def _sse(event: str, data: Any) -> str:
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


def _streaming_response(
    messages: List[Dict[str, str]],
    documents: List[RetrievedDocument],
) -> AsyncGenerator[bytes, None]:
    async def generator() -> AsyncGenerator[bytes, None]:
        yield _sse(
            "meta",
            {
                "model": settings.model.model_name,
                "documents": _serialize_documents(documents),
            },
        ).encode("utf-8")

        buffer: List[str] = []
        try:
            async for chunk in client.stream_chat(messages):
                buffer.append(chunk)
                yield _sse("delta", chunk).encode("utf-8")
        except RuntimeError as exc:
            yield _sse("error", {"message": str(exc)}).encode("utf-8")
            return
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text or exc.response.reason_phrase
            yield _sse(
                "error",
                {"message": f"Upstream error: {detail}"},
            ).encode("utf-8")
            return
        except httpx.HTTPError:
            yield _sse("error", {"message": "Upstream SiliconFlow request failed"}).encode(
                "utf-8"
            )
            return

        answer = "".join(buffer).strip()
        yield _sse("end", {"answer": answer}).encode("utf-8")

    return generator()
