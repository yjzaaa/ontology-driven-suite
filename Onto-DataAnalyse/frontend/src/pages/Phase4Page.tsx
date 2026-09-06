import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { phase4Api, type ChatMessage } from '../api/phase4Api';
import { sseRequest } from '../api/sseClient';
import { phase3Api } from '../api/phase3Api';
import ConfidenceBadge from '../components/shared/ConfidenceBadge';
import ReasoningStream from '../components/phase3/ReasoningStream';
import StepCard from '../components/phase3/StepCard';
import ReportContainer from '../components/report/ReportContainer';
import type { ExecutionStep, ScenarioSummary } from '../types/scenario';
import styles from './Phase4Page.module.css';

interface PendingExec {
  scenarioId: string;
  scenarioName: string;
  scenarioIcon?: string;
  intent?: any;
  steps: Record<string, ExecutionStep>;
  stepOrder: string[];
  report?: any;
  done: boolean;
}

export default function Phase4Page() {
  const [sessionId, setSessionId] = useState('');
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [intent, setIntent] = useState<any>(null);
  const [running, setRunning] = useState(false);
  const [streaming, setStreaming] = useState<PendingExec | null>(null);
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const intentDebounce = useRef<number | null>(null);

  // 初始加载
  useEffect(() => {
    (async () => {
      try {
        const s = await phase4Api.getSessions();
        setSessionId(s.default_session_id);
        if (s.default_session_id) {
          const msgs = await phase4Api.getMessages(s.default_session_id);
          setHistory(msgs);
        }
        const scs = await phase3Api.listScenarios();
        setScenarios(scs);
      } catch (err) {
        console.warn(err);
      }
    })();
  }, []);

  // 输入时实时意图识别（带防抖）
  useEffect(() => {
    if (!input.trim() || running) {
      setIntent(null);
      return;
    }
    if (intentDebounce.current) {
      window.clearTimeout(intentDebounce.current);
    }
    intentDebounce.current = window.setTimeout(async () => {
      try {
        const r = await phase4Api.detectIntent(input);
        setIntent(r);
      } catch {
        setIntent(null);
      }
    }, 350);
  }, [input, running]);

  // 滚到底
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [history, streaming?.stepOrder.length, streaming?.report]);

  const updateStep = useCallback((sid: string, patch: Partial<ExecutionStep>) => {
    setStreaming((prev) => {
      if (!prev) return prev;
      const cur = prev.steps[sid] ?? { step_id: sid, step_type: 'SQL' as const, description: '', status: 'pending' as const };
      return {
        ...prev,
        steps: { ...prev.steps, [sid]: { ...cur, ...patch } },
      };
    });
  }, []);

  const handleMsg = useCallback((m: any) => {
    switch (m.type) {
      case 'intent':
        setStreaming((prev) => prev ? { ...prev, intent: m } : prev);
        break;
      case 'execution_start':
        setStreaming((prev) => prev ? {
          ...prev,
          scenarioId: m.scenario?.id ?? prev.scenarioId,
          scenarioName: m.scenario?.name ?? prev.scenarioName,
          scenarioIcon: m.scenario?.icon,
        } : prev);
        break;
      case 'step_start':
        setStreaming((prev) => {
          if (!prev) return prev;
          const sid = m.step_id;
          return {
            ...prev,
            stepOrder: prev.stepOrder.includes(sid) ? prev.stepOrder : [...prev.stepOrder, sid],
            steps: { ...prev.steps, [sid]: { step_id: sid, step_type: m.step_type, description: m.description, status: 'running' } },
          };
        });
        break;
      case 'step_sql_attempt':
        setStreaming((prev) => {
          if (!prev) return prev;
          const cur = prev.steps[m.step_id] ?? { step_id: m.step_id, step_type: 'SQL' as const, description: '', status: 'running' as const };
          return {
            ...prev,
            steps: {
              ...prev.steps,
              [m.step_id]: {
                ...cur,
                attempts: [...(cur.attempts ?? []), { source: m.source, attempt: m.attempt, reason: m.reason }],
                source: m.source,
              },
            },
          };
        });
        break;
      case 'step_sql':
        updateStep(m.step_id, { sql: m.sql, source: m.source });
        break;
      case 'step_result':
        updateStep(m.step_id, {
          ok: m.ok, source: m.source, rows_preview: m.rows_preview, row_count: m.row_count,
          columns: m.columns, duration_ms: m.duration_ms, stats: m.stats, error: m.error,
        });
        break;
      case 'ai_thinking':
        setStreaming((prev) => {
          if (!prev) return prev;
          const cur = prev.steps[m.step_id] ?? { step_id: m.step_id, step_type: 'AI_REASONING' as const, description: '', status: 'running' as const };
          return {
            ...prev,
            steps: { ...prev.steps, [m.step_id]: { ...cur, thinking_buffer: (cur.thinking_buffer ?? '') + (m.delta ?? '') } },
          };
        });
        break;
      case 'ai_complete':
        updateStep(m.step_id, {
          thinking: m.thinking, conclusion: m.conclusion,
          recommendations: m.recommendations, charts_parsed: m.charts_parsed,
          confidence: m.confidence,
        });
        break;
      case 'step_done':
        updateStep(m.step_id, { status: 'done' });
        break;
      case 'step_error':
        updateStep(m.step_id, { status: 'error', error: m.error });
        break;
      case 'report_ready':
        setStreaming((prev) => prev ? { ...prev, report: m.report } : prev);
        break;
      case 'done':
        setStreaming((prev) => prev ? { ...prev, done: true } : prev);
        setRunning(false);
        // 重新拉取消息历史
        if (sessionId) {
          phase4Api.getMessages(sessionId).then(setHistory).catch(() => {});
        }
        break;
      case 'assistant_fallback':
        setStreaming((prev) => prev ? { ...prev, done: true } : prev);
        setRunning(false);
        if (sessionId) {
          phase4Api.getMessages(sessionId).then(setHistory).catch(() => {});
        }
        break;
    }
  }, [sessionId, updateStep]);

  const send = useCallback(async (msg: string) => {
    if (!msg.trim() || running) return;
    setRunning(true);
    setInput('');
    setIntent(null);
    setStreaming({
      scenarioId: '',
      scenarioName: '识别中...',
      steps: {},
      stepOrder: [],
      done: false,
    });
    await sseRequest(
      '/api/phase4/chat',
      { method: 'POST', body: { message: msg, session_id: sessionId || undefined } },
      {
        onMessage: handleMsg,
        onError: (err) => {
          setRunning(false);
          alert(`错误：${err.message}`);
        },
      },
    );
  }, [running, sessionId, handleMsg]);

  const orderedSteps = useMemo(() => {
    if (!streaming) return [];
    return streaming.stepOrder.map((sid) => streaming.steps[sid]).filter(Boolean);
  }, [streaming]);

  return (
    <div className={styles.layout}>
      {/* 左侧：快捷场景 + 会话信息 */}
      <aside className={styles.sidebar}>
        <div className={styles.sidebarTitle}>预设场景快捷</div>
        <div className={styles.shortcutList}>
          {scenarios.map((s) => (
            <button
              key={s.id}
              type="button"
              className={styles.shortcut}
              onClick={() => send(s.triggers[0] ?? s.name)}
              disabled={running}
            >
              <span className={styles.shortcutIcon}>{s.icon}</span>
              <span className={styles.shortcutName}>{s.name}</span>
            </button>
          ))}
        </div>

        <div className={styles.sidebarSection}>
          <div className={styles.sidebarSubtitle}>历史对话</div>
          <div className={styles.historyMini}>
            {history.length === 0 && <div className={styles.muted}>暂无历史</div>}
            {history.slice(-8).reverse().map((m) => (
              <div key={m.id} className={`${styles.histItem} ${m.role === 'user' ? styles.histUser : styles.histBot}`}>
                <span className={styles.histRole}>{m.role === 'user' ? '👤' : '🤖'}</span>
                <span className={styles.histText}>{m.content.slice(0, 28)}{m.content.length > 28 ? '…' : ''}</span>
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* 中间：对话流 */}
      <main className={styles.main}>
        <div className={styles.chatScroll} ref={scrollRef}>
          {/* 历史消息 */}
          {history.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}

          {/* 正在执行的消息 */}
          {streaming && (
            <div className={styles.streamingBubble}>
              <div className={styles.bubbleHead}>
                <span className={styles.botAvatar}>🤖</span>
                <span className={styles.botName}>分析助手</span>
              </div>
              {streaming.intent && (
                <div className={styles.intentBox}>
                  <span>意图识别：</span>
                  <b>{streaming.intent.matched_keywords?.length ? streaming.intent.matched_keywords.join(' / ') : streaming.intent.scenario_id}</b>
                  {' '}
                  <ConfidenceBadge value={streaming.intent.confidence ?? 0} />
                  <span className={styles.intentReason}>{streaming.intent.reasoning}</span>
                </div>
              )}
              {streaming.scenarioName && streaming.scenarioName !== '识别中...' && (
                <div className={styles.execTitle}>
                  {streaming.scenarioIcon} 执行中：{streaming.scenarioName}
                </div>
              )}
              {orderedSteps.length > 0 && !streaming.report && (
                <div className={styles.miniPipeline}>
                  {orderedSteps.map((step) => (
                    step.step_type === 'AI_REASONING' ? (
                      <ReasoningStream key={step.step_id} step={step} />
                    ) : (
                      <StepCard key={step.step_id} step={step} />
                    )
                  ))}
                </div>
              )}
              {streaming.report && <ReportContainer report={streaming.report} />}
            </div>
          )}

          {!history.length && !streaming && (
            <div className={styles.welcome}>
              <div className={styles.welcomeIcon}>💬</div>
              <h2>开始你的数据分析对话</h2>
              <p>用自然语言描述你想分析的问题，系统将自动匹配场景并生成可视化报告。</p>
              <div className={styles.exampleList}>
                <div className={styles.exampleTitle}>示例提问：</div>
                {[
                  '分析一下我们的 GMV 趋势',
                  '近期经营有什么异常',
                  '客户流失情况怎么样',
                  'GMV 同比下降了多少',
                ].map((ex) => (
                  <button key={ex} type="button" className={styles.example}
                          onClick={() => send(ex)}>「{ex}」</button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 输入框 */}
        <div className={styles.inputBar}>
          {intent && input.trim() && (
            <div className={styles.intentHint}>
              识别为 <b>{intent.scenario_id ?? '未匹配'}</b>{' '}
              <ConfidenceBadge value={intent.confidence ?? 0} />
              {intent.reasoning && <span className={styles.intentReason}>· {intent.reasoning}</span>}
            </div>
          )}
          <textarea
            className={styles.textarea}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                send(input);
              }
            }}
            placeholder="输入你的分析需求，Enter 发送，Shift+Enter 换行"
            disabled={running}
            rows={2}
          />
          <button
            type="button"
            className="btn-primary"
            onClick={() => send(input)}
            disabled={running || !input.trim()}
          >
            {running ? '推理中...' : '发送'}
          </button>
        </div>
      </main>

      {/* 右侧：推理过程实时面板 */}
      <aside className={styles.reasoningPanel}>
        <div className={styles.panelTitle}>AI 推理过程</div>
        {!streaming && <div className={styles.muted}>等待对话开始</div>}
        {streaming && (
          <div className={styles.panelContent}>
            <div className={styles.panelStat}>
              <span>步骤数</span><b>{orderedSteps.length}</b>
            </div>
            <div className={styles.panelStat}>
              <span>SQL 步骤</span>
              <b>{orderedSteps.filter((s) => s.step_type === 'SQL').length}</b>
            </div>
            <div className={styles.panelStat}>
              <span>AI 推理</span>
              <b>{orderedSteps.filter((s) => s.step_type === 'AI_REASONING').length}</b>
            </div>
            <div className={styles.panelStat}>
              <span>当前</span>
              <b>{streaming.done ? '✓ 完成' : '⏳ 进行中'}</b>
            </div>
            {orderedSteps
              .filter((s) => s.step_type === 'AI_REASONING' && s.thinking_buffer)
              .map((s) => (
                <div key={s.step_id} className={styles.thinkingPreview}>
                  <div className={styles.thinkingHead}>{s.description}</div>
                  <div className={styles.thinkingText}>
                    {(s.thinking ?? s.thinking_buffer ?? '').slice(-600)}
                  </div>
                </div>
              ))}
          </div>
        )}
      </aside>
    </div>
  );
}

// ============================================================
// 单条历史消息气泡
// ============================================================
function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user';
  if (isUser) {
    return (
      <div className={styles.userBubble}>
        <div className={styles.userText}>{message.content}</div>
      </div>
    );
  }
  return (
    <div className={styles.botBubble}>
      <div className={styles.bubbleHead}>
        <span className={styles.botAvatar}>🤖</span>
        <span className={styles.botName}>分析助手</span>
        <span className={styles.timestamp}>{message.created_at.slice(5, 16).replace('T', ' ')}</span>
      </div>
      <div className={styles.userText}>{message.content}</div>
      {message.report_data && <ReportContainer report={message.report_data} />}
    </div>
  );
}
