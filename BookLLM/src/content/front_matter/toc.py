from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

from ...core.base import BaseAgent


@dataclass
class LabelOutput:
    """Represents label information for a chapter."""

    label: str


@dataclass
class TOCOutput:
    """Markdown table of contents."""

    toc_markdown: str


class TOCBuilderAgent(BaseAgent):
    """Build a markdown table of contents from chapter labels."""

    def run(self, inputs: List[LabelOutput]) -> TOCOutput:
        lines: List[str] = []
        for idx, item in enumerate(inputs, 1):
            slug = re.sub(r"[^a-z0-9]+", "-", item.label.lower()).strip("-")
            lines.append(f"- [Chapter {idx} \u2013 {item.label}](#{slug})")
        return TOCOutput(toc_markdown="\n".join(lines))
