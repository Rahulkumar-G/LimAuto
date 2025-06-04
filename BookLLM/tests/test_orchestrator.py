import sys
import types
from pathlib import Path
import yaml
import pytest

# Ensure repository root is on the path
sys.path.append(str(Path(__file__).resolve().parents[2]))

# Stub out heavy optional dependencies used during imports
langgraph_stub = types.ModuleType("graph")
class DummyStateGraph:
    def __init__(self, *args, **kwargs):
        pass
    def add_node(self, *args, **kwargs):
        pass
    def set_entry_point(self, *args, **kwargs):
        pass
    def add_edge(self, *args, **kwargs):
        pass
    def add_conditional_edges(self, *args, **kwargs):
        pass
    def compile(self):
        return self

langgraph_stub.StateGraph = DummyStateGraph
langgraph_stub.END = "end"
sys.modules.setdefault("langgraph.graph", langgraph_stub)

tiktoken_stub = types.ModuleType("tiktoken")
tiktoken_stub.encoding_for_model = lambda name: types.SimpleNamespace(encode=lambda s: [])
tiktoken_stub.get_encoding = lambda name: types.SimpleNamespace(encode=lambda s: [])
sys.modules.setdefault("tiktoken", tiktoken_stub)

from BookLLM.src.core import orchestrator as orchestrator_module
from BookLLM.src.core.orchestrator import BookOrchestrator
from BookLLM.src.models.config import ModelConfig

class DummyLLM:
    def __init__(self, config):
        self.config = config

class DummyGraph:
    def __init__(self, llm):
        self.llm = llm
    def build(self):
        return self
    def invoke(self, state):
        return state

class DummyWorkflow:
    def start(self, state):
        return state
    def complete(self, state):
        return state

@pytest.fixture(autouse=True)
def stub_components(monkeypatch):
    monkeypatch.setattr(orchestrator_module, "EnhancedLLMInterface", lambda cfg: DummyLLM(cfg))
    monkeypatch.setattr(orchestrator_module, "BookGraph", lambda llm: DummyGraph(llm))
    monkeypatch.setattr(orchestrator_module, "BookWorkflow", DummyWorkflow)


def test_orchestrator_default_config():
    o = BookOrchestrator()
    assert o.config["model"]["name"] == ModelConfig().name
    assert isinstance(o.config["system"]["output_dir"], Path)


def test_orchestrator_config_dict(tmp_path):
    custom_dir = tmp_path / "custom"
    cfg = {"model": {"name": "gpt"}, "system": {"output_dir": str(custom_dir)}}
    o = BookOrchestrator(cfg)
    assert o.config["model"]["name"] == "gpt"
    assert Path(o.config["system"]["output_dir"]) == custom_dir


def test_orchestrator_config_file(tmp_path):
    custom_dir = tmp_path / "out"
    cfg = {"model": {"name": "file"}, "system": {"output_dir": str(custom_dir)}}
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg))
    o = BookOrchestrator(str(cfg_path))
    assert o.config["model"]["name"] == "file"
    assert Path(o.config["system"]["output_dir"]) == custom_dir


def test_orchestrator_invalid_type():
    o = BookOrchestrator(123)
    assert o.config["model"]["name"] == ModelConfig().name

