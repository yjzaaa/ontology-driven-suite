import { apiClient } from './client';
import type { ApiResponse } from '../types/api';
import type { ScenarioSummary } from '../types/scenario';

export const phase3Api = {
  async listScenarios(): Promise<ScenarioSummary[]> {
    const { data } = await apiClient.get<ApiResponse<ScenarioSummary[]>>('/phase3/scenarios');
    return data.data ?? [];
  },

  async confirm(): Promise<void> {
    const { data } = await apiClient.post<ApiResponse>('/phase3/confirm');
    if (!data.success) throw new Error(data.message);
  },
};
