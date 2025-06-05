import asyncio
import subprocess
import time
from typing import Any, Dict, Optional, Tuple

import tiktoken

from ..models.config import CostConfig, ModelConfig, SystemConfig, TokenMetrics
from ..utils.logger import get_logger


class LLMInterface:
    """Base interface for LLM interactions"""

    def __init__(self, config: Dict[str, Any]):
        self.model_config = ModelConfig(**config.get("model", {}))
        self.cost_config = CostConfig(**config.get("cost", {}))
        self.system_config = SystemConfig(**config.get("system", {}))
        self.logger = get_logger(__name__)

        try:
            self.encoding = tiktoken.encoding_for_model("gpt-4")
        except Exception:
            self.encoding = tiktoken.get_encoding("cl100k_base")

        if not self._verify_setup():
            raise RuntimeError("LLM setup failed")

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for a given text"""
        if not text:  # Handle empty or None text
            return 0
        return len(self.encoding.encode(text))

    def _verify_setup(self) -> bool:
        """Verify basic LLM setup"""
        return bool(self.model_config.name)


class EnhancedLLMInterface(LLMInterface):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = get_logger(__name__)  # Use consistent logger
        self.metrics = TokenMetrics()  # Initialize metrics tracking
        self._check_ollama_setup()

    def _validate_prompt(self, prompt: str) -> None:
        """Basic validation for prompts before sending to the LLM."""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        token_count = self.estimate_tokens(prompt)
        if token_count > self.model_config.max_tokens:
            raise ValueError("Prompt exceeds max token limit")

    def _check_ollama_setup(self) -> bool:
        """Verify Ollama installation and model availability"""
        try:
            # Check Ollama version
            version_cmd = ["ollama", "--version"]
            version_result = subprocess.run(version_cmd, capture_output=True, text=True)
            if version_result.returncode == 0:
                self.logger.info(f"Ollama version: {version_result.stdout.strip()}")
            else:
                raise RuntimeError(
                    f"Failed to get Ollama version: {version_result.stderr}"
                )

            # Check if model exists using show command
            model_name = self.model_config.name
            self.logger.info(f"Checking for model '{model_name}'")

            show_cmd = ["ollama", "show", model_name]
            show_result = subprocess.run(show_cmd, capture_output=True, text=True)

            if show_result.returncode != 0:
                self.logger.warning(
                    f"Model '{model_name}' not found. Attempting to pull..."
                )
                pull_cmd = ["ollama", "pull", model_name]
                pull_result = subprocess.run(pull_cmd, capture_output=True, text=True)

                if pull_result.returncode != 0:
                    raise RuntimeError(
                        f"Failed to pull model '{model_name}': {pull_result.stderr}"
                    )

                self.logger.info(f"Successfully pulled model '{model_name}'")

            return True

        except FileNotFoundError:
            raise RuntimeError(
                "Ollama not found. Please install it using 'brew install ollama'"
            )
        except Exception as e:
            raise RuntimeError(
                "Ollama setup failed. Please ensure:\n"
                "1. Ollama is installed (brew install ollama)\n"
                "2. Ollama service is running (ollama serve)\n"
                "3. Required model is available (ollama pull modelname)\n"
                f"Error: {str(e)}"
            )

    async def acall_llm(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> Tuple[str, Dict[str, int]]:
        """Asynchronous LLM call with retry logic"""
        if system_prompt is None:
            system_prompt = (
                "You are a professional author and content creator. "
                "Provide comprehensive, well-structured content."
            )

        self._validate_prompt(prompt)

        full_prompt = f"{system_prompt}\n\n{prompt}"
        input_tokens = self.estimate_tokens(full_prompt)

        for attempt in range(self.system_config.max_retries):
            try:
                # Removed --format json flag since it's not supported
                cmd = ["ollama", "run", self.model_config.name, "--nowordwrap"]

                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate(full_prompt.encode())

                if process.returncode != 0:
                    raise RuntimeError(f"LLM call failed: {stderr.decode()}")

                response = stdout.decode(errors="replace").strip()
                output_tokens = self.estimate_tokens(response)

                # Update cumulative metrics
                self.metrics.add_usage(input_tokens, output_tokens, self.cost_config)

                return response, {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                }

            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.system_config.max_retries - 1:
                    raise
                await asyncio.sleep(self.system_config.retry_delay * (2**attempt))

        # This part should ideally not be reached if max_retries > 0
        raise RuntimeError("LLM call failed after all retries.")

    def call_llm(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> Tuple[str, Dict[str, int]]:
        """Synchronous LLM call with retry logic"""
        if system_prompt is None:
            system_prompt = (
                "You are a professional author and content creator. "
                "Provide comprehensive, well-structured content."
            )

        self._validate_prompt(prompt)

        full_prompt = f"{system_prompt}\n\n{prompt}"
        input_tokens = self.estimate_tokens(full_prompt)

        for attempt in range(self.system_config.max_retries):
            try:
                cmd = ["ollama", "run", self.model_config.name, "--nowordwrap"]

                process = subprocess.run(
                    cmd,
                    input=full_prompt.encode(),
                    capture_output=True,
                    text=False,  # stdout/stderr are bytes
                    timeout=self.model_config.timeout,
                )

                if process.returncode != 0:
                    stderr_msg = (
                        process.stderr.decode(errors="replace")
                        if process.stderr
                        else "Unknown error"
                    )
                    raise RuntimeError(f"LLM call failed: {stderr_msg}")

                response = process.stdout.decode(errors="replace").strip()
                output_tokens = self.estimate_tokens(response)

                # Update cumulative metrics
                self.metrics.add_usage(input_tokens, output_tokens, self.cost_config)

                return response, {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                }
            except subprocess.TimeoutExpired:
                self.logger.error(
                    f"Attempt {attempt + 1} failed: Timeout after {self.model_config.timeout}s for prompt: {prompt[:100]}..."
                )
                if attempt == self.system_config.max_retries - 1:
                    raise RuntimeError(
                        f"LLM call failed after {self.system_config.max_retries} attempts due to timeout."
                    )
                time.sleep(self.system_config.retry_delay * (2**attempt))

            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.system_config.max_retries - 1:
                    raise
                time.sleep(self.system_config.retry_delay * (2**attempt))

        # This part should ideally not be reached if max_retries > 0
        raise RuntimeError("LLM call failed after all retries.")
