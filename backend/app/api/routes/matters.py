from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.state import orchestrator
from app.orchestrator import Orchestrator
from app.schemas import Matter

router = APIRouter()


def get_orchestrator() -> Orchestrator:
    return orchestrator()


@router.get("")
def list_matters(orch: Orchestrator = Depends(get_orchestrator)) -> list[Matter]:  # noqa: B008
    return [plan.matter for plan in orch.load_matters()]


@router.post("/{matter_id}/prepare")
def prepare_matter(matter_id: str, orch: Orchestrator = Depends(get_orchestrator)) -> Matter:  # noqa: B008
    plan = next((p for p in orch.load_matters() if p.matter.matter_id == matter_id), None)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"matter {matter_id} not found")
    orch.ingest_and_process(plan)
    orch.index(plan.matter)
    return plan.matter


@router.post("/{matter_id}/draft")
def draft_matter(matter_id: str, orch: Orchestrator = Depends(get_orchestrator)) -> dict:  # noqa: B008
    plan = next((p for p in orch.load_matters() if p.matter.matter_id == matter_id), None)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"matter {matter_id} not found")
    orch.ingest_and_process(plan)
    orch.index(plan.matter)
    bundle = orch.draft(plan.matter, orch.current_style_memory())
    return {"draft_id": bundle.draft.draft_id, "markdown": bundle.markdown}
