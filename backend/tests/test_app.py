import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app import app  # noqa: E402
from retriever import Chunk, Retriever, tokenize  # noqa: E402

client = TestClient(app)


def test_tokenize_drops_stopwords_and_punctuation():
    assert tokenize("What is the SLA, exactly?") == ["sla", "exactly"]


def test_bm25_prefers_the_matching_chunk():
    r = Retriever([
        Chunk("a", "a.md", "Refunds", "Refunds are issued within 5 business days."),
        Chunk("b", "b.md", "Shipping", "Orders ship from our Chicago warehouse."),
    ])
    top, _ = r.search("how long do refunds take")[0]
    assert top.id == "a"


def test_health_reports_indexed_chunks():
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["chunks"] > 0


def test_search_returns_scored_sources():
    hits = client.post("/search", json={"question": "reset password"}).json()
    assert hits and {"source", "heading", "score", "text"} <= hits[0].keys()


def test_chat_streams_sources_then_tokens_then_done(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with client.stream("POST", "/chat", json={"question": "reset password"}) as r:
        text = "".join(r.iter_text())
    assert text.index("event: sources") < text.index("event: token") < text.index("event: done")


def test_empty_question_is_rejected():
    assert client.post("/chat", json={"question": ""}).status_code == 422
