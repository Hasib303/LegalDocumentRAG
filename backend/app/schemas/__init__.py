"""Pydantic message contracts shared across agents.

Schemas are the only types crossing agent boundaries. Agents never import
each other; they exchange instances of the models exported here.
"""

from app.schemas._types import EditType, ExtractionMethod
from app.schemas.chunks import Chunk
from app.schemas.documents import (
    Annotation,
    Attorney,
    CaseMetadata,
    DocumentManifest,
    ExtractionSummary,
    Party,
    ProcessedDocument,
    ProcessedPage,
    TextBlock,
)
from app.schemas.drafts import (
    Bullet,
    BulletStatus,
    FaithfulnessReport,
    Section,
    SectionType,
    StructuredDraft,
)
from app.schemas.edits import (
    ClassifiedEdit,
    EditAction,
    EditAlignment,
    EditSession,
)
from app.schemas.matters import Matter
from app.schemas.memory import (
    Exemplar,
    SectionRule,
    StructuralPreferences,
    StyleMemory,
    TerminologyEntry,
)
from app.schemas.retrieval import (
    RetrievalConfig,
    RetrievalResult,
    RetrievedChunk,
)

__all__ = [
    "Annotation",
    "Attorney",
    "Bullet",
    "BulletStatus",
    "CaseMetadata",
    "Chunk",
    "ClassifiedEdit",
    "DocumentManifest",
    "EditAction",
    "EditAlignment",
    "EditSession",
    "EditType",
    "Exemplar",
    "ExtractionMethod",
    "ExtractionSummary",
    "FaithfulnessReport",
    "Matter",
    "Party",
    "ProcessedDocument",
    "ProcessedPage",
    "RetrievalConfig",
    "RetrievalResult",
    "RetrievedChunk",
    "Section",
    "SectionRule",
    "SectionType",
    "StructuralPreferences",
    "StructuredDraft",
    "StyleMemory",
    "TerminologyEntry",
    "TextBlock",
]
