import sys
import types
from pathlib import Path

import pytest

from . import pydantic_patch  # noqa: F401  # apply compatibility patch

# Stub out optional langsmith dependency used by langgraph to avoid heavy imports
langsmith_stub = types.ModuleType("langsmith")
sys.modules.setdefault("langsmith", langsmith_stub)
sys.modules.setdefault("langsmith.client", types.ModuleType("client"))
sys.modules.setdefault("langsmith.env", types.ModuleType("env"))

run_helpers_mod = types.ModuleType("run_helpers")


class _DummyCtx:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def get_run_tree_context(*args, **kwargs):
    return _DummyCtx()


run_helpers_mod.get_run_tree_context = get_run_tree_context
sys.modules.setdefault("langsmith.run_helpers", run_helpers_mod)

sys.modules.setdefault("langsmith.utils", types.ModuleType("utils"))
schemas_mod = types.ModuleType("schemas")


class RunBase: ...


class RunTypeEnum: ...


schemas_mod.RunBase = RunBase
schemas_mod.RunTypeEnum = RunTypeEnum
sys.modules.setdefault("langsmith.schemas", schemas_mod)

from BookLLM.src.agents.content.back_matter import (
    AboutAuthorAgent,
    AcknowledgmentsAgent,
    BibliographyAgent,
    IndexAgent,
)
from BookLLM.src.agents.content.chapter import ChapterWriterAgent
from BookLLM.src.agents.content.outline import OutlineAgent
from BookLLM.src.agents.content.writer import WriterAgent
from BookLLM.src.agents.enhancement.code import CodeSampleAgent
from BookLLM.src.agents.enhancement.glossary import GlossaryAgent
from BookLLM.src.models.config import CostConfig, ModelConfig, SystemConfig
from BookLLM.src.models.state import BookState
from BookLLM.src.utils.metrics import TokenMetricsTracker


class DummyLLM:
    def __init__(self):
        self.system_config = SystemConfig(output_dir=Path("test_output"))
        self.model_config = ModelConfig()
        self.cost_config = CostConfig()
        self.metrics = TokenMetricsTracker()

    def call_llm(self, prompt: str, json_mode: bool = False, **kwargs):
        if "book outline" in prompt:
            return '["Intro","Chapter 1"]', {}
        if "Extract and define technical terms" in prompt:
            return '{"term":"definition"}', {}
        if "Write a comprehensive chapter" in prompt:
            return "This chapter includes code snippets", {}
        if "Create practical code examples" in prompt:
            return "```python\nprint('example')\n```", {}
        if "acknowledgments" in prompt.lower():
            return "Thanks to everyone", {}
        if "biography" in prompt.lower() or "about the author" in prompt.lower():
            return "Author bio", {}
        if "detailed bibliography" in prompt.lower() or "Format entries" in prompt:
            return "Reference 1", {}
        if "comprehensive index" in prompt:
            return "Topic\nConcept", {}
        return "text", {}

    async def acall_llm(self, prompt: str, json_mode: bool = False, **kwargs):
        return self.call_llm(prompt, json_mode=json_mode, **kwargs)


def test_agent_workflow():
    dummy_llm = DummyLLM()
    state = BookState(topic="Test")

    # Outline generation
    outline_agent = OutlineAgent(dummy_llm)
    state = outline_agent._execute_logic(state)
    assert state.outline == ["Intro", "Chapter 1"]

    # Chapter writing
    chapter_agent = ChapterWriterAgent(dummy_llm)
    state = chapter_agent._execute_logic(state)
    assert state.chapter_map

    # Enhancements
    glossary_agent = GlossaryAgent(dummy_llm)
    state = glossary_agent._execute_logic(state)
    assert state.glossary == {"term": "definition"}

    code_agent = CodeSampleAgent(dummy_llm)
    state = code_agent._execute_logic(state)
    assert state.code_samples

    ack_agent = AcknowledgmentsAgent(dummy_llm)
    state = ack_agent._execute_logic(state)
    assert state.acknowledgments == "Thanks to everyone"

    about_agent = AboutAuthorAgent(dummy_llm)
    state = about_agent._execute_logic(state)
    assert state.about_the_author == "Author bio"

    state.references = ["Reference 1"]
    biblio_agent = BibliographyAgent(dummy_llm)
    state = biblio_agent._execute_logic(state)
    assert "Reference" in state.bibliography

    index_agent = IndexAgent(dummy_llm)
    state.glossary = {"Term": "Def"}
    state = index_agent._execute_logic(state)
    assert any("see Glossary" in t for t in state.index_terms)
