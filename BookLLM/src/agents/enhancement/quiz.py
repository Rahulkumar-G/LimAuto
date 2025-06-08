from ...models.agent_type import AgentType
from ...models.state import BookState
from ..base import BaseAgent


class QuizAgent(BaseAgent):
    """Create 'Check Your Understanding' questions for each chapter."""

    def __init__(self, llm, agent_type: AgentType = AgentType.ENHANCER):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        for chapter_title, content in state.chapter_map.items():
            try:
                self._generate_questions(state, chapter_title, content)
            except Exception as e:
                self.logger.error(
                    f"Failed to generate questions for {chapter_title}: {e}"
                )
                state.warnings.append(f"Question generation failed for {chapter_title}")
        return state

    def _generate_questions(
        self, state: BookState, chapter_title: str, content: str
    ) -> None:
        prompt = f"""
        Generate 3-5 short 'Check Your Understanding' questions based on chapter "{chapter_title}" about {state.topic}.
        Audience: {state.target_audience}.
        Return the questions as a JSON list of strings.
        Chapter excerpt: {content[:1000]}...
        """
        response, _ = self.llm.call_llm(prompt, json_mode=True)
        questions = self._parse_json(response)
        if isinstance(questions, list):
            state.check_questions[chapter_title] = [str(q).strip() for q in questions]
        else:
            state.warnings.append(f"Invalid question format for {chapter_title}")
