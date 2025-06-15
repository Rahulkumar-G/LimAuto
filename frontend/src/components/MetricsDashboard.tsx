import React, { useState, useEffect } from 'react';
import { apiClient, TokenMetrics, HealthStatus } from '../api/client';

interface MetricsDashboardProps {
  className?: string;
}

export const MetricsDashboard: React.FC<MetricsDashboardProps> = ({ className = '' }) => {
  const [metrics, setMetrics] = useState<TokenMetrics | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [metricsData, healthData] = await Promise.all([
        apiClient.getMetrics().catch(() => null),
        apiClient.getHealth().catch(() => null)
      ]);

      setMetrics(metricsData);
      setHealth(healthData);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setError('Failed to load metrics data');
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 4
    }).format(amount);
  };

  const formatNumber = (num: number): string => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  const getTopAgents = (agents: Record<string, any>, sortBy: 'tokens' | 'cost' | 'calls') => {
    return Object.entries(agents)
      .sort(([, a], [, b]) => b[sortBy] - a[sortBy])
      .slice(0, 5);
  };

  if (isLoading && !metrics) {
    return (
      <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-gray-50 p-4 rounded">
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-3/4"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">System Metrics</h2>
        <div className="flex items-center space-x-4">
          {lastUpdate && (
            <span className="text-xs text-gray-500">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
          <button
            onClick={loadData}
            disabled={isLoading}
            className="text-sm text-blue-600 hover:text-blue-800 flex items-center space-x-1"
          >
            <svg className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Health Status */}
      <div className="mb-6">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            health?.status === 'ok' ? 'bg-green-500' : 'bg-red-500'
          }`}></div>
          <span className="text-sm font-medium text-gray-700">
            System Status: {health?.status === 'ok' ? 'Healthy' : 'Error'}
          </span>
        </div>
      </div>

      {/* Overview Cards */}
      {metrics && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-sm font-medium text-blue-800 mb-1">Total Tokens</div>
              <div className="text-2xl font-bold text-blue-900">
                {formatNumber(metrics.total_tokens)}
              </div>
            </div>
            
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="text-sm font-medium text-green-800 mb-1">Total Cost</div>
              <div className="text-2xl font-bold text-green-900">
                {formatCurrency(metrics.total_cost)}
              </div>
            </div>
            
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-sm font-medium text-purple-800 mb-1">Active Agents</div>
              <div className="text-2xl font-bold text-purple-900">
                {Object.keys(metrics.agents).length}
              </div>
            </div>
          </div>

          {/* Agent Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Top by Tokens */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Top Agents by Tokens</h3>
              <div className="space-y-2">
                {getTopAgents(metrics.agents, 'tokens').map(([agentName, agentData], index) => (
                  <div key={agentName} className="flex justify-between items-center py-2 border-b border-gray-200 last:border-b-0">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        #{index + 1}
                      </span>
                      <span className="text-sm font-medium text-gray-700 truncate">
                        {agentName.replace('Agent', '')}
                      </span>
                    </div>
                    <span className="text-sm text-gray-600">
                      {formatNumber(agentData.tokens)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Top by Cost */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Top Agents by Cost</h3>
              <div className="space-y-2">
                {getTopAgents(metrics.agents, 'cost').map(([agentName, agentData], index) => (
                  <div key={agentName} className="flex justify-between items-center py-2 border-b border-gray-200 last:border-b-0">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                        #{index + 1}
                      </span>
                      <span className="text-sm font-medium text-gray-700 truncate">
                        {agentName.replace('Agent', '')}
                      </span>
                    </div>
                    <span className="text-sm text-gray-600">
                      {formatCurrency(agentData.cost)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Top by API Calls */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">Top Agents by API Calls</h3>
              <div className="space-y-2">
                {getTopAgents(metrics.agents, 'calls').map(([agentName, agentData], index) => (
                  <div key={agentName} className="flex justify-between items-center py-2 border-b border-gray-200 last:border-b-0">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">
                        #{index + 1}
                      </span>
                      <span className="text-sm font-medium text-gray-700 truncate">
                        {agentName.replace('Agent', '')}
                      </span>
                    </div>
                    <span className="text-sm text-gray-600">
                      {formatNumber(agentData.calls)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Detailed Agent Table */}
          <div className="mt-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">All Agent Metrics</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border border-gray-200 rounded-lg">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left font-medium text-gray-700">Agent</th>
                    <th className="px-4 py-2 text-right font-medium text-gray-700">Tokens</th>
                    <th className="px-4 py-2 text-right font-medium text-gray-700">Cost</th>
                    <th className="px-4 py-2 text-right font-medium text-gray-700">API Calls</th>
                    <th className="px-4 py-2 text-right font-medium text-gray-700">Avg Cost/Call</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(metrics.agents)
                    .sort(([, a], [, b]) => b.cost - a.cost)
                    .map(([agentName, agentData]) => (
                    <tr key={agentName} className="border-t border-gray-200 hover:bg-gray-50">
                      <td className="px-4 py-2 font-medium text-gray-800">
                        {agentName.replace('Agent', '')}
                      </td>
                      <td className="px-4 py-2 text-right text-gray-600">
                        {formatNumber(agentData.tokens)}
                      </td>
                      <td className="px-4 py-2 text-right text-gray-600">
                        {formatCurrency(agentData.cost)}
                      </td>
                      <td className="px-4 py-2 text-right text-gray-600">
                        {formatNumber(agentData.calls)}
                      </td>
                      <td className="px-4 py-2 text-right text-gray-600">
                        {agentData.calls > 0 ? formatCurrency(agentData.cost / agentData.calls) : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {!metrics && !isLoading && (
        <div className="text-center py-8">
          <div className="text-gray-500 mb-2">No metrics data available</div>
          <div className="text-sm text-gray-400">
            Metrics will appear here after book generation activities
          </div>
        </div>
      )}
    </div>
  );
};

export default MetricsDashboard;