from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app import __version__
from app.api.routes import drafts, evidence, matters
from app.api.state import startup_state, teardown_state


@asynccontextmanager
async def _lifespan(_: FastAPI) -> AsyncIterator[None]:
    startup_state()
    try:
        yield
    finally:
        teardown_state()


def create_app() -> FastAPI:
    app = FastAPI(title="NerdFarm", version=__version__, lifespan=_lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    app.include_router(matters.router, prefix="/matters", tags=["matters"])
    app.include_router(drafts.router, prefix="/drafts", tags=["drafts"])
    app.include_router(evidence.router, prefix="/evidence", tags=["evidence"])
    return app


app = create_app()
