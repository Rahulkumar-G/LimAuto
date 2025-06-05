from ....models.agent_type import AgentType
from ....models.state import BookState
from ...base import BaseAgent


class DedicationAgent(BaseAgent):
    """Generates meaningful dedication for the book"""

    def __init__(self, llm, agent_type: AgentType = AgentType.CONTENT_CREATOR):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        """Generate the book's dedication"""
        prompt = f"""
        Create a meaningful dedication for a book on "{state.topic}".
        
        Style: {state.book_style}
        Length: 30-50 words
        Tone: Sincere and heartfelt
        
        Consider dedicating to:
        - Learners and practitioners in the field
        - Mentors and inspirations
        - Community members
        - Future generations
        """

        state.dedication, _ = self.llm.call_llm(prompt)
        return state
