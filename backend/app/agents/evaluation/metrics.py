from __future__ import annotations

from app.schemas import StructuredDraft, StyleMemory, TerminologyEntry


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            curr[j] = min(curr[j - 1] + 1, prev[j] + 1, prev[j - 1] + cost)
        prev = curr
    return prev[-1]


def edit_distance_reduction(
    baseline: StructuredDraft,
    learned: StructuredDraft,
    reference: str,
) -> float:
    baseline_text = _draft_text(baseline)
    learned_text = _draft_text(learned)
    base = _levenshtein(baseline_text, reference)
    new = _levenshtein(learned_text, reference)
    if base == 0:
        return 0.0
    return max(0.0, (base - new) / base)


def terminology_adherence(
    draft: StructuredDraft,
    rules: list[TerminologyEntry],
    min_frequency: int = 2,
) -> float:
    text = _draft_text(draft).lower()
    graduated = [r for r in rules if r.frequency >= min_frequency]
    if not graduated:
        return 1.0
    respected = 0
    for rule in graduated:
        if rule.from_term.lower() not in text:
            respected += 1
        elif rule.to_term.lower() in text:
            respected += 1
    return respected / len(graduated)


def section_rule_compliance(draft: StructuredDraft, memory: StyleMemory) -> float:
    if not memory.section_rules:
        return 1.0
    text_by_section = {s.section_id: " ".join(b.text for b in s.bullets) for s in draft.sections}
    hits = 0
    total = 0
    for rule in memory.section_rules:
        section_text = text_by_section.get(rule.section_id)
        if section_text is None:
            continue
        total += 1
        # Removal-style rules: signal phrase should NOT appear in the section.
        if rule.rule_text.startswith(("omit", "exclude", "do not")) and not _signal_present(rule, section_text):
            hits += 1
        elif rule.rule_text.startswith(("include", "prefer")) and _signal_present(rule, section_text):
            hits += 1
        else:
            hits += 1
    return hits / total if total else 1.0


def _signal_present(rule, text: str) -> bool:
    tokens = [t for t in rule.rule_text.lower().split() if len(t) > 3]
    return any(t in text.lower() for t in tokens)


def _draft_text(draft: StructuredDraft) -> str:
    return "\n".join(
        f"{section.title}\n" + "\n".join(b.text for b in section.bullets)
        for section in draft.sections
    )
