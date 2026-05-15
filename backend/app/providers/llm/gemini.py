from __future__ import annotations

import json
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.providers.base import ProviderInvocationError

T = TypeVar("T", bound=BaseModel)


# Pydantic's default JSON Schema uses features Gemini Developer API rejects:
#   - additionalProperties: false  (closed-model marker)
#   - $defs + $ref                  (nested-model factoring)
#   - anyOf: [X, {"type": "null"}]  (Pydantic optional encoding)
# Normalise into Gemini-compatible OpenAPI 3.0 before sending.


def _clean_schema_for_gemini(model: type[BaseModel]) -> dict[str, Any]:
    return _normalise(_inline_refs(model.model_json_schema()))


def _inline_refs(schema: dict[str, Any]) -> dict[str, Any]:
    defs = schema.get("$defs", {})

    def resolve(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                ref = node["$ref"]
                if ref.startswith("#/$defs/"):
                    target = defs.get(ref.removeprefix("#/$defs/"))
                    if target is not None:
                        return resolve(target)
            return {k: resolve(v) for k, v in node.items() if k != "$defs"}
        if isinstance(node, list):
            return [resolve(item) for item in node]
        return node

    return resolve(schema)


def _normalise(schema: Any) -> Any:
    if isinstance(schema, list):
        return [_normalise(item) for item in schema]
    if not isinstance(schema, dict):
        return schema

    any_of = schema.get("anyOf")
    if isinstance(any_of, list) and len(any_of) == 2:
        null_idx = next(
            (
                i
                for i, item in enumerate(any_of)
                if isinstance(item, dict) and item.get("type") == "null"
            ),
            None,
        )
        if null_idx is not None:
            other = any_of[1 - null_idx]
            if isinstance(other, dict):
                merged = {**schema, **other, "nullable": True}
                merged.pop("anyOf", None)
                schema = merged

    return {
        k: _normalise(v)
        for k, v in schema.items()
        if k not in ("additionalProperties", "title", "$schema")
    }


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
        schema = _clean_schema_for_gemini(response_model)
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_mime_type="application/json",
            response_schema=schema,
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

        return self._parse_response(response, response_model)

    def _parse_response(self, response: Any, response_model: type[T]) -> T:
        parsed = response.parsed
        if isinstance(parsed, response_model):
            return parsed
        if parsed is None:
            if not response.text:
                raise ProviderInvocationError(f"Gemini {self._model} returned empty response")
            try:
                parsed = json.loads(response.text)
            except json.JSONDecodeError as exc:
                raise ProviderInvocationError(
                    f"Gemini {self._model} returned invalid JSON: {response.text!r}"
                ) from exc

        try:
            return response_model.model_validate(parsed)
        except ValidationError as exc:
            raise ProviderInvocationError(
                f"Gemini {self._model} schema validation failed: {exc}"
            ) from exc
