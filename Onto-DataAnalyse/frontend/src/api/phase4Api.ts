import { apiClient } from './client';
import type { ApiResponse } from '../types/api';

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  message_type: 'text' | 'report';
  report_data?: any;
  reasoning_data?: any;
  created_at: string;
}

export interface SessionInfo {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  msg_count: number;
}

export interface IntentResult {
  scenario_id: string | null;
  confidence: number;
  matched_keywords: string[];
  reasoning: string;
  source?: string;
  alternatives?: any[];
}

export const phase4Api = {
  async getSessions(): Promise<{ default_session_id: string; sessions: SessionInfo[] }> {
    const { data } = await apiClient.get<ApiResponse<any>>('/phase4/sessions');
    return data.data ?? { default_session_id: '', sessions: [] };
  },

  async getMessages(sessionId: string): Promise<ChatMessage[]> {
    const { data } = await apiClient.get<ApiResponse<ChatMessage[]>>(`/phase4/messages/${sessionId}`);
    return data.data ?? [];
  },

  async detectIntent(message: string): Promise<IntentResult> {
    const { data } = await apiClient.post<ApiResponse<IntentResult>>('/phase4/intent', { message });
    if (!data.data) throw new Error(data.message);
    return data.data;
  },
};
