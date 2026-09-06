import type {
  AIAssistantPayload,
  ContractDetail,
  ContractSummary,
  InvoiceRecord,
  NavigationNode,
  PageRegistryItem,
  ReferenceData,
  UserProfile,
} from '../types';

interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  errorCode: string | null;
}

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers ?? {}),
    },
    ...options,
  });
  const payload = (await response.json()) as ApiResponse<T>;
  if (!response.ok || !payload.success) {
    throw new Error(payload.message || '请求失败');
  }
  return payload.data;
}

export async function login(username: string, password: string) {
  return request<UserProfile>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export async function logout() {
  return request<Record<string, never>>('/api/auth/logout', { method: 'POST' });
}

export async function getCurrentUser() {
  return request<UserProfile>('/api/auth/me');
}

export async function getNavigation() {
  return request<NavigationNode[]>('/api/meta/navigation');
}

export async function getPages() {
  return request<PageRegistryItem[]>('/api/meta/pages');
}

export async function getReferenceData() {
  return request<ReferenceData>('/api/meta/reference-data');
}

export async function queryContracts(filters: Record<string, unknown>) {
  return request<ContractSummary[]>('/api/queries/Contract_Query/execute', {
    method: 'POST',
    body: JSON.stringify(filters),
  });
}

export async function getContractDetail(contractId: number) {
  return request<ContractDetail>(`/api/queries/Contract_GetDetail/execute?contractId=${contractId}`);
}

export async function createContract(payload: Record<string, unknown>) {
  return request<ContractDetail>('/api/behaviors/Contract_Create/execute', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function createInvoice(payload: Record<string, unknown>) {
  return request<InvoiceRecord>('/api/behaviors/Invoice_Create/execute', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function queryOpenInvoices(filters: Record<string, unknown>) {
  return request<InvoiceRecord[]>('/api/support/open-invoices', {
    method: 'POST',
    body: JSON.stringify(filters),
  });
}

export async function receivePayment(payload: { invoiceId: number; receivedDate?: string }) {
  return request<InvoiceRecord>('/api/behaviors/Payment_Receive/execute', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function streamChat(
  sessionId: string | null,
  message: string,
  handlers: {
    onEvent: (eventName: string, data: Record<string, unknown>) => void;
    onError: (error: Error) => void;
  },
) {
  const response = await fetch(`${API_BASE}/api/ai/chat/stream`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sessionId, message }),
  });

  if (!response.ok || !response.body) {
    handlers.onError(new Error('AI 流式请求失败'));
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  let sawAssistant = false;

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        break;
      }
      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split('\n\n');
      buffer = chunks.pop() ?? '';

      for (const chunk of chunks) {
        const lines = chunk.split('\n');
        const eventLine = lines.find((line) => line.startsWith('event:'));
        const dataLine = lines.find((line) => line.startsWith('data:'));
        if (!eventLine || !dataLine) {
          continue;
        }

        const eventName = eventLine.replace('event:', '').trim();
        const data = JSON.parse(dataLine.replace('data:', '').trim()) as Record<string, unknown>;

        if (eventName === 'assistant') {
          sawAssistant = true;
        }
        if (eventName === 'error') {
          handlers.onError(new Error(String(data.message ?? 'AI 对话处理失败')));
          return;
        }

        handlers.onEvent(eventName, data);
      }
    }

    if (!sawAssistant) {
      handlers.onError(new Error('AI 未返回有效结果'));
    }
  } catch (error) {
    handlers.onError(error instanceof Error ? error : new Error('AI 流式响应解析失败'));
  } finally {
    reader.releaseLock();
  }
}

export async function chatOnce(message: string) {
  return request<AIAssistantPayload>('/api/ai/chat', {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}
