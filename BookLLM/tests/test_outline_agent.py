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


class DictOutlineLLM:
    def call_llm(self, prompt, **kwargs):
        return (
            '[{"Chapter": 1, "Title": "Intro"}, {"Chapter": 2, "Title": "Chapter Two"}]',
            {},
        )


def test_outline_agent_extracts_titles_from_dict():
    state = BookState(topic="LLM")
    agent = OutlineAgent(DictOutlineLLM())
    new_state = agent._execute_logic(state)
    assert new_state.chapters == ["Intro", "Chapter Two"]


class MixedKeysLLM:
    def call_llm(self, prompt, **kwargs):
        return (
            '[{"chapter_title": "Intro"}, {"name": "Chapter Two"}, {"Title": "Third Chapter"}]',
            {},
        )


def test_outline_agent_handles_varied_dict_keys():
    state = BookState(topic="LLM")
    agent = OutlineAgent(MixedKeysLLM())
    new_state = agent._execute_logic(state)
    assert new_state.chapters == ["Intro", "Chapter Two", "Third Chapter"]
