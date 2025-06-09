from __future__ import annotations

import re
from typing import Dict

from ...core.base import BaseAgent
from ...core.types import AgentInput, AgentOutput
from ...utils import external_dictionary


class AcronymAgent(BaseAgent):
    """Resolve acronyms and build a glossary."""

    def run(self, input: AgentInput) -> AgentOutput:
        """Expand acronyms on first use and append a glossary."""
        tokens = set(re.findall(r"\b[A-Z]{2,6}\b", input.content))
        glossary: Dict[str, str] = {}
        content = input.content
        for token in tokens:
            definition = external_dictionary.lookup(token)
            glossary[token] = definition
            pattern = re.compile(rf"\b{token}\b")
            content = pattern.sub(f"{definition} ({token})", content, count=1)
        if glossary:
            glossary_section = "\n".join(
                f"- **{tok}**: {defn}" for tok, defn in glossary.items()
            )
            content += f"\n\n## Acronym Glossary\n{glossary_section}\n"
        return AgentOutput(resolved_content=content, acronym_glossary=glossary)

    def process(self, state: "BookState") -> "BookState":
        """Expand acronyms across the book."""
        from ...models.state import BookState

        if not isinstance(state, BookState):
            return state

        combined = "\n\n".join(state.chapter_map.values())
        output = self.run(AgentInput(content=combined))
        if output.acronym_glossary:
            state.acronyms.update(output.acronym_glossary)
        # This simple implementation does not update chapter text
        return state
