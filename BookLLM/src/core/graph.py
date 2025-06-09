from typing import Any, Dict, List
from datetime import datetime

from BookLLM.src.agents.content.chapter import ChapterWriterAgent
from BookLLM.src.agents.enhancement.case_study import CaseStudyAgent
from BookLLM.src.agents.enhancement.glossary import GlossaryAgent
from BookLLM.src.agents.enhancement.quiz import QuizAgent
from BookLLM.src.agents.enhancement.template import TemplateAgent
from BookLLM.src.agents.review.proofreader import ProofreaderAgent
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
            "chapter": ChapterWriterAgent(self.llm, AgentType.CONTENT_CREATOR),
            "proofreader": ProofreaderAgent(self.llm, AgentType.REVIEWER),
            "glossary": GlossaryAgent(self.llm, AgentType.ENHANCER),
            # "code": CodeSampleAgent(self.llm, AgentType.ENHANCER),
            "case": CaseStudyAgent(self.llm, AgentType.ENHANCER),
            "quiz": QuizAgent(self.llm, AgentType.ENHANCER),
            "template": TemplateAgent(self.llm, AgentType.ENHANCER),

        }

    def _create_nodes(self) -> Dict[str, callable]:
        """Create graph nodes from agents"""
        nodes = {}
        for name, agent in self.agents.items():
            def make_func(a, step_name):
                def _inner(state: BookState):
                    if step_name in state.completed_steps:
                        return state

                    # Legacy agents operate directly on BookState
                    state = a.process(state)
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
            "chapter_node",
            "glossary_node",
            # "code_node",
            "case_node",
            "quiz_node",
            "template_node",
            "proofreader_node",
        ]
