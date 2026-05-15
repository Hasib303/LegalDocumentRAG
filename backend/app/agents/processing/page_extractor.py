from __future__ import annotations

import pymupdf

from app.agents.processing.text_quality import has_usable_text
from app.providers.base import VisionProvider
from app.schemas import TextBlock

_PDF_TEXT_CONFIDENCE = 0.99
_VISION_FALLBACK_CONFIDENCE = 0.85


class PageExtractor:
    def __init__(self, vision: VisionProvider, *, rasterize_dpi: int = 300) -> None:
        self._vision = vision
        self._dpi = rasterize_dpi

    def extract(self, page: pymupdf.Page, page_number: int) -> tuple[TextBlock, str]:
        text = page.get_text("text")
        if has_usable_text(text):
            return (
                TextBlock(
                    block_id=f"p{page_number}_b0",
                    text=text.strip(),
                    extraction_method="pdf-text",
                    confidence=_PDF_TEXT_CONFIDENCE,
                ),
                "pdf-text",
            )

        pix = page.get_pixmap(dpi=self._dpi)
        vision_text = self._vision.extract_text_from_image(
            pix.tobytes("png"),
            mime_type="image/png",
        )
        return (
            TextBlock(
                block_id=f"p{page_number}_b0",
                text=vision_text.strip(),
                extraction_method="vision_llm",
                confidence=_VISION_FALLBACK_CONFIDENCE,
            ),
            "vision_llm",
        )
