import asyncio
import hashlib
from typing import Any, Dict, Optional, Tuple

import openai

from ..models.config import CostConfig, ModelConfig, SystemConfig
from ..utils.metrics import TokenMetricsTracker
from ..utils.logger import get_logger
from .llm import LLMInterface


class OpenAIInterface(LLMInterface):
    """Interface for OpenAI's chat completion API"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = get_logger(__name__)
        self.metrics = TokenMetricsTracker()
        self.client = openai.AsyncOpenAI()

    async def acall_llm(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> Tuple[str, Dict[str, int]]:
        if system_prompt is None:
            system_prompt = (
                "You are a professional author and content creator. "
                "Provide comprehensive, well-structured content."
            )
        model_name = self.model_config.name
        full_prompt = f"{system_prompt}\n\n{prompt}"
        input_tokens = self.estimate_tokens(full_prompt)
        request_id = hashlib.md5(full_prompt.encode()).hexdigest()

        for attempt in range(self.system_config.max_retries):
            try:
                resp = await self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.model_config.temperature,
                    max_tokens=self.model_config.max_tokens,
                )
                text = resp.choices[0].message.content.strip()
                usage = resp.usage
                if usage:
                    input_tokens = usage.prompt_tokens
                    output_tokens = usage.completion_tokens
                else:
                    output_tokens = self.estimate_tokens(text)
                self.metrics.add_usage(
                    input_tokens,
                    output_tokens,
                    self.cost_config,
                    request_id=request_id,
                )
                return text, {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                }
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self.system_config.max_retries - 1:
                    raise
                await asyncio.sleep(self.system_config.retry_delay * (2**attempt))
        raise RuntimeError("LLM call failed after all retries")

    def call_llm(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> Tuple[str, Dict[str, int]]:
        return asyncio.run(self.acall_llm(prompt, system_prompt, **kwargs))
