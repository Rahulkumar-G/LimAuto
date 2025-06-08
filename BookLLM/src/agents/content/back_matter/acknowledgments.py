from ....models.agent_type import AgentType
from ....models.state import BookState
from ...base import BaseAgent


class AcknowledgmentsAgent(BaseAgent):
    """Generate an acknowledgments section"""

    def __init__(self, llm, agent_type: AgentType = AgentType.COMPILER):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        prompt = f"""
        Draft a sincere acknowledgments section for this {state.topic} book.

        Mention key contributors, mentors, peer reviewers, and organizations that supported the work.
        Keep the length between 100 and 150 words.
        """
        state.acknowledgments, _ = self.llm.call_llm(prompt)
        return state
