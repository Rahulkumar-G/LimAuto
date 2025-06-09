import json
import types
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))

from BookLLM.src.core import orchestrator as orchestrator_module
from BookLLM.src.core.orchestrator import BookOrchestrator
from BookLLM.src.models.state import BookState

class DummyLLM:
    def __init__(self, config):
        self.config = config
        class Metrics:
            def get_summary(self):
                return {}
            def save_metrics(self, path):
                pass
        self.metrics = Metrics()

class DummyWorkflow:
    def start(self, state):
        return state
    def complete(self, state):
        return state

executed_steps = []
class DummyGraph:
    def __init__(self, llm, save_callback=None):
        self.save_callback = save_callback
    def build(self):
        return self
    def invoke(self, state):
        for step in ["outline", "writer"]:
            if step in state.completed_steps:
                continue
            state.completed_steps.append(step)
            state.current_step = step
            if self.save_callback:
                self.save_callback(state)
            executed_steps.append(step)
        return state

@pytest.fixture(autouse=True)
def stub(monkeypatch):
    monkeypatch.setattr(orchestrator_module, "EnhancedLLMInterface", lambda cfg: DummyLLM(cfg))
    monkeypatch.setattr(orchestrator_module, "BookGraph", lambda llm, save_callback=None: DummyGraph(llm, save_callback))
    monkeypatch.setattr("BookLLM.src.core.graph.BookGraph", DummyGraph)
    monkeypatch.setattr(orchestrator_module, "BookWorkflow", DummyWorkflow)

def test_resume_from_checkpoint(tmp_path):
    o = BookOrchestrator({"system": {"output_dir": str(tmp_path)}})
    state = BookState(topic="Test", completed_steps=["outline"], current_step="outline")
    o._save_checkpoint(state)
    executed_steps.clear()
    o2 = BookOrchestrator({"system": {"output_dir": str(tmp_path)}})
    resumed = o2.generate_book("Test", resume=True)
    assert executed_steps == ["writer"]
    assert resumed.completed_steps == ["outline", "writer"]
