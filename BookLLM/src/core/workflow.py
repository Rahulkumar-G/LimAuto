from dataclasses import dataclass
from datetime import datetime
from typing import List

from ..models.state import BookState


@dataclass
class WorkflowStep:
    name: str
    agent: str
    dependencies: List[str]
    retry_count: int = 3
    timeout: int = 300


class BookWorkflow:
    """Manages the book generation workflow steps and state"""

    def __init__(self):
        self.steps = self._define_steps()
        self.current_step = 0
        self.start_time = None
        self.end_time = None

    def _define_steps(self) -> List[WorkflowStep]:
        """Define workflow steps"""
        return [
            WorkflowStep(name="outline", agent="OutlineAgent", dependencies=[]),
            WorkflowStep(
                name="chapters", agent="ChapterWriterAgent", dependencies=["outline"]
            ),
            WorkflowStep(
                name="review", agent="ReviewerAgent", dependencies=["chapters"]
            ),
            WorkflowStep(
                name="enhance", agent="ContentEnhancementAgent", dependencies=["review"]
            ),
            WorkflowStep(
                name="quality", agent="QualityAssuranceAgent", dependencies=["enhance"]
            ),
            WorkflowStep(
                name="compile", agent="FinalCompilationAgent", dependencies=["quality"]
            ),
        ]

    def start(self, state: BookState):
        """Start workflow execution"""
        self.start_time = datetime.now()
        state.generation_started = self.start_time
        return state

    def complete(self, state: BookState):
        """Complete workflow execution"""
        self.end_time = datetime.now()
        state.generation_completed = self.end_time
        return state

    def get_next_step(self, state: BookState) -> WorkflowStep:
        """Get next workflow step based on state"""
        for step in self.steps:
            if step.name not in state.completed_steps:
                if all(dep in state.completed_steps for dep in step.dependencies):
                    return step
        return None

    def validate_step(self, step: WorkflowStep, state: BookState) -> bool:
        """Validate if step can be executed"""
        return all(dep in state.completed_steps for dep in step.dependencies)
