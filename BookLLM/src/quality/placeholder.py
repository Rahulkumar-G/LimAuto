from __future__ import annotations

import re
from typing import Iterable

from ..models.state import BookState


class QAError(Exception):
    """Raised when placeholder text is detected after enhancement."""


class PlaceholderValidator:
    PLACEHOLDER_RE = re.compile(r"\*{7}|_{4,}")

    @classmethod
    def validate(cls, state: BookState, contents: Iterable[str] | None = None) -> None:
        if contents is None:
            contents = list(state.chapter_map.values())
            if state.title_page:
                contents.append(state.title_page)
            if state.about_the_author:
                contents.append(state.about_the_author)
        for section in contents:
            if section and cls.PLACEHOLDER_RE.search(section):
                raise QAError("Placeholder content detected")

