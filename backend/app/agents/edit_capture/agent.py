from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.agents.edit_capture.aligner import align_bullets
from app.agents.edit_capture.classifier import EditClassifier
from app.agents.edit_capture.markdown_renderer import parse_draft_markdown
from app.providers.base import EmbeddingProvider, LLMProvider
from app.schemas import EditSession, StructuredDraft


class EditCaptureAgent:
    def __init__(
        self,
        *,
        embedder: EmbeddingProvider,
        llm: LLMProvider,
    ) -> None:
        self._embedder = embedder
        self._classifier = EditClassifier(llm)

    def capture(
        self,
        original: StructuredDraft,
        edited_markdown: str,
        operator_id: str | None = None,
    ) -> EditSession:
        edited_sections = dict(parse_draft_markdown(edited_markdown))

        alignment = []
        for section in original.sections:
            original_pairs = [(b.bullet_id, b.text) for b in section.bullets]
            edited_bullets = edited_sections.get(section.title, [])
            alignment.extend(align_bullets(original_pairs, edited_bullets, self._embedder))

        classified = self._classifier.classify(alignment)

        return EditSession(
            edit_id=f"edit_{uuid.uuid4().hex[:12]}",
            draft_id=original.draft_id,
            operator_id=operator_id,
            edited_at=datetime.now(timezone.utc),
            alignment=alignment,
            classified_edits=classified,
        )
