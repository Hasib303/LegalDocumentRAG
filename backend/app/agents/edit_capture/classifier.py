from __future__ import annotations

import re

from pydantic import BaseModel, Field

from app.providers.base import LLMProvider, ProviderInvocationError
from app.schemas import ClassifiedEdit, EditAlignment, EditType

_SYSTEM_PROMPT = (
    "You classify an edit a paralegal made to a draft bullet.\n"
    "Pick ONE label from the allowed set; describe the reusable signal in "
    "one sentence the system can apply to future drafts."
)

_MONEY_RE = re.compile(r"\$\d|\d+[\d,]*\.\d|\b\d{4,}\b")
_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d", re.IGNORECASE)


class _LLMLabel(BaseModel):
    edit_type: EditType
    extracted_signal: str = Field(max_length=240)
    confidence: float = Field(ge=0.0, le=1.0)


def _heuristic(edit: EditAlignment) -> ClassifiedEdit | None:
    if edit.action == "added":
        return ClassifiedEdit(
            bullet_id=edit.bullet_id,
            edit_type="addition",
            extracted_signal=f"include: {edit.after[:120] if edit.after else ''}",
            confidence=0.9,
        )
    if edit.action == "removed":
        return ClassifiedEdit(
            bullet_id=edit.bullet_id,
            edit_type="removal",
            extracted_signal=f"omit: {edit.before[:120] if edit.before else ''}",
            confidence=0.9,
        )
    if edit.action == "reordered":
        return ClassifiedEdit(
            bullet_id=edit.bullet_id,
            edit_type="ordering",
            extracted_signal="move bullet to a different position",
            confidence=0.95,
        )
    if edit.action == "modified" and edit.before and edit.after:
        before_has_numbers = bool(_MONEY_RE.search(edit.before) or _DATE_RE.search(edit.before))
        after_has_numbers = bool(_MONEY_RE.search(edit.after) or _DATE_RE.search(edit.after))
        if after_has_numbers and not before_has_numbers:
            return ClassifiedEdit(
                bullet_id=edit.bullet_id,
                edit_type="specificity_increase",
                extracted_signal="prefer specific dates/amounts over vague language",
                confidence=0.85,
            )
    return None


class EditClassifier:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    def classify(self, edits: list[EditAlignment]) -> list[ClassifiedEdit]:
        out: list[ClassifiedEdit] = []
        for edit in edits:
            heuristic = _heuristic(edit)
            if heuristic is not None:
                out.append(heuristic)
                continue
            out.append(self._llm_classify(edit))
        return out

    def _llm_classify(self, edit: EditAlignment) -> ClassifiedEdit:
        user = (
            f"Action: {edit.action}\n"
            f"Before: {edit.before or '(none)'}\n"
            f"After: {edit.after or '(none)'}\n\n"
            "Allowed labels: terminology, style, specificity_increase, "
            "factual_correction, addition, removal, structure, tone, ordering."
        )
        try:
            label = self._llm.generate_structured(
                system=_SYSTEM_PROMPT,
                user=user,
                response_model=_LLMLabel,
                temperature=0.0,
                max_output_tokens=200,
            )
        except ProviderInvocationError:
            return ClassifiedEdit(
                bullet_id=edit.bullet_id,
                edit_type="style",
                extracted_signal="classifier unavailable",
                confidence=0.2,
            )
        return ClassifiedEdit(
            bullet_id=edit.bullet_id,
            edit_type=label.edit_type,
            extracted_signal=label.extracted_signal,
            confidence=label.confidence,
        )
