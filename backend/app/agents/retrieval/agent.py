from __future__ import annotations

from datetime import datetime, timezone

from app.agents.indexer.agent import QDRANT_COLLECTION
from app.agents.indexer.sparse_index import SparseIndex
from app.agents.indexer.vector_store import VectorStore
from app.agents.retrieval.fusion import rrf_fuse
from app.providers.base import EmbeddingProvider, RerankerProvider
from app.repositories.chunks import ChunkRepository
from app.schemas import RetrievalConfig, RetrievalResult, RetrievedChunk

_SNIPPET_CHARS = 320


class RetrievalAgent:
    def __init__(
        self,
        *,
        embedder: EmbeddingProvider,
        reranker: RerankerProvider,
        vector_store: VectorStore,
        sparse_index: SparseIndex,
        chunk_repo: ChunkRepository,
        config: RetrievalConfig,
    ) -> None:
        self._embedder = embedder
        self._reranker = reranker
        self._vector_store = vector_store
        self._sparse_index = sparse_index
        self._repo = chunk_repo
        self._config = config

    def retrieve(
        self,
        query: str,
        matter_id: str | None,
        document_ids: list[str],
    ) -> RetrievalResult:
        query_vec = self._embedder.embed_one(query)
        dense = self._vector_store.search(
            QDRANT_COLLECTION,
            query_vec,
            top_k=self._config.k_dense,
            matter_id=matter_id,
        )
        sparse = (
            self._sparse_index.search(matter_id, query, top_k=self._config.k_sparse)
            if matter_id
            else []
        )

        fused = rrf_fuse(
            [[cid for cid, _ in dense], [cid for cid, _ in sparse]],
            k=self._config.rrf_k,
        )
        candidate_ids = [cid for cid, _ in fused[: max(50, self._config.rerank_top_n * 4)]]
        if not candidate_ids:
            return self._empty(query, matter_id)

        chunks_by_id = self._repo.by_id(self._repo.load_many(document_ids))
        candidates = [chunks_by_id[cid] for cid in candidate_ids if cid in chunks_by_id]
        if not candidates:
            return self._empty(query, matter_id)

        ranked = self._reranker.rerank(
            query,
            [c.text for c in candidates],
            top_k=self._config.rerank_top_n,
        )

        dense_ranks = {cid: rank + 1 for rank, (cid, _) in enumerate(dense)}
        sparse_ranks = {cid: rank + 1 for rank, (cid, _) in enumerate(sparse)}
        rrf_scores = dict(fused)

        retrieved: list[RetrievedChunk] = []
        for idx, rerank_score in ranked:
            chunk = candidates[idx]
            retrieved.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    snippet=chunk.text[:_SNIPPET_CHARS],
                    section_label=chunk.section_label,
                    page_range=chunk.page_range,
                    rrf_score=rrf_scores.get(chunk.chunk_id, 0.0),
                    bm25_rank=sparse_ranks.get(chunk.chunk_id),
                    vector_rank=dense_ranks.get(chunk.chunk_id),
                    rerank_score=rerank_score,
                )
            )

        return RetrievalResult(
            query=query,
            matter_id=matter_id,
            retrieved=retrieved,
            config=self._config,
            retrieved_at=datetime.now(timezone.utc),
        )

    def _empty(self, query: str, matter_id: str | None) -> RetrievalResult:
        return RetrievalResult(
            query=query,
            matter_id=matter_id,
            retrieved=[],
            config=self._config,
            retrieved_at=datetime.now(timezone.utc),
        )
