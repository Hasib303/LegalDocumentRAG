from __future__ import annotations

import re

_SEPARATORS = ["\n\n\n", "\n\n", "\n", ". ", " "]
_CHARS_PER_TOKEN = 4


def approx_tokens(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)


def split_text(
    text: str,
    target_tokens: int = 450,
    overlap_tokens: int = 90,
) -> list[str]:
    target_chars = target_tokens * _CHARS_PER_TOKEN
    overlap_chars = overlap_tokens * _CHARS_PER_TOKEN
    raw = _recursive_split(text, target_chars, _SEPARATORS)
    return _with_overlap([c for c in raw if c.strip()], overlap_chars)


def _recursive_split(text: str, target: int, seps: list[str]) -> list[str]:
    if len(text) <= target:
        return [text]
    if not seps:
        return [text[i : i + target] for i in range(0, len(text), target)]
    sep = seps[0]
    parts = text.split(sep)
    chunks: list[str] = []
    current = ""
    for part in parts:
        candidate = f"{current}{sep}{part}" if current else part
        if len(candidate) <= target:
            current = candidate
            continue
        if current:
            chunks.append(current)
        if len(part) > target:
            chunks.extend(_recursive_split(part, target, seps[1:]))
            current = ""
        else:
            current = part
    if current:
        chunks.append(current)
    return chunks


def _with_overlap(chunks: list[str], overlap_chars: int) -> list[str]:
    if overlap_chars <= 0 or len(chunks) <= 1:
        return chunks
    out = [chunks[0]]
    for i in range(1, len(chunks)):
        tail = chunks[i - 1][-overlap_chars:]
        out.append(tail + chunks[i])
    return out


_SECTION_HEADING_RE = re.compile(
    r"^\s*(?:SECTION|Section|ARTICLE|Article|§)\s+[\dIVXLC][\w.()]*",
    re.MULTILINE,
)


def find_section_label(text: str) -> str | None:
    match = _SECTION_HEADING_RE.search(text)
    return match.group(0).strip() if match else None
