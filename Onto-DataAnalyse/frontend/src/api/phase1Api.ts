import { apiClient } from './client';
import type { ApiResponse } from '../types/api';
import type { ParsedRequirement } from '../types/requirement';

export interface DemoFileInfo {
  name: string;
  size: number;
  download_url: string;
}

export interface Phase1State {
  has_db_schema: boolean;
  has_requirement: boolean;
  db_schema_preview: string;
  requirement_preview: string;
  parsed_requirement: ParsedRequirement | null;
  current_stage: number;
}

export const phase1Api = {
  async listDemoFiles(): Promise<DemoFileInfo[]> {
    const { data } = await apiClient.get<ApiResponse<DemoFileInfo[]>>('/system/demo-files');
    return data.data ?? [];
  },

  async downloadDemoFile(name: string): Promise<string> {
    const res = await fetch(`/api/system/demo-files/${name}`);
    if (!res.ok) throw new Error(`下载失败：${res.status}`);
    return res.text();
  },

  async upload(dbSchemaDoc: string, requirementDoc: string): Promise<void> {
    const { data } = await apiClient.post<ApiResponse>('/phase1/upload', {
      db_schema_doc: dbSchemaDoc,
      requirement_doc: requirementDoc,
    });
    if (!data.success) throw new Error(data.message);
  },

  async getState(): Promise<Phase1State> {
    const { data } = await apiClient.get<ApiResponse<Phase1State>>('/phase1/state');
    if (!data.data) throw new Error(data.message || '无法获取阶段一状态');
    return data.data;
  },

  async confirm(): Promise<void> {
    const { data } = await apiClient.post<ApiResponse>('/phase1/confirm');
    if (!data.success) throw new Error(data.message);
  },
};
