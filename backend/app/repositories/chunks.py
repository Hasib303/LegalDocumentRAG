from __future__ import annotations

import json
from pathlib import Path

from app.schemas import Chunk


class ChunkRepository:
    def __init__(self, chunks_dir: Path) -> None:
        self._dir = chunks_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, document_id: str) -> Path:
        return self._dir / f"{document_id}.jsonl"

    def save(self, document_id: str, chunks: list[Chunk]) -> None:
        with self._path(document_id).open("w", encoding="utf-8") as f:
            for chunk in chunks:
                f.write(chunk.model_dump_json() + "\n")

    def load(self, document_id: str) -> list[Chunk]:
        path = self._path(document_id)
        if not path.is_file():
            return []
        return [Chunk.model_validate_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

    def load_many(self, document_ids: list[str]) -> list[Chunk]:
        return [c for doc_id in document_ids for c in self.load(doc_id)]

    def by_id(self, chunks: list[Chunk]) -> dict[str, Chunk]:
        return {c.chunk_id: c for c in chunks}

    def exists(self, document_id: str) -> bool:
        return self._path(document_id).is_file()
