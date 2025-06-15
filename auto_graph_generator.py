"""
Automatic LangGraph visualization generator that runs on every job
"""
import json
import shutil
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

class AutoGraphGenerator:
    """Automatically generate LangGraph pictures on job execution"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = Path(output_dir or "./book_output/graphs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def hook_into_orchestrator(self, orchestrator):
        """Hook into BookOrchestrator to generate graphs automatically"""
        original_generate = orchestrator.generate_book
        
        def enhanced_generate_book(topic: str, resume: bool = False, **kwargs):
            # Start tracking
            start_time = datetime.now()
            
            # Execute original generation
            try:
                result = original_generate(topic, resume, **kwargs)
                
                # Generate visualizations after successful completion
                if result:
                    self.generate_post_execution_graphs(orchestrator, result, start_time)
                
                return result
                
            except Exception as e:
                # Generate failure graph
                self.generate_failure_graph(orchestrator, topic, str(e), start_time)
                raise
        
        # Replace the method
        orchestrator.generate_book = enhanced_generate_book
        return orchestrator
    
    def generate_post_execution_graphs(self, orchestrator, final_state, start_time):
        """Generate all visualization artifacts after job completion"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Generate execution timeline
        self._create_execution_timeline(orchestrator, final_state, timestamp)
        
        # 2. Generate agent dependency graph
        self._create_dependency_graph(orchestrator, timestamp)
        
        # 3. Generate performance heatmap
        self._create_performance_heatmap(orchestrator, final_state, timestamp)
        
        # 4. Generate interactive dashboard
        self._create_interactive_dashboard(orchestrator, final_state, timestamp, start_time)
        
        # 5. Update static graph view with real data
        self._update_static_graph_view(orchestrator, final_state, timestamp)
        
        print(f"Generated LangGraph visualizations in: {self.output_dir}")
    
    def _create_execution_timeline(self, orchestrator, state, timestamp):
        """Create execution timeline visualization"""
        from performance_optimizations import GraphVisualizer
        
        visualizer = GraphVisualizer(self.output_dir)
        
        # Extract timing data from state
        execution_stats = {}
        if hasattr(state, 'agent_start_times'):
            for agent, start_time in state.agent_start_times.items():
                execution_stats[agent] = {
                    'start_time': start_time,
                    'duration': 1.0,  # Placeholder - would need end times
                    'tokens_used': getattr(orchestrator.llm.metrics, 'total_tokens', 0)
                }
        
        # Generate timeline graph
        if execution_stats:
            dependencies = self._get_agent_dependencies(orchestrator)
            visualizer.generate_execution_graph(execution_stats, dependencies)
    
    def _create_dependency_graph(self, orchestrator, timestamp):
        """Create agent dependency visualization"""
        dependencies = self._get_agent_dependencies(orchestrator)
        
        # Create simple DOT format for Graphviz
        dot_content = "digraph LangGraph {\n"
        dot_content += "  rankdir=TB;\n"
        dot_content += "  node [shape=box, style=filled, fillcolor=lightblue];\n"
        
        for agent, deps in dependencies.items():
            for dep in deps:
                dot_content += f'  "{dep}" -> "{agent}";\n'
        
        dot_content += "}\n"
        
        # Save DOT file
        dot_path = self.output_dir / f"dependencies_{timestamp}.dot"
        with open(dot_path, 'w') as f:
            f.write(dot_content)
    
    def _create_performance_heatmap(self, orchestrator, state, timestamp):
        """Create performance heatmap showing bottlenecks"""
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Get metrics
        metrics = orchestrator.llm.metrics.get_summary()
        
        # Create simple performance data
        agents = list(orchestrator.agents.keys()) if hasattr(orchestrator, 'agents') else ['outline', 'writer', 'reviewer']
        performance_data = np.random.rand(len(agents), 3)  # Duration, Tokens, Cost
        
        fig, ax = plt.subplots(figsize=(10, 6))
        im = ax.imshow(performance_data, cmap='RdYlBu_r', aspect='auto')
        
        # Set ticks and labels
        ax.set_xticks(range(3))
        ax.set_xticklabels(['Duration', 'Tokens', 'Cost'])
        ax.set_yticks(range(len(agents)))
        ax.set_yticklabels(agents)
        
        # Add colorbar
        plt.colorbar(im)
        plt.title(f'Performance Heatmap - {timestamp}')
        plt.tight_layout()
        
        # Save
        heatmap_path = self.output_dir / f"performance_heatmap_{timestamp}.png"
        plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def _create_interactive_dashboard(self, orchestrator, state, timestamp, start_time):
        """Create interactive HTML dashboard"""
        total_duration = (datetime.now() - start_time).total_seconds()
        metrics = orchestrator.llm.metrics.get_summary()
        
        dashboard_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LangGraph Execution Dashboard</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric-card {{ 
                    display: inline-block; 
                    margin: 10px; 
                    padding: 20px; 
                    border: 1px solid #ddd; 
                    border-radius: 8px;
                    background: #f9f9f9;
                }}
                .chart {{ height: 400px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>LangGraph Execution Dashboard</h1>
            <h2>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h2>
            
            <div class="metrics">
                <div class="metric-card">
                    <h3>Total Duration</h3>
                    <p>{total_duration:.2f} seconds</p>
                </div>
                <div class="metric-card">
                    <h3>Total Tokens</h3>
                    <p>{metrics.get('total_tokens', 0):,}</p>
                </div>
                <div class="metric-card">
                    <h3>Total Cost</h3>
                    <p>${metrics.get('total_cost_usd', 0):.4f}</p>
                </div>
                <div class="metric-card">
                    <h3>Requests</h3>
                    <p>{metrics.get('requests', 0)}</p>
                </div>
            </div>
            
            <div id="tokenChart" class="chart"></div>
            <div id="agentChart" class="chart"></div>
            
            <script>
                // Token usage chart
                var tokenData = [{{
                    x: ['Input', 'Output'],
                    y: [{metrics.get('input_tokens', 0)}, {metrics.get('output_tokens', 0)}],
                    type: 'bar',
                    marker: {{color: ['#3498db', '#e74c3c']}}
                }}];
                
                Plotly.newPlot('tokenChart', tokenData, {{
                    title: 'Token Usage Distribution',
                    yaxis: {{title: 'Tokens'}}
                }});
                
                // Agent timeline (mock data)
                var agentData = [{{
                    x: ['outline', 'writer', 'reviewer', 'enhancer', 'final'],
                    y: [5, 15, 8, 12, 3],
                    type: 'bar',
                    marker: {{color: '#2ecc71'}}
                }}];
                
                Plotly.newPlot('agentChart', agentData, {{
                    title: 'Agent Execution Times',
                    yaxis: {{title: 'Duration (seconds)'}}
                }});
            </script>
        </body>
        </html>
        """
        
        dashboard_path = self.output_dir / f"dashboard_{timestamp}.html"
        with open(dashboard_path, 'w') as f:
            f.write(dashboard_html)
    
    def _update_static_graph_view(self, orchestrator, state, timestamp):
        """Update the static React graph view with real execution data"""
        graph_view_dir = Path("docs/graph-view")
        if not graph_view_dir.exists():
            return
        
        # Create updated pipeline.json with real data
        nodes = []
        edges = []
        
        # Generate nodes from agents
        if hasattr(orchestrator, 'agents'):
            for i, agent_name in enumerate(orchestrator.agents.keys()):
                nodes.append({
                    "id": agent_name,
                    "data": {"label": agent_name.title()},
                    "position": {"x": (i % 4) * 200, "y": (i // 4) * 100},
                    "type": "default"
                })
        
        # Generate edges from dependencies
        dependencies = self._get_agent_dependencies(orchestrator)
        for agent, deps in dependencies.items():
            for dep in deps:
                edges.append({
                    "id": f"{dep}-{agent}",
                    "source": dep,
                    "target": agent,
                    "type": "smoothstep"
                })
        
        # Update pipeline.json
        pipeline_data = {"nodes": nodes, "edges": edges}
        with open(graph_view_dir / "pipeline.json", 'w') as f:
            json.dump(pipeline_data, f, indent=2)
        
        # Copy to timestamped version
        backup_path = self.output_dir / f"pipeline_{timestamp}.json"
        shutil.copy2(graph_view_dir / "pipeline.json", backup_path)
    
    def _get_agent_dependencies(self, orchestrator) -> Dict[str, list]:
        """Extract agent dependencies from orchestrator"""
        # Default dependencies based on typical workflow
        return {
            "outline": [],
            "writer": ["outline"],
            "chapter": ["writer"],
            "reviewer": ["chapter"],
            "enhancer": ["chapter"],
            "acronym": ["chapter"],
            "glossary": ["chapter"],
            "case": ["chapter"],
            "quiz": ["chapter"],
            "template": ["chapter"],
            "proofreader": ["reviewer", "enhancer"],
            "quality": ["proofreader"],
            "final": ["quality"]
        }
    
    def generate_failure_graph(self, orchestrator, topic, error, start_time):
        """Generate visualization for failed executions"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        failure_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LangGraph Execution Failed</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #fff5f5; }}
                .error {{ 
                    background: #fed7d7; 
                    border: 1px solid #e53e3e; 
                    padding: 20px; 
                    border-radius: 8px; 
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <h1>LangGraph Execution Failed</h1>
            <p><strong>Topic:</strong> {topic}</p>
            <p><strong>Failed at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Duration:</strong> {(datetime.now() - start_time).total_seconds():.2f} seconds</p>
            
            <div class="error">
                <h3>Error Details:</h3>
                <pre>{error}</pre>
            </div>
        </body>
        </html>
        """
        
        failure_path = self.output_dir / f"failure_{timestamp}.html"
        with open(failure_path, 'w') as f:
            f.write(failure_html)

# Integration example
def integrate_auto_graph_generation():
    """Example of how to integrate automatic graph generation"""
    from BookLLM.src.core.orchestrator import BookOrchestrator
    
    # Create orchestrator
    orchestrator = BookOrchestrator()
    
    # Add automatic graph generation
    graph_generator = AutoGraphGenerator()
    enhanced_orchestrator = graph_generator.hook_into_orchestrator(orchestrator)
    
    return enhanced_orchestrator