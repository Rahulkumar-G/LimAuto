from pathlib import Path

from ....models.agent_type import AgentType
from ....models.state import BookState
from ...base import BaseAgent


class TitlePageAgent(BaseAgent):
    """Generates professional title page"""

    def __init__(self, llm, agent_type: AgentType = AgentType.FRONT_MATTER):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        """Generate the book's title page"""
        title = state.book_title or state.topic
        author = state.metadata.get("author", "Unknown")

        maketitle = f"\\title{{{title}}}\n\\author{{{author}}}\n\\maketitle\n"
        state.title_page = maketitle

        output_dir = Path(self.llm.system_config.output_dir)
        tex_path = output_dir / "title.tex"
        try:
            tex_path.write_text(maketitle)
        except Exception as e:
            self.logger.warning(f"Failed to write title.tex: {e}")

        return state
