from dataclasses import dataclass
from pathlib import Path
from enum import Enum
from typing import Optional

@dataclass
class ModelConfig:
    """Configuration for the LLM model"""
    name: str = "llama2"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.9
    repeat_penalty: float = 1.1
    timeout: int = 120

@dataclass
class CostConfig:
    """Configuration for cost tracking"""
    cost_per_input_token: float = 0.0
    cost_per_output_token: float = 0.0
    cost_per_request: float = 0.0

@dataclass
class SystemConfig:
    """System-wide configuration"""
    output_dir: Path = Path("./book_output")
    log_level: str = "INFO"
    max_retries: int = 3
    retry_delay: float = 2.0
    parallel_agents: bool = True
    max_workers: int = 4
    save_intermediates: bool = True
    backup_frequency: int = 5
    max_steps: int = 50

    def __post_init__(self):
        # Ensure output_dir is a Path object
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

class AgentType(Enum):
    """Types of agents in the system"""
    CONTENT_CREATOR = "content"
    REVIEWER = "review"
    ENHANCER = "enhance"
    COMPILER = "compile"

@dataclass
class TokenMetrics:
    """Metrics for token usage and cost tracking"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    requests_count: int = 0
    total_cost: float = 0.0
    
    def add_usage(
        self, 
        input_tokens: int, 
        output_tokens: int, 
        cost_config: CostConfig
    ) -> None:
        """Add token usage and update costs"""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        self.total_tokens += (input_tokens + output_tokens)
        self.requests_count += 1
        self.total_cost += (
            input_tokens * cost_config.cost_per_input_token +
            output_tokens * cost_config.cost_per_output_token +
            cost_config.cost_per_request
        )
    
    def get_summary(self) -> dict:
        """Get summary of token usage and costs"""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "requests_count": self.requests_count,
            "total_cost_usd": round(self.total_cost, 4),
            "avg_tokens_per_request": round(
                self.total_tokens / self.requests_count 
                if self.requests_count > 0 else 0, 
                2
            )
        }