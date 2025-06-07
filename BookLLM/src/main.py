from .core import BookOrchestrator
from .logging_config import setup_logging
from .services.export import ExportService
from pathlib import Path
import argparse
import asyncio
import logging
import yaml
import shutil

from .core import BookOrchestrator


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="AI Book Writing System")
    parser.add_argument("topic", help="Book topic")
    parser.add_argument("--config", help="Path to config YAML")
    parser.add_argument("--audience", default="beginners", help="Target audience")
    parser.add_argument("--style", default="professional", help="Writing style")
    parser.add_argument("--pages", type=int, default=100, help="Target page count")
    parser.add_argument("--lang", default="en", help="Book language")
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Export the generated book to PDF (requires pandoc and xelatex)",
    )

    args = parser.parse_args()

    setup_logging(args.config or str(Path(__file__).resolve().parents[1] / "config.yaml"))
    logger = logging.getLogger(__name__)

    if args.pdf and shutil.which("xelatex") is None:
        logger.error("xelatex is required for PDF export but was not found. Please install a TeX distribution that provides xelatex or omit the --pdf option.")
        return

    # Create output directory
    output_dir = Path("book_output")
    output_dir.mkdir(exist_ok=True)

    # Load config if provided, otherwise use default config
    default_config = {
        "model": {"name": "gpt-4", "temperature": 0.7, "max_tokens": 2000},
        "system": {"output_dir": str(output_dir)},
    }

    if args.config:
        with open(args.config, "r") as f:
            user_config = yaml.safe_load(f)
            # Merge user config with default config
            default_config.update(user_config)

    # Initialize orchestrator with merged config
    orchestrator = BookOrchestrator(default_config)

    try:
        state = orchestrator.generate_book(
            topic=args.topic,
            target_audience=args.audience,
            style=args.style,
            pages=args.pages,
            language=args.lang,
        )

        if args.pdf:
            exporter = ExportService(output_dir)
            pdf_path = asyncio.run(exporter.export_pdf(state))
            logger.info(f"📄 PDF exported to: {pdf_path}")

        logger.info("\n✅ Book generation completed!")
        logger.info(f"📚 Files saved in: {output_dir}")
        
    except Exception as e:
        logger.exception("❌ Error generating book")
        exit(1)


if __name__ == "__main__":
    main()
