import React, { useEffect, useState } from 'react';

interface TokenSummary {
  total_tokens: number;
  input_tokens: number;
  output_tokens: number;
  total_cost_usd: number;
  avg_tokens_per_request: number;
}

export const MetricsPage: React.FC = () => {
  const [summary, setSummary] = useState<TokenSummary | null>(null);

  useEffect(() => {
    fetch('/api/metrics')
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((json: TokenSummary) => setSummary(json))
      .catch(() => {
        setSummary(null);
      });
  }, []);

  if (!summary) {
    return <div>Loading metrics...</div>;
  }

  return (
    <div className="p-4 space-y-2">
      <h2 className="text-xl font-bold">Token Usage Summary</h2>
      <ul className="list-disc pl-5 space-y-1">
        <li>Total tokens: {summary.total_tokens}</li>
        <li>Input tokens: {summary.input_tokens}</li>
        <li>Output tokens: {summary.output_tokens}</li>
        <li>Total cost (USD): ${summary.total_cost_usd.toFixed(4)}</li>
        <li>Average tokens per request: {summary.avg_tokens_per_request}</li>
      </ul>
    </div>
  );
};

export default MetricsPage;
