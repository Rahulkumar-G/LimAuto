from ....models.agent_type import AgentType
from ....models.state import BookState
from ...base import BaseAgent


class PrefaceAgent(BaseAgent):
    """Generates compelling preface for the book"""

    def __init__(self, llm, agent_type: AgentType = AgentType.CONTENT_CREATOR):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        """Generate the book's preface with vivid opening scenario"""
        prompt = f"""
        Write a compelling preface for a book on "{state.topic}" for {state.target_audience}.
        
        REQUIRED STRUCTURE:
        1. Open with a vivid, real-world scenario (1-2 sentences) that illustrates what happens when regulatory strategy is mishandled in medical device launches
        2. Establish urgency - explain what's at stake when regulatory affairs goes wrong
        3. Underscore author credibility with specific experience and quantified achievements
        4. Preview the practical benefits readers will gain from this book
        
        REQUIREMENTS:
        - Under 300 words total
        - Use active voice throughout
        - Conversational yet professional tone
        - Focus on real-world impact and consequences
        - Make regulatory affairs feel strategic, not bureaucratic
        
        Do NOT include:
        - Generic motivational language
        - Lengthy acknowledgments
        - Detailed book structure explanations
        - Passive voice constructions
        
        The preface should immediately grab attention and position regulatory affairs as a critical business advantage, not just compliance.
        """

        state.preface, _ = self.llm.call_llm(prompt)
        return state
