from ....models.agent_type import AgentType
from ....models.state import BookState
from ...base import BaseAgent


class ForewordAgent(BaseAgent):
    """Generates engaging foreword for the book"""

    def __init__(self, llm, agent_type: AgentType = AgentType.CONTENT_CREATOR):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        """Generate the book's foreword"""
        prompt = f"""
        Write an engaging foreword for a book on "{state.topic}".
        
        Consider:
        - Target audience: {state.target_audience}
        - Book style: {state.book_style}
        - Purpose and significance of the topic
        - Current state of the field
        - Future implications
        
        Requirements:
        - Professional yet personal tone
        - Include expert perspective
        - Highlight book's unique value
        - Length: 500-700 words
        - End with a compelling call to read
        """

        state.foreword, _ = self.llm.call_llm(prompt)
        return state
