from ...models.agent_type import AgentType
from ...models.state import BookState
from ..base import BaseAgent


class CaseStudyAgent(BaseAgent):
    """Generate short case studies for each chapter."""

    def __init__(self, llm, agent_type: AgentType = AgentType.ENHANCER):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        for chapter_title, content in state.chapter_map.items():
            try:
                self._generate_case_study(state, chapter_title, content)
            except Exception as e:
                self.logger.error(
                    f"Failed to generate case study for {chapter_title}: {e}"
                )
                state.warnings.append(
                    f"Case study generation failed for {chapter_title}"
                )
        return state

    def _generate_case_study(
        self, state: BookState, chapter_title: str, content: str
    ) -> None:
        prompt = f"""
        Write a practical case study demonstrating the key ideas from chapter "{chapter_title}" of a book on {state.topic}.
        Audience: {state.target_audience}.
        Provide a concise scenario (200-300 words).
        Content preview: {content[:1000]}...
        """
        response, _ = self.llm.call_llm(prompt)
        state.case_studies[chapter_title] = response.strip()
