from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas._types import EditType


class TerminologyEntry(BaseModel):

    model_config = ConfigDict(populate_by_name=True)

    from_term: str = Field(alias="from")
    to_term: str = Field(alias="to")
    frequency: int = Field(ge=1)
    first_seen_edit_id: str


class SectionRule(BaseModel):
    section_id: str
    rule_text: str
    support_count: int = Field(ge=1)
    source_matter_ids: list[str] = []


class Exemplar(BaseModel):

    exemplar_id: str
    section_id: str
    matter_type: str | None = None
    topic_chunk_id: str | None = None
    before: str
    after: str
    evidence_chunk_ids: list[str] = []
    edit_classes: list[EditType] = []
    created_at: datetime


class StructuralPreferences(BaseModel):
    section_order: list[str] = []
    avg_bullets_per_section: dict[str, float] = {}


class StyleMemory(BaseModel):
    version: int = Field(ge=0)
    updated_at: datetime
    based_on_edit_ids: list[str] = []
    terminology_map: list[TerminologyEntry] = []
    section_rules: list[SectionRule] = []
    exemplar_store: list[Exemplar] = []
    structural_preferences: StructuralPreferences = Field(default_factory=StructuralPreferences)
