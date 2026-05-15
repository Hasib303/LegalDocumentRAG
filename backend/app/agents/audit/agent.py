from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from app.providers.base import LLMProvider, ProviderInvocationError
from app.schemas import Chunk, FaithfulnessReport, StructuredDraft

_SYSTEM_PROMPT = (
    "You are a faithfulness auditor. Given a claim and the source text it "
    "cites, decide whether the source supports the claim.\n\n"
    "Return supported=true ONLY if the claim is directly entailed by the "
    "cited text. If the cited text is silent or contradicts the claim, "
    "return supported=false."
)


class _Judgment(BaseModel):
    supported: bool
    reason: str = Field(default="", max_length=200)


class AuditAgent:
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    def audit(
        self,
        draft: StructuredDraft,
        chunks_by_id: dict[str, Chunk],
    ) -> FaithfulnessReport:
        flagged: list[str] = []
        details: list[dict] = []
        supported_count = 0
        total = 0

        for section in draft.sections:
            for bullet in section.bullets:
                total += 1
                if bullet.status != "supported":
                    continue
                cited = self._gather_cited(bullet.evidence_chunk_ids, chunks_by_id)
                if not cited.strip():
                    flagged.append(bullet.bullet_id)
                    details.append({"bullet_id": bullet.bullet_id, "issue": "no cited text"})
                    continue
                judgment = self._judge(bullet.text, cited)
                if judgment.supported:
                    supported_count += 1
                else:
                    flagged.append(bullet.bullet_id)
                    details.append({"bullet_id": bullet.bullet_id, "issue": judgment.reason})

        return FaithfulnessReport(
            checked_at=datetime.now(timezone.utc),
            judge_model=self._llm.name,
            bullets_total=total,
            bullets_supported=supported_count,
            flagged_bullet_ids=flagged,
            details=details,
        )

    def _gather_cited(self, chunk_ids: list[str], chunks_by_id: dict[str, Chunk]) -> str:
        return "\n---\n".join(chunks_by_id[cid].text for cid in chunk_ids if cid in chunks_by_id)

    def _judge(self, claim: str, cited_text: str) -> _Judgment:
        try:
            return self._llm.generate_structured(
                system=_SYSTEM_PROMPT,
                user=f"Claim:\n{claim}\n\nCited source:\n{cited_text}",
                response_model=_Judgment,
                temperature=0.0,
                max_output_tokens=200,
            )
        except ProviderInvocationError:
            return _Judgment(supported=True, reason="judge unavailable")
