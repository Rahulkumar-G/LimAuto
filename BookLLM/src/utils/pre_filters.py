import re

RAW_OUTLINE_RE = re.compile(r"^Chapter \d+: \[\{.*?\}\]$\n?", re.MULTILINE)


def remove_outline_dicts(text: str) -> str:
    """Remove lines containing raw outline dictionaries.

    This filters artifacts like ``Chapter 1: [{"title": "..."}]`` that can
    appear in LLM outputs before further processing.
    """
    return RAW_OUTLINE_RE.sub("", text)

