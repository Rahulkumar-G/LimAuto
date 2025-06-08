import sys
from pathlib import Path

# Ensure repository root is on the path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from BookLLM.src.agents.content.front_matter.table_of_contents import TableOfContentsAgent
from BookLLM.src.models.state import BookState


def test_table_of_contents_links():
    state = BookState(topic="Test", chapters=["Intro", "Advanced Topics"])
    agent = TableOfContentsAgent(None)
    new_state = agent._execute_logic(state)
    assert "[Intro](#chapter-1-intro)" in new_state.table_of_contents
    assert "[Advanced Topics](#chapter-2-advanced-topics)" in new_state.table_of_contents
