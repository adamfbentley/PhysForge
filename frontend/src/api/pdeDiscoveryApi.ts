// Mirroring backend/pde_discovery_service/schemas.py -> PdeDiscoveryResultResponse
export interface PdeDiscoveryResultResponse {
  id: number;
  job_id: number;
  owner_id: number;
  discovery_algorithm: string;
  target_variable: string;
  candidate_features_path: string;
  discovered_equation?: string;
  canonical_equation?: string;
  equation_metrics?: Record<string, any>;
  uncertainty_metrics?: Record<string, any>;
  sensitivity_analysis_results_path?: string;
  model_ranking_score?: number;
  results_path?: string;
  logs_path?: string;
  created_at: string;
  updated_at?: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function fetchPdeDiscoveryResults(ownerId: number, token: string): Promise<PdeDiscoveryResultResponse[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/pde-discovery/results?owner_id=${ownerId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch PDE discovery results');
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching PDE discovery results:', error);
    throw error;
  }
}
