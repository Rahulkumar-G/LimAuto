from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from textstat import textstat


@dataclass
class TuneResult:
    """Result of readability tuning."""

    grade: float
    suggestions: List[str]


class ReadabilityTuner:
    """Suggest sentence splits when FK grade exceeds threshold."""

    def __init__(self, threshold: float = 12.0) -> None:
        self.threshold = threshold

    def tune(self, text: str) -> TuneResult:
        grade = textstat.flesch_kincaid_grade(text)
        suggestions: List[str] = []

        if grade > self.threshold:
            sentences = re.split(r"(?<=[.!?])\s+", text)
            for sentence in sentences:
                words = sentence.split()
                if len(words) > 25:
                    snippet = (
                        " ".join(words[:10]) + "..." if len(words) > 10 else sentence
                    )
                    suggestions.append(
                        f"Consider splitting sentence starting: '{snippet}'"
                    )

        return TuneResult(grade=grade, suggestions=suggestions)
