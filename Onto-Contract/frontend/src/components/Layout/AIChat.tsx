import React, { useMemo, useRef, useState } from 'react';
import { Bot, CircleDashed, Send, Sparkles, User } from 'lucide-react';
import ReactECharts from 'echarts-for-react';
import { streamChat } from '../../api/client';
import type { AIAssistantPayload, AIRenderChart, AIRenderTable } from '../../types';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  render?: AIAssistantPayload['render'];
  pending?: boolean;
}

interface AIChatProps {
  onOpenPage: (pageId: string) => void;
}

const initialMessages: ChatMessage[] = [
  {
    id: 'welcome',
    role: 'assistant',
    text: '我是合同智能助理。您可以直接让我打开业务页面、查询合同、查看详情，或者生成按部门、客户、产品维度的统计图表。',
  },
];

const AIChat: React.FC<AIChatProps> = ({ onOpenPage }) => {
  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const canSend = useMemo(() => input.trim().length > 0 && !submitting, [input, submitting]);

  const scrollToBottom = () => {
    requestAnimationFrame(() => {
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
    });
  };

  const appendAssistantShell = (id: string) => {
    setMessages((prev) => [...prev, { id, role: 'assistant', text: '', pending: true }]);
    scrollToBottom();
  };

  const updateAssistantMessage = (id: string, updater: (message: ChatMessage) => ChatMessage) => {
    setMessages((prev) => prev.map((message) => (message.id === id ? updater(message) : message)));
    scrollToBottom();
  };

  const handleSend = async () => {
    const message = input.trim();
    if (!message || submitting) {
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      text: message,
    };
    const assistantId = `assistant-${Date.now() + 1}`;

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setSubmitting(true);
    appendAssistantShell(assistantId);

    try {
      await streamChat(sessionId, message, {
        onEvent: (eventName, data) => {
          if (eventName === 'message_start') {
            const incomingSession = typeof data.sessionId === 'string' ? data.sessionId : null;
            if (incomingSession) {
              setSessionId(incomingSession);
            }
            return;
          }

          if (eventName === 'delta') {
            const deltaText = typeof data.text === 'string' ? data.text : '';
            updateAssistantMessage(assistantId, (current) => ({
              ...current,
              text: current.text ? `${current.text}\n${deltaText}` : deltaText,
            }));
            return;
          }

          if (eventName === 'assistant') {
            const payload = data as unknown as AIAssistantPayload;
            updateAssistantMessage(assistantId, (current) => ({
              ...current,
              text: payload.message,
              render: payload.render,
              pending: false,
            }));
            if (payload.action?.type === 'OPEN_PAGE' && payload.action.pageId) {
              onOpenPage(payload.action.pageId);
            }
          }
        },
        onError: (error) => {
          updateAssistantMessage(assistantId, (current) => ({
            ...current,
            text: error.message,
            pending: false,
          }));
        },
      });
    } catch (error) {
      updateAssistantMessage(assistantId, (current) => ({
        ...current,
        text: error instanceof Error ? error.message : 'AI 对话失败',
        pending: false,
      }));
    } finally {
      setSubmitting(false);
      scrollToBottom();
    }
  };

  const renderStructuredContent = (message: ChatMessage) => {
    if (!message.render) {
      return null;
    }

    if (message.render.type === 'table') {
      const table = message.render as AIRenderTable;
      return (
        <div className="chat-table-plain table-wrap compact">
          <table className="data-table">
            <thead>
              <tr>
                {table.headers.map((header) => (
                  <th key={header}>{header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {table.rows.map((row, index) => (
                <tr key={`${message.id}-${index}`}>
                  {row.map((cell, cellIndex) => (
                    <td key={`${message.id}-${index}-${cellIndex}`}>{String(cell)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    const chart = message.render as AIRenderChart;
    return (
      <div className="chat-render-card">
        {chart.title ? (
          <div className="chat-render-title">
            <Sparkles size={14} />
            {chart.title}
          </div>
        ) : null}
        <ReactECharts option={chart.option} style={{ height: 260, width: '100%' }} opts={{ renderer: 'canvas' }} />
        {chart.table ? (
          <div className="table-wrap compact">
            <table className="data-table">
              <thead>
                <tr>
                  {chart.table.headers.map((header) => (
                    <th key={header}>{header}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {chart.table.rows.map((row, index) => (
                  <tr key={`${message.id}-${index}`}>
                    {row.map((cell, cellIndex) => (
                      <td key={`${message.id}-${index}-${cellIndex}`}>{String(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    );
  };

  return (
    <div className="chat-shell">
      <div className="chat-header">
        <div className="chat-header__mark">
          <Sparkles size={18} />
        </div>
        <div>
          <div className="chat-header__title">合同智能助理</div>
          <div className="chat-header__subtitle">DeepSeek + Function Calling + Readonly SQL</div>
        </div>
      </div>

      <div ref={scrollRef} className="chat-messages">
        {messages.map((message) => (
          <div key={message.id} className={`chat-message ${message.role}`}>
            <div className="chat-message__meta">
              {message.role === 'assistant' ? <Bot size={14} /> : <User size={14} />}
              <span>{message.role === 'assistant' ? '合同助手' : '我'}</span>
            </div>
            <div className={`chat-bubble ${message.role}`}>
              <div className="chat-bubble__text">{message.text}</div>
              {message.pending ? (
                <div className="chat-pending">
                  <CircleDashed size={14} />
                  正在生成结果...
                </div>
              ) : null}
              {renderStructuredContent(message)}
            </div>
          </div>
        ))}
      </div>

      <div className="chat-input">
        <textarea
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              event.preventDefault();
              void handleSend();
            }
          }}
          placeholder="例如：查询合同、查看 HT2026040001 详情、按部门统计合同金额"
        />
        <button type="button" className="chat-send-btn" onClick={() => void handleSend()} disabled={!canSend}>
          <Send size={16} />
        </button>
        <div className="chat-input__tip">AI 对话仅支持只读查询和页面导航，写操作请使用固定业务页面。</div>
      </div>
    </div>
  );
};

export default AIChat;
