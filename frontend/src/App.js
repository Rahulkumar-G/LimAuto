import React, { useState, useEffect } from 'react';
import { BookGenerationForm } from './components/BookGenerationForm';
import { AgentProgress } from './components/AgentProgress';
import { AgentManager } from './components/AgentManager';
import { MetricsDashboard } from './components/MetricsDashboard';
import { ExportManager } from './components/ExportManager';
import { LogViewer } from './components/LogViewer';
import { useRealTimeStatus } from './hooks/useRealTimeStatus';
import { apiClient } from './api/client';
import './index.css';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isGenerating, setIsGenerating] = useState(false);
  const [systemHealth, setSystemHealth] = useState(null);
  const [error, setError] = useState(null);
  
  const { agentStatuses, isConnected, error: realtimeError } = useRealTimeStatus();

  useEffect(() => {
    // Check system health on app load
    checkSystemHealth();
  }, []);

  const checkSystemHealth = async () => {
    try {
      const health = await apiClient.getHealth();
      setSystemHealth(health);
    } catch (error) {
      console.error('System health check failed:', error);
      setError('Unable to connect to BookLLM API');
    }
  };

  const handleGenerationStart = (request) => {
    setIsGenerating(true);
    setActiveTab('dashboard'); // Switch to dashboard to show progress
  };

  const handleGenerationComplete = () => {
    setIsGenerating(false);
  };

  const handleGenerationError = (errorMessage) => {
    setError(errorMessage);
    setIsGenerating(false);
  };

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'generate', label: 'Generate Book', icon: '📚' },
    { id: 'agents', label: 'Agent Manager', icon: '🤖' },
    { id: 'metrics', label: 'Metrics', icon: '📈' },
    { id: 'export', label: 'Export & Download', icon: '📥' },
    { id: 'logs', label: 'System Logs', icon: '📋' }
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">BookLLM</h1>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  systemHealth?.status === 'ok' ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                <span className="text-sm text-gray-600">
                  {systemHealth?.status === 'ok' ? 'System Online' : 'System Offline'}
                </span>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Live Updates' : 'Disconnected'}
                </span>
              </div>
              
              {isGenerating && (
                <div className="flex items-center space-x-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full">
                  <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600"></div>
                  <span className="text-sm font-medium">Generating...</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Error Alert */}
      {(error || realtimeError) && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mx-4 mt-4 rounded">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">
                {error || realtimeError}
              </p>
              <button
                onClick={() => {
                  setError(null);
                  checkSystemHealth();
                }}
                className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
              >
                Retry Connection
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Navigation Tabs */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <AgentProgress showDetailed={true} />
            
            {Object.keys(agentStatuses).length > 0 && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-800 mb-4">Live Agent Status</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(agentStatuses).map(([agentName, status]) => (
                    <div key={agentName} className="border rounded-lg p-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-gray-700">{agentName}</span>
                        <span className={`text-xs px-2 py-1 rounded ${
                          status.status === 'completed' ? 'bg-green-100 text-green-800' :
                          status.status === 'running' ? 'bg-blue-100 text-blue-800' :
                          status.status === 'failed' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {status.status}
                        </span>
                      </div>
                      {status.progress !== undefined && (
                        <div className="mt-2">
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full transition-all"
                              style={{ width: `${status.progress}%` }}
                            ></div>
                          </div>
                          <div className="text-xs text-gray-500 mt-1">{status.progress}%</div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'generate' && (
          <BookGenerationForm
            onGenerationStart={handleGenerationStart}
            onGenerationComplete={handleGenerationComplete}
            onError={handleGenerationError}
          />
        )}

        {activeTab === 'agents' && (
          <AgentManager />
        )}

        {activeTab === 'metrics' && (
          <MetricsDashboard />
        )}

        {activeTab === 'export' && (
          <ExportManager />
        )}

        {activeTab === 'logs' && (
          <div className="bg-white rounded-lg shadow">
            <LogViewer />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <div className="text-center text-sm text-gray-500">
            BookLLM - AI-Powered Book Generation Platform
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;