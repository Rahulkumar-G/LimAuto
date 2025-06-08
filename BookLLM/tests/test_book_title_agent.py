import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from BookLLM.src.agents.content.front_matter.book_title import BookTitleAgent
from BookLLM.src.models.state import BookState


class DummyLLM:
    def call_llm(self, prompt, **kwargs):
        return ('{"title": "Great Book", "subtitle": "A Journey"}', {})


def test_book_title_agent_sets_metadata():
    state = BookState(topic="LLM")
    agent = BookTitleAgent(DummyLLM())
    new_state = agent._execute_logic(state)
    assert new_state.book_title == "Great Book"
    assert new_state.book_subtitle == "A Journey"
    assert new_state.metadata["title"] == "Great Book"
    assert new_state.metadata["subtitle"] == "A Journey"
