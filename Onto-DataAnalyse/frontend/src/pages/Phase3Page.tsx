import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { phase3Api } from '../api/phase3Api';
import { sseRequest } from '../api/sseClient';
import ReasoningStream from '../components/phase3/ReasoningStream';
import ScenarioCard from '../components/phase3/ScenarioCard';
import StepCard from '../components/phase3/StepCard';
import type {
  ExecutionStep, ScenarioSummary,
} from '../types/scenario';
import styles from './Phase3Page.module.css';

type SseMsg = {
  type: string;
  step_id?: string;
  step_type?: string;
  description?: string;
  source?: string;
  sql?: string;
  attempt?: number;
  reason?: string;
  rows_preview?: any[];
  row_count?: number;
  columns?: string[];
  duration_ms?: number;
  ok?: boolean;
  stats?: any;
  delta?: string;
  thinking?: string;
  conclusion?: string;
  recommendations?: string;
  charts?: string;
  charts_parsed?: any[];
  confidence?: any;
  error?: string;
  message?: string;
  report?: any;
  scenario?: any;
  execution_id?: string;
};

export default function Phase3Page() {
  const navigate = useNavigate();
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [steps, setSteps] = useState<Record<string, ExecutionStep>>({});
  const [stepOrder, setStepOrder] = useState<string[]>([]);
  const [report, setReport] = useState<any>(null);
  const [error, setError] = useState('');
  const [confirmedAtLeastOne, setConfirmedAtLeastOne] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    phase3Api.listScenarios().then(setScenarios).catch((e) => setError(e.message));
  }, []);

  const updateStep = useCallback((sid: string, patch: Partial<ExecutionStep>) => {
    setSteps((prev) => ({
      ...prev,
      [sid]: { ...(prev[sid] ?? { step_id: sid, step_type: 'SQL', description: '', status: 'pending' as const }), ...patch },
    }));
  }, []);

  const handleMsg = useCallback((m: SseMsg) => {
    switch (m.type) {
      case 'scenario_start':
        break;
      case 'step_start': {
        const sid = m.step_id!;
        setStepOrder((prev) => prev.includes(sid) ? prev : [...prev, sid]);
        updateStep(sid, {
          step_id: sid,
          step_type: m.step_type as any,
          description: m.description ?? '',
          status: 'running',
          attempts: [],
        });
        break;
      }
      case 'step_sql_attempt': {
        const sid = m.step_id!;
        setSteps((prev) => {
          const cur = prev[sid] ?? { step_id: sid, step_type: 'SQL' as const, description: '', status: 'running' as const };
          return {
            ...prev,
            [sid]: {
              ...cur,
              attempts: [...(cur.attempts ?? []), { source: m.source ?? '', attempt: m.attempt, reason: m.reason }],
              source: m.source as any,
            },
          };
        });
        break;
      }
      case 'step_sql':
        updateStep(m.step_id!, { sql: m.sql, source: m.source as any });
        break;
      case 'step_result':
        updateStep(m.step_id!, {
          ok: m.ok,
          source: (m.source as any) ?? undefined,
          rows_preview: m.rows_preview,
          row_count: m.row_count,
          columns: m.columns,
          duration_ms: m.duration_ms,
          stats: m.stats,
          error: m.error,
        });
        break;
      case 'ai_thinking':
        setSteps((prev) => {
          const sid = m.step_id!;
          const cur = prev[sid] ?? { step_id: sid, step_type: 'AI_REASONING' as const, description: '', status: 'running' as const };
          return {
            ...prev,
            [sid]: { ...cur, thinking_buffer: (cur.thinking_buffer ?? '') + (m.delta ?? '') },
          };
        });
        break;
      case 'ai_complete':
        updateStep(m.step_id!, {
          thinking: m.thinking,
          conclusion: m.conclusion,
          recommendations: m.recommendations,
          charts: m.charts,
          charts_parsed: m.charts_parsed,
          confidence: m.confidence,
        });
        break;
      case 'step_done':
        updateStep(m.step_id!, { status: 'done' });
        break;
      case 'step_error':
        updateStep(m.step_id!, { status: 'error', error: m.error });
        break;
      case 'report_ready':
        setReport(m.report);
        break;
      case 'error':
        setError(m.message ?? '执行出错');
        setRunning(false);
        break;
      case 'done':
        setRunning(false);
        setConfirmedAtLeastOne(true);
        break;
    }
  }, [updateStep]);

  const runScenario = useCallback(async (scenarioId: string) => {
    setSelectedId(scenarioId);
    setRunning(true);
    setSteps({});
    setStepOrder([]);
    setReport(null);
    setError('');

    const ac = new AbortController();
    abortRef.current = ac;
    await sseRequest(
      '/api/phase3/execute',
      { method: 'POST', body: { scenario_id: scenarioId }, signal: ac.signal },
      {
        onMessage: handleMsg,
        onError: (err) => {
          setError(err.message);
          setRunning(false);
        },
        onDone: () => setRunning(false),
      },
    );
  }, [handleMsg]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    setRunning(false);
  }, []);

  const goToPhase4 = useCallback(async () => {
    try {
      await phase3Api.confirm();
      navigate('/phase4');
    } catch (e) {
      setError((e as Error).message);
    }
  }, [navigate]);

  const orderedSteps = stepOrder.map((sid) => steps[sid]).filter(Boolean);

  // 不在场景执行状态时显示场景选择
  if (!selectedId) {
    return (
      <div className={styles.selectionView}>
        <div className={styles.selectionHead}>
          <h2 className={styles.title}>选择一个预设场景</h2>
          <p className={styles.subtitle}>
            每个场景将自动执行 SQL 数据采集 + 统计计算 + DeepSeek 真实推理，最后输出可视化分析报告。
          </p>
        </div>
        <div className={styles.cardGrid}>
          {scenarios.map((sc) => (
            <ScenarioCard
              key={sc.id}
              scenario={sc}
              onSelect={runScenario}
              disabled={running}
            />
          ))}
        </div>
        {error && <div className={styles.error}>⚠ {error}</div>}
      </div>
    );
  }

  return (
    <div className={styles.execLayout}>
      {/* 左：执行流水线 */}
      <div className={styles.leftPanel}>
        <div className={styles.execHead}>
          <div>
            <button
              type="button"
              className={styles.backBtn}
              onClick={() => { setSelectedId(null); setRunning(false); }}
            >
              ← 返回场景选择
            </button>
            <div className={styles.execTitle}>
              {scenarios.find((s) => s.id === selectedId)?.icon}{' '}
              {scenarios.find((s) => s.id === selectedId)?.name}
            </div>
          </div>
          <div className={styles.execActions}>
            {running && (
              <button className="btn-secondary" type="button" onClick={stop}>停止</button>
            )}
            {!running && report && (
              <button className="btn-primary" type="button" onClick={() => runScenario(selectedId)}>
                重新执行
              </button>
            )}
          </div>
        </div>

        <div className={styles.pipeline}>
          {orderedSteps.length === 0 && (
            <div className={styles.emptyHint}>等待执行...</div>
          )}
          {orderedSteps.map((step) => (
            step.step_type === 'AI_REASONING' ? (
              <ReasoningStream key={step.step_id} step={step} />
            ) : (
              <StepCard key={step.step_id} step={step} />
            )
          ))}
        </div>

        {error && <div className={styles.error}>⚠ {error}</div>}

        {!running && report && confirmedAtLeastOne && (
          <button
            type="button"
            className="btn-primary"
            style={{ width: '100%', marginTop: 12 }}
            onClick={goToPhase4}
          >
            进入阶段四：自然语言对话 →
          </button>
        )}
      </div>

      {/* 右：报告预览 */}
      <div className={styles.rightPanel}>
        <div className={styles.reportHead}>
          <span>📋 报告预览</span>
          {report && (
            <span className={styles.timestamp}>{report.generated_at}</span>
          )}
        </div>
        <div className={styles.reportBody}>
          {!report && running && (
            <div className={styles.placeholder}>
              <div className={styles.placeholderIcon}>⏳</div>
              <div>报告将在所有步骤完成后呈现</div>
            </div>
          )}
          {!report && !running && (
            <div className={styles.placeholder}>
              <div className={styles.placeholderIcon}>📋</div>
              <div>等待场景执行</div>
            </div>
          )}
          {report && <ReportPreview report={report} />}
        </div>
      </div>
    </div>
  );
}

// ============================================================
// 报告预览（简版，第六批会做完整咨询公司风格报告）
// ============================================================
function ReportPreview({ report }: { report: any }) {
  return (
    <div className={styles.report}>
      <div className={styles.reportTitle}>
        {report.scenario.icon} {report.scenario.name}
      </div>
      <div className={styles.reportDesc}>{report.scenario.description}</div>

      {/* SQL 步骤摘要 */}
      <div className={styles.reportSection}>
        <div className={styles.reportSectionTitle}>数据采集</div>
        {report.sql_steps.map((s: any) => (
          <div key={s.step_id} className={styles.reportItem}>
            <div className={styles.reportItemTitle}>
              {s.step_id} · {s.description}
              <span className={styles.reportBadge}>{s.row_count} 行</span>
              <span className={`${styles.reportBadge} ${s.source === 'ai' ? styles.badgeAi : styles.badgeFb}`}>
                {s.source === 'ai' ? 'AI 生成' : 'Fallback'}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* 统计 */}
      {report.stat_steps.length > 0 && (
        <div className={styles.reportSection}>
          <div className={styles.reportSectionTitle}>统计计算</div>
          {report.stat_steps.map((s: any) => (
            <div key={s.step_id} className={styles.reportItem}>
              <div className={styles.reportItemTitle}>
                {s.step_id} · {s.description} · {s.algorithm}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* AI 推理结论 */}
      {report.ai_steps.length > 0 && report.ai_steps[0].ai_output && (
        <div className={styles.reportSection}>
          <div className={styles.reportSectionTitle}>AI 推理结论</div>
          <ReasoningStream
            step={{
              step_id: report.ai_steps[0].step_id,
              step_type: 'AI_REASONING',
              description: report.ai_steps[0].description,
              status: 'done',
              ...report.ai_steps[0].ai_output,
            }}
          />
        </div>
      )}
    </div>
  );
}
