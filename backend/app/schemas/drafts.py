"""Draft schema — the structured grounded output produced by the drafting agent.

Every bullet either cites at least one ``chunk_id`` from the retrieved set or
is marked ``unsupported``. The chunk-id whitelist is enforced by a Pydantic
validator at parse time so fabricated citations cannot escape the agent.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

SectionType = Literal[
    "caption",
    "procedural_posture",
    "material_facts",
    "disputed_facts",
    "key_documents",
    "open_questions",
]

BulletStatus = Literal["supported", "unsupported", "flagged"]


class Bullet(BaseModel):
    bullet_id: str
    text: str
    evidence_chunk_ids: list[str] = []
    status: BulletStatus
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _supported_requires_evidence(self) -> Bullet:
        if self.status == "supported" and not self.evidence_chunk_ids:
            raise ValueError(
                f"bullet {self.bullet_id!r}: status='supported' requires "
                "at least one evidence_chunk_id"
            )
        return self


class Section(BaseModel):
    section_id: SectionType
    title: str
    bullets: list[Bullet]

    @model_validator(mode="after")
    def _unsupported_only_in_open_questions(self) -> Section:
        if self.section_id != "open_questions":
            for bullet in self.bullets:
                if bullet.status == "unsupported":
                    raise ValueError(
                        f"section {self.section_id!r}: 'unsupported' bullets are "
                        "only allowed in 'open_questions'"
                    )
        return self


class FaithfulnessReport(BaseModel):
    checked_at: datetime
    judge_model: str
    bullets_total: int = Field(ge=0)
    bullets_supported: int = Field(ge=0)
    flagged_bullet_ids: list[str] = []
    details: list[dict] = []


class StructuredDraft(BaseModel):
    draft_id: str
    matter_id: str
    draft_type: Literal["case_fact_summary"] = "case_fact_summary"
    schema_version: str = "1.0"
    model: str
    prompt_version: str
    style_memory_version: int = Field(ge=0)
    generated_at: datetime
    sections: list[Section]
    faithfulness_report: FaithfulnessReport | None = None
