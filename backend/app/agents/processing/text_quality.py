from __future__ import annotations

import re

_REPLACEMENT_CHAR_RE = re.compile(r"[\ufffd]")
_PRINTABLE_RE = re.compile(r"[A-Za-z0-9\s.,;:!?'\"()\-\[\]/$@#&%*+=<>{}|`~^]")

_MIN_USEFUL_CHARS = 100
_MAX_REPLACEMENT_RATE = 0.02
_MIN_PRINTABLE_RATE = 0.75


def has_usable_text(text: str) -> bool:
    stripped = text.strip()
    length = len(stripped)
    if length < _MIN_USEFUL_CHARS:
        return False

    replacement_rate = len(_REPLACEMENT_CHAR_RE.findall(stripped)) / length
    if replacement_rate > _MAX_REPLACEMENT_RATE:
        return False

    printable_rate = len(_PRINTABLE_RE.findall(stripped)) / length
    if printable_rate < _MIN_PRINTABLE_RATE:
        return False

    return True
