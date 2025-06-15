"""
Example integration showing how to use the performance optimizations
"""
from pathlib import Path
from BookLLM.src.core.orchestrator import BookOrchestrator
from auto_graph_generator import AutoGraphGenerator

def create_optimized_orchestrator(config_path=None):
    """Create an optimized orchestrator with automatic graph generation"""
    
    # Create base orchestrator  
    orchestrator = BookOrchestrator(config_path)
    
    # Add automatic graph generation
    graph_generator = AutoGraphGenerator(Path("./book_output/graphs"))
    enhanced_orchestrator = graph_generator.hook_into_orchestrator(orchestrator)
    
    return enhanced_orchestrator

def run_optimized_book_generation():
    """Example of running optimized book generation"""
    
    # Create optimized orchestrator
    orchestrator = create_optimized_orchestrator()
    
    # Generate book with automatic visualization
    topic = "Introduction to Machine Learning"
    result = orchestrator.generate_book(
        topic=topic,
        audience="beginners", 
        style="educational",
        pages=50
    )
    
    print(f"Book generation completed!")
    print(f"- Generated book: {len(result.compiled_book)} characters")
    print(f"- Total tokens used: {orchestrator.llm.metrics.total_tokens}")
    print(f"- Visualizations saved to: ./book_output/graphs/")
    
    return result

if __name__ == "__main__":
    run_optimized_book_generation()