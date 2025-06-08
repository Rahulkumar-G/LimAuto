from __future__ import annotations

import re
from typing import List

from ..core.types import Suggestion


def spell_check(text: str) -> List[Suggestion]:
    """Very naive spell checker for demo purposes."""
    suggestions: List[Suggestion] = []
    if "teh" in text:
        idx = text.index("teh")
        suggestions.append(Suggestion(position=idx, original="teh", recommendation="the"))
    return suggestions


def grammar_check(text: str) -> List[Suggestion]:
    """Detect double spaces as a grammar issue."""
    suggestions: List[Suggestion] = []
    for m in re.finditer(r" {2,}", text):
        suggestions.append(Suggestion(position=m.start(), original=m.group(0), recommendation=" "))
    return suggestions


def enforce_style_rules(text: str) -> List[Suggestion]:
    """Check for trailing whitespace violations."""
    suggestions: List[Suggestion] = []
    if text.endswith(" "):
        suggestions.append(Suggestion(position=len(text) - 1, original=" ", recommendation=""))
    return suggestions
