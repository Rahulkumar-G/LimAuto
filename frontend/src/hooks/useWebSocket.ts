import { useEffect, useRef, useState } from 'react';

export interface LogEntry {
  step: number;
  message: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'UNKNOWN';
}

export function useWebSocket(url: string): LogEntry[] {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const stepRef = useRef(1);

  useEffect(() => {
    if (!url) return;
    const ws = new WebSocket(url);
    ws.onmessage = (event: MessageEvent) => {
      const raw = String(event.data);
      const match = raw.match(/(INFO|WARN|ERROR)/);
      const level = (match ? match[1] : 'UNKNOWN') as LogEntry['level'];
      const step = stepRef.current++;
      const entry: LogEntry = {
        step,
        message: `STEP ${step}: ${raw}`,
        level,
      };
      setLogs(prev => [...prev, entry]);
    };
    return () => {
      ws.close();
    };
  }, [url]);

  return logs;
}
