from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.state import orchestrator
from app.orchestrator import Orchestrator

router = APIRouter()


def get_orchestrator() -> Orchestrator:
    return orchestrator()


class EvidenceItem(BaseModel):
    chunk_id: str
    document_id: str
    page_range: tuple[int, int]
    text: str


@router.get("/{draft_id}/{bullet_id}")
def get_evidence(
    draft_id: str,
    bullet_id: str,
    orch: Orchestrator = Depends(get_orchestrator),  # noqa: B008
) -> list[EvidenceItem]:
    try:
        draft = orch._draft_repo.load(draft_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    target = None
    for section in draft.sections:
        for bullet in section.bullets:
            if bullet.bullet_id == bullet_id:
                target = bullet
                break
        if target is not None:
            break
    if target is None:
        raise HTTPException(status_code=404, detail=f"bullet {bullet_id} not found")

    document_ids = list({cid.split(":")[0] for cid in target.evidence_chunk_ids})
    chunks = orch._chunk_repo.load_many(document_ids)
    by_id = orch._chunk_repo.by_id(chunks)
    return [
        EvidenceItem(
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            page_range=c.page_range,
            text=c.text,
        )
        for cid in target.evidence_chunk_ids
        if (c := by_id.get(cid)) is not None
    ]
