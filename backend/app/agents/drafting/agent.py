from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from app.agents.drafting.prompts import SECTION_QUERIES
from app.agents.drafting.section_generator import SectionGenerator
from app.agents.retrieval.agent import RetrievalAgent
from app.providers.base import LLMProvider, ProviderInvocationError

logger = logging.getLogger(__name__)
from app.schemas import (
    Bullet,
    RetrievedChunk,
    Section,
    SectionType,
    StructuredDraft,
    StyleMemory,
)

PROMPT_VERSION = "v1"
_SECTION_ORDER: tuple[SectionType, ...] = (
    "caption",
    "procedural_posture",
    "material_facts",
    "disputed_facts",
    "key_documents",
    "open_questions",
)


class DraftingAgent:
    def __init__(
        self,
        *,
        llm: LLMProvider,
        retrieval: RetrievalAgent,
        temperature: float = 0.1,
        max_output_tokens: int = 1500,
    ) -> None:
        self._llm = llm
        self._retrieval = retrieval
        self._generator = SectionGenerator(
            llm,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

    def draft(
        self,
        *,
        matter_id: str,
        document_ids: list[str],
        style_memory: StyleMemory,
    ) -> StructuredDraft:
        sections: list[Section] = []
        all_retrieved: list[RetrievedChunk] = []

        for section_id in _SECTION_ORDER:
            query = self._enrich_query(SECTION_QUERIES[section_id], style_memory)
            result = self._retrieval.retrieve(query, matter_id, document_ids)
            retrieved_ids = {rc.chunk_id for rc in result.retrieved}
            all_retrieved.extend(result.retrieved)
            logger.info(
                "draft %s/%s: %d chunks retrieved", matter_id, section_id, len(result.retrieved)
            )
            try:
                section = self._generator.generate(section_id, result.retrieved)
            except ProviderInvocationError as exc:
                logger.warning("draft %s/%s: provider failed → empty: %s", matter_id, section_id, exc)
                section = _empty_section(section_id)
            except Exception:
                logger.exception("draft %s/%s: unexpected failure → empty", matter_id, section_id)
                section = _empty_section(section_id)
            sections.append(_enforce_citation_whitelist(section, retrieved_ids))

        return StructuredDraft(
            draft_id=f"draft_{uuid.uuid4().hex[:12]}",
            matter_id=matter_id,
            model=self._llm.name,
            prompt_version=PROMPT_VERSION,
            style_memory_version=style_memory.version,
            generated_at=datetime.now(timezone.utc),
            sections=sections,
        )

    def _enrich_query(self, base_query: str, style: StyleMemory) -> str:
        if not style.section_rules:
            return base_query
        terms = " ".join(rule.rule_text for rule in style.section_rules[:3])
        return f"{base_query} {terms}".strip()


def _empty_section(section_id: SectionType) -> Section:
    from app.agents.drafting.prompts import SECTION_TITLES

    return Section(section_id=section_id, title=SECTION_TITLES[section_id], bullets=[])


def _enforce_citation_whitelist(section: Section, retrieved_ids: set[str]) -> Section:
    sanitised: list[Bullet] = []
    for bullet in section.bullets:
        valid_ids = [cid for cid in bullet.evidence_chunk_ids if cid in retrieved_ids]
        if bullet.status == "supported" and not valid_ids:
            sanitised.append(
                Bullet(
                    bullet_id=bullet.bullet_id,
                    text=bullet.text,
                    evidence_chunk_ids=[],
                    status="flagged",
                    confidence=bullet.confidence,
                )
            )
            continue
        sanitised.append(
            Bullet(
                bullet_id=bullet.bullet_id,
                text=bullet.text,
                evidence_chunk_ids=valid_ids,
                status=bullet.status,
                confidence=bullet.confidence,
            )
        )
    return Section(section_id=section.section_id, title=section.title, bullets=sanitised)
