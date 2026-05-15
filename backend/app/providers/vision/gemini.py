from __future__ import annotations

from app.providers.base import ProviderInvocationError

# Forbids the model from inferring obscured content — known failure mode of
# open VLMs that fill in redacted regions from surrounding context.
_DEFAULT_OCR_PROMPT = (
    "Extract ALL visible text from this image exactly as written. "
    "Preserve original formatting, including punctuation, capitalization, "
    "and line breaks. "
    "For redacted (blacked-out) regions, output the literal token [REDACTED]. "
    "Do not infer or fill in obscured content under any circumstances. "
    "If the image is entirely unreadable, respond with [ILLEGIBLE]. "
    "Return only the extracted text — no commentary."
)


class GeminiVisionProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def extract_text_from_image(
        self,
        image_bytes: bytes,
        *,
        mime_type: str = "image/png",
        prompt: str | None = None,
    ) -> str:
        from google.genai import types
        from google.genai.errors import APIError

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=[
                    prompt or _DEFAULT_OCR_PROMPT,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ],
            )
        except APIError as exc:
            raise ProviderInvocationError(f"Gemini vision {self._model} failed: {exc}") from exc

        return response.text or ""
