import { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface MetricPoint {
  timestamp: string;
  p99_latency_ms: number;
  tokens_per_minute: number;
}

const mockData: MetricPoint[] = [
  { timestamp: '00:00', p99_latency_ms: 950, tokens_per_minute: 210 },
  { timestamp: '00:01', p99_latency_ms: 1020, tokens_per_minute: 180 },
  { timestamp: '00:02', p99_latency_ms: 980, tokens_per_minute: 195 },
];

export default function MetricsChartSection() {
  const [data, setData] = useState<MetricPoint[]>(mockData);

  useEffect(() => {
    fetch('/api/metrics')
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((json) => {
        if (Array.isArray(json)) {
          setData(json as MetricPoint[]);
        }
      })
      .catch(() => {
        // keep mock data on failure
      });
  }, []);

  return (
    <section>
      <h2>Metrics</h2>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        <div>
          <h3>P99 Latency (ms)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="p99_latency_ms" stroke="#8884d8" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div>
          <h3>Tokens per Minute</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="tokens_per_minute" stroke="#82ca9d" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}
