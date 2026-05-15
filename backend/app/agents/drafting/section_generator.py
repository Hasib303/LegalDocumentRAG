from __future__ import annotations

from pydantic import BaseModel, Field

from app.agents.drafting.prompts import (
    SECTION_INSTRUCTIONS,
    SECTION_TITLES,
    SYSTEM_PROMPT,
    render_evidence,
)
from app.providers.base import LLMProvider
from app.schemas import Bullet, RetrievedChunk, Section, SectionType
from app.schemas.drafts import BulletStatus


# Sent to the LLM. No model_validators here — those live on the public Bullet
# and would reject slightly-off LLM output. We coerce defensively in _to_bullet
# instead, so a "supported but no evidence" bullet becomes "flagged", never an
# exception that kills the whole section.
class _DraftBullet(BaseModel):
    text: str
    evidence_chunk_ids: list[str] = []
    status: BulletStatus
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class _DraftSection(BaseModel):
    bullets: list[_DraftBullet]


class SectionGenerator:
    def __init__(
        self,
        llm: LLMProvider,
        *,
        temperature: float = 0.1,
        max_output_tokens: int = 1500,
    ) -> None:
        self._llm = llm
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens

    def generate(
        self,
        section_id: SectionType,
        retrieved: list[RetrievedChunk],
    ) -> Section:
        numbered = [(rc.chunk_id, rc.snippet) for rc in retrieved]
        evidence_block = render_evidence(numbered) if numbered else "(no evidence retrieved)"

        user = (
            f"Section: {SECTION_TITLES[section_id]}\n"
            f"Task: {SECTION_INSTRUCTIONS[section_id]}\n\n"
            f"Evidence (cite by chunk_id):\n{evidence_block}"
        )

        draft = self._llm.generate_structured(
            system=SYSTEM_PROMPT,
            user=user,
            response_model=_DraftSection,
            temperature=self._temperature,
            max_output_tokens=self._max_output_tokens,
        )

        bullets = [_to_bullet(section_id, i, b) for i, b in enumerate(draft.bullets)]
        return Section(
            section_id=section_id,
            title=SECTION_TITLES[section_id],
            bullets=bullets,
        )


def _to_bullet(section_id: SectionType, idx: int, draft: _DraftBullet) -> Bullet:
    status: BulletStatus = draft.status
    if status == "supported" and not draft.evidence_chunk_ids:
        status = "flagged"
    if status == "unsupported" and section_id != "open_questions":
        status = "flagged"
    return Bullet(
        bullet_id=f"{section_id}.{idx}",
        text=draft.text,
        evidence_chunk_ids=draft.evidence_chunk_ids,
        status=status,
        confidence=draft.confidence,
    )
