from __future__ import annotations

from app.config import get_settings
from app.orchestrator import Orchestrator

_orchestrator: Orchestrator | None = None


def startup_state() -> None:
    global _orchestrator
    _orchestrator = Orchestrator(get_settings())


def teardown_state() -> None:
    global _orchestrator
    _orchestrator = None


def orchestrator() -> Orchestrator:
    if _orchestrator is None:
        raise RuntimeError("Orchestrator not initialised; FastAPI lifespan did not run.")
    return _orchestrator
