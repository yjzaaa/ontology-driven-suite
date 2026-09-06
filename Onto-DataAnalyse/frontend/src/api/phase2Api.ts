import { apiClient } from './client';
import type { ApiResponse } from '../types/api';
import type { GraphData } from '../types/graph';
import type { MappingVisualization, ModelKey, ModelYamlPayload, Phase2State } from '../types/ontology';

export const phase2Api = {
  async getState(): Promise<Phase2State> {
    const { data } = await apiClient.get<ApiResponse<Phase2State>>('/phase2/state');
    if (!data.data) throw new Error(data.message);
    return data.data;
  },

  async getGraph(): Promise<GraphData> {
    const { data } = await apiClient.get<ApiResponse<GraphData>>('/phase2/graph');
    return data.data ?? { nodes: [], edges: [] };
  },

  async getMapping(): Promise<MappingVisualization> {
    const { data } = await apiClient.get<ApiResponse<MappingVisualization>>('/phase2/mapping');
    return (
      data.data ?? {
        entities: [],
        tables: [],
        links: [],
        stats: { entity_count: 0, table_count: 0, link_count: 0, low_confidence_count: 0 },
      }
    );
  },

  async getYaml(modelKey: ModelKey): Promise<ModelYamlPayload> {
    const { data } = await apiClient.get<ApiResponse<ModelYamlPayload>>(`/phase2/yaml/${modelKey}`);
    if (!data.data) throw new Error(data.message || '获取 YAML 失败');
    return data.data;
  },

  async confirm(): Promise<void> {
    const { data } = await apiClient.post<ApiResponse>('/phase2/confirm');
    if (!data.success) throw new Error(data.message);
  },
};
