"""A tiny BM25 retriever over Markdown files.

No vector database and no embeddings API, on purpose: it keeps the demo runnable
anywhere and makes the retrieval step easy to read. Swapping in pgvector or any
embedding store only means replacing `Retriever.search`.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

TOKEN = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do", "does", "for", "from",
    "how", "i", "if", "in", "is", "it", "of", "on", "or", "that", "the", "this", "to",
    "what", "when", "where", "which", "who", "why", "with", "you", "your",
}


def tokenize(text: str) -> list[str]:
    return [t for t in TOKEN.findall(text.lower()) if t not in STOPWORDS]


@dataclass
class Chunk:
    id: str
    source: str
    heading: str
    text: str


def chunk_markdown(path: Path, max_chars: int = 800) -> list[Chunk]:
    """Split a Markdown file on headings, then on paragraphs if a section is long."""
    chunks: list[Chunk] = []
    heading = path.stem
    buf: list[str] = []

    def flush() -> None:
        body = "\n".join(buf).strip()
        if not body:
            return
        paras, cur = [p for p in body.split("\n\n") if p.strip()], ""
        for p in paras:
            if cur and len(cur) + len(p) > max_chars:
                chunks.append(Chunk(f"{path.name}#{len(chunks)}", path.name, heading, cur.strip()))
                cur = ""
            cur += p + "\n\n"
        if cur.strip():
            chunks.append(Chunk(f"{path.name}#{len(chunks)}", path.name, heading, cur.strip()))

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            flush()
            buf = []
            heading = line.lstrip("#").strip()
        else:
            buf.append(line)
    flush()
    return chunks


class Retriever:
    """Okapi BM25 over heading + text of each chunk."""

    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1, self.b = k1, b
        self.docs = [tokenize(f"{c.heading} {c.text}") for c in chunks]
        self.tf = [Counter(d) for d in self.docs]
        self.avgdl = sum(len(d) for d in self.docs) / max(len(self.docs), 1)
        df: Counter[str] = Counter()
        for d in self.docs:
            df.update(set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    @classmethod
    def from_folder(cls, folder: Path) -> "Retriever":
        chunks: list[Chunk] = []
        for path in sorted(folder.glob("*.md")):
            chunks.extend(chunk_markdown(path))
        return cls(chunks)

    def search(self, query: str, k: int = 3) -> list[tuple[Chunk, float]]:
        q = tokenize(query)
        scored = []
        for i, tf in enumerate(self.tf):
            dl = len(self.docs[i])
            s = 0.0
            for t in q:
                if t not in tf:
                    continue
                f = tf[t]
                s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            if s > 0:
                scored.append((self.chunks[i], s))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]
