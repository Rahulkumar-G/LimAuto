import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

def get_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """Create a logger with both file and console handlers"""
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if log_file is specified
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def setup_project_logging(
    log_dir: Path = Path("logs"),
    level: int = logging.INFO
) -> None:
    """Setup project-wide logging configuration"""
    
    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"bookllm_{timestamp}.log"
    
    # Configure root logger
    root_logger = get_logger(
        name="bookllm",
        log_file=log_file,
        level=level
    )
    
    # Set as root logger
    logging.root = root_logger