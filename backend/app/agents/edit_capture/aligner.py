from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment

from app.providers.base import EmbeddingProvider
from app.schemas import EditAlignment

_SIMILARITY_THRESHOLD = 0.65


def align_bullets(
    original: list[tuple[str, str]],
    edited: list[str],
    embedder: EmbeddingProvider,
) -> list[EditAlignment]:
    """Align ``(bullet_id, text)`` pairs from the original draft to edited bullet
    texts. Uses Hungarian assignment on cosine similarity; unmatched ends become
    pure ``added``/``removed`` edits."""
    if not original and not edited:
        return []
    if not original:
        return [
            EditAlignment(bullet_id=f"new_{i}", action="added", after=text)
            for i, text in enumerate(edited)
        ]
    if not edited:
        return [
            EditAlignment(bullet_id=bid, action="removed", before=text)
            for bid, text in original
        ]

    orig_texts = [text for _, text in original]
    orig_ids = [bid for bid, _ in original]
    orig_embs = np.asarray(embedder.embed(orig_texts), dtype=np.float32)
    edit_embs = np.asarray(embedder.embed(edited), dtype=np.float32)
    similarity = orig_embs @ edit_embs.T

    cost = -similarity
    n, m = similarity.shape
    if n != m:
        size = max(n, m)
        padded = np.full((size, size), 1.0, dtype=np.float32)
        padded[:n, :m] = cost
        row_ind, col_ind = linear_sum_assignment(padded)
    else:
        row_ind, col_ind = linear_sum_assignment(cost)

    edits: list[EditAlignment] = []
    matched_orig: set[int] = set()
    matched_edit: set[int] = set()

    for r, c in zip(row_ind, col_ind):
        if r >= n or c >= m:
            continue
        sim = float(similarity[r, c])
        if sim < _SIMILARITY_THRESHOLD:
            continue
        matched_orig.add(r)
        matched_edit.add(c)
        if orig_texts[r] == edited[c]:
            continue
        edits.append(
            EditAlignment(
                bullet_id=orig_ids[r],
                action="modified",
                before=orig_texts[r],
                after=edited[c],
            )
        )

    for r in range(n):
        if r not in matched_orig:
            edits.append(
                EditAlignment(
                    bullet_id=orig_ids[r],
                    action="removed",
                    before=orig_texts[r],
                )
            )
    for c in range(m):
        if c not in matched_edit:
            edits.append(
                EditAlignment(
                    bullet_id=f"new_{c}",
                    action="added",
                    after=edited[c],
                )
            )

    return edits
