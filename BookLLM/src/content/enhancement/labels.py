from __future__ import annotations

import re
import string
from typing import Dict

from ...core.base import BaseAgent
from ...core.types import AgentInput, LabelOutput


class LabelGeneratorAgent(BaseAgent):
    """Insert anchor labels after headings."""

    def run(self, input: AgentInput) -> LabelOutput:
        """Add labels to headings and return map."""
        format_type = "markdown"
        if input.metadata:
            fmt = input.metadata.get("format") or input.metadata.get("type")
            if isinstance(fmt, str) and fmt.lower() == "latex":
                format_type = "latex"
        lines = input.content.splitlines()
        labeled_lines = []
        labels: Dict[str, str] = {}

        for line in lines:
            m = re.match(r"^(#{1,2})\s+(.*)$", line)
            if m:
                heading = m.group(2).strip()
                slug = self._slugify(heading)
                labels[heading] = slug
                labeled_lines.append(line)
                label = (
                    f"\\label{{{slug}}}" if format_type == "latex" else f"{{#{slug}}}"
                )
                labeled_lines.append(label)
            else:
                labeled_lines.append(line)

        labeled_content = "\n".join(labeled_lines)
        return LabelOutput(labeled_content=labeled_content, labels=labels)

    @staticmethod
    def _slugify(text: str) -> str:
        text = text.lower()
        text = text.translate(str.maketrans("", "", string.punctuation))
        slug = re.sub(r"\s+", "-", text).strip("-")
        return slug
