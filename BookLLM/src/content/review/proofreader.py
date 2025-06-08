from __future__ import annotations

import re
from typing import List

from ...core.base import BaseAgent
from ...core.types import AgentInput, AgentOutput, Suggestion
from ...utils import language_tools


class ReviewerAgent(BaseAgent):
    """Perform basic proofreading on the provided content."""

    def run(self, input: AgentInput) -> AgentOutput:
        """Review and correct text.

        Parameters
        ----------
        input: AgentInput
            ``content`` contains the text to proofread. ``metadata`` may include
            chapter information.

        Returns
        -------
        AgentOutput
            ``corrected_text`` with simple fixes applied and a list of
            ``suggestions`` for the user.
        """
        sentences = re.split(r"(?<=[.!?]) +", input.content)
        corrected_parts: List[str] = []
        suggestions: List[Suggestion] = []
        offset = 0
        for sentence in sentences:
            spell = language_tools.spell_check(sentence)
            grammar = language_tools.grammar_check(sentence)
            style = language_tools.enforce_style_rules(sentence)
            all_sug = spell + grammar + style
            for s in all_sug:
                s.position += offset
                suggestions.append(s)
            corrected = sentence
            for s in all_sug:
                if s.recommendation:
                    corrected = corrected.replace(s.original, s.recommendation)
            corrected_parts.append(corrected)
            offset += len(sentence) + 1
        corrected_text = " ".join(corrected_parts)
        return AgentOutput(corrected_text=corrected_text, suggestions=suggestions)
