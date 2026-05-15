from __future__ import annotations

import uuid
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.schemas import Chunk


def _point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_OID, chunk_id))


class VectorStore:
    def __init__(self, url: str | None = None, path: Path | None = None) -> None:
        if url:
            self._client = QdrantClient(url=url)
        elif path:
            path.mkdir(parents=True, exist_ok=True)
            self._client = QdrantClient(path=str(path))
        else:
            self._client = QdrantClient(":memory:")

    def ensure_collection(self, name: str, dim: int) -> None:
        if not self._client.collection_exists(name):
            self._client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )

    def upsert(
        self,
        collection: str,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> None:
        points = [
            PointStruct(
                id=_point_id(chunk.chunk_id),
                vector=embedding,
                payload={
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "matter_id": chunk.matter_id,
                    "text": chunk.text,
                    "section_label": chunk.section_label,
                    "page_range": list(chunk.page_range),
                },
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]
        self._client.upsert(collection_name=collection, points=points)

    def search(
        self,
        collection: str,
        query_vector: list[float],
        top_k: int,
        matter_id: str | None = None,
    ) -> list[tuple[str, float]]:
        query_filter = (
            Filter(must=[FieldCondition(key="matter_id", match=MatchValue(value=matter_id))])
            if matter_id
            else None
        )
        result = self._client.query_points(
            collection_name=collection,
            query=query_vector,
            limit=top_k,
            query_filter=query_filter,
        )
        return [(hit.payload["chunk_id"], float(hit.score)) for hit in result.points]
