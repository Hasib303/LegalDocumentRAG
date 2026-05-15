from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class Matter(BaseModel):

    matter_id: str
    name: str
    document_ids: list[str]
    matter_type: str | None = None
    created_at: datetime
    held_out: bool = False
