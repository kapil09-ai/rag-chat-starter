"""FastAPI server: retrieval + streaming answers over Server-Sent Events."""
from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from llm import stream_answer
from retriever import Retriever

DOCS_DIR = Path(os.getenv("DOCS_DIR", Path(__file__).resolve().parent.parent / "docs"))

app = FastAPI(title="rag-chat-starter")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
retriever = Retriever.from_folder(DOCS_DIR)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    k: int = Field(default=3, ge=1, le=8)


def sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "chunks": len(retriever.chunks)}


@app.post("/search")
def search(req: ChatRequest) -> list[dict]:
    return [
        {"id": c.id, "source": c.source, "heading": c.heading, "score": round(s, 3), "text": c.text}
        for c, s in retriever.search(req.question, req.k)
    ]


@app.post("/chat")
async def chat(req: ChatRequest) -> StreamingResponse:
    hits = [c for c, _ in retriever.search(req.question, req.k)]

    async def events():
        # Send sources first so the UI can render citations before the answer arrives.
        yield sse("sources", [{"n": i + 1, "source": c.source, "heading": c.heading} for i, c in enumerate(hits)])
        try:
            async for token in stream_answer(req.question, hits):
                yield sse("token", token)
        except Exception as exc:  # surface provider errors to the UI instead of hanging
            yield sse("error", str(exc))
        yield sse("done", {})

    return StreamingResponse(events(), media_type="text/event-stream")
