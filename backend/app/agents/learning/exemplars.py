from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.schemas import ClassifiedEdit, EditAlignment, Exemplar


def build_exemplars(
    aligned: list[EditAlignment],
    classified: list[ClassifiedEdit],
    bullet_section_map: dict[str, str],
    matter_type: str | None,
) -> list[Exemplar]:
    by_bullet = {c.bullet_id: c for c in classified}
    now = datetime.now(timezone.utc)
    exemplars: list[Exemplar] = []
    for edit in aligned:
        if edit.action != "modified" or not edit.before or not edit.after:
            continue
        cls = by_bullet.get(edit.bullet_id)
        exemplars.append(
            Exemplar(
                exemplar_id=f"ex_{uuid.uuid4().hex[:12]}",
                section_id=bullet_section_map.get(edit.bullet_id, "unknown"),
                matter_type=matter_type,
                before=edit.before,
                after=edit.after,
                evidence_chunk_ids=edit.evidence_chunk_ids,
                edit_classes=[cls.edit_type] if cls else [],
                created_at=now,
            )
        )
    return exemplars


def prune_exemplars(exemplars: list[Exemplar], cap_per_section: int) -> list[Exemplar]:
    by_section: dict[str, list[Exemplar]] = {}
    for ex in exemplars:
        by_section.setdefault(ex.section_id, []).append(ex)
    pruned: list[Exemplar] = []
    for items in by_section.values():
        items.sort(key=lambda x: x.created_at, reverse=True)
        pruned.extend(items[:cap_per_section])
    return pruned
