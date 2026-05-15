from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from app.providers.base import ProviderInvocationError

T = TypeVar("T", bound=BaseModel)


class GeminiLLMProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def generate_structured(
        self,
        *,
        system: str,
        user: str,
        response_model: type[T],
        temperature: float = 0.1,
        max_output_tokens: int = 1500,
        thinking_budget: int = 0,
    ) -> T:
        from google.genai import types
        from google.genai.errors import APIError

        thinking_config = (
            types.ThinkingConfig(thinking_budget=thinking_budget)
            if thinking_budget > 0
            else None
        )
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_mime_type="application/json",
            response_schema=response_model,
            thinking_config=thinking_config,
        )

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=user,
                config=config,
            )
        except APIError as exc:
            raise ProviderInvocationError(f"Gemini {self._model} failed: {exc}") from exc

        parsed = response.parsed
        if isinstance(parsed, response_model):
            return parsed
        if parsed is None:
            raise ProviderInvocationError(
                f"Gemini {self._model} returned no parsed response; raw: {response.text!r}"
            )
        return response_model.model_validate(parsed)
