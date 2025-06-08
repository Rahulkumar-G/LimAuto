from ....models.agent_type import AgentType
from ....models.state import BookState
from ...base import BaseAgent


class BookTitleAgent(BaseAgent):
    """Generate a cohesive book title and subtitle."""

    def __init__(self, llm, agent_type: AgentType = AgentType.FRONT_MATTER):
        super().__init__(llm, agent_type)

    def _execute_logic(self, state: BookState) -> BookState:
        """Create the book's title and subtitle."""
        if state.book_title:
            # Title already generated
            state.metadata["title"] = state.book_title
            if state.book_subtitle:
                state.metadata["subtitle"] = state.book_subtitle
            return state

        prompt = f"""
        Propose a concise and engaging title and optional subtitle for a book about "{state.topic}".
        Audience: {state.target_audience}
        Style: {state.book_style}

        Return a JSON object with keys 'title' and 'subtitle'.
        """

        response, _ = self.llm.call_llm(prompt, json_mode=True)
        try:
            data = self._parse_json(response)
            state.book_title = data.get("title") or state.topic
            state.book_subtitle = data.get("subtitle")
        except Exception:
            lines = [line.strip() for line in response.splitlines() if line.strip()]
            if lines:
                state.book_title = lines[0]
            if len(lines) > 1:
                state.book_subtitle = lines[1]

        state.metadata["title"] = state.book_title
        if state.book_subtitle:
            state.metadata["subtitle"] = state.book_subtitle
        return state
