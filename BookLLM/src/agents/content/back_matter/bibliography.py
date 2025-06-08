from ....models.agent_type import AgentType
from ....models.state import BookState
from ...base import BaseAgent


class BibliographyAgent(BaseAgent):
    """Generates detailed bibliography"""

    def __init__(self, llm, agent_type: AgentType = AgentType.COMPILER):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        """Generate comprehensive bibliography"""
        if not state.references:
            return state

        prompt = f"""
        Create a detailed bibliography for references in {state.topic} book.

        References to format:
        {state.references}

        Requirements:
        - Format entries using APA citation style
        - Sort alphabetically by author
        - Include all necessary metadata
        - Add brief annotations where helpful
        - Provide cross-references so citations can be linked to chapters
        """

        state.bibliography, _ = self.llm.call_llm(prompt)
        return state
