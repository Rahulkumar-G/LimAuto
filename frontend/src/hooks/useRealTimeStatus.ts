import { useState, useEffect, useRef, useCallback } from 'react';
import { apiClient, AgentStatus } from '../api/client';

interface UseRealTimeStatusReturn {
  agentStatuses: Record<string, AgentStatus>;
  isConnected: boolean;
  error: string | null;
  lastUpdate: Date | null;
  reconnect: () => void;
}

export const useRealTimeStatus = (): UseRealTimeStatusReturn => {
  const [agentStatuses, setAgentStatuses] = useState<Record<string, AgentStatus>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  
  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    try {
      // Close existing connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      const eventSource = apiClient.createEventSource();
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        setIsConnected(true);
        setError(null);
        console.log('Connected to real-time status updates');
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          setAgentStatuses(prev => ({
            ...prev,
            [data.agent]: {
              agent: data.agent,
              status: data.status,
              progress: data.progress,
              message: data.message,
              timestamp: data.timestamp || new Date().toISOString()
            }
          }));
          
          setLastUpdate(new Date());
        } catch (parseError) {
          console.error('Failed to parse status update:', parseError);
        }
      };

      eventSource.onerror = (event) => {
        console.error('EventSource error:', event);
        setIsConnected(false);
        setError('Connection lost. Attempting to reconnect...');
        
        // Auto-reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 5000);
      };

    } catch (connectionError) {
      console.error('Failed to establish EventSource connection:', connectionError);
      setError('Failed to connect to real-time updates');
      setIsConnected(false);
    }
  }, []);

  const reconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    connect();
  }, [connect]);

  useEffect(() => {
    connect();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

  return {
    agentStatuses,
    isConnected,
    error,
    lastUpdate,
    reconnect
  };
};