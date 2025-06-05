from typing import List

from ....models.agent_type import AgentType
from ....models.state import BookState
from ...base import BaseAgent


class IndexAgent(BaseAgent):
    """Generates comprehensive index"""

    def __init__(self, llm, agent_type: AgentType = AgentType.COMPILER):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        """Generate detailed index"""
        combined_content = "\n".join(state.chapter_map.values())

        prompt = f"""
        Create a comprehensive index for this {state.topic} book.
        
        Content to index:
        {combined_content[:2000]}...

        Requirements:
        - Include main topics and subtopics
        - Cross-reference related terms
        - Include technical terms from glossary
        - Format with proper indentation
        - Sort alphabetically
        
        Focus on terms relevant to {state.target_audience}.
        """

        index_content, _ = self.llm.call_llm(prompt)
        state.index_terms = self._process_index(index_content)
        return state

    def _process_index(self, index_content: str) -> List[str]:
        """Process and format index entries"""
        # Remove empty lines and strip whitespace
        entries = [line.strip() for line in index_content.split("\n") if line.strip()]
        # Sort alphabetically
        return sorted(entries)
