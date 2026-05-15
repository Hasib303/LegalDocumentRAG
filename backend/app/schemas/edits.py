from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas._types import EditType

EditAction = Literal["modified", "added", "removed", "reordered"]


class EditAlignment(BaseModel):

    bullet_id: str
    action: EditAction
    before: str | None = None
    after: str | None = None
    evidence_chunk_ids: list[str] = []
    from_index: int | None = None
    to_index: int | None = None

    @model_validator(mode="after")
    def _action_invariants(self) -> EditAlignment:
        if self.action == "added" and self.before is not None:
            raise ValueError("'added' edits must have before=None")
        if self.action == "removed" and self.after is not None:
            raise ValueError("'removed' edits must have after=None")
        if self.action == "reordered" and (self.from_index is None or self.to_index is None):
            raise ValueError("'reordered' edits require from_index and to_index")
        return self


class ClassifiedEdit(BaseModel):
    bullet_id: str
    edit_type: EditType
    extracted_signal: str
    confidence: float = Field(ge=0.0, le=1.0)


class EditSession(BaseModel):
    edit_id: str
    draft_id: str
    operator_id: str | None = None
    edited_at: datetime
    alignment: list[EditAlignment]
    classified_edits: list[ClassifiedEdit]
