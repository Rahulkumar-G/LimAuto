import subprocess
import json
import time
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from ..utils.logger import get_logger
from ..models import ModelConfig, SystemConfig

class OllamaService:
    """Service for managing Ollama LLM interactions"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        
    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        model: str = "llama2",
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate text using Ollama"""
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt

        cmd = [
            "ollama", "run",
            model,
            "--nowordwrap"
        ]

        if kwargs.get("json_mode"):
            cmd.extend(["--format", "json"])

        try:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(
                input=full_prompt,
                timeout=kwargs.get("timeout", 120)
            )

            if process.returncode != 0:
                raise subprocess.CalledProcessError(
                    process.returncode, cmd, 
                    output=stdout, stderr=stderr
                )

            output = stdout.strip()
            if not output:
                raise ValueError("Empty response from Ollama")

            # Process JSON response if requested
            if kwargs.get("json_mode"):
                try:
                    parsed = json.loads(output)
                    if isinstance(parsed, dict) and "response" in parsed:
                        output = parsed["response"]
                    else:
                        output = json.dumps(parsed, indent=2)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON response: {e}")

            return output, {"model": model}

        except subprocess.TimeoutExpired:
            process.kill()
            raise
        except Exception as e:
            self.logger.error(f"Ollama generation failed: {e}")
            raise

    def verify_setup(self) -> bool:
        """Verify Ollama installation and service status"""
        try:
            # Check if Ollama is installed
            subprocess.run(
                ["ollama", "version"],
                capture_output=True,
                check=True
            )
            
            # Check if service is running
            subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                check=True
            )
            
            return True
        except subprocess.CalledProcessError:
            return False

    def start_service(self) -> bool:
        """Start Ollama service"""
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            time.sleep(5)  # Wait for service to start
            return self.verify_setup()
        except Exception as e:
            self.logger.error(f"Failed to start Ollama service: {e}")
            return False

    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama"""
        try:
            subprocess.run(
                ["ollama", "pull", model_name],
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to pull model {model_name}: {e}")
            return False