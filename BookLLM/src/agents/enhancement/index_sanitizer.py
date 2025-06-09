from __future__ import annotations

from pathlib import Path
from typing import Set

from ...models.agent_type import AgentType
from ...models.state import BookState
from ..base import BaseAgent


class IndexSanitizerAgent(BaseAgent):
    """Sanitize and sort index terms."""

    def __init__(self, llm, agent_type: AgentType = AgentType.COMPILER):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        master_labels: Set[str] = set(
            str(l).lower() for l in state.metadata.get("master_label_set", [])
        )

        cleaned = []
        seen: Set[str] = set()
        for term in state.index_terms:
            slug = term.split("(")[0].strip().lower()
            if master_labels and slug not in master_labels:
                continue
            if slug in seen:
                continue
            seen.add(slug)
            cleaned.append(term.strip())

        state.index_terms = sorted(cleaned, key=lambda s: s.lower())
        return state
