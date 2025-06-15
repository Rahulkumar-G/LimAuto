import React, { useState, useEffect } from 'react';
import { apiClient, DispatchRequest } from '../api/client';

interface AgentManagerProps {
  className?: string;
}

export const AgentManager: React.FC<AgentManagerProps> = ({ className = '' }) => {
  const [agents, setAgents] = useState<string[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>('');
  const [prompt, setPrompt] = useState<string>('');
  const [response, setResponse] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [agentStartTimes, setAgentStartTimes] = useState<Record<string, string>>({});

  useEffect(() => {
    loadAgents();
    loadAgentStartTimes();
  }, []);

  const loadAgents = async () => {
    try {
      const agentList = await apiClient.getAgents();
      setAgents(agentList);
      if (agentList.length > 0 && !selectedAgent) {
        setSelectedAgent(agentList[0]);
      }
    } catch (error) {
      console.error('Failed to load agents:', error);
      setError('Failed to load available agents');
    }
  };

  const loadAgentStartTimes = async () => {
    try {
      const startTimes = await apiClient.getAgentStartTimes();
      setAgentStartTimes(startTimes);
    } catch (error) {
      console.error('Failed to load agent start times:', error);
    }
  };

  const handleDispatch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedAgent || !prompt.trim()) {
      setError('Please select an agent and enter a prompt');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResponse('');

    try {
      const request: DispatchRequest = {
        agent: selectedAgent,
        prompt: prompt.trim()
      };

      const result = await apiClient.dispatchAgent(request);
      setResponse(result.response);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to dispatch agent';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const getAgentCategory = (agentName: string): string => {
    if (agentName.includes('Title') || agentName.includes('Dedication') || agentName.includes('Foreword')) {
      return 'Front Matter';
    }
    if (agentName.includes('Chapter') || agentName.includes('Writer') || agentName.includes('Outline')) {
      return 'Content';
    }
    if (agentName.includes('Bibliography') || agentName.includes('Index') || agentName.includes('About')) {
      return 'Back Matter';
    }
    if (agentName.includes('Proofreader') || agentName.includes('Validator') || agentName.includes('Readability')) {
      return 'Review';
    }
    if (agentName.includes('Glossary') || agentName.includes('Code') || agentName.includes('Case')) {
      return 'Enhancement';
    }
    return 'Other';
  };

  const groupedAgents = agents.reduce((groups, agent) => {
    const category = getAgentCategory(agent);
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(agent);
    return groups;
  }, {} as Record<string, string[]>);

  return (
    <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Agent Manager</h2>
        <button
          onClick={loadAgents}
          className="text-sm text-blue-600 hover:text-blue-800 flex items-center space-x-1"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>Refresh</span>
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Selection */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Agent ({agents.length} available)
            </label>
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              disabled={isLoading}
            >
              <option value="">Choose an agent...</option>
              {Object.entries(groupedAgents).map(([category, categoryAgents]) => (
                <optgroup key={category} label={category}>
                  {categoryAgents.map((agent) => (
                    <option key={agent} value={agent}>
                      {agent}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>

          {/* Agent Info */}
          {selectedAgent && (
            <div className="bg-gray-50 p-3 rounded-lg">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Agent Information</h4>
              <div className="text-xs text-gray-600 space-y-1">
                <div><span className="font-medium">Name:</span> {selectedAgent}</div>
                <div><span className="font-medium">Category:</span> {getAgentCategory(selectedAgent)}</div>
                {agentStartTimes[selectedAgent] && (
                  <div><span className="font-medium">Last Started:</span> {new Date(agentStartTimes[selectedAgent]).toLocaleString()}</div>
                )}
              </div>
            </div>
          )}

          {/* Prompt Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Prompt
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your prompt for the selected agent..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              rows={4}
              disabled={isLoading}
            />
          </div>

          {/* Submit Button */}
          <button
            onClick={handleDispatch}
            disabled={isLoading || !selectedAgent || !prompt.trim()}
            className={`w-full py-2 px-4 rounded-lg font-medium transition-all ${
              isLoading || !selectedAgent || !prompt.trim()
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
            } text-white`}
          >
            {isLoading ? (
              <div className="flex items-center justify-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Processing...</span>
              </div>
            ) : (
              'Dispatch Agent'
            )}
          </button>
        </div>

        {/* Response Display */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Agent Response
            </label>
            <div className="bg-gray-50 border border-gray-300 rounded-lg p-3 min-h-[200px]">
              {response ? (
                <div className="text-sm text-gray-800 whitespace-pre-wrap font-mono">
                  {response}
                </div>
              ) : (
                <div className="text-sm text-gray-500 italic">
                  Agent response will appear here...
                </div>
              )}
            </div>
          </div>

          {/* Example Prompts */}
          <div className="bg-blue-50 p-3 rounded-lg">
            <h4 className="text-sm font-medium text-blue-800 mb-2">Example Prompts:</h4>
            <div className="text-xs text-blue-700 space-y-1">
              <div><span className="font-medium">BookTitleAgent:</span> "Generate a compelling title for a book about machine learning"</div>
              <div><span className="font-medium">ChapterWriterAgent:</span> "Write an introduction chapter about artificial intelligence"</div>
              <div><span className="font-medium">OutlineAgent:</span> "Create a detailed outline for a data science textbook"</div>
              <div><span className="font-medium">ProofreaderAgent:</span> "Review this text for grammar and clarity: [your text]"</div>
            </div>
          </div>
        </div>
      </div>

      {/* Agent Categories Summary */}
      <div className="mt-6 border-t pt-4">
        <h3 className="text-lg font-medium text-gray-800 mb-3">Available Agent Categories</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {Object.entries(groupedAgents).map(([category, categoryAgents]) => (
            <div key={category} className="bg-gray-50 p-3 rounded-lg">
              <div className="text-sm font-medium text-gray-700">{category}</div>
              <div className="text-xs text-gray-500">{categoryAgents.length} agents</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AgentManager;