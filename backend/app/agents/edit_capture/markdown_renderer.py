from __future__ import annotations

import re

from app.schemas import Section, StructuredDraft

_BULLET_RE = re.compile(r"^\s*[-*]\s+(.+?)\s*$")
_HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
_CITE_TAIL_RE = re.compile(r"\s*\[(?:[A-Za-z0-9_:,\s]+)\]\s*$")


def render_draft(draft: StructuredDraft) -> str:
    lines = [f"# Case Fact Summary — {draft.matter_id}", ""]
    for section in draft.sections:
        lines.append(f"## {section.title}")
        lines.append("")
        if not section.bullets:
            lines.append("_(no content)_")
            lines.append("")
            continue
        for bullet in section.bullets:
            citation = (
                " [" + ", ".join(bullet.evidence_chunk_ids) + "]"
                if bullet.evidence_chunk_ids
                else ""
            )
            tag = "" if bullet.status == "supported" else f" _({bullet.status})_"
            lines.append(f"- {bullet.text}{tag}{citation}")
        lines.append("")
    return "\n".join(lines)


def parse_draft_markdown(markdown: str) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_bullets: list[str] = []
    for line in markdown.splitlines():
        heading = _HEADING_RE.match(line)
        if heading:
            if current_title is not None:
                sections.append((current_title, current_bullets))
            current_title = heading.group(1)
            current_bullets = []
            continue
        bullet = _BULLET_RE.match(line)
        if bullet:
            text = _CITE_TAIL_RE.sub("", bullet.group(1)).strip()
            text = re.sub(r"\s*_\(.*?\)_\s*$", "", text).strip()
            if text:
                current_bullets.append(text)
    if current_title is not None:
        sections.append((current_title, current_bullets))
    return sections
