from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.api.state import orchestrator
from app.orchestrator import DraftBundle, Orchestrator
from app.schemas import StructuredDraft, StyleMemory

router = APIRouter()


def get_orchestrator() -> Orchestrator:
    return orchestrator()


class EditPayload(BaseModel):
    matter_id: str
    matter_type: str | None = None
    operator_id: str | None = None
    edited_markdown: str


@router.get("/{draft_id}")
def get_draft(draft_id: str, orch: Orchestrator = Depends(get_orchestrator)) -> StructuredDraft:  # noqa: B008
    try:
        return orch._draft_repo.load(draft_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{draft_id}/edit")
def submit_edit(
    draft_id: str,
    payload: EditPayload,
    orch: Orchestrator = Depends(get_orchestrator),  # noqa: B008
) -> StyleMemory:
    try:
        draft = orch._draft_repo.load(draft_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    bundle = DraftBundle(draft=draft, markdown="", reference_chunks={})
    return orch.apply_edit(
        bundle,
        payload.edited_markdown,
        matter_type=payload.matter_type,
        matter_id=payload.matter_id,
        operator_id=payload.operator_id,
    )
