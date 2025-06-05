from enum import Enum


class AgentType(Enum):
    """Types of agents in the book generation system"""

    CONTENT_CREATOR = "content"  # Agents that create primary content
    REVIEWER = "review"  # Agents that review and validate content
    ENHANCER = "enhance"  # Agents that enhance existing content
    COMPILER = "compile"  # Agents that compile and format content
    FRONT_MATTER = "front_matter"  # Agents that generate book front matter

    def __str__(self) -> str:
        return self.value
