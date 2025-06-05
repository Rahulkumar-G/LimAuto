import argparse
from pathlib import Path

import yaml

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

    args = parser.parse_args()

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
        orchestrator.generate_book(
            topic=args.topic,
            target_audience=args.audience,
            style=args.style,
            pages=args.pages,
            language=args.lang,
        )

        print("\n✅ Book generation completed!")
        print(f"📚 Files saved in: {output_dir}")

    except Exception as e:
        print(f"❌ Error generating book: {e}")
        exit(1)


if __name__ == "__main__":
    main()
