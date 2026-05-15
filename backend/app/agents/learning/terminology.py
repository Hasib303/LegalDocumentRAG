from __future__ import annotations

from app.schemas import EditAlignment, TerminologyEntry

_MAX_TERM_WORDS = 6


def _candidate_pairs(before: str, after: str) -> list[tuple[str, str]]:
    before_tokens = before.split()
    after_tokens = after.split()
    pairs: list[tuple[str, str]] = []
    # Greedy diff at the token level — find the smallest spans that differ.
    i = j = 0
    while i < len(before_tokens) and j < len(after_tokens):
        if before_tokens[i] == after_tokens[j]:
            i += 1
            j += 1
            continue
        b_start, a_start = i, j
        while (
            i < len(before_tokens)
            and j < len(after_tokens)
            and before_tokens[i] != after_tokens[j]
        ):
            i += 1
            j += 1
        b_span = " ".join(before_tokens[b_start:i])
        a_span = " ".join(after_tokens[a_start:j])
        if b_span and a_span and len(b_span.split()) <= _MAX_TERM_WORDS and len(a_span.split()) <= _MAX_TERM_WORDS:
            pairs.append((b_span, a_span))
    return pairs


def extract_terminology(
    edits: list[EditAlignment],
    existing: list[TerminologyEntry],
    edit_session_id: str,
) -> list[TerminologyEntry]:
    by_pair: dict[tuple[str, str], TerminologyEntry] = {
        (e.from_term, e.to_term): e for e in existing
    }
    for edit in edits:
        if edit.action != "modified" or not edit.before or not edit.after:
            continue
        for from_term, to_term in _candidate_pairs(edit.before, edit.after):
            key = (from_term, to_term)
            entry = by_pair.get(key)
            if entry is None:
                by_pair[key] = TerminologyEntry(
                    from_term=from_term,
                    to_term=to_term,
                    frequency=1,
                    first_seen_edit_id=edit_session_id,
                )
            else:
                by_pair[key] = entry.model_copy(update={"frequency": entry.frequency + 1})
    return list(by_pair.values())
