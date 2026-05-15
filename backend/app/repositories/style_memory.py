from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.schemas import StyleMemory


class StyleMemoryRepository:
    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)
        self._current_link = root / "current.json"

    def _version_path(self, version: int) -> Path:
        return self._root / f"v{version:04d}.json"

    def latest(self) -> StyleMemory:
        if self._current_link.is_file():
            return StyleMemory.model_validate_json(
                self._current_link.read_text(encoding="utf-8")
            )
        return StyleMemory(version=0, updated_at=datetime.now(timezone.utc))

    def load_version(self, version: int) -> StyleMemory:
        return StyleMemory.model_validate_json(
            self._version_path(version).read_text(encoding="utf-8")
        )

    def save(self, memory: StyleMemory) -> None:
        body = memory.model_dump_json(indent=2)
        self._version_path(memory.version).write_text(body, encoding="utf-8")
        self._current_link.write_text(body, encoding="utf-8")
