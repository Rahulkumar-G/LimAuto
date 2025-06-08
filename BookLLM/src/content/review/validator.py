from __future__ import annotations

import re
from typing import List

from ...core.base import BaseAgent
from ...core.types import AgentInput, AgentOutput


class QualityAssuranceAgent(BaseAgent):
    """Validate structural quality of the content."""

    def run(self, input: AgentInput) -> AgentOutput:
        """Run quality checks on the provided content."""
        text = input.content
        metadata = input.metadata or {}
        min_words = int(metadata.get("min_words", 0))
        max_words = int(metadata.get("max_words", 1e9))
        issues: List[str] = []

        for heading in ["# Introduction", "# Body", "# Summary"]:
            if heading not in text:
                issues.append(f"Missing section {heading}")

        sections = {"Introduction": "", "Body": "", "Summary": ""}
        current = None
        for line in text.splitlines():
            if line.startswith("# Introduction"):
                current = "Introduction"
                continue
            if line.startswith("# Body"):
                current = "Body"
                continue
            if line.startswith("# Summary"):
                current = "Summary"
                continue
            if current:
                sections[current] += line + " "
        for name, content in sections.items():
            wc = len(content.split())
            if wc < min_words or wc > max_words:
                issues.append(f"{name} word count {wc} outside range")

        for text_link, url in re.findall(r"\[(.*?)\]\((.*?)\)", text):
            if not url or " " in url:
                issues.append(f"Broken link: {url}")

        is_valid = len(issues) == 0
        return AgentOutput(is_valid=is_valid, issues=issues)
