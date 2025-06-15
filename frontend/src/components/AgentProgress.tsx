import React, { useState, useEffect } from 'react';
import { useAgentStatus } from '../hooks/useAgentStatus';
import { useEnhancedWebSocket } from '../hooks/useEnhancedWebSocket';

export interface AgentProgressProps {
  statusUrl?: string;
  websocketUrl?: string;
  showDetailed?: boolean;
}

interface EnhancedAgentStatus {
  agent_name: string;
  agent_type: string;
  current_step: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'paused';
  progress_percent: number;
  iteration_count: number;
  max_iterations: number;
  quality_score: number;
  start_time: string;
  estimated_completion: string;
  domain: string;
  word_count: number;
  tokens_used: number;
  errors: string[];
  warnings: string[];
}

interface WorkflowProgress {
  total_agents: number;
  completed_agents: number;
  current_agent: string;
  next_agent?: string;
  overall_progress: number;
  estimated_time_remaining: string;
  quality_score: number;
  book_title: string;
  chapter_count: number;
  word_count: number;
}

export const AgentProgress: React.FC<AgentProgressProps> = ({ 
  statusUrl = '/events/agent-status', 
  websocketUrl = 'ws://localhost:8765',
  showDetailed = true 
}) => {
  const [enhancedStatus, setEnhancedStatus] = useState<{
    agents: Record<string, EnhancedAgentStatus>;
    workflow_progress: WorkflowProgress | null;
    quality_metrics: any;
  } | null>(null);
  
  const fallbackStatus = useAgentStatus(statusUrl);
  const { messages, isConnected } = useEnhancedWebSocket(websocketUrl);

  useEffect(() => {
    // Process WebSocket messages
    const latestMessage = messages[messages.length - 1];
    if (latestMessage) {
      try {
        const data = JSON.parse(latestMessage.message);
        
        if (data.type === 'complete_status' || data.type === 'workflow_progress') {
          setEnhancedStatus(data.data);
        } else if (data.type === 'agent_status') {
          setEnhancedStatus(prev => ({
            ...prev!,
            agents: {
              ...prev?.agents || {},
              [data.data.agent_name]: data.data
            }
          }));
        }
      } catch (e) {
        console.warn('Failed to parse WebSocket message:', e);
      }
    }
  }, [messages]);

  // Use enhanced status if available, otherwise fallback
  const displayStatus = enhancedStatus?.workflow_progress || fallbackStatus;
  const currentAgentDetails = enhancedStatus?.agents?.[displayStatus?.current_agent || ''];

  if (!displayStatus) {
    return (
      <div className="p-4 space-y-2">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
        <div className="text-sm text-gray-500">
          {isConnected ? 'Loading agent status...' : 'Connecting to real-time updates...'}
        </div>
      </div>
    );
  }

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'completed': return 'bg-green-500';
      case 'failed': return 'bg-red-500';
      case 'running': return 'bg-blue-500';
      case 'paused': return 'bg-yellow-500';
      default: return 'bg-gray-400';
    }
  };

  const getProgressColor = (progress: number) => {
    if (progress >= 90) return 'bg-green-600';
    if (progress >= 70) return 'bg-blue-600';
    if (progress >= 50) return 'bg-yellow-600';
    return 'bg-gray-600';
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-lg space-y-4">
      {/* Header with connection status */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-800">
          {enhancedStatus?.workflow_progress?.book_title || 'Book Generation Progress'}
        </h3>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${
            isConnected ? 'bg-green-500' : 'bg-red-500'
          }`}></div>
          <span className="text-xs text-gray-500">
            {isConnected ? 'Live' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Overall Progress */}
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium text-gray-700">
            Overall Progress ({enhancedStatus?.workflow_progress?.completed_agents || 0}/
            {enhancedStatus?.workflow_progress?.total_agents || 1})
          </span>
          <span className="text-sm text-gray-500">
            {Math.round(('progress_percent' in displayStatus ? displayStatus.progress_percent : displayStatus.overall_progress) || 0)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 h-3 rounded-full">
          <div
            className={`h-3 rounded-full transition-all duration-300 ${
              getProgressColor(('progress_percent' in displayStatus ? displayStatus.progress_percent : displayStatus.overall_progress) || 0)
            }`}
            style={{ 
              width: `${Math.min(('progress_percent' in displayStatus ? displayStatus.progress_percent : displayStatus.overall_progress) || 0, 100)}%` 
            }}
          ></div>
        </div>
      </div>

      {/* Current Agent Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <div className="text-sm font-medium text-gray-700">Current Agent</div>
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${
              getStatusColor(currentAgentDetails?.status)
            }`}></div>
            <span className="font-semibold text-gray-800">
              {displayStatus.current_agent}
            </span>
          </div>
          {currentAgentDetails && (
            <div className="text-xs text-gray-500">
              {currentAgentDetails.current_step}
              {currentAgentDetails.iteration_count > 0 && (
                <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 rounded">
                  Iteration {currentAgentDetails.iteration_count}/{currentAgentDetails.max_iterations}
                </span>
              )}
            </div>
          )}
        </div>

        <div className="space-y-2">
          <div className="text-sm font-medium text-gray-700">Next Agent</div>
          <div className="text-gray-600">
            {displayStatus.next_agent || 'Finalizing...'}
          </div>
          {enhancedStatus?.workflow_progress?.estimated_time_remaining && (
            <div className="text-xs text-gray-500">
              ETA: {enhancedStatus.workflow_progress.estimated_time_remaining}
            </div>
          )}
        </div>
      </div>

      {/* Enhanced Details */}
      {showDetailed && enhancedStatus && (
        <div className="border-t pt-4 space-y-3">
          {/* Quality Score */}
          {(enhancedStatus.workflow_progress?.quality_score || 0) > 0 && (
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">Quality Score</span>
              <div className="flex items-center space-x-2">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  (enhancedStatus.workflow_progress?.quality_score || 0) >= 0.9 
                    ? 'bg-green-100 text-green-800'
                    : (enhancedStatus.workflow_progress?.quality_score || 0) >= 0.7
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {((enhancedStatus.workflow_progress?.quality_score || 0) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          )}

          {/* Book Statistics */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Chapters:</span>
              <span className="ml-2 font-medium">
                {enhancedStatus.workflow_progress?.chapter_count || 0}
              </span>
            </div>
            <div>
              <span className="text-gray-500">Words:</span>
              <span className="ml-2 font-medium">
                {(enhancedStatus.workflow_progress?.word_count || 0).toLocaleString()}
              </span>
            </div>
          </div>

          {/* Current Agent Details */}
          {currentAgentDetails && (
            <div className="bg-gray-50 p-3 rounded">
              <div className="text-xs font-medium text-gray-700 mb-2">
                {currentAgentDetails.agent_name} Details
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-gray-500">Domain:</span>
                  <span className="ml-1">{currentAgentDetails.domain}</span>
                </div>
                <div>
                  <span className="text-gray-500">Tokens:</span>
                  <span className="ml-1">{currentAgentDetails.tokens_used.toLocaleString()}</span>
                </div>
              </div>
              
              {/* Errors and Warnings */}
              {(currentAgentDetails.errors.length > 0 || currentAgentDetails.warnings.length > 0) && (
                <div className="mt-2 space-y-1">
                  {currentAgentDetails.errors.map((error, idx) => (
                    <div key={idx} className="text-xs text-red-600 bg-red-50 p-1 rounded">
                      ⚠️ {error}
                    </div>
                  ))}
                  {currentAgentDetails.warnings.map((warning, idx) => (
                    <div key={idx} className="text-xs text-yellow-600 bg-yellow-50 p-1 rounded">
                      ⚡ {warning}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AgentProgress;
