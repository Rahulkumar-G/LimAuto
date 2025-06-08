import json
import re
from typing import Any, Dict, List

from ..utils.logger import get_logger


class SanityChecker:
    """Simple sanity checks for compiled book content."""

    JSON_LINE_RE = re.compile(r"^\s*[\[{].*[\]}]\s*$")

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def check(self, content: str) -> Dict[str, Any]:
        """Check book content for common formatting issues.

        Currently detects stray JSON snippets that occasionally appear in
        LLM output.
        """
        issues: List[str] = []
        for i, line in enumerate(content.splitlines(), 1):
            if self.JSON_LINE_RE.match(line):
                stripped = line.strip()
                try:
                    json.loads(stripped)
                    issues.append(f"Line {i} contains JSON snippet")
                except json.JSONDecodeError:
                    continue
        return {"passed": not issues, "issues": issues}
