from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_CONFIG_PATH = _BACKEND_ROOT / "config.yaml"


class ModelSettings(BaseModel):
    embedder: str
    reranker: str
    generator_primary: str
    generator_fallback: str
    vision: str
    context_writer: str
    edit_classifier: str


class OCRSettings(BaseModel):
    confidence_threshold: float = Field(ge=0.0, le=1.0)
    rasterize_dpi: int = Field(ge=72)
    rasterize_dpi_degraded: int = Field(ge=72)


class ChunkingSettings(BaseModel):
    target_tokens: int = Field(ge=64)
    overlap_tokens: int = Field(ge=0)
    respect_sections: bool
    contextual_prepend: bool


class RetrievalSettings(BaseModel):
    k_dense: int = Field(ge=1)
    k_sparse: int = Field(ge=1)
    rrf_k: int = Field(ge=1)
    rerank_top_n: int = Field(ge=1)


class GenerationSettings(BaseModel):
    temperature: float = Field(ge=0.0, le=2.0)
    max_output_tokens: int = Field(ge=64)
    require_citations: bool
    thinking_budget: int = Field(ge=0)


class LearningSettings(BaseModel):
    terminology_graduation_threshold: int = Field(ge=1)
    exemplars_per_section: int = Field(ge=1)
    rule_min_corroborating_edits: int = Field(ge=1)
    exemplar_decay_days: int = Field(ge=1)


class EvaluationSettings(BaseModel):
    held_out_matter_ids: list[str] = []


class Paths(BaseModel):
    data_root: Path
    raw: Path
    manifests: Path
    processed: Path
    chunks: Path
    vector_store: Path
    drafts: Path
    edits: Path
    style_memory: Path
    evals: Path
    logs: Path

    def resolve_all(self, base: Path) -> Paths:
        resolved = {
            name: (base / value).resolve() if not value.is_absolute() else value
            for name, value in self.model_dump().items()
        }
        return Paths.model_validate(resolved)


class AppConfig(BaseModel):
    models: ModelSettings
    ocr: OCRSettings
    chunking: ChunkingSettings
    retrieval: RetrievalSettings
    generation: GenerationSettings
    learning: LearningSettings
    evaluation: EvaluationSettings
    paths: Paths


class EnvSecrets(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str | None = None
    groq_api_key: str | None = None
    qdrant_url: str = "http://localhost:6333"
    ollama_base_url: str = "http://localhost:11434"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    voyage_api_key: str | None = None


class Settings(BaseModel):
    config: AppConfig
    secrets: EnvSecrets


@lru_cache(maxsize=1)
def get_settings(config_path: Path | None = None) -> Settings:
    path = config_path or _DEFAULT_CONFIG_PATH
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    config = AppConfig.model_validate(raw)
    config = config.model_copy(update={"paths": config.paths.resolve_all(_BACKEND_ROOT)})
    return Settings(config=config, secrets=EnvSecrets())
