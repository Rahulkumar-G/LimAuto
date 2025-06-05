import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from ..interfaces.llm import EnhancedLLMInterface
from ..models.config import ModelConfig, SystemConfig
from ..models.state import BookState
from ..utils.logger import get_logger
from ..utils.step_tracker import StepEvent, step_tracker
from .graph import BookGraph
from .workflow import BookWorkflow


class BookOrchestrator:
    """Main orchestrator for book generation process"""

    def __init__(self, config: Optional[Any] = None):
        """Initialize the orchestrator.

        Parameters
        ----------
        config: str | dict | None
            Either a path to a YAML configuration file or a pre-loaded
            configuration dictionary. When ``None`` default configuration
            values are used.
        """
        self.logger = get_logger(__name__)
        self.config = self._load_config(config)
        self.llm = EnhancedLLMInterface(self.config)
        self.graph = BookGraph(self.llm).build()
        self.workflow = BookWorkflow()

    def generate_book(self, topic: str, **kwargs) -> BookState:
        """Execute full book generation process"""
        try:
            # Step 1: Initialize state
            initial_state = self._create_initial_state(topic, **kwargs)
            step_tracker.dispatch(StepEvent("Scaffolding"))

            # Step 2: Start workflow
            state = self.workflow.start(initial_state)

            # Step 3: Execute graph
            self.logger.info(f"Starting book generation for: {topic}")
            final_state = self.graph.invoke(state)
            step_tracker.dispatch(StepEvent("Wiring API"))

            # Step 4: Complete workflow
            final_state = self.workflow.complete(final_state)

            # Step 5: Save artifacts
            self._save_artifacts(final_state)
            step_tracker.dispatch(StepEvent("Styling"))

            return final_state

        except Exception as e:
            self.logger.error(f"Book generation failed: {e}")
            raise

    def _load_config(self, config: Optional[Any]) -> Dict[str, Any]:
        """Load configuration from a dict or file path."""
        default_config = {
            "model": ModelConfig().__dict__,
            "system": SystemConfig().__dict__,
        }

        if config:
            try:
                if isinstance(config, (str, Path)):
                    with open(config) as f:
                        user_config = yaml.safe_load(f) or {}
                elif isinstance(config, dict):
                    user_config = config
                else:
                    raise TypeError(
                        "config must be a path to a YAML file or a dictionary"
                    )
                default_config.update(user_config)
            except Exception as e:
                # logger is available because __init__ sets it before this call
                self.logger.warning(f"Failed to load config: {e}")

        return default_config

    def _create_initial_state(self, topic: str, **kwargs) -> BookState:
        """Create initial book state"""
        return BookState(
            topic=topic,
            target_audience=kwargs.get("audience", "beginners"),
            book_style=kwargs.get("style", "professional"),
            estimated_pages=kwargs.get("pages", 100),
            language=kwargs.get("language", "en"),
        )

    def _save_artifacts(self, state: BookState):
        """Save generation artifacts"""
        output_dir = Path(self.config["system"].output_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save book content
        with open(output_dir / f"book_{timestamp}.md", "w") as f:
            f.write(state.compiled_book)

        # Save metadata
        with open(output_dir / f"metadata_{timestamp}.json", "w") as f:
            json.dump(state.metadata, f, indent=2)

        # Save metrics
        with open(output_dir / f"metrics_{timestamp}.json", "w") as f:
            json.dump(self.llm.metrics.get_summary(), f, indent=2)
