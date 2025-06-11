from datetime import datetime
from typing import Dict

# Global mapping of agent names to ISO timestamps
agent_start_times: Dict[str, str] = {}

def mark_start(agent: str) -> None:
    """Record the start time for an agent."""
    agent_start_times[agent] = datetime.now().isoformat()
