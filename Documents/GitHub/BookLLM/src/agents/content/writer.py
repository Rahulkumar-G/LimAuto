from typing import Dict, Type, Optional
from datetime import datetime
from ..base import BaseAgent
from ...models.state import BookState
from ...models.agent_type import AgentType
from .outline import OutlineAgent
from .chapter import ChapterWriterAgent

class WriterAgent(BaseAgent):
    """Coordinates the overall writing process"""
    
    def __init__(self, llm, agent_type: AgentType = AgentType.CONTENT_CREATOR):
        super().__init__(llm, agent_type)
        
    def _execute_logic(self, state: BookState) -> BookState:
        """Coordinates the overall writing process"""
        # Initialize book structure
        state.generation_started = datetime.now()
        
        # Create outline if not exists
        if not state.outline:
            outline_agent = OutlineAgent(self.llm, self.agent_type)
            state = outline_agent.execute(state)
        
        # Generate front matter
        front_matter_agents = [
            'ForewordAgent',
            'DedicationAgent', 
            'EpigraphAgent',
            'PrefaceAgent',
            'PrologueAgent'
        ]
        
        for agent_name in front_matter_agents:
            agent_class = self._get_agent_class(agent_name)
            if agent_class:
                agent = agent_class(self.llm, self.agent_type)
                state = agent.execute(state)
        
        # Generate main content
        chapter_writer = ChapterWriterAgent(self.llm, self.agent_type)
        state = chapter_writer.execute(state)
        
        state.generation_completed = datetime.now()
        return state
    
    def _get_agent_class(self, agent_name: str) -> Optional[Type[BaseAgent]]:
        """Get agent class by name"""
        try:
            # Import front matter agents dynamically
            module = __import__(
                f"src.agents.content.front_matter.{agent_name.lower()}", 
                fromlist=[agent_name]
            )
            return getattr(module, agent_name)
        except (ImportError, AttributeError) as e:
            self.logger.warning(f"Failed to load agent {agent_name}: {e}")
            return None