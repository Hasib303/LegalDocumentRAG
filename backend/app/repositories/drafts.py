from __future__ import annotations

from pathlib import Path

from app.schemas import StructuredDraft


class DraftRepository:
    def __init__(self, drafts_dir: Path) -> None:
        self._dir = drafts_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, draft_id: str) -> Path:
        return self._dir / f"{draft_id}.json"

    def _markdown_path(self, draft_id: str) -> Path:
        return self._dir / f"{draft_id}.md"

    def save(self, draft: StructuredDraft, markdown: str | None = None) -> None:
        self._path(draft.draft_id).write_text(draft.model_dump_json(indent=2), encoding="utf-8")
        if markdown is not None:
            self._markdown_path(draft.draft_id).write_text(markdown, encoding="utf-8")

    def load(self, draft_id: str) -> StructuredDraft:
        return StructuredDraft.model_validate_json(self._path(draft_id).read_text(encoding="utf-8"))

    def exists(self, draft_id: str) -> bool:
        return self._path(draft_id).is_file()
