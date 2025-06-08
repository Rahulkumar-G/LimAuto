from ....models.agent_type import AgentType
from ....models.state import BookState
from ...base import BaseAgent


class AboutAuthorAgent(BaseAgent):
    """Generate an 'About the Author' section"""

    def __init__(self, llm, agent_type: AgentType = AgentType.COMPILER):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        prompt = f"""
        Write a short biography for the author of this {state.topic} book.

        Highlight relevant expertise, notable accomplishments, and connection to the topic.
        Tone should be professional yet approachable.
        Length: 150-200 words.
        """
        state.about_the_author, _ = self.llm.call_llm(prompt)
        return state
