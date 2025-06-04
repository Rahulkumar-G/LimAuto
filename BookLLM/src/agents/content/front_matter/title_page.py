from ...base import BaseAgent
from ....models.state import BookState
from ....models.agent_type import AgentType
from datetime import datetime

class TitlePageAgent(BaseAgent):
    """Generates professional title page"""
    
    def __init__(self, llm, agent_type: AgentType = AgentType.FRONT_MATTER):
        super().__init__(llm, agent_type)
    
    def _execute_logic(self, state: BookState) -> BookState:
        """Generate the book's title page"""
        prompt = f"""
        Create a professional title page for book:
        
        Title: {state.topic}
        Style: {state.book_style}
        Audience: {state.target_audience}
        
        Include:
        - Main title
        - Subtitle (if appropriate)
        - Author name/pseudonym
        - Edition information: {state.edition}
        - Publisher info (if available)
        - Copyright year: {datetime.now().year}
        
        Format in standard title page layout.
        """
        
        state.title_page, _ = self.llm.call_llm(prompt)
        return state