from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

from app.agents.audit import AuditAgent
from app.agents.drafting import DraftingAgent
from app.agents.edit_capture import EditCaptureAgent, render_draft
from app.agents.evaluation import EvaluationAgent, HeldOutComparison
from app.agents.indexer import IndexerAgent, SparseIndex, VectorStore
from app.agents.ingest import IngestAgent
from app.agents.learning import LearningAgent
from app.agents.processing import ProcessingAgent
from app.agents.retrieval import RetrievalAgent
from app.config import Settings
from app.providers import (
    embedding_provider,
    llm_provider,
    reranker_provider,
    vision_provider,
)
from app.repositories import (
    ChunkRepository,
    DocumentRepository,
    DraftRepository,
    EditRepository,
    StyleMemoryRepository,
)
from app.schemas import (
    DocumentManifest,
    Matter,
    RetrievalConfig,
    StructuredDraft,
    StyleMemory,
)


@dataclass
class MatterPlan:
    matter: Matter
    document_paths: dict[str, Path] = field(default_factory=dict)


@dataclass
class DraftBundle:
    draft: StructuredDraft
    markdown: str
    reference_chunks: dict[str, str]


class Orchestrator:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        paths = settings.config.paths

        self._doc_repo = DocumentRepository(paths.manifests, paths.processed)
        self._chunk_repo = ChunkRepository(paths.chunks)
        self._draft_repo = DraftRepository(paths.drafts)
        self._edit_repo = EditRepository(paths.edits)
        self._style_repo = StyleMemoryRepository(paths.style_memory)

        embedder = embedding_provider()
        reranker = reranker_provider()
        primary_llm = llm_provider("primary")
        vision = vision_provider()
        classifier_llm = llm_provider("edit_classifier")
        judge_llm = llm_provider("edit_classifier")

        vector_store = VectorStore(path=paths.vector_store)
        sparse_index = SparseIndex()

        self._ingest = IngestAgent(self._doc_repo)
        self._processing = ProcessingAgent(
            repo=self._doc_repo,
            vision=vision,
            llm=primary_llm,
            rasterize_dpi=settings.config.ocr.rasterize_dpi,
        )
        self._indexer = IndexerAgent(
            embedder=embedder,
            vector_store=vector_store,
            sparse_index=sparse_index,
            chunk_repo=self._chunk_repo,
            target_tokens=settings.config.chunking.target_tokens,
            overlap_tokens=settings.config.chunking.overlap_tokens,
        )
        retrieval_config = RetrievalConfig(**settings.config.retrieval.model_dump())
        self._retrieval = RetrievalAgent(
            embedder=embedder,
            reranker=reranker,
            vector_store=vector_store,
            sparse_index=sparse_index,
            chunk_repo=self._chunk_repo,
            config=retrieval_config,
        )
        self._drafting = DraftingAgent(
            llm=primary_llm,
            retrieval=self._retrieval,
            temperature=settings.config.generation.temperature,
            max_output_tokens=settings.config.generation.max_output_tokens,
        )
        self._audit = AuditAgent(judge_llm)
        self._edit_capture = EditCaptureAgent(embedder=embedder, llm=classifier_llm)
        self._learning = LearningAgent(
            repo=self._style_repo,
            exemplars_per_section=settings.config.learning.exemplars_per_section,
        )
        self._evaluation = EvaluationAgent(paths.evals / "results")

    # ─── corpus + matters ────────────────────────────────────────────────────

    def load_matters(self) -> list[MatterPlan]:
        config_path = self._settings.config.paths.data_root / "matters.yaml"
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        plans: list[MatterPlan] = []
        for entry in raw.get("matters", []):
            paths = {
                p.name: (self._settings.config.paths.data_root / p).resolve()
                for p in (Path(rel) for rel in entry["documents"])
            }
            matter = Matter(
                matter_id=entry["id"],
                name=entry["name"],
                document_ids=[],
                matter_type=entry.get("matter_type"),
                created_at=datetime.now(timezone.utc),
                held_out=entry.get("held_out", False),
            )
            plans.append(MatterPlan(matter=matter, document_paths=paths))
        return plans

    def ingest_and_process(self, plan: MatterPlan) -> Matter:
        manifests: list[DocumentManifest] = []
        for path in plan.document_paths.values():
            manifest = self._ingest.ingest(path, tags=[plan.matter.matter_id])
            self._processing.process(manifest, path)
            manifests.append(manifest)
        plan.matter.document_ids = [m.document_id for m in manifests]
        return plan.matter

    def index(self, matter: Matter) -> None:
        for doc_id in matter.document_ids:
            processed = self._doc_repo.load_processed(doc_id)
            self._indexer.index_document(processed, matter_id=matter.matter_id)
        self._indexer.index_matter(matter.matter_id, matter.document_ids)

    # ─── drafts ──────────────────────────────────────────────────────────────

    def draft(self, matter: Matter, style_memory: StyleMemory) -> DraftBundle:
        draft = self._drafting.draft(
            matter_id=matter.matter_id,
            document_ids=matter.document_ids,
            style_memory=style_memory,
        )
        chunks = self._chunk_repo.load_many(matter.document_ids)
        chunks_by_id = self._chunk_repo.by_id(chunks)
        report = self._audit.audit(draft, chunks_by_id)
        draft = draft.model_copy(update={"faithfulness_report": report})

        markdown = render_draft(draft)
        self._draft_repo.save(draft, markdown=markdown)
        return DraftBundle(
            draft=draft,
            markdown=markdown,
            reference_chunks={cid: c.text for cid, c in chunks_by_id.items()},
        )

    # ─── learning ────────────────────────────────────────────────────────────

    def apply_edit(
        self,
        bundle: DraftBundle,
        edited_markdown: str,
        matter_type: str | None,
        matter_id: str,
        operator_id: str | None = None,
    ) -> StyleMemory:
        edit = self._edit_capture.capture(bundle.draft, edited_markdown, operator_id)
        self._edit_repo.save(edit)
        return self._learning.learn(
            edit=edit,
            original_draft=bundle.draft,
            matter_type=matter_type,
            matter_id=matter_id,
        )

    # ─── evaluation ──────────────────────────────────────────────────────────

    def evaluate(
        self,
        *,
        matter: Matter,
        baseline: DraftBundle,
        learned: DraftBundle,
        reference_markdown: str,
        style_memory: StyleMemory,
    ) -> HeldOutComparison:
        return self._evaluation.compare(
            matter_id=matter.matter_id,
            baseline_draft=baseline.draft,
            learned_draft=learned.draft,
            reference_text=reference_markdown,
            style_memory=style_memory,
        )

    # ─── style-memory helpers ────────────────────────────────────────────────

    def current_style_memory(self) -> StyleMemory:
        return self._style_repo.latest()

    def style_memory_version(self, version: int) -> StyleMemory:
        return self._style_repo.load_version(version)

    def reset_style_memory(self) -> StyleMemory:
        empty = StyleMemory(version=0, updated_at=datetime.now(timezone.utc))
        self._style_repo.save(empty)
        return empty
