from typing import Any, Dict, List
from datetime import datetime

from langgraph.graph import END, StateGraph

from ..agents.content import OutlineAgent, WriterAgent
from ..models.agent_type import AgentType
from ..models.state import BookState
from ..content.review.proofreader import ReviewerAgent
from ..content.enhancement.enhancer import ContentEnhancementAgent
from ..content.enhancement.acronym import AcronymAgent
from ..content.review.validator import QualityAssuranceAgent
from .orchestrator import FinalCompilationAgent
from .types import Config, AgentInput


class BookGraph:
    """Manages the book generation workflow graph"""

    def __init__(self, llm, save_callback=None):
        self.llm = llm
        self.graph = StateGraph(BookState)
        self.agents = self._initialize_agents()
        self.save_callback = save_callback

    def build(self) -> StateGraph:
        """Build and compile the workflow graph"""
        # Create nodes from agents
        nodes = self._create_nodes()

        # Add nodes to graph
        for node_name, execute_func in nodes.items():
            self.graph.add_node(node_name, execute_func)

        # Define workflow sequence
        workflow = self._define_workflow()

        # Set entry point
        self.graph.set_entry_point(workflow[0])

        # Create edges between nodes
        self._create_edges(workflow)

        # Add end condition
        self.graph.add_edge(workflow[-1], END)

        return self.graph.compile()

    def _create_edges(self, workflow: List[str]):
        """Create linear edges between workflow nodes."""
        for i in range(len(workflow) - 1):
            self.graph.add_edge(workflow[i], workflow[i + 1])

    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all required agents for the simplified pipeline."""
        cfg = Config()
        return {
            "outline": OutlineAgent(self.llm, AgentType.CONTENT_CREATOR),
            "writer": WriterAgent(self.llm, AgentType.CONTENT_CREATOR),
            "reviewer": ReviewerAgent(cfg),
            "enhancer": ContentEnhancementAgent(cfg),
            "acronym": AcronymAgent(cfg),
            "quality": QualityAssuranceAgent(cfg),
            "final": FinalCompilationAgent(cfg),
        }

    def _create_nodes(self) -> Dict[str, callable]:
        """Create graph nodes from agents"""
        nodes = {}
        for name, agent in self.agents.items():
            def make_func(a, step_name):
                def _inner(state: BookState):
                    if step_name in state.completed_steps:
                        return state
                    input_data = AgentInput(
                        content=state.compiled_book or "\n".join(state.chapters),
                        metadata=state.metadata,
                        outline=None,
                    )
                    result = a.run(input_data)
                    if result.corrected_text:
                        state.compiled_book = result.corrected_text
                    if result.enhanced_content:
                        state.compiled_book = result.enhanced_content
                    if result.resolved_content:
                        state.compiled_book = result.resolved_content
                    if result.acronym_glossary:
                        state.acronyms.update(result.acronym_glossary)
                    if result.final_doc:
                        state.compiled_book = result.final_doc
                        if result.toc:
                            state.table_of_contents = "\n".join(
                                f"{e.chapter}. {e.title}" for e in result.toc
                            )
                    if result.is_valid is not None:
                        state.metadata.setdefault("qa", {})["is_valid"] = result.is_valid
                        state.metadata.setdefault("qa", {})["issues"] = result.issues
                    state.current_step = step_name
                    if step_name not in state.completed_steps:
                        state.completed_steps.append(step_name)
                    state.last_modified = datetime.now()
                    if self.save_callback:
                        self.save_callback(state)
                    return state

                return _inner

            nodes[f"{name}_node"] = make_func(agent, name)
        return nodes

    def _define_workflow(self) -> List[str]:
        """Define the workflow sequence"""
        return [
            "outline_node",
            "writer_node",
            "reviewer_node",
            "enhancer_node",
            "acronym_node",
            "quality_node",
            "final_node",
        ]
