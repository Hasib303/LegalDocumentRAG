from __future__ import annotations

from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class ProviderError(Exception):
    pass


class ProviderConfigError(ProviderError):
    pass


class ProviderInvocationError(ProviderError):
    pass


class LLMProvider(Protocol):
    name: str

    def generate_structured(
        self,
        *,
        system: str,
        user: str,
        response_model: type[T],
        temperature: float = 0.1,
        max_output_tokens: int = 1500,
        thinking_budget: int = 0,
    ) -> T: ...


class EmbeddingProvider(Protocol):
    name: str
    dim: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...

    def embed_one(self, text: str) -> list[float]: ...


class RerankerProvider(Protocol):
    name: str

    def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int,
    ) -> list[tuple[int, float]]: ...


class VisionProvider(Protocol):
    name: str

    def extract_text_from_image(
        self,
        image_bytes: bytes,
        *,
        mime_type: str = "image/png",
        prompt: str | None = None,
    ) -> str: ...
