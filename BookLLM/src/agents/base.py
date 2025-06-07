import asyncio
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional

from ..interfaces.llm import EnhancedLLMInterface
from ..models.agent_type import AgentType
from ..models.state import BookState
from ..utils.logger import get_logger


class BaseAgent:
    """Base class for all book generation agents"""

    def __init__(self, llm: EnhancedLLMInterface, agent_type: AgentType):
        if not isinstance(agent_type, AgentType):
            raise ValueError(
                f"agent_type must be an AgentType enum, got {type(agent_type)}"
            )
        self.llm = llm
        self.agent_type = agent_type
        self.logger = get_logger(__name__)

    async def run(self) -> Optional[Dict[str, Any]]:
        """Execute the agent's task"""
        try:
            start_time = asyncio.get_event_loop().time()

            # Ensure self.prompt exists; otherwise, provide a default or handle error
            current_prompt = getattr(self, "prompt", "")
            if not current_prompt:
                self.logger.warning(
                    f"Agent {self.__class__.__name__} run method called with empty/missing self.prompt."
                )

            # Use acall_llm for async operations. json_mode is not directly supported by acall_llm's current Ollama flags.
            # If JSON output is needed, it should be requested in the prompt itself.
            response, metadata = await self.llm.acall_llm(current_prompt)
            duration = asyncio.get_event_loop().time() - start_time

            return {
                "response": response,
                "metadata": metadata,  # Contains token counts for this call
                "duration": duration,
            }
        except Exception as e:
            self.logger.error(
                f"❌ Failed {self.__class__.__name__} in 'run' method: {str(e)}"
            )
            return None

    async def execute(self, prompt: str, **kwargs) -> str:
        """Execute agent task asynchronously"""
        response, metrics = await self.llm.acall_llm(prompt, **kwargs)
        return response

    def execute_sync(self, prompt: str, **kwargs) -> str:
        """Execute agent task synchronously"""
        response, metrics = self.llm.call_llm(prompt, **kwargs)
        return response

    def process(self, state: BookState) -> BookState:
        """Run agent logic with retry-based healing and detailed logging."""
        max_retries = self.llm.system_config.max_retries
        delay = self.llm.system_config.retry_delay

        for attempt in range(max_retries):
            try:
                self.logger.debug(
                    f"Starting {self.__class__.__name__} (attempt {attempt + 1})"
                )
                result_state = self._execute_logic(state)
                result_state.completed_steps.append(self.__class__.__name__)
                if self.llm.system_config.save_intermediates:
                    self._save_agent_output(result_state, self.__class__.__name__)
                return result_state
            except Exception as e:
                self.logger.error(
                    f"Error in {self.__class__.__name__} attempt {attempt + 1}: {e}",
                    exc_info=True,
                )
                if attempt == max_retries - 1:
                    state.errors.append(f"{self.__class__.__name__}: {e}")
                    return state
                time.sleep(delay * (2**attempt))

    def _execute_logic(self, state: BookState) -> BookState:
        """Override this method in subclasses"""
        raise NotImplementedError

    def _save_agent_output(self, state: BookState, step_name: str):
        """Saves the agent's output to a file."""
        output_dir = self.llm.system_config.output_dir / "agent_outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = output_dir / f"{step_name}_{timestamp}.json"
        try:
            with open(file_path, "w") as f:
                json.dump(state.dict(), f, indent=2, default=str)
            self.logger.info(f"Saved output for {step_name} to {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to save output for {step_name}: {e}")

    @staticmethod
    def _parse_json(response: str) -> Any:
        """Parse JSON from a string, ignoring text before/after the JSON block."""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            cleaned = response.strip()
            # Look for object or array delimiters
            first_obj = cleaned.find("{")
            last_obj = cleaned.rfind("}")
            first_arr = cleaned.find("[")
            last_arr = cleaned.rfind("]")
            candidates = []
            if first_obj != -1 and last_obj != -1 and last_obj > first_obj:
                candidates.append(cleaned[first_obj : last_obj + 1])
            if first_arr != -1 and last_arr != -1 and last_arr > first_arr:
                candidates.append(cleaned[first_arr : last_arr + 1])
            for snippet in candidates:
                try:
                    return json.loads(snippet)
                except json.JSONDecodeError:
                    continue
            raise

