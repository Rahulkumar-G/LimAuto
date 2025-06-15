from typing import Any, Dict, List
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..agents.content.chapter import ChapterWriterAgent
from ..agents.enhancement.case_study import CaseStudyAgent
from ..agents.enhancement.glossary import GlossaryAgent
from ..agents.enhancement.quiz import QuizAgent
from ..agents.enhancement.template import TemplateAgent
from ..agents.review.proofreader import ProofreaderAgent
from langgraph.graph import END, StateGraph

from ..agents.content import OutlineAgent, WriterAgent
from ..models.agent_type import AgentType
from ..monitoring import mark_start
from ..models.state import BookState
from ..content.review.proofreader import ReviewerAgent
from ..content.enhancement.enhancer import ContentEnhancementAgent
from ..content.enhancement.acronym import AcronymAgent
from ..content.review.validator import QualityAssuranceAgent
from .orchestrator import FinalCompilationAgent
from .types import Config, AgentInput


class BookGraph:
    """Manages the book generation workflow graph"""

    def __init__(self, llm, save_callback=None, enable_parallel=True, max_workers=3):
        self.llm = llm
        self.graph = StateGraph(BookState)
        self.agents = self._initialize_agents()
        self.save_callback = save_callback
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        self.parallel_groups = self._get_parallel_groups()

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
        all_agents = {
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

        seq = getattr(getattr(self.llm, "system_config", None), "agent_sequence", None)
        if seq:
            return {name: all_agents[name] for name in seq if name in all_agents}
        return all_agents

    def _create_nodes(self) -> Dict[str, callable]:
        """Create graph nodes from agents"""
        nodes = {}
        for name, agent in self.agents.items():
            def make_func(a, step_name):
                def _inner(state: BookState):
                    if step_name in state.completed_steps:
                        return state

                    if step_name not in state.agent_start_times:
                        mark_start(step_name)
                        state.agent_start_times[step_name] = datetime.now().isoformat()

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
        seq = getattr(getattr(self.llm, "system_config", None), "agent_sequence", None)
        if seq:
            return [f"{name}_node" for name in seq]
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

    def _get_parallel_groups(self) -> List[List[str]]:
        """Define which agents can run in parallel"""
        if not self.enable_parallel:
            return []
        
        # Groups of agents that can run simultaneously
        return [
            ["enhancer_node", "acronym_node", "glossary_node"],  # Enhancement agents
            ["case_node", "quiz_node", "template_node"],         # Content agents
        ]

    def _can_run_parallel(self, agent_name: str, completed_steps: List[str]) -> bool:
        """Check if agent can run in parallel with others"""
        dependencies = {
            "enhancer_node": ["chapter_node"],
            "acronym_node": ["chapter_node"], 
            "glossary_node": ["chapter_node"],
            "case_node": ["chapter_node"],
            "quiz_node": ["chapter_node"],
            "template_node": ["chapter_node"],
        }
        
        required_deps = dependencies.get(agent_name, [])
        return all(dep.replace("_node", "") in completed_steps for dep in required_deps)

    def _execute_parallel_group(self, group: List[str], state: BookState) -> BookState:
        """Execute a group of agents in parallel"""
        if not self.enable_parallel or len(group) <= 1:
            # Fall back to sequential execution
            for agent_name in group:
                agent = self.agents[agent_name.replace("_node", "")]
                state = agent.process(state)
            return state

        def run_agent(agent_name: str):
            """Run single agent"""
            try:
                agent = self.agents[agent_name.replace("_node", "")]
                return agent.process(state)
            except Exception as e:
                self.llm.logger.error(f"Parallel agent {agent_name} failed: {e}")
                return state

        # Execute agents in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=min(len(group), self.max_workers)) as executor:
            futures = [executor.submit(run_agent, agent_name) for agent_name in group]
            results = [future.result() for future in futures]

        # Merge results - simple strategy: use the last successful result
        # In production, you'd want more sophisticated state merging
        final_state = state
        for result in results:
            if result and hasattr(result, 'last_modified'):
                if not hasattr(final_state, 'last_modified') or result.last_modified > final_state.last_modified:
                    final_state = result

        return final_state
