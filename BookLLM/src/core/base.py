from dataclasses import dataclass
from .types import AgentInput, AgentOutput, Config


class BaseAgent:
    """Base class for simple pipeline agents."""

    def __init__(self, config: Config) -> None:
        self.config = config

    def run(self, input: AgentInput) -> AgentOutput:  # pragma: no cover - abstract
        """Execute agent logic.

        Parameters
        ----------
        input: AgentInput
            Input data for the agent.
        Returns
        -------
        AgentOutput
            Resulting output from the agent.
        """
        raise NotImplementedError
