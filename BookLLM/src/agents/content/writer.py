import importlib
from datetime import datetime
from typing import Optional, Type

from ...models.agent_type import AgentType
from ...models.state import BookState
from ..base import BaseAgent
from .chapter import ChapterWriterAgent
from .outline import OutlineAgent


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
            state = outline_agent.process(state)

        # Generate front matter only once
        front_matter_agents = {
            "ForewordAgent": "foreword",
            "DedicationAgent": "dedication",
            "EpigraphAgent": "epigraph",
            "PrefaceAgent": "preface",
            "PrologueAgent": "prologue",
        }

        for agent_name, attr in front_matter_agents.items():
            if getattr(state, attr, None):
                continue  # Skip if already generated
            agent_class = self._get_agent_class(agent_name)
            if agent_class:
                agent = agent_class(self.llm, self.agent_type)
                state = agent.process(state)

        # Generate main content
        chapter_writer = ChapterWriterAgent(self.llm, self.agent_type)
        state = chapter_writer.process(state)

        state.generation_completed = datetime.now()
        return state

    def _get_agent_class(self, agent_name: str) -> Optional[Type[BaseAgent]]:
        """Get agent class by name"""
        try:
            # Import front matter agents dynamically using the package path of
            # this module. When executed with ``python -m BookLLM.src.main`` the
            # project is namespaced under ``BookLLM`` so there is no top-level
            # ``src`` package. ``__package__`` resolves to ``BookLLM.src.agents.content``
            # which ensures the dynamic import works regardless of how the
            # project is executed.
            module_base = agent_name.removesuffix("Agent") if agent_name.lower().endswith("agent") else agent_name
            module_name = f"{__package__}.front_matter.{module_base.lower()}"
            module = importlib.import_module(module_name)
            return getattr(module, agent_name)
        except (ImportError, AttributeError) as e:
            self.logger.warning(f"Failed to load agent {agent_name}: {e}")
            return None
