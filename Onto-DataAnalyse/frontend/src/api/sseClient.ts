/**
 * SSE 客户端封装（基于 fetch ReadableStream）
 * 用于消费后端 SSE 流式接口（POST + text/event-stream）
 *
 * 使用方式：
 *   await sseRequest('/api/phase2/generate', { body: {...} }, {
 *     onMessage: (msg) => { ... },
 *     onError: (err) => { ... },
 *     onDone: () => { ... }
 *   });
 */

export interface SseMessage {
  type: string;
  [key: string]: unknown;
}

export interface SseHandlers {
  onMessage?: (msg: SseMessage) => void;
  onError?: (err: Error) => void;
  onDone?: () => void;
}

export interface SseRequestOptions {
  method?: 'POST' | 'GET';
  body?: unknown;
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

export async function sseRequest(
  url: string,
  options: SseRequestOptions,
  handlers: SseHandlers,
): Promise<void> {
  const { method = 'POST', body, headers = {}, signal } = options;
  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
    });
  } catch (err) {
    handlers.onError?.(err as Error);
    return;
  }

  if (!response.ok) {
    let errMsg = `HTTP ${response.status}`;
    try {
      const txt = await response.text();
      errMsg = `${errMsg}: ${txt}`;
    } catch {
      /* ignore */
    }
    handlers.onError?.(new Error(errMsg));
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    handlers.onError?.(new Error('响应无 body 流'));
    return;
  }

  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';
      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith('data:')) continue;
        const payload = trimmed.slice(5).trim();
        if (!payload) continue;
        try {
          const msg = JSON.parse(payload) as SseMessage;
          handlers.onMessage?.(msg);
        } catch (e) {
          // 忽略单条 JSON 解析失败，继续后续消息
          // eslint-disable-next-line no-console
          console.warn('SSE 解析失败:', payload);
        }
      }
    }
    handlers.onDone?.();
  } catch (err) {
    if ((err as DOMException).name === 'AbortError') return;
    handlers.onError?.(err as Error);
  }
}
