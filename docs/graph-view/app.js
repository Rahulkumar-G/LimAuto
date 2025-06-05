import React, { useState, useEffect, useCallback } from 'https://esm.sh/react?dev';
import ReactDOM from 'https://esm.sh/react-dom/client?dev';
import ReactFlow, { MiniMap, Controls, Background } from 'https://esm.sh/reactflow?dev';
import graph from './pipeline.json' assert { type: 'json' };

function App() {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [activeNode, setActiveNode] = useState(null);

  // CURRENT STEP → load mock graph data on mount
  useEffect(() => {
    setNodes(graph.nodes);
    setEdges(graph.edges);
  }, []);

  // CURRENT STEP → handle node click and open drawer
  const onNodeClick = useCallback((_, node) => {
    // CURRENT STEP → future hook placeholder for runtime stats
    // fetch(`/api/stats?node=${node.id}`).then(r => r.json()).then(data => setActiveNode({ ...node, stats: data }));
    setActiveNode({ ...node, stats: { duration: 'N/A', tokens: 0 } });
  }, []);

  const closeDrawer = () => setActiveNode(null);

  return (
    <>
      <ReactFlow nodes={nodes} edges={edges} onNodeClick={onNodeClick} fitView>
        <MiniMap />
        <Controls />
        <Background />
      </ReactFlow>
      <div className={`drawer ${activeNode ? 'open' : ''}`}>
        {activeNode && (
          <>
            <h3>{activeNode.data.label}</h3>
            {/* CURRENT STEP → display runtime statistics */}
            <pre>{JSON.stringify(activeNode.stats, null, 2)}</pre>
            <button onClick={closeDrawer}>Close</button>
          </>
        )}
      </div>
    </>
  );
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
