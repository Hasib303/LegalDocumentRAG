"""Document ingestion and processing schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.schemas._types import ExtractionMethod


class DocumentManifest(BaseModel):
    """Result of ingesting a raw file. SHA-256 makes the id idempotent."""

    document_id: str
    sha256: str
    original_filename: str
    mime_type: str
    page_count: int = Field(ge=1)
    bytes: int = Field(ge=0)
    ingested_at: datetime
    tags: list[str] = []


class Party(BaseModel):
    name: str
    role: str | None = None


class Attorney(BaseModel):
    name: str
    represents: str | None = None
    bar_number: str | None = None


class CaseMetadata(BaseModel):
    """Structured-extraction output. Every field nullable — never invented."""

    case_caption: str | None = None
    case_number: str | None = None
    court: str | None = None
    filing_date: date | None = None
    document_type: str | None = None
    parties: list[Party] = []
    attorneys: list[Attorney] = []
    aliases: dict[str, str] = {}


class TextBlock(BaseModel):
    block_id: str
    text: str
    bbox: tuple[float, float, float, float] | None = None
    extraction_method: ExtractionMethod
    confidence: float = Field(ge=0.0, le=1.0)


class Annotation(BaseModel):
    """Margin notes, stamps, signatures — anything not part of the body text."""

    annotation_id: str
    text: str
    annotation_type: str
    bbox: tuple[float, float, float, float] | None = None


class ProcessedPage(BaseModel):
    page_number: int = Field(ge=1)
    blocks: list[TextBlock]
    annotations: list[Annotation] = []
    quality_score: float = Field(ge=0.0, le=1.0)


class ExtractionSummary(BaseModel):
    total_pages: int = Field(ge=0)
    pages_pdf_text: int = 0
    pages_tesseract: int = 0
    pages_paddle_ocr: int = 0
    pages_vision_llm: int = 0
    low_confidence_pages: list[int] = []


class ProcessedDocument(BaseModel):
    document_id: str
    pages: list[ProcessedPage]
    metadata: CaseMetadata
    extraction_summary: ExtractionSummary
    processed_at: datetime
