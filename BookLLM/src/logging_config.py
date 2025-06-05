import logging
import logging.handlers
import sys
from pathlib import Path
import yaml


def setup_logging(config_path: str = "config.yaml") -> logging.Logger:
    """Configure root logger with console and rotating file handlers."""
    level = logging.DEBUG
    cfg_path = Path(config_path)
    if cfg_path.is_file():
        try:
            with open(cfg_path, "r") as f:
                cfg = yaml.safe_load(f) or {}
            level_name = str(cfg.get("system", {}).get("log_level", "DEBUG")).upper()
            level = getattr(logging, level_name, logging.DEBUG)
        except Exception:
            pass

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.handlers.clear()

    console_fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_fmt)

    file_fmt = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "langgraph.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_fmt)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger

