from __future__ import annotations

from app.providers.base import LLMProvider
from app.schemas import CaseMetadata

_SYSTEM_PROMPT = (
    "You extract structured metadata from a legal document.\n\n"
    "Rules:\n"
    "1. Return only what is explicitly stated in the document.\n"
    "2. If a field is not stated, leave it null. Do not infer or invent.\n"
    "3. For dates, use ISO format YYYY-MM-DD.\n"
    "4. For aliases, capture defined terms (e.g. hereinafter \"the Company\")."
)


class MetadataExtractor:
    def __init__(self, llm: LLMProvider, *, max_chars: int = 8000) -> None:
        self._llm = llm
        self._max_chars = max_chars

    def extract(self, document_text: str) -> CaseMetadata:
        excerpt = document_text[: self._max_chars]
        return self._llm.generate_structured(
            system=_SYSTEM_PROMPT,
            user=f"Document text:\n\n{excerpt}",
            response_model=CaseMetadata,
            temperature=0.0,
            max_output_tokens=1000,
        )
