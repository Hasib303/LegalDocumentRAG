from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from app.agents.evaluation.metrics import (
    edit_distance_reduction,
    section_rule_compliance,
    terminology_adherence,
)
from app.schemas import StructuredDraft, StyleMemory


class HeldOutComparison(BaseModel):
    matter_id: str
    baseline_draft_id: str
    learned_draft_id: str
    style_memory_version: int
    edit_distance_reduction: float
    terminology_adherence: float
    section_rule_compliance: float
    evaluated_at: datetime


class EvaluationAgent:
    def __init__(self, results_dir: Path) -> None:
        self._dir = results_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def compare(
        self,
        *,
        matter_id: str,
        baseline_draft: StructuredDraft,
        learned_draft: StructuredDraft,
        reference_text: str,
        style_memory: StyleMemory,
    ) -> HeldOutComparison:
        comparison = HeldOutComparison(
            matter_id=matter_id,
            baseline_draft_id=baseline_draft.draft_id,
            learned_draft_id=learned_draft.draft_id,
            style_memory_version=style_memory.version,
            edit_distance_reduction=edit_distance_reduction(
                baseline_draft, learned_draft, reference_text
            ),
            terminology_adherence=terminology_adherence(
                learned_draft, style_memory.terminology_map
            ),
            section_rule_compliance=section_rule_compliance(learned_draft, style_memory),
            evaluated_at=datetime.now(timezone.utc),
        )
        self._persist(comparison)
        return comparison

    def _persist(self, comparison: HeldOutComparison) -> None:
        timestamp = comparison.evaluated_at.strftime("%Y%m%dT%H%M%S")
        path = self._dir / f"{timestamp}_{comparison.matter_id}.json"
        path.write_text(comparison.model_dump_json(indent=2), encoding="utf-8")
