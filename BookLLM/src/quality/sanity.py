
import re
from typing import List


CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
JSON_RE = re.compile(r"\{[^{}]*:[^{}]*\}|\[[^\[\]]*\]", re.DOTALL)


class SanityChecker:
    """Utility class for sanity checks."""

    @staticmethod
    def find_unexpected_json(text: str) -> List[str]:
        return find_unexpected_json(text)

    @staticmethod
    def check_book_content(contents: List[str]) -> List[str]:
        return check_book_content(contents)


def find_unexpected_json(text: str) -> List[str]:
    """Return JSON-like snippets that appear outside code blocks."""
    sanitized = CODE_BLOCK_RE.sub("", text)
    return [m.group(0) for m in JSON_RE.finditer(sanitized)]


def check_book_content(contents: List[str]) -> List[str]:
    """Check a list of text sections for stray JSON."""
    issues = []
    for i, section in enumerate(contents, 1):
        for snippet in find_unexpected_json(section):
            preview = snippet.replace("\n", " ")
            if len(preview) > 30:
                preview = preview[:27] + "..."
            issues.append(f"Section {i}: {preview}")
    return issues
