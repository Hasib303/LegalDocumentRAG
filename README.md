# NerdFarm

> **Legal Document AI Workflow** — built for the fictional Pearson Specter Litt. Messy documents in, grounded drafts out, smarter with every operator edit.

## What it does


| Pillar                     | What you get                                                                                                                                                                                |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Document Processing**    | OCR + layout extraction on scanned, photographed, handwritten, and redacted legal PDFs. Structured metadata (parties, court, dates, case number) via Pydantic.                              |
| **Grounded Retrieval**     | Hybrid BM25 + dense (BGE-M3) over a Qdrant index, cross-encoder rerank, contextual chunk prepend. Every retrieved span carries its provenance.                                              |
| **Draft Generation**       | Structured Case Fact Summary with inline citations. Chunk-ID whitelist + faithfulness audit. `UNSUPPORTED` flags instead of fabrication.                                                    |
| **Improvement from Edits** | Operator edits → aligned (Hungarian) → classified → four memory stores (terminology, section rules, exemplars, structural prefs) → next draft is measurably better on **held-out** matters. |


## 1 · Set up the backend

```bash
git clone git@github.com:Hasib303/LegalDocumentRAG.git nerdfarm
cd nerdfarm/backend

cp .env.example .env
# Open .env and paste your two free keys:
#   GEMINI_API_KEY=AIza...
#   GROQ_API_KEY=gsk_...

make setup        # uv sync --extra dev   (~3–5 min first time)
```

---

## 2 · Run the end-to-end CLI demo (fastest path)

```bash
make demo         # from backend/
```

---

## 3 · Run the API + Streamlit UI (operator workflow)

**Terminal 1 — FastAPI**

```bash
cd backend
uv run uvicorn app.api.main:app --reload --port 8000
# Interactive docs: http://localhost:8000/docs
```

**Terminal 2 — Streamlit**

```bash
cd frontend
uv venv && source .venv/bin/activate          # or:  python3 -m venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt            # or:  python3 -m pip install -r requirements.txt
streamlit run src/app.py
# UI: http://localhost:8501
```

In the UI:


| Tab          | What it does                                                                                               |
| ------------ | ---------------------------------------------------------------------------------------------------------- |
| **Draft**    | Pick a matter, click "Draft now" → backend ingests/indexes (idempotent) + drafts → markdown renders inline |
| **Edit**     | Paste the modified markdown → backend aligns + classifies + updates style memory → returns the new version |
| **Evidence** | Enter `draft_id` + `bullet_id` → see the exact source chunks (text + page range)                           |


Sidebar has a "Health check" button to confirm the backend is reachable.

---

## 4 · Run everything in Docker (alternative)

```bash
# from repo root
cp backend/.env.example .env
# add your two keys in .env (note: this .env lives at the repo root for compose)

docker compose up --build
# Streamlit:  http://localhost:8501
# FastAPI:    http://localhost:8000
# Qdrant:     http://localhost:6333
```

`make up` / `make down` (from `backend/`) wrap the same commands.

## Architecture at a glance

```
                    ┌─────────────────────┐
                    │    Orchestrator     │
                    └──────────┬──────────┘
        ┌────────┬────────┬────┴───┬────────┬────────┬────────┐
        ▼        ▼        ▼        ▼        ▼        ▼        ▼
   ┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
   │ Ingest ││Process ││Indexer ││Retrieve││Drafting││ Audit  ││Learning│
   └────────┘└────────┘└────────┘└────────┘└────────┘└────────┘└────────┘
```

- **Agentic monolith.** Stateless agents communicate via typed Pydantic messages through the Orchestrator. No agent-to-agent imports.
- **Microservice-ready.** Frontend ↔ backend over HTTP only. Any agent can be lifted into its own service tomorrow without rewrites.
- **Provider-agnostic.** LLM / embedding / reranker / vision behind `Protocol` interfaces. Swap defaults via `config.yaml` — one line.

Full diagrams, schemas, and module map in `[backend/docs/DATA_FLOW.md](backend/docs/DATA_FLOW.md)`.

---

## Tech stack — all open-source or no-card free tier


| Layer                 | Pick                                                      | Why                                                       |
| --------------------- | --------------------------------------------------------- | --------------------------------------------------------- |
| Born-digital layout   | **Docling** + PyMuPDF4LLM fast-path                       | 97.9 % table accuracy, Apache-2.0                         |
| OCR (scans)           | **PaddleOCR PP-OCRv5**                                    | Top OmniDocBench score, per-word confidence               |
| Vision-LLM fallback   | **Qwen2.5-VL-7B** local · **Gemini 2.5 Flash** hosted     | Free tier, no card                                        |
| Structured extraction | **Instructor** + Qwen3-4B (no-think) + Outlines           | Pydantic-native, grammar-constrained                      |
| Embedder              | **BGE-M3**                                                | Dense + sparse + ColBERT in one pass · 8 192 tokens · MIT |
| Sparse / BM25         | **bm25s**                                                 | 500× faster than `rank_bm25`                              |
| Vector DB             | **Qdrant** (Docker, ARM64)                                | Native hybrid search + RRF + payload filter               |
| Reranker              | **bge-reranker-v2-m3**                                    | ~0.5 s / batch on M-series CPU                            |
| Generator (primary)   | **Gemini 2.5 Flash-Lite** (server-side `response_schema`) | ~390 tok/s, free, no card                                 |
| Generator (fallback)  | **Qwen QwQ-32B** on Groq free tier                        | Reasoning, no card                                        |
| Faithfulness          | **Bespoke-MiniCheck** + **DeepEval**                      | Open-source NLI grounding                                 |
| Edit alignment        | **Hungarian** (`scipy`) + diff-match-patch                | Handles bullet reorderings                                |
| Edit classifier       | Heuristics → Qwen3-4B-Thinking → Gemini Flash             | Tiered cost-aware                                         |
| Memory store          | **Qdrant** multitenancy + SQLite sidecar                  | Rolled to fit the four-store pattern                      |
| Eval                  | **DeepEval** + **LeMAJ** LDP methodology                  | ACL 2025 NLLP recognized                                  |
| Preference loop       | **PRELUDE/CIPHER** pattern                                | NeurIPS 2024                                              |


Production-upgrade path (when paid keys are added): swap Gemini → Claude Sonnet, BGE-M3 → voyage-law-2, bge-reranker → Voyage Rerank — one config line each.

---

## Repository layout

```
NerdFarm/
├── backend/
│   ├── app/
│   │   ├── orchestrator/        # state + routing
│   │   ├── agents/              # ingest, processing, indexer, retrieval,
│   │   │                        # drafting, audit, edit_capture, learning, evaluation
│   │   ├── providers/           # LLM / embedding / reranker / vision interfaces
│   │   ├── schemas/             # Pydantic contracts (the only shared types)
│   │   ├── repositories/        # filesystem now, swappable for Postgres/S3
│   │   ├── api/                 # FastAPI surface
│   │   ├── synthetic/           # transform_messy.py — handwritten/photographed/redacted gen
│   │   ├── config.py
│   │   └── cli.py
│   ├── data/                    # 13 real legal PDFs + INVENTORY.md
│   ├── docs/                    # FEATURE_REQUIREMENTS, DATA_FLOW, BACKEND_DESIGN, assessment PDF
│   ├── samples/                 # sample inputs / drafts / edits for reviewers
│   ├── tests/
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                    # Streamlit — upload, draft viewer, evidence inspector, inline edit
│   ├── src/
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml           # backend + frontend + Qdrant + Ollama
├── Makefile                     # make setup · make demo · make test · make up
└── README.md                    # you are here
```

