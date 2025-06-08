from __future__ import annotations

import re
from typing import List

from ...core.base import BaseAgent
from ...core.types import AgentInput, AgentOutput, EmbeddedElement, SectionMeta
from ...utils import prompt_engine


class ContentEnhancementAgent(BaseAgent):
    """Insert questions and examples into content."""

    def run(self, input: AgentInput) -> AgentOutput:
        """Enhance content with interactive elements.

        Parameters
        ----------
        input: AgentInput
            ``content`` is markdown text. ``outline`` defines section boundaries.

        Returns
        -------
        AgentOutput
            ``enhanced_content`` with new elements and ``added_elements`` list.
        """
        text = input.content
        added: List[EmbeddedElement] = []
        outline = input.outline or []
        for section in sorted(outline, key=lambda s: s.end, reverse=True):
            section_text = text[section.start:section.end]
            question = prompt_engine.generate_question(section.heading, section_text)
            insertion = f"\n\n> {question}\n"
            text = text[: section.end] + insertion + text[section.end :]
            added.append(
                EmbeddedElement(
                    element_type="question",
                    content=question,
                    position=section.end,
                )
            )
        pattern = re.compile(r"^#+\s*Example:\s*(.*)$", re.MULTILINE)
        for match in pattern.finditer(text):
            topic = match.group(1)
            example = prompt_engine.generate_example(topic)
            pos = match.end()
            insertion = f"\n\n{example}\n"
            text = text[:pos] + insertion + text[pos:]
            added.append(
                EmbeddedElement(
                    element_type="example",
                    content=example,
                    position=pos,
                )
            )
        return AgentOutput(enhanced_content=text, added_elements=added)
