from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from ..models.state import BookState
from ..models.agent_type import AgentType
from ..agents.content import WriterAgent, OutlineAgent, ChapterWriterAgent
from ..agents.review import ProofreaderAgent
from ..agents.enhancement import GlossaryAgent, CodeSampleAgent

class BookGraph:
    """Manages the book generation workflow graph"""
    
    def __init__(self, llm):
        self.llm = llm
        self.graph = StateGraph(BookState)
        self.agents = self._initialize_agents()
        
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
        """Create edges between nodes"""
        # Create linear chain
        for i in range(len(workflow) - 1):
            self.graph.add_edge(workflow[i], workflow[i + 1])
        
        # Add conditional branching for review
        def review_router(state: BookState) -> str:
            """Route based on quality check"""
            quality_score = (
                state.technical_accuracy_score or 0.0 +
                state.consistency_score or 0.0 +
                state.completeness_score or 0.0
            ) / 3.0
            
            if quality_score < 0.8:
                return "writer_node"  # Revise content
            return workflow[-1]  # Move to final node
        
        # Add conditional branching using the correct method
        self.graph.add_conditional_edges(
            "proofreader_node",
            review_router
        )
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all required agents"""
        return {
            'writer': WriterAgent(self.llm, AgentType.CONTENT_CREATOR),
            'outline': OutlineAgent(self.llm, AgentType.CONTENT_CREATOR),
            'chapter': ChapterWriterAgent(self.llm, AgentType.CONTENT_CREATOR),
            'proofreader': ProofreaderAgent(self.llm, AgentType.REVIEWER),
            'glossary': GlossaryAgent(self.llm, AgentType.ENHANCER),
            'code': CodeSampleAgent(self.llm, AgentType.ENHANCER)
        }
    
    def _create_nodes(self) -> Dict[str, callable]:
        """Create graph nodes from agents"""
        nodes = {}
        for name, agent in self.agents.items():
            def make_func(a):
                def _inner(state: BookState):
                    return a.process(state)
                return _inner

            nodes[f"{name}_node"] = make_func(agent)
        return nodes
    
    def _define_workflow(self) -> List[str]:
        """Define the workflow sequence"""
        return [
            "outline_node",
            "writer_node",
            "chapter_node",
            "glossary_node",
            "code_node",
            "proofreader_node"
        ]