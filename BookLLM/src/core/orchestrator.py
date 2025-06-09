import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List
from threading import Lock

import yaml

from ..interfaces.llm import EnhancedLLMInterface
from ..models.config import ModelConfig, SystemConfig
from ..models.state import BookState
from ..services import ExportService
from ..utils.logger import get_logger
from ..utils.step_tracker import StepEvent, step_tracker
from .workflow import BookWorkflow
from typing import TYPE_CHECKING

BookGraph = None
if TYPE_CHECKING:  # pragma: no cover - for type hints
    from .graph import BookGraph as _BookGraph


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
        system_cfg = self.config.get("system", {})
        output_dir = (
            system_cfg.output_dir
            if hasattr(system_cfg, "output_dir")
            else system_cfg.get("output_dir", "./book_output")
        )
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path = self.output_dir / "checkpoint.json"

        from .graph import BookGraph as GraphClass
        global BookGraph
        BookGraph = GraphClass
        self.graph = BookGraph(self.llm, save_callback=self._save_checkpoint).build()
        self.workflow = BookWorkflow()
        self._active_topics = set()
        self._lock = Lock()

    def generate_book(self, topic: str, resume: bool = False, **kwargs) -> BookState:
        """Execute full book generation process"""
        with self._lock:
            if topic in self._active_topics:
                self.logger.warning(
                    f"Book generation already in progress for '{topic}'. Skipping."
                )
                return None
            self._active_topics.add(topic)

        try:
            # Step 1: Initialize or resume state
            if resume:
                state = self._load_checkpoint() or self._create_initial_state(topic, **kwargs)
            else:
                state = self._create_initial_state(topic, **kwargs)

            step_tracker.dispatch(StepEvent("Scaffolding"))

            # Step 2: Start workflow
            state = self.workflow.start(state)

            # Step 3: Execute graph
            self.logger.info(f"Starting book generation for: {topic}")
            final_state = self.graph.invoke(state)

            # langgraph returns a mapping object, not our dataclass
            if not isinstance(final_state, BookState):
                try:
                    final_state = BookState(**dict(final_state))
                except Exception as e:
                    self.logger.error(
                        f"Failed to convert graph output to BookState: {e}"
                    )
                    raise
            step_tracker.dispatch(StepEvent("Wiring API"))

            # Step 4: Complete workflow
            final_state = self.workflow.complete(final_state)

            # Step 5: Save artifacts
            self._save_artifacts(final_state)
            step_tracker.dispatch(StepEvent("Styling"))
            if self.checkpoint_path.exists():
                self.checkpoint_path.unlink()

            return final_state

        except Exception as e:
            self.logger.error(f"Book generation failed: {e}")
            raise

        finally:
            with self._lock:
                self._active_topics.discard(topic)

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
        system_cfg = self.config.get("system", {})
        output_dir = (
            system_cfg.output_dir
            if hasattr(system_cfg, "output_dir")
            else system_cfg.get("output_dir", "./book_output")
        )
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Ensure compiled_book is available
        if not state.compiled_book:
            try:
                exporter = ExportService(output_dir)
                state.compiled_book = exporter._compile_content(state)
            except Exception as e:
                self.logger.error(f"Failed to compile book content: {e}")
                state.compiled_book = ""

        # Save book content
        with open(output_dir / f"book_{timestamp}.md", "w") as f:
            f.write(state.compiled_book)

        # Save metadata
        with open(output_dir / f"metadata_{timestamp}.json", "w") as f:
            json.dump(state.metadata, f, indent=2)

        # Save metrics summary with timestamp
        with open(output_dir / f"metrics_{timestamp}.json", "w") as f:
            json.dump(self.llm.metrics.get_summary(), f, indent=2)

        # Persist full token metrics for later analysis
        try:
            self.llm.metrics.save_metrics(output_dir / "final_token_metrics.json")
        except Exception as e:
            self.logger.error(f"Failed to save final token metrics: {e}")

    def _save_checkpoint(self, state: BookState) -> None:
        """Persist intermediate state for resuming later."""
        try:
            with open(self.checkpoint_path, "w") as f:
                json.dump(state.model_dump(), f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}")

    def _load_checkpoint(self) -> Optional[BookState]:
        """Load previously saved state if available."""
        try:
            if self.checkpoint_path.exists():
                with open(self.checkpoint_path) as f:
                    data = json.load(f)
                return BookState(**data)
        except Exception as e:
            self.logger.error(f"Failed to load checkpoint: {e}")
        return None

from .types import AgentInput, AgentOutput, TOCEntry, ChapterOutput, Config
from .base import BaseAgent


class FinalCompilationAgent(BaseAgent):
    """Compile processed chapters into the final document."""

    def run(self, input: AgentInput) -> AgentOutput:
        """Assemble chapters and append back matter."""
        chapters = input.inputs or []
        doc = f"# {self.config.book_title}\n\n**Author:** {self.config.author}\n"
        toc: List[TOCEntry] = []
        glossary: Dict[str, str] = {}
        for idx, ch in enumerate(chapters, 1):
            title = ch.metadata.get("title", f"Chapter {idx}")
            toc.append(TOCEntry(chapter=str(idx), title=title))
            doc += f"\n\n<a name='chapter-{idx}'></a>\n# {title}\n\n{ch.content}\n"
            if ch.acronym_glossary:
                glossary.update(ch.acronym_glossary)
        if glossary:
            doc += "\n\n## Acronym Glossary\n"
            for tok, defi in glossary.items():
                doc += f"- **{tok}**: {defi}\n"
        return AgentOutput(final_doc=doc, toc=toc)
