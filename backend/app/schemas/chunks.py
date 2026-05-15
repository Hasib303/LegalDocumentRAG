from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas._types import ExtractionMethod


class Chunk(BaseModel):

    chunk_id: str
    document_id: str
    matter_id: str | None = None
    section_label: str | None = None
    page_range: tuple[int, int]
    char_offsets: tuple[int, int]
    text: str
    token_count: int = Field(ge=1)
    extraction_method: ExtractionMethod
    embedding_model: str | None = None
    contextual_prefix: str | None = None
