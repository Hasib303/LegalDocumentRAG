from __future__ import annotations

from app.agents.indexer.chunker import approx_tokens, find_section_label, split_text
from app.agents.indexer.sparse_index import SparseIndex
from app.agents.indexer.vector_store import VectorStore
from app.providers.base import EmbeddingProvider
from app.repositories.chunks import ChunkRepository
from app.schemas import Chunk, ProcessedDocument

QDRANT_COLLECTION = "nerdfarm_chunks"


class IndexerAgent:
    def __init__(
        self,
        *,
        embedder: EmbeddingProvider,
        vector_store: VectorStore,
        sparse_index: SparseIndex,
        chunk_repo: ChunkRepository,
        target_tokens: int = 450,
        overlap_tokens: int = 90,
    ) -> None:
        self._embedder = embedder
        self._vector_store = vector_store
        self._sparse_index = sparse_index
        self._repo = chunk_repo
        self._target_tokens = target_tokens
        self._overlap_tokens = overlap_tokens
        self._vector_store.ensure_collection(QDRANT_COLLECTION, embedder.dim)

    def index_document(
        self,
        doc: ProcessedDocument,
        matter_id: str | None = None,
    ) -> list[Chunk]:
        chunks = self._chunk_document(doc, matter_id)
        if not chunks:
            return []
        embeddings = self._embedder.embed([c.text for c in chunks])
        self._vector_store.upsert(QDRANT_COLLECTION, chunks, embeddings)
        self._repo.save(doc.document_id, chunks)
        return chunks

    def index_matter(self, matter_id: str, document_ids: list[str]) -> None:
        matter_chunks = self._repo.load_many(document_ids)
        self._sparse_index.index(matter_id, matter_chunks)

    def _chunk_document(
        self,
        doc: ProcessedDocument,
        matter_id: str | None,
    ) -> list[Chunk]:
        chunks: list[Chunk] = []
        counter = 0
        for page in doc.pages:
            page_text = "\n".join(b.text for b in page.blocks).strip()
            if not page_text:
                continue
            method = page.blocks[0].extraction_method
            for text in split_text(page_text, self._target_tokens, self._overlap_tokens):
                chunks.append(
                    Chunk(
                        chunk_id=f"{doc.document_id}:c{counter:04d}",
                        document_id=doc.document_id,
                        matter_id=matter_id,
                        section_label=find_section_label(text),
                        page_range=(page.page_number, page.page_number),
                        char_offsets=(0, len(text)),
                        text=text,
                        token_count=approx_tokens(text),
                        extraction_method=method,
                        embedding_model=self._embedder.name,
                    )
                )
                counter += 1
        return chunks
