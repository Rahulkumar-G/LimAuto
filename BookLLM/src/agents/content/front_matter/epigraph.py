from ....models.agent_type import AgentType
from ....models.state import BookState
from ...base import BaseAgent


class EpigraphAgent(BaseAgent):
    """Generates inspiring epigraph for the book"""

    def __init__(self, llm, agent_type: AgentType = AgentType.CONTENT_CREATOR):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        """Generate the book's epigraph"""
        prompt = f"""
        Create an inspiring epigraph for a book on "{state.topic}".
        
        Requirements:
        - Relevant quote or passage
        - Connection to the book's theme
        - Attribution to source
        - Resonates with {state.target_audience}
        - Sets the tone for the content
        
        Format as: "> Quote\n> -- Attribution"
        """

        state.epigraph, _ = self.llm.call_llm(prompt)
        return state
