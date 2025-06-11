import useSWR from 'swr';
import React from 'react';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export default function AgentStatusPanel() {
  const { data, error } = useSWR<Record<string, string>>(
    '/api/agent-starts',
    fetcher,
    { refreshInterval: 5000 }
  );

  if (error) return <div className="text-red-500">Failed to load agents.</div>;
  if (!data) return <div>Loading...</div>;

  return (
    <div className="p-4 space-y-4">
      {Object.entries(data).map(([name, ts]) => (
        <div key={name} className="border p-2 rounded-md">
          <div className="flex items-center justify-between">
            <div className="font-semibold text-lg">{name}</div>
            <div className="text-sm text-gray-500">
              Started: {new Date(ts).toLocaleTimeString()}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
