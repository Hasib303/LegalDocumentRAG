from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.providers.base import ProviderInvocationError

T = TypeVar("T", bound=BaseModel)


class GroqLLMProvider:
    name = "groq"

    def __init__(self, api_key: str, model: str) -> None:
        import instructor
        from groq import Groq

        self._client = instructor.from_groq(Groq(api_key=api_key))
        self._model = model

    def generate_structured(
        self,
        *,
        system: str,
        user: str,
        response_model: type[T],
        temperature: float = 0.1,
        max_output_tokens: int = 1500,
        thinking_budget: int = 0,  # noqa: ARG002 — Groq has no thinking-budget knob
    ) -> T:
        from groq import GroqError

        try:
            return self._client.chat.completions.create(
                model=self._model,
                response_model=response_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature,
                max_tokens=max_output_tokens,
                max_retries=2,
            )
        except GroqError as exc:
            raise ProviderInvocationError(f"Groq {self._model} failed: {exc}") from exc
        except ValidationError as exc:
            raise ProviderInvocationError(
                f"Groq {self._model} schema validation failed: {exc}"
            ) from exc
