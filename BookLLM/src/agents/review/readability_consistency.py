from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List

from textstat import textstat


@dataclass
class ConsistencyReport:
    readability: Dict[str, float]
    jargon: List[str]
    passive_sentences: List[str]
    terminology_issues: List[str]


class ReadabilityConsistencyChecker:
    """Check text for readability and terminology consistency."""

    def __init__(self, terminology_map: Dict[str, str] | None = None) -> None:
        self.terminology_map = terminology_map or {}

    def check_readability(self, text: str) -> Dict[str, float]:
        """Return common readability scores."""
        return {
            "flesch_reading_ease": textstat.flesch_reading_ease(text),
            "flesch_kincaid_grade": textstat.flesch_kincaid_grade(text),
        }

    def detect_passive_voice(self, text: str) -> List[str]:
        """Detect sentences that appear to use passive voice."""
        passive_re = re.compile(
            r"\b(?:was|were|is|are|been|be|being)\s+\w+(?:ed|en)\b",
            flags=re.IGNORECASE,
        )
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s for s in sentences if passive_re.search(s)]

    def detect_jargon(self, text: str) -> List[str]:
        """Flag uncommon long words as potential jargon."""
        words = re.findall(r"[A-Za-z']+", text)
        jargon_words = {w for w in words if len(w) >= 12}
        return sorted(jargon_words, key=str.lower)

    def enforce_terminology(self, text: str) -> List[str]:
        """Return terminology inconsistencies based on the provided map."""
        issues = []
        for short, canonical in self.terminology_map.items():
            short_re = re.compile(rf"\b{re.escape(short)}\b", re.IGNORECASE)
            canonical_re = re.compile(rf"\b{re.escape(canonical)}\b", re.IGNORECASE)
            if short_re.search(text) and canonical_re.search(text):
                issues.append(f"Use either '{short}' or '{canonical}', not both")
        return issues

    def analyze(self, text: str) -> ConsistencyReport:
        """Run all checks and return a consolidated report."""
        return ConsistencyReport(
            readability=self.check_readability(text),
            jargon=self.detect_jargon(text),
            passive_sentences=self.detect_passive_voice(text),
            terminology_issues=self.enforce_terminology(text),
        )
