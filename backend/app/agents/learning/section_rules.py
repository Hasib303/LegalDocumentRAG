from __future__ import annotations

from app.schemas import ClassifiedEdit, EditAlignment, SectionRule


def update_section_rules(
    aligned: list[EditAlignment],
    classified: list[ClassifiedEdit],
    bullet_section_map: dict[str, str],
    existing: list[SectionRule],
    matter_id: str,
) -> list[SectionRule]:
    rules = {(r.section_id, r.rule_text): r for r in existing}

    cls_by_bullet = {c.bullet_id: c for c in classified}
    for edit in aligned:
        cls = cls_by_bullet.get(edit.bullet_id)
        if cls is None:
            continue
        section_id = bullet_section_map.get(edit.bullet_id, "unknown")
        if cls.edit_type not in {"removal", "addition", "structure", "tone"}:
            continue
        rule_text = cls.extracted_signal.strip()
        if not rule_text:
            continue
        key = (section_id, rule_text)
        if key in rules:
            rule = rules[key]
            rules[key] = rule.model_copy(
                update={
                    "support_count": rule.support_count + 1,
                    "source_matter_ids": list({*rule.source_matter_ids, matter_id}),
                }
            )
        else:
            rules[key] = SectionRule(
                section_id=section_id,
                rule_text=rule_text,
                support_count=1,
                source_matter_ids=[matter_id],
            )
    return list(rules.values())
