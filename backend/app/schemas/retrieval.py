"""Retrieval results — what the retrieval agent hands to drafting."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: str
    snippet: str
    section_label: str | None = None
    page_range: tuple[int, int]
    rrf_score: float
    bm25_rank: int | None = None
    vector_rank: int | None = None
    rerank_score: float | None = None


class RetrievalConfig(BaseModel):
    k_dense: int = Field(ge=1)
    k_sparse: int = Field(ge=1)
    rrf_k: int = Field(ge=1)
    rerank_top_n: int = Field(ge=1)


class RetrievalResult(BaseModel):
    query: str
    matter_id: str | None = None
    retrieved: list[RetrievedChunk]
    config: RetrievalConfig
    retrieved_at: datetime
