import { useEffect, useState } from 'react';
import { apiClient } from '../api/client';

export interface AgentStatus {
  current_agent: string;
  next_agent: string;
  progress_percent: number;
  total_agents?: number;
  completed_agents?: number;
  overall_progress?: number;
}

export function useAgentStatus(url: string = '/events/agent-status'): AgentStatus | null {
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!url) return;
    
    let eventSource: EventSource;
    
    try {
      eventSource = apiClient.createEventSource(url);
      
      eventSource.onopen = () => {
        setIsConnected(true);
        console.log('Connected to agent status stream');
      };
      
      eventSource.onmessage = (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data) as AgentStatus;
          setStatus(data);
          window.dispatchEvent(
            new CustomEvent('agentStatusUpdate', { detail: data })
          );
        } catch (error) {
          console.warn('Failed to parse agent status:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('Agent status stream error:', error);
        setIsConnected(false);
      };

    } catch (error) {
      console.error('Failed to create EventSource:', error);
      setIsConnected(false);
    }

    return () => {
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [url]);

  return status;
}
