import useSWR from 'swr';
import React from 'react';

const fetcher = (url: string) => fetch(url).then(res => res.json());

interface Agent {
  name: string;
  lastHeartbeat: string;
  health: 'green' | 'yellow' | 'red';
  currentStep?: string;
}

const healthColorMap: Record<Agent['health'], string> = {
  green: 'bg-green-500',
  yellow: 'bg-yellow-500',
  red: 'bg-red-500',
};

export default function AgentStatusPanel() {
  const { data, error } = useSWR<Agent[]>('/api/agents', fetcher, {
    refreshInterval: 5000,
  });

  if (error) return <div className="text-red-500">Failed to load agents.</div>;
  if (!data) return <div>Loading...</div>;

  return (
    <div className="p-4 space-y-4">
      {data.map((agent) => (
        <div key={agent.name} className="border p-2 rounded-md">
          {agent.currentStep && (
            <div className="text-sm font-bold mb-1">Current coding step: {agent.currentStep}</div>
          )}
          <div className="flex items-center justify-between">
            <div className="font-semibold text-lg flex items-center">
              <span className={`inline-block w-3 h-3 rounded-full mr-2 ${healthColorMap[agent.health]}`}/>
              {agent.name}
            </div>
            <div className="text-sm text-gray-500">Last heartbeat: {agent.lastHeartbeat}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
