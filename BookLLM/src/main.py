from src.core import BookOrchestrator
from pathlib import Path
import argparse

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
    Path("book_output").mkdir(exist_ok=True)
    
    # Initialize orchestrator
    orchestrator = BookOrchestrator(args.config)
    
    try:
        # Changed from write_book to generate_book
        orchestrator.generate_book(
            topic=args.topic,
            target_audience=args.audience,
            style=args.style,
            pages=args.pages,
            language=args.lang
        )

        print("\n✅ Book generation completed!")
        print(f"📚 Files saved in: {orchestrator.config['system'].output_dir}")
        
    except Exception as e:
        print(f"❌ Error generating book: {e}")
        exit(1)

if __name__ == "__main__":
    main()