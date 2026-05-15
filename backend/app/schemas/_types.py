from __future__ import annotations

from typing import Literal

ExtractionMethod = Literal["pdf-text", "tesseract", "paddle_ocr", "vision_llm"]

EditType = Literal[
    "terminology",
    "style",
    "specificity_increase",
    "factual_correction",
    "addition",
    "removal",
    "structure",
    "tone",
    "ordering",
]
