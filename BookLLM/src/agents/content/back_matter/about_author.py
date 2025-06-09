from pathlib import Path

from ....models.agent_type import AgentType
from ....models.state import BookState
from ....core.types import Config
from ...base import BaseAgent


class AboutAuthorAgent(BaseAgent):
    """Generate an 'About the Author' section"""

    def __init__(self, llm, agent_type: AgentType = AgentType.COMPILER):
        super().__init__(llm, agent_type)
        self.config = Config()

    def _execute_logic(self, state: BookState) -> BookState:
        prompt = f"""
        Write a short biography for the author of this {state.topic} book.

        Highlight relevant expertise, notable accomplishments, and connection to the topic.
        Tone should be professional yet approachable.
        Length: 150-200 words.
        """

        try:
            state.about_the_author, _ = self.llm.call_llm(prompt)
        except Exception as e:
            self.logger.warning(f"About the Author generation failed: {e}")
            state.about_the_author = ""

        if not state.about_the_author:
            placeholder = " ".join(["Lorem ipsum dolor sit amet"] * 30)
            state.about_the_author = placeholder

        output_dir = Path(self.llm.system_config.output_dir)
        tex_path = output_dir / "about_author.tex"
        try:
            tex_path.write_text(state.about_the_author)
        except Exception as e:
            self.logger.warning(f"Failed to write about_author.tex: {e}")

        return state
