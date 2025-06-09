import { useEffect, useState } from 'react';

export interface AgentStatus {
  current_agent: string;
  next_agent: string;
  progress_percent: number;
}

export function useAgentStatus(url: string): AgentStatus | null {
  const [status, setStatus] = useState<AgentStatus | null>(null);

  useEffect(() => {
    if (!url) return;
    const es = new EventSource(url);
    es.onmessage = (e: MessageEvent) => {
      try {
        const data = JSON.parse(e.data) as AgentStatus;
        setStatus(data);
        window.dispatchEvent(
          new CustomEvent('agentStatusUpdate', { detail: data })
        );
      } catch {
        // ignore parse errors
      }
    };
    return () => {
      es.close();
    };
  }, [url]);

  return status;
}
