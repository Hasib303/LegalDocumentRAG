from __future__ import annotations

from pathlib import Path

from app.schemas import EditSession


class EditRepository:
    def __init__(self, edits_dir: Path) -> None:
        self._dir = edits_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, edit_id: str) -> Path:
        return self._dir / f"{edit_id}.json"

    def save(self, edit: EditSession) -> None:
        self._path(edit.edit_id).write_text(edit.model_dump_json(indent=2), encoding="utf-8")

    def load(self, edit_id: str) -> EditSession:
        return EditSession.model_validate_json(self._path(edit_id).read_text(encoding="utf-8"))

    def list_all(self) -> list[EditSession]:
        return [
            EditSession.model_validate_json(p.read_text(encoding="utf-8"))
            for p in sorted(self._dir.glob("*.json"))
        ]
