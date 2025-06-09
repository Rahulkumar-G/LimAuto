import React from 'react';
import { useAgentStatus } from '../src/hooks/useAgentStatus';

export interface AgentProgressProps {
  statusUrl: string;
}

export const AgentProgress: React.FC<AgentProgressProps> = ({ statusUrl }) => {
  const status = useAgentStatus(statusUrl);

  if (!status) {
    return <div>Loading agent status...</div>;
  }

  return (
    <div className="p-4 space-y-2">
      <div className="text-sm font-semibold">Current: {status.current_agent}</div>
      <div className="w-full bg-gray-200 h-4 rounded">
        <div
          className="bg-blue-600 h-4 rounded"
          style={{ width: `${status.progress_percent}%` }}
        ></div>
      </div>
      <div className="text-sm text-gray-500">Up Next: {status.next_agent}</div>
    </div>
  );
};

export default AgentProgress;
