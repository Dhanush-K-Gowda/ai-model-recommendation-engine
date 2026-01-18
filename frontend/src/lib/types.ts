// Type definitions for API responses
export type Application = {
  id: number;
  application_id: string;
  name: string;
  model: string;
  category: string;
  usage: string;
  cost: string;
  total_requests: number;
  total_cost: number;
  total_tokens: number;
  categories: string[];
  is_active: boolean;
};

export type Recommendation = {
  id: number;
  application_id?: string;
  application_name?: string;
  current_model: string;
  recommended_model: string;
  provider: string;
  recommendation_type: string;
  confidence_score: number;
  cost_savings_percent: number;
  monthly_savings: number;
  reasoning: string;
  test_status: string;
  quality_overall_score: number | null;
  features?: string[];
};

export type ApplicationDetail = {
  id: number;
  application_id: string;
  name: string;
  categories: string[];
  assigned_model: string | null;
  is_active: boolean;
  stats: {
    total_requests: number;
    successful_requests: number;
    total_cost: number;
    avg_cost: number;
    total_tokens: number;
    avg_latency_sec: number;
  };
  usage_analysis: {
    model_name: string;
    total_requests: number;
    avg_cost_per_request: number;
    max_total_tokens: number;
    avg_latency_sec: number | null;
  } | null;
  recommendations: Recommendation[];
};

export type DashboardStats = {
  total_applications: number;
  total_requests: number;
  total_cost: number;
  total_tokens: number;
  active_recommendations: number;
  apps_with_recommendations: number;
};
