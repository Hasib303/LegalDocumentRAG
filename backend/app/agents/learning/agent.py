from __future__ import annotations

from datetime import datetime, timezone

from app.agents.learning.exemplars import build_exemplars, prune_exemplars
from app.agents.learning.section_rules import update_section_rules
from app.agents.learning.terminology import extract_terminology
from app.repositories.style_memory import StyleMemoryRepository
from app.schemas import EditSession, StructuredDraft, StyleMemory


class LearningAgent:
    def __init__(
        self,
        *,
        repo: StyleMemoryRepository,
        exemplars_per_section: int = 20,
    ) -> None:
        self._repo = repo
        self._cap = exemplars_per_section

    def learn(
        self,
        *,
        edit: EditSession,
        original_draft: StructuredDraft,
        matter_type: str | None,
        matter_id: str,
    ) -> StyleMemory:
        current = self._repo.latest()
        bullet_section_map = {
            b.bullet_id: section.section_id
            for section in original_draft.sections
            for b in section.bullets
        }

        terminology = extract_terminology(
            edit.alignment, current.terminology_map, edit.edit_id
        )
        section_rules = update_section_rules(
            edit.alignment,
            edit.classified_edits,
            bullet_section_map,
            current.section_rules,
            matter_id,
        )
        new_exemplars = build_exemplars(
            edit.alignment, edit.classified_edits, bullet_section_map, matter_type
        )
        exemplars = prune_exemplars(current.exemplar_store + new_exemplars, self._cap)

        next_memory = StyleMemory(
            version=current.version + 1,
            updated_at=datetime.now(timezone.utc),
            based_on_edit_ids=[*current.based_on_edit_ids, edit.edit_id],
            terminology_map=terminology,
            section_rules=section_rules,
            exemplar_store=exemplars,
            structural_preferences=current.structural_preferences,
        )
        self._repo.save(next_memory)
        return next_memory
