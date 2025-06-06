import types
from BookLLM.src.agents.content.outline import OutlineAgent
from BookLLM.src.models.state import BookState


class DummyLLM:
    def call_llm(self, prompt, **kwargs):
        return (
            'Here is your outline:\n```json\n[\n "Intro", "Chapter Two"\n]\n```',
            {},
        )


def test_outline_agent_parses_json_code_block():
    state = BookState(topic="LLM")
    agent = OutlineAgent(DummyLLM())
    new_state = agent._execute_logic(state)
    assert new_state.chapters == ["Intro", "Chapter Two"]


class BadJSONLLM:
    def call_llm(self, prompt, **kwargs):
        return (
            'Here is your outline:\n```json\n[\n "Intro",\n "Chapter Two",\n]\n```',
            {},
        )


def test_outline_agent_handles_invalid_json():
    state = BookState(topic="LLM")
    agent = OutlineAgent(BadJSONLLM())
    new_state = agent._execute_logic(state)
    assert new_state.chapters == ["Intro", "Chapter Two"]
