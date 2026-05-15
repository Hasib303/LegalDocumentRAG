from __future__ import annotations

from typing import TYPE_CHECKING

from app.schemas import Chunk

if TYPE_CHECKING:
    import bm25s


class SparseIndex:
    def __init__(self) -> None:
        self._by_matter: dict[str, tuple[bm25s.BM25, list[str]]] = {}

    def index(self, matter_id: str, chunks: list[Chunk]) -> None:
        import bm25s

        if not chunks:
            return
        texts = [c.text for c in chunks]
        chunk_ids = [c.chunk_id for c in chunks]
        tokens = bm25s.tokenize(texts, stopwords="en")
        retriever = bm25s.BM25()
        retriever.index(tokens)
        self._by_matter[matter_id] = (retriever, chunk_ids)

    def search(self, matter_id: str, query: str, top_k: int) -> list[tuple[str, float]]:
        import bm25s

        if matter_id not in self._by_matter:
            return []
        retriever, chunk_ids = self._by_matter[matter_id]
        tokens = bm25s.tokenize([query], stopwords="en")
        k = min(top_k, len(chunk_ids))
        results, scores = retriever.retrieve(tokens, k=k)
        return [(chunk_ids[idx], float(score)) for idx, score in zip(results[0], scores[0])]
