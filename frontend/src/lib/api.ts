import type { Application, ApplicationDetail, Recommendation, DashboardStats } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

interface ApiResponse<T> {
  status: 'success' | 'error';
  message?: string;
  data?: T;
  [key: string]: any;
}

// Re-export types for convenience
export type { Application, ApplicationDetail, Recommendation, DashboardStats } from './types';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      console.log(`[API] Requesting: ${url}`);
      const response = await fetch(url, config);

      // Handle non-JSON responses
      let data;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        console.error(`[API] Non-JSON response from ${url}:`, {
          status: response.status,
          statusText: response.statusText,
          contentType,
          preview: text.substring(0, 200)
        });
        throw new Error(
          `Expected JSON but got HTML (status ${response.status}). ` +
          `Make sure the backend is running at ${this.baseUrl} and the endpoint exists. ` +
          `Response preview: ${text.substring(0, 100)}`
        );
      }

      if (!response.ok) {
        throw new Error(data.message || data.error || `HTTP error! status: ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error(`[API] Request failed: ${url}`, error);
      // Return error response instead of throwing to prevent app crash
      return {
        status: 'error',
        message: error instanceof Error ? error.message : 'Unknown error',
        error: error
      } as T;
    }
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<any>> {
    return this.request('/health/');
  }

  // Ingestion endpoints
  async ingestTrace(traceData: {
    application_id: string;
    prompt: string;
    response: string;
    model_name: string;
    input_token_count?: number;
    output_token_count?: number;
    total_token_count?: number;
    input_cost?: number;
    output_cost?: number;
    total_cost?: number;
    latency_sec?: number;
    latency_ms?: number;
    category?: string;
    tool_used?: boolean;
    status?: string;
    external_id?: string;
    traced_at?: string;
  }): Promise<ApiResponse<any>> {
    return this.request('/ingest/', {
      method: 'POST',
      body: JSON.stringify(traceData),
    });
  }

  async ingestTracesBulk(traces: any[]): Promise<ApiResponse<any>> {
    return this.request('/ingest/bulk/', {
      method: 'POST',
      body: JSON.stringify({ traces }),
    });
  }

  // Applications endpoints
  async getApplications(): Promise<ApiResponse<{
    applications: Application[];
    count: number;
  }>> {
    return this.request('/applications/');
  }

  async getApplicationDetail(applicationId: string): Promise<ApiResponse<ApplicationDetail>> {
    return this.request(`/applications/${applicationId}/`);
  }

  // Recommendations endpoints
  async getRecommendations(applicationId?: string): Promise<ApiResponse<{
    recommendations: Recommendation[];
    count: number;
  }>> {
    const endpoint = applicationId
      ? `/recommendations/?application_id=${applicationId}`
      : '/recommendations/';
    return this.request(endpoint);
  }

  async generateRecommendations(params: {
    task_type: string;
    priorities: {
      low_cost?: number;
      low_latency?: number;
      high_quality?: number;
    };
  }): Promise<ApiResponse<{
    recommendations: Array<{
      name: string;
      provider: string;
      score: number;
      cost: string;
      speed: string;
      features: string[];
      bestFor: string;
      model_id?: number;
    }>;
    count: number;
  }>> {
    return this.request('/recommendations/', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  // Dashboard endpoints
  async getDashboardStats(): Promise<ApiResponse<DashboardStats>> {
    return this.request('/dashboard/stats/');
  }

  // Generate recommendations for a specific application
  async generateRecommendationsForApp(applicationId: string): Promise<ApiResponse<{
    recommendations: Recommendation[];
    count: number;
    analyses_created: number;
  }>> {
    return this.request('/recommendations/generate/', {
      method: 'POST',
      body: JSON.stringify({ application_id: applicationId }),
    });
  }
}

// Export singleton instance
export const apiClient = new ApiClient(API_BASE_URL);
export default apiClient;
