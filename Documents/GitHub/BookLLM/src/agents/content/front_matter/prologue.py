from ...base import BaseAgent
from ....models.state import BookState
from ....models.agent_type import AgentType

class PrologueAgent(BaseAgent):
    """Generates engaging prologue for the book"""
    
    def __init__(self, llm, agent_type: AgentType = AgentType.CONTENT_CREATOR):
        super().__init__(llm, agent_type)
    
    def _execute_logic(self, state: BookState) -> BookState:
        """Generate the book's prologue"""
        prompt = f"""
        Create an engaging prologue for "{state.topic}" that:
        
        - Sets the scene and context
        - Explains why this topic is important now
        - Outlines the journey ahead
        - Builds excitement and motivation
        - Addresses common misconceptions or fears
        
        Target audience: {state.target_audience}
        Style: {state.book_style}
        Length: 400-600 words.
        """
        
        state.prologue, _ = self.llm.call_llm(prompt)
        return state