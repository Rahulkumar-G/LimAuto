from typing import Dict, Any, Optional
from pathlib import Path
import yaml
from datetime import datetime
import json

from ..models.state import BookState
from ..models.config import ModelConfig, SystemConfig
from .graph import BookGraph
from .workflow import BookWorkflow
from ..interfaces.llm import EnhancedLLMInterface
from ..utils.logger import get_logger

class BookOrchestrator:
    """Main orchestrator for book generation process"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.llm = EnhancedLLMInterface(self.config)
        self.logger = get_logger(__name__)
        self.graph = BookGraph(self.llm).build()
        self.workflow = BookWorkflow()
        
    def generate_book(self, topic: str, **kwargs) -> BookState:
        """Execute full book generation process"""
        try:
            # Initialize state
            initial_state = self._create_initial_state(topic, **kwargs)
            
            # Start workflow
            state = self.workflow.start(initial_state)
            
            # Execute graph
            self.logger.info(f"Starting book generation for: {topic}")
            final_state = self.graph.invoke(state)
            
            # Complete workflow
            final_state = self.workflow.complete(final_state)
            
            # Save artifacts
            self._save_artifacts(final_state)
            
            return final_state
            
        except Exception as e:
            self.logger.error(f"Book generation failed: {e}")
            raise
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            'model': ModelConfig(),
            'system': SystemConfig()
        }
        
        if config_path:
            try:
                with open(config_path) as f:
                    user_config = yaml.safe_load(f)
                default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"Failed to load config: {e}")
        
        return default_config
    
    def _create_initial_state(self, topic: str, **kwargs) -> BookState:
        """Create initial book state"""
        return BookState(
            topic=topic,
            target_audience=kwargs.get('audience', 'beginners'),
            book_style=kwargs.get('style', 'professional'),
            estimated_pages=kwargs.get('pages', 100),
            language=kwargs.get('language', 'en'),
        )
    
    def _save_artifacts(self, state: BookState):
        """Save generation artifacts"""
        output_dir = Path(self.config['system'].output_dir)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save book content
        with open(output_dir / f"book_{timestamp}.md", 'w') as f:
            f.write(state.compiled_book)
        
        # Save metadata
        with open(output_dir / f"metadata_{timestamp}.json", 'w') as f:
            json.dump(state.metadata, f, indent=2)
        
        # Save metrics
        with open(output_dir / f"metrics_{timestamp}.json", 'w') as f:
            json.dump(self.llm.metrics.get_summary(), f, indent=2)