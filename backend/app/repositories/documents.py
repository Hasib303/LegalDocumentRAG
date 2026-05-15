from __future__ import annotations

from pathlib import Path

from app.schemas import DocumentManifest, ProcessedDocument


class DocumentRepository:
    def __init__(self, manifests_dir: Path, processed_dir: Path) -> None:
        self._manifests = manifests_dir
        self._processed = processed_dir
        self._manifests.mkdir(parents=True, exist_ok=True)
        self._processed.mkdir(parents=True, exist_ok=True)

    def _manifest_path(self, document_id: str) -> Path:
        return self._manifests / f"{document_id}.json"

    def _processed_path(self, document_id: str) -> Path:
        return self._processed / f"{document_id}.json"

    def save_manifest(self, manifest: DocumentManifest) -> None:
        self._manifest_path(manifest.document_id).write_text(
            manifest.model_dump_json(indent=2), encoding="utf-8"
        )

    def load_manifest(self, document_id: str) -> DocumentManifest:
        return DocumentManifest.model_validate_json(
            self._manifest_path(document_id).read_text(encoding="utf-8")
        )

    def manifest_exists(self, document_id: str) -> bool:
        return self._manifest_path(document_id).is_file()

    def save_processed(self, processed: ProcessedDocument) -> None:
        self._processed_path(processed.document_id).write_text(
            processed.model_dump_json(indent=2), encoding="utf-8"
        )

    def load_processed(self, document_id: str) -> ProcessedDocument:
        return ProcessedDocument.model_validate_json(
            self._processed_path(document_id).read_text(encoding="utf-8")
        )

    def processed_exists(self, document_id: str) -> bool:
        return self._processed_path(document_id).is_file()

    def list_manifests(self) -> list[DocumentManifest]:
        return [
            DocumentManifest.model_validate_json(p.read_text(encoding="utf-8"))
            for p in sorted(self._manifests.glob("*.json"))
        ]
