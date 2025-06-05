from ....models.agent_type import AgentType
from ....models.state import BookState
from ...base import BaseAgent


class PrefaceAgent(BaseAgent):
    """Generates compelling preface for the book"""

    def __init__(self, llm, agent_type: AgentType = AgentType.CONTENT_CREATOR):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        """Generate the book's preface"""
        prompt = f"""
        Write a compelling preface for a book on "{state.topic}" for {state.target_audience}.
        
        Include:
        - Author's motivation and background
        - Book's unique value proposition
        - What readers will gain
        - How to use this book effectively
        - Acknowledgment of the learning journey
        
        Style: {state.book_style}, engaging, and encouraging.
        Length: 300-500 words.
        """

        state.preface, _ = self.llm.call_llm(prompt)
        return state
