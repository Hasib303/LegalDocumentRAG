from __future__ import annotations

from functools import lru_cache

from app.config import Settings, get_settings
from app.providers.base import (
    EmbeddingProvider,
    LLMProvider,
    ProviderConfigError,
    RerankerProvider,
    VisionProvider,
)
from app.providers.embedding.local import LocalEmbedder
from app.providers.llm.gemini import GeminiLLMProvider
from app.providers.llm.groq import GroqLLMProvider
from app.providers.reranker.local import LocalReranker
from app.providers.vision.gemini import GeminiVisionProvider


def _make_llm(model_id: str, settings: Settings, role: str) -> LLMProvider:
    if model_id.startswith("groq:"):
        if not settings.secrets.groq_api_key:
            raise ProviderConfigError(f"{role}: GROQ_API_KEY not set")
        return GroqLLMProvider(
            api_key=settings.secrets.groq_api_key,
            model=model_id.removeprefix("groq:"),
        )
    if model_id.startswith("gemini"):
        if not settings.secrets.gemini_api_key:
            raise ProviderConfigError(f"{role}: GEMINI_API_KEY not set")
        return GeminiLLMProvider(
            api_key=settings.secrets.gemini_api_key,
            model=model_id,
        )
    raise ProviderConfigError(f"{role}: unrecognised model id {model_id!r}")


def _make_vision(model_id: str, settings: Settings) -> VisionProvider:
    if model_id.startswith("gemini"):
        if not settings.secrets.gemini_api_key:
            raise ProviderConfigError("vision: GEMINI_API_KEY not set")
        return GeminiVisionProvider(
            api_key=settings.secrets.gemini_api_key,
            model=model_id,
        )
    raise ProviderConfigError(f"vision: unrecognised model id {model_id!r}")


# Roles: primary, fallback, context_writer, edit_classifier
@lru_cache(maxsize=4)
def llm_provider(role: str = "primary") -> LLMProvider:
    settings = get_settings()
    models = settings.config.models
    model_id = {
        "primary": models.generator_primary,
        "fallback": models.generator_fallback,
        "context_writer": models.context_writer,
        "edit_classifier": models.edit_classifier,
    }.get(role)
    if model_id is None:
        raise ProviderConfigError(f"unknown LLM role {role!r}")
    return _make_llm(model_id, settings, role)


@lru_cache(maxsize=1)
def vision_provider() -> VisionProvider:
    settings = get_settings()
    return _make_vision(settings.config.models.vision, settings)


@lru_cache(maxsize=1)
def embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    return LocalEmbedder(model_name=settings.config.models.embedder)


@lru_cache(maxsize=1)
def reranker_provider() -> RerankerProvider:
    settings = get_settings()
    return LocalReranker(model_name=settings.config.models.reranker)
