import re

from ....models.agent_type import AgentType
from ....models.state import BookState
from ...base import BaseAgent


class TableOfContentsAgent(BaseAgent):
    """Generates structured table of contents"""

    def __init__(self, llm, agent_type: AgentType = AgentType.FRONT_MATTER):
        super().__init__(llm, agent_type)

    @staticmethod
    def _slugify(text: str) -> str:
        """Simplistic slugify helper for generating markdown anchors"""
        slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
        return slug

    def _execute_logic(self, state: BookState) -> BookState:
        """Generate comprehensive table of contents"""
        toc = ["# Table of Contents\n"]

        # Front Matter
        if any(
            [
                state.title_page,
                state.foreword,
                state.dedication,
                state.preface,
                state.prologue,
            ]
        ):
            toc.append("\n## Front Matter")
            if state.title_page:
                toc.append("- [Title Page](#title-page)")
            if state.foreword:
                toc.append("- [Foreword](#foreword)")
            if state.dedication:
                toc.append("- [Dedication](#dedication)")
            if state.preface:
                toc.append("- [Preface](#preface)")
            if state.prologue:
                toc.append("- [Prologue](#prologue)")

        # Main Content
        if state.chapters:
            toc.append("\n## Contents")
            for i, chapter in enumerate(state.chapters, 1):
                anchor = self._slugify(f"chapter-{i}-{chapter}")
                toc.append(f"{i}. [{chapter}](#{anchor})")
                if chapter in state.chapter_summaries:
                    summary = state.chapter_summaries[chapter].split(".")[0]
                    toc.append(f"   _{summary}_\n")

        # Back Matter
        back_matter = []
        if state.glossary:
            back_matter.append("- [Glossary](#glossary)")
        if state.bibliography:
            back_matter.append("- [Bibliography](#bibliography)")
        if state.index_terms:
            back_matter.append("- [Index](#index)")
        if state.appendices:
            back_matter.append("- [Appendices](#appendices)")

        if back_matter:
            toc.append("\n## Back Matter")
            toc.extend(back_matter)

        state.table_of_contents = "\n".join(toc)
        return state
