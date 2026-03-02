# Website Chat

**Turn any website into a chatbot — in minutes.**

Paste a URL, hit crawl, and start asking questions. Answers are pulled directly from the site's content, cited with links, and written in the site's own voice. No hallucination, no generic AI nonsense — just the information that's actually on the page.

### Why it's cool

Ever landed on a massive docs site or a company knowledge base and wished you could just *ask* it something? That's exactly what this does. It's also fully local — your API key is the only thing leaving your machine. No cloud vector database, no data storage subscription, no monthly bill for embeddings.

- **Docs sites** — ask questions instead of ctrl-F-ing forever
- **Company websites** — instant FAQ bot from the real content
- **Research** — crawl a site and interview it
- **Personal projects** — give any static site a chat interface

---

## 📖 Code walkthrough

→ **[View the full walkthrough](docs/walkthrough.html)** — file structure, how the RAG pipeline works, all the tech explained simply.

---

## Tech stack

| Layer | Tech |
|---|---|
| Backend | Python · FastAPI · uvicorn |
| Crawler | Playwright (real Chromium browser) |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (local, CPU) |
| Vector store | hnswlib (local HNSW index, no cloud) |
| LLM | xAI / Grok via OpenAI-compatible API |
| Frontend | React · Vite · TypeScript · Tailwind v4 |
| State | Zustand |
| Streaming | Server-Sent Events (SSE) for both crawl progress and chat |

---

## How it works

```
URL → Playwright BFS crawl → extract text → chunk (500 chars) →
embed (384-dim vectors) → store in hnswlib

Question → embed → retrieve top-5 chunks → inject into prompt →
stream LLM response → cite source pages
```

This is **RAG (Retrieval-Augmented Generation)** — the LLM only answers from the retrieved chunks, not from its training data. The system prompt has a hard rule: if the context doesn't cover it, say so.

An extra step runs brand tone analysis on the first few pages so chat responses match the site's writing style.

---

## Getting started

**1. Backend**
```bash
cd backend
cp .env.example .env        # add your XAI_API_KEY
pip install -r requirements.txt
python -m playwright install chromium
python run.py               # starts on :8000
```

**2. Frontend**
```bash
cd frontend
npm install
npm run dev                 # starts on :5173
```

Or run both at once:
```bash
./start.sh
```

---

## Environment variables

Copy `backend/.env.example` to `backend/.env`:

```
XAI_API_KEY=your-key-here
```

Everything else has sensible defaults (max pages, chunk size, embedding model, etc.).

---

## Project structure

```
website-chat/
├── backend/
│   ├── app/
│   │   ├── api/          # crawl, chat, sessions endpoints
│   │   ├── crawler/      # Playwright BFS + content extraction
│   │   ├── indexer/      # chunker, embedder, hnswlib store
│   │   ├── rag/          # retrieve → prompt → stream pipeline
│   │   ├── brand/        # tone analysis
│   │   └── jobs/         # background job state + sessions.json
│   └── run.py
├── frontend/
│   └── src/
│       ├── components/   # CrawlPanel, ChatPanel
│       ├── hooks/        # useCrawl, useChat, useSessions
│       └── store/        # Zustand global state
└── docs/
    └── walkthrough.html  # full visual code guide
```
