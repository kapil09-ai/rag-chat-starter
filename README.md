# rag-chat-starter

A small, readable retrieval-augmented generation (RAG) chat app: a **FastAPI** backend that finds the relevant passages in your Markdown docs and streams an answer over **Server-Sent Events**, and a **React** frontend that renders the answer token by token with its sources.

It's meant to be read in one sitting. There's no framework magic: retrieval is ~100 lines of BM25, the stream is plain SSE, and the UI is one hook and one component.

```
docs/*.md ──► chunk by heading ──► BM25 index
                                        │
React UI ──POST /chat──► FastAPI ──► top-k passages ──► LLM (or offline fallback)
   ▲                                                        │
   └──────── SSE: sources → token → token → … → done ◄──────┘
```

## Run it

**Backend** (Python 3.11+)
```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload          # http://localhost:8000
```

**Frontend** (Node 20+)
```bash
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

No API key? It still works: in offline mode it streams back the best-matching passage, so you can try retrieval and the streaming UI straight away. To get generated answers, set an OpenAI-compatible key before starting the backend:

```bash
export OPENAI_API_KEY=sk-...
export LLM_MODEL=gpt-4o-mini                # optional
export OPENAI_BASE_URL=https://...          # optional, any OpenAI-compatible provider
```

Point it at your own docs with `DOCS_DIR=/path/to/markdown`.

## API

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | Status and number of indexed chunks |
| POST | `/search` | `{"question": "...", "k": 3}` → scored passages (no LLM) |
| POST | `/chat` | Same body → SSE stream of `sources`, `token`, `error`, `done` events |

Sources are sent **before** the first token so the UI can show citations immediately.

## Design notes

- **Why BM25 instead of embeddings?** It runs anywhere with no extra services and is easy to follow. `Retriever.search` is the only thing to replace to move to pgvector or another vector store.
- **Why parse SSE from `fetch`?** `EventSource` only supports GET; the question goes in a POST body. `useChatStream` handles partial events across reads and supports cancel via `AbortController`.
- **Grounding:** the system prompt restricts answers to the numbered passages and asks for inline `[n]` citations.

## Tests

```bash
cd backend && pytest -q
```

Covers tokenization, BM25 ranking, the `/search` shape, SSE event order and input validation.

## Ideas for next steps

- Swap BM25 for hybrid search (BM25 + embeddings in pgvector)
- Add an evaluation set of question/expected-source pairs and run it in CI
- Tool calling so the assistant can take actions, with a confirmation step

MIT licensed.
