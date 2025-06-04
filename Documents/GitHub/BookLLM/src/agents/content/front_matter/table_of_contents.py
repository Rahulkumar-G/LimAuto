from ...base import BaseAgent
from ....models.state import BookState
from ....models.agent_type import AgentType

class TableOfContentsAgent(BaseAgent):
    """Generates structured table of contents"""
    
    def __init__(self, llm, agent_type: AgentType = AgentType.FRONT_MATTER):
        super().__init__(llm, agent_type)
    
    def _execute_logic(self, state: BookState) -> BookState:
        """Generate comprehensive table of contents"""
        toc = ["# Table of Contents\n"]
        
        # Front Matter
        if any([state.title_page, state.foreword, state.dedication, 
                state.preface, state.prologue]):
            toc.append("\n## Front Matter")
            if state.title_page:
                toc.append("- Title Page")
            if state.foreword:
                toc.append("- Foreword")
            if state.dedication:
                toc.append("- Dedication")
            if state.preface:
                toc.append("- Preface")
            if state.prologue:
                toc.append("- Prologue")
        
        # Main Content
        if state.chapters:
            toc.append("\n## Contents")
            for i, chapter in enumerate(state.chapters, 1):
                toc.append(f"{i}. {chapter}")
                # Add chapter summaries if available
                if chapter in state.chapter_summaries:
                    summary = state.chapter_summaries[chapter].split('.')[0]
                    toc.append(f"   _{summary}_\n")
        
        # Back Matter
        back_matter = []
        if state.glossary:
            back_matter.append("- Glossary")
        if state.bibliography:
            back_matter.append("- Bibliography")
        if state.index_terms:
            back_matter.append("- Index")
        if state.appendices:
            back_matter.append("- Appendices")
        
        if back_matter:
            toc.append("\n## Back Matter")
            toc.extend(back_matter)
        
        state.table_of_contents = "\n".join(toc)
        return state