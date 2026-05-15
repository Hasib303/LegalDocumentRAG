from __future__ import annotations

import hashlib
import mimetypes
from datetime import datetime, timezone
from pathlib import Path

import pymupdf

from app.repositories.documents import DocumentRepository
from app.schemas import DocumentManifest


def _document_id_from_hash(sha256_hex: str) -> str:
    return f"doc_{sha256_hex[:16]}"


def _guess_mime_type(path: Path) -> str:
    mime, _ = mimetypes.guess_type(path.name)
    return mime or "application/octet-stream"


def _count_pages(path: Path, mime: str) -> int:
    if mime == "application/pdf":
        with pymupdf.open(path) as doc:
            return doc.page_count
    return 1


class IngestAgent:
    def __init__(self, repo: DocumentRepository) -> None:
        self._repo = repo

    def ingest(self, file_path: Path, tags: list[str] | None = None) -> DocumentManifest:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(path)

        data = path.read_bytes()
        sha256 = hashlib.sha256(data).hexdigest()
        document_id = _document_id_from_hash(sha256)

        # Idempotency: re-ingesting the same bytes returns the original manifest.
        if self._repo.manifest_exists(document_id):
            return self._repo.load_manifest(document_id)

        mime = _guess_mime_type(path)
        manifest = DocumentManifest(
            document_id=document_id,
            sha256=sha256,
            original_filename=path.name,
            mime_type=mime,
            page_count=_count_pages(path, mime),
            bytes=len(data),
            ingested_at=datetime.now(timezone.utc),
            tags=tags or [],
        )
        self._repo.save_manifest(manifest)
        return manifest
