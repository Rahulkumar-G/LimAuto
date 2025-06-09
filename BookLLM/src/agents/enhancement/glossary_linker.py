from __future__ import annotations

import re
from typing import Set

from ...models.agent_type import AgentType
from ...models.state import BookState
from ..base import BaseAgent


class GlossaryLinker(BaseAgent):
    """Link first occurrence of glossary terms to glossary section."""

    def __init__(self, llm, agent_type: AgentType = AgentType.ENHANCER):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        linked: Set[str] = set()
        for chapter, content in state.chapter_map.items():
            for term in state.glossary.keys():
                lower = term.lower()
                if lower in linked:
                    continue
                pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
                if pattern.search(content):
                    label = lower.replace(" ", "-")
                    link = f"[{term}](#glossary-{label})"
                    content = pattern.sub(link, content, count=1)
                    linked.add(lower)
            state.chapter_map[chapter] = content
        return state

