/**
 * API Client for BookLLM Backend
 * Communicates with the Flask API running on port 8000
 */

export interface Agent {
  name: string;
  type: string;
  description?: string;
}

export interface AgentStatus {
  agent: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress?: number;
  message?: string;
  timestamp?: string;
}

export interface GenerationRequest {
  topic: string;
  target_audience?: string;
  style?: string;
  pages?: number;
  language?: string;
}

export interface DispatchRequest {
  agent: string;
  prompt: string;
}

export interface DispatchResponse {
  response: string;
}

export interface TokenMetrics {
  total_tokens: number;
  total_cost: number;
  agents: Record<string, {
    tokens: number;
    cost: number;
    calls: number;
  }>;
}

export interface HealthStatus {
  status: string;
  timestamp?: string;
}

class BookLLMAPI {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request to ${url} failed:`, error);
      throw error;
    }
  }

  // Health check
  async getHealth(): Promise<HealthStatus> {
    return this.request<HealthStatus>('/health');
  }

  // Agent management
  async getAgents(): Promise<string[]> {
    return this.request<string[]>('/api/agents');
  }

  async getAgentStartTimes(): Promise<Record<string, string>> {
    return this.request<Record<string, string>>('/api/agent-starts');
  }

  // Book generation
  async generateBook(request: GenerationRequest): Promise<{ message: string }> {
    return this.request<{ message: string }>('/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Agent dispatch
  async dispatchAgent(request: DispatchRequest): Promise<DispatchResponse> {
    return this.request<DispatchResponse>('/api/dispatch', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Metrics
  async getMetrics(): Promise<TokenMetrics> {
    return this.request<TokenMetrics>('/api/metrics');
  }

  // Server-Sent Events for real-time status
  createEventSource(endpoint: string = '/events/agent-status'): EventSource {
    const url = `${this.baseUrl}${endpoint}`;
    return new EventSource(url);
  }
}

export const apiClient = new BookLLMAPI();
export default BookLLMAPI;