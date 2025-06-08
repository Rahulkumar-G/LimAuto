from ...models.agent_type import AgentType
from ...models.state import BookState
from ..base import BaseAgent


class TemplateAgent(BaseAgent):
    """Generate simple downloadable templates for each chapter."""

    def __init__(self, llm, agent_type: AgentType = AgentType.ENHANCER):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        for chapter_title, content in state.chapter_map.items():
            try:
                self._generate_template(state, chapter_title, content)
            except Exception as e:
                self.logger.error(
                    f"Failed to generate template for {chapter_title}: {e}"
                )
                state.warnings.append(f"Template generation failed for {chapter_title}")
        return state

    def _generate_template(
        self, state: BookState, chapter_title: str, content: str
    ) -> None:
        prompt = f"""
        Create a short downloadable worksheet or template that complements chapter "{chapter_title}" of a book on {state.topic}.
        Provide the template in Markdown format.
        Chapter excerpt: {content[:1000]}...
        """
        response, _ = self.llm.call_llm(prompt)
        state.templates[chapter_title] = response.strip()
