"""
Performance optimizations for BookLLM pipeline
"""
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Any
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime

class OptimizedBookGraph:
    """Enhanced BookGraph with performance optimizations"""
    
    def __init__(self, llm, save_callback=None, max_workers=4):
        self.llm = llm
        self.save_callback = save_callback
        self.max_workers = max_workers
        self.execution_stats = {}
        
    def analyze_dependencies(self, agents: Dict[str, Any]) -> Dict[str, List[str]]:
        """Analyze agent dependencies to enable parallel execution"""
        dependencies = {
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
        return dependencies
    
    def get_parallel_batches(self, dependencies: Dict[str, List[str]]) -> List[List[str]]:
        """Group agents into parallel execution batches"""
        completed = set()
        batches = []
        
        while len(completed) < len(dependencies):
            current_batch = []
            for agent, deps in dependencies.items():
                if agent not in completed and all(dep in completed for dep in deps):
                    current_batch.append(agent)
            
            if not current_batch:
                break
                
            batches.append(current_batch)
            completed.update(current_batch)
            
        return batches
    
    async def execute_parallel_batch(self, batch: List[str], state, agents: Dict[str, Any]):
        """Execute a batch of agents in parallel"""
        async def run_agent(agent_name: str):
            start_time = datetime.now()
            agent = agents[agent_name]
            
            # Skip if already completed
            if agent_name in state.completed_steps:
                return state
                
            # Run agent
            result_state = agent.process(state)
            
            # Track execution stats
            duration = (datetime.now() - start_time).total_seconds()
            self.execution_stats[agent_name] = {
                'duration': duration,
                'start_time': start_time.isoformat(),
                'tokens_used': getattr(self.llm.metrics, 'total_tokens', 0)
            }
            
            return result_state
        
        # Execute batch in parallel
        tasks = [run_agent(agent_name) for agent_name in batch]
        results = await asyncio.gather(*tasks)
        
        # Merge results (simple approach - last result wins)
        return results[-1] if results else state

class GraphVisualizer:
    """Generate LangGraph interaction pictures automatically"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_execution_graph(self, execution_stats: Dict[str, Any], 
                                dependencies: Dict[str, List[str]]) -> str:
        """Generate visual representation of the execution graph"""
        # Create directed graph
        G = nx.DiGraph()
        
        # Add nodes with execution info
        for agent, stats in execution_stats.items():
            G.add_node(agent, 
                      duration=stats.get('duration', 0),
                      tokens=stats.get('tokens_used', 0))
        
        # Add edges based on dependencies
        for agent, deps in dependencies.items():
            for dep in deps:
                if dep in G.nodes:
                    G.add_edge(dep, agent)
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G, k=2, iterations=50)
        
        # Draw nodes with size based on duration
        durations = [execution_stats.get(node, {}).get('duration', 1) for node in G.nodes()]
        node_sizes = [max(500, d * 100) for d in durations]
        
        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, 
                              node_color='lightblue', alpha=0.7)
        nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True)
        nx.draw_networkx_labels(G, pos, font_size=8)
        
        # Add duration labels
        duration_labels = {node: f"{stats.get('duration', 0):.2f}s" 
                          for node, stats in execution_stats.items()}
        nx.draw_networkx_labels(G, pos, duration_labels, font_size=6, 
                               font_color='red', verticalalignment='bottom')
        
        plt.title(f"LangGraph Execution - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        plt.axis('off')
        
        # Save image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = self.output_dir / f"langgraph_execution_{timestamp}.png"
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(image_path)
    
    def generate_interactive_html(self, execution_stats: Dict[str, Any],
                                 dependencies: Dict[str, List[str]]) -> str:
        """Generate interactive HTML visualization"""
        nodes = []
        edges = []
        
        # Create nodes
        for i, (agent, stats) in enumerate(execution_stats.items()):
            nodes.append({
                'id': agent,
                'label': f"{agent}\n{stats.get('duration', 0):.2f}s",
                'color': {'background': '#e1f5fe', 'border': '#0288d1'},
                'shape': 'box',
                'font': {'size': 12}
            })
        
        # Create edges
        for agent, deps in dependencies.items():
            for dep in deps:
                edges.append({
                    'from': dep,
                    'to': agent,
                    'arrows': 'to'
                })
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LangGraph Execution Visualization</title>
            <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
            <style>
                #network {{ width: 100%; height: 600px; border: 1px solid lightgray; }}
                .stats {{ margin: 20px; padding: 10px; background: #f5f5f5; }}
            </style>
        </head>
        <body>
            <h1>LangGraph Execution - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h1>
            <div class="stats">
                <h3>Execution Statistics</h3>
                <pre>{json.dumps(execution_stats, indent=2)}</pre>
            </div>
            <div id="network"></div>
            <script>
                var nodes = new vis.DataSet({json.dumps(nodes)});
                var edges = new vis.DataSet({json.dumps(edges)});
                var container = document.getElementById('network');
                var data = {{ nodes: nodes, edges: edges }};
                var options = {{
                    layout: {{ hierarchical: {{ direction: 'UD', sortMethod: 'directed' }} }},
                    physics: false
                }};
                var network = new vis.Network(container, data, options);
            </script>
        </body>
        </html>
        """
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = self.output_dir / f"langgraph_interactive_{timestamp}.html"
        with open(html_path, 'w') as f:
            f.write(html_content)
            
        return str(html_path)

class CacheManager:
    """Intelligent caching for agent results"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
    def get_cache_key(self, agent_name: str, state_hash: str) -> str:
        """Generate cache key for agent result"""
        return f"{agent_name}_{state_hash}"
    
    def get_state_hash(self, state) -> str:
        """Generate hash of relevant state for caching"""
        # Simple hash based on topic and relevant state fields
        import hashlib
        cache_data = {
            'topic': getattr(state, 'topic', ''),
            'outline': getattr(state, 'outline', []),
            'chapters': getattr(state, 'chapters', [])
        }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
    
    def get_cached_result(self, agent_name: str, state) -> Any:
        """Get cached result if available"""
        cache_key = self.get_cache_key(agent_name, self.get_state_hash(state))
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return None
    
    def cache_result(self, agent_name: str, state, result: Any):
        """Cache agent result"""
        cache_key = self.get_cache_key(agent_name, self.get_state_hash(state))
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
        except Exception as e:
            print(f"Failed to cache result for {agent_name}: {e}")