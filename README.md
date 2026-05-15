# NerdFarm

> **Legal Document AI Workflow** — built for the fictional Pearson Specter Litt.
> Messy documents in, grounded drafts out, smarter with every operator edit.

AI Engineer take-home assessment for [Ideabuilders.studio](https://ideabuilders.studio).
Deadline: **2026-05-15 EOD**.

---

## What it does


| Pillar                     | What you get                                                                                                                                                                                |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Document Processing**    | OCR + layout extraction on scanned, photographed, handwritten, and redacted legal PDFs. Structured metadata (parties, court, dates, case number) via Pydantic.                              |
| **Grounded Retrieval**     | Hybrid BM25 + dense (BGE-M3) over a Qdrant index, cross-encoder rerank, contextual chunk prepend. Every retrieved span carries its provenance.                                              |
| **Draft Generation**       | Structured Case Fact Summary with inline citations. Chunk-ID whitelist + faithfulness audit. `UNSUPPORTED` flags instead of fabrication.                                                    |
| **Improvement from Edits** | Operator edits → aligned (Hungarian) → classified → four memory stores (terminology, section rules, exemplars, structural prefs) → next draft is measurably better on **held-out** matters. |


---

## Quick start

```bash
# one-time setup
make setup

# end-to-end demo on the bundled corpus
make demo
```

The demo:

1. Ingests `backend/data/{clean_borndigital, scanned_*}/` — 13 real public legal PDFs (313 pages)
2. Generates Draft v1 for Matter A
3. Applies bundled operator edits from `backend/samples/edits/`
4. Re-drafts a held-out Matter B with and without the learned memory
5. Prints an A/B comparison: edit-distance reduction · terminology adherence · rule compliance

Runs in under 5 minutes on Apple Silicon with 16 GB RAM.

---

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

---

## Documentation


| Doc                                                                            | Purpose                                                                    |
| ------------------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| `[backend/docs/FEATURE_REQUIREMENTS.md](backend/docs/FEATURE_REQUIREMENTS.md)` | What the system must do — MoSCoW requirements mapped to the rubric         |
| `[backend/docs/DATA_FLOW.md](backend/docs/DATA_FLOW.md)`                       | How data moves — agent topology, schemas, storage layout, improvement loop |
| `[backend/docs/BACKEND_DESIGN.md](backend/docs/BACKEND_DESIGN.md)`             | Which libraries / models / patterns and why — benchmark-backed picks       |
| `[backend/data/INVENTORY.md](backend/data/INVENTORY.md)`                       | Document corpus inventory grouped by extraction difficulty                 |
| `[backend/docs/AI Engineer - Assessment.pdf](backend/docs/)`                   | Original assessment brief                                                  |


