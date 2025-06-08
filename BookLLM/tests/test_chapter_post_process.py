import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from BookLLM.src.agents.content.chapter import ChapterWriterAgent
from BookLLM.src.models.state import BookState


class DummyLLM:
    def call_llm(self, prompt, **kwargs):
        return ("Body", {})


def test_post_process_inserts_header():
    state = BookState(topic="LLM", chapters=["Intro"])
    agent = ChapterWriterAgent(DummyLLM())
    result = agent._post_process_chapter("Some text", state, "Intro")
    assert result.startswith("# Chapter 1: Intro")
