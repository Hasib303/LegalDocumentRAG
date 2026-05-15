from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pymupdf

from app.agents.processing.metadata_extractor import MetadataExtractor
from app.agents.processing.page_extractor import PageExtractor
from app.providers.base import LLMProvider, ProviderInvocationError, VisionProvider
from app.repositories.documents import DocumentRepository
from app.schemas import (
    CaseMetadata,
    DocumentManifest,
    ExtractionSummary,
    ProcessedDocument,
    ProcessedPage,
)

_LOW_CONFIDENCE_THRESHOLD = 0.80


class ProcessingAgent:
    def __init__(
        self,
        *,
        repo: DocumentRepository,
        vision: VisionProvider,
        llm: LLMProvider,
        rasterize_dpi: int = 300,
    ) -> None:
        self._repo = repo
        self._page_extractor = PageExtractor(vision, rasterize_dpi=rasterize_dpi)
        self._metadata_extractor = MetadataExtractor(llm)

    def process(
        self,
        manifest: DocumentManifest,
        source_path: Path,
    ) -> ProcessedDocument:
        if self._repo.processed_exists(manifest.document_id):
            return self._repo.load_processed(manifest.document_id)

        pages, summary = self._extract_pages(source_path)
        metadata = self._safe_extract_metadata(pages)

        processed = ProcessedDocument(
            document_id=manifest.document_id,
            pages=pages,
            metadata=metadata,
            extraction_summary=summary,
            processed_at=datetime.now(timezone.utc),
        )
        self._repo.save_processed(processed)
        return processed

    def _extract_pages(
        self, source_path: Path
    ) -> tuple[list[ProcessedPage], ExtractionSummary]:
        pages: list[ProcessedPage] = []
        counts = {"pdf-text": 0, "tesseract": 0, "paddle_ocr": 0, "vision_llm": 0}
        low_confidence: list[int] = []

        with pymupdf.open(source_path) as doc:
            for page_number, page in enumerate(doc, start=1):
                block, method = self._page_extractor.extract(page, page_number)
                pages.append(
                    ProcessedPage(
                        page_number=page_number,
                        blocks=[block],
                        quality_score=block.confidence,
                    )
                )
                counts[method] += 1
                if block.confidence < _LOW_CONFIDENCE_THRESHOLD:
                    low_confidence.append(page_number)

        summary = ExtractionSummary(
            total_pages=len(pages),
            pages_pdf_text=counts["pdf-text"],
            pages_tesseract=counts["tesseract"],
            pages_paddle_ocr=counts["paddle_ocr"],
            pages_vision_llm=counts["vision_llm"],
            low_confidence_pages=low_confidence,
        )
        return pages, summary

    def _safe_extract_metadata(self, pages: list[ProcessedPage]) -> CaseMetadata:
        full_text = "\n\n".join(b.text for page in pages for b in page.blocks)
        # LLM may rate-limit or 4xx; we'd rather ship a draft with null metadata
        # than abort the whole pipeline on a single document.
        try:
            return self._metadata_extractor.extract(full_text)
        except ProviderInvocationError:
            return CaseMetadata()
