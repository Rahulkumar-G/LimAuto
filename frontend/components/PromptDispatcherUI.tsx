import React, { useEffect, useState } from 'react';

interface DispatchResponse {
  response?: string;
  error?: string;
}

export default function PromptDispatcherUI() {
  const [agents, setAgents] = useState<string[]>([]);
  const [selectedAgent, setSelectedAgent] = useState('');
  const [prompt, setPrompt] = useState('');
  const [output, setOutput] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch('/api/agents')
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((list: string[]) => {
        setAgents(list);
        if (list.length > 0) {
          setSelectedAgent(list[0]);
        }
      })
      .catch(() => setError('Failed to load agents.'));
  }, []);

  const sendPrompt = () => {
    setError('');
    setOutput('');
    if (!prompt.trim()) {
      setError('Prompt cannot be empty.');
      return;
    }
    setLoading(true);
    fetch('/api/dispatch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent: selectedAgent, prompt }),
    })
      .then((r) => (r.ok ? r.json() : r.json().then((j) => Promise.reject(j))))
      .then((json: DispatchResponse) => {
        if (json.error) {
          setError(json.error);
        } else if (json.response) {
          setOutput(json.response);
        }
      })
      .catch((e) => {
        setError(e.error || 'Failed to dispatch prompt.');
      })
      .finally(() => setLoading(false));
  };

  return (
    <div className="p-4 space-y-2">
      <div className="flex gap-2 items-center">
        <select
          className="border p-2 rounded"
          value={selectedAgent}
          onChange={(e) => setSelectedAgent(e.target.value)}
        >
          {agents.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
        <button
          onClick={sendPrompt}
          className="px-4 py-2 bg-blue-600 text-white rounded"
          disabled={loading}
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>
      <textarea
        className="w-full border rounded p-2 h-32"
        placeholder="Enter prompt..."
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      />
      {error && <div className="text-red-500">{error}</div>}
      {output && (
        <pre className="border rounded p-2 h-64 overflow-auto whitespace-pre-wrap">
          {output}
        </pre>
      )}
    </div>
  );
}
