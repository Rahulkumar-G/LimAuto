import React, { useMemo, useState } from 'react';
import { FixedSizeList as List } from 'react-window';
import { LogEntry, useWebSocket } from '../hooks/useWebSocket';

export interface LogViewerProps {
  url: string;
}

const LEVELS: LogEntry['level'][] = ['INFO', 'WARN', 'ERROR'];

export const LogViewer: React.FC<LogViewerProps> = ({ url }) => {
  const logs = useWebSocket(url);
  const [search, setSearch] = useState('');
  const [activeLevels, setActiveLevels] = useState<Record<string, boolean>>({
    INFO: true,
    WARN: true,
    ERROR: true,
  });

  const filtered = useMemo(() => {
    return logs.filter(
      (l) =>
        activeLevels[l.level] &&
        l.message.toLowerCase().includes(search.toLowerCase())
    );
  }, [logs, search, activeLevels]);

  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style} className="whitespace-pre-wrap font-mono text-sm px-2">
      {filtered[index].message}
    </div>
  );

  return (
    <div className="p-4 space-y-2">
      <input
        className="w-full border rounded p-2"
        placeholder="Search logs..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />
      <div className="flex gap-2">
        {LEVELS.map((level) => (
          <button
            key={level}
            onClick={() =>
              setActiveLevels((prev) => ({ ...prev, [level]: !prev[level] }))
            }
            className={`px-3 py-1 rounded-full border text-sm ${
              activeLevels[level] ? 'bg-blue-600 text-white' : 'bg-gray-200'
            }`}
          >
            {level}
          </button>
        ))}
      </div>
      <div className="h-96 border rounded">
        <List height={384} itemCount={filtered.length} itemSize={24} width="100%">
          {Row}
        </List>
      </div>
    </div>
  );
};

export default LogViewer;
