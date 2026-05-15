from __future__ import annotations

from app.schemas import SectionType

SECTION_QUERIES: dict[SectionType, str] = {
    "caption": "case caption parties court case number filing date jurisdiction",
    "procedural_posture": "procedural posture pending motions rulings filings current stage",
    "material_facts": "material facts allegations chronology events what happened damages",
    "disputed_facts": "disputed contested conflicting facts in dispute",
    "key_documents": "exhibits attachments referenced filings supporting documents",
    "open_questions": "missing information evidence gaps unclear unknown not in record",
}

SECTION_TITLES: dict[SectionType, str] = {
    "caption": "Caption and Parties",
    "procedural_posture": "Procedural Posture",
    "material_facts": "Material Facts",
    "disputed_facts": "Disputed Facts",
    "key_documents": "Key Documents",
    "open_questions": "Open Questions / Evidence Gaps",
}

SECTION_INSTRUCTIONS: dict[SectionType, str] = {
    "caption": (
        "List the case caption, parties (with roles), court, case number, filing date. "
        "One bullet per discrete fact. Cite the chunk_id(s) supporting each bullet."
    ),
    "procedural_posture": (
        "Summarise where the case stands procedurally: filings made, motions pending, "
        "rulings issued. Chronological, one bullet per event."
    ),
    "material_facts": (
        "Establish the material facts in chronological order. One bullet per fact. "
        "Prefer specific dates, amounts, parties over vague language."
    ),
    "disputed_facts": (
        "List facts where the record shows conflict or contradiction. "
        "Empty list if none are disputed."
    ),
    "key_documents": (
        "List documents referenced by name with their type and significance."
    ),
    "open_questions": (
        "List gaps in the evidence — facts the operator should investigate. "
        "These bullets MAY be 'unsupported' (no evidence_chunk_ids) and that is correct."
    ),
}

SYSTEM_PROMPT = """\
You are drafting one section of a Case Fact Summary for an attorney's first \
review pass.

Strict rules:
1. Cite ONLY chunk_ids from the numbered evidence below — never invent.
2. Every 'supported' bullet must list at least one evidence_chunk_id.
3. If a claim cannot be supported by the evidence, do NOT write it.
   In the 'open_questions' section ONLY, you may mark unsupported gaps.
4. Be specific. Prefer dates, dollar amounts, named parties over hedged \
language.
5. One discrete fact per bullet. Keep bullets concise (one sentence preferred).
"""


def render_evidence(numbered_chunks: list[tuple[str, str]]) -> str:
    return "\n\n".join(
        f"[{chunk_id}]\n{text}" for chunk_id, text in numbered_chunks
    )
