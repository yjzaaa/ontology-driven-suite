import { useState } from 'react';
import type { ExecutionStep } from '../../types/scenario';
import styles from './StepCard.module.css';

interface Props {
  step: ExecutionStep;
}

const TYPE_LABEL: Record<string, { label: string; cls: string }> = {
  SQL: { label: 'SQL', cls: 'badgeSql' },
  STAT: { label: '统计', cls: 'badgeStat' },
  AI_REASONING: { label: 'AI推理', cls: 'badgeAi' },
};

export default function StepCard({ step }: Props) {
  const [showSql, setShowSql] = useState(false);
  const [showRows, setShowRows] = useState(false);
  const meta = TYPE_LABEL[step.step_type] ?? { label: step.step_type, cls: 'badgeStat' };

  return (
    <div className={`${styles.card} ${styles[`status_${step.status}`]}`}>
      <div className={styles.head}>
        <span className={`${styles.badge} ${styles[meta.cls]}`}>{meta.label}</span>
        <span className={styles.title}>{step.description}</span>
        <span className={styles.statusIcon}>{statusIcon(step.status)}</span>
      </div>

      {/* SQL 步骤 */}
      {step.step_type === 'SQL' && (
        <>
          {/* Source 信息 + 重试历史 */}
          {step.source && (
            <div className={styles.metaRow}>
              <span className={`${styles.source} ${step.source === 'ai' ? styles.srcAi : styles.srcFallback}`}>
                {step.source === 'ai' ? '🤖 AI 生成' : '🛡 Fallback'}
              </span>
              {step.row_count !== undefined && (
                <span className={styles.metaText}>
                  {step.row_count} 行 · {step.duration_ms ?? 0}ms
                </span>
              )}
            </div>
          )}
          {/* 重试历史 */}
          {step.attempts && step.attempts.length > 1 && (
            <div className={styles.attempts}>
              {step.attempts.map((a, i) => (
                <div key={i} className={styles.attemptItem}>
                  {a.source === 'ai' ? `AI 尝试 #${a.attempt}` : `→ Fallback: ${a.reason ?? ''}`}
                </div>
              ))}
            </div>
          )}
          {/* 折叠 SQL */}
          {step.sql && (
            <details className={styles.collapse} open={showSql}>
              <summary onClick={(e) => { e.preventDefault(); setShowSql(!showSql); }}>
                {showSql ? '▼' : '▶'} 查看 SQL
              </summary>
              <pre className={styles.sqlBox}>{step.sql}</pre>
            </details>
          )}
          {/* 折叠数据预览 */}
          {step.rows_preview && step.rows_preview.length > 0 && (
            <details className={styles.collapse} open={showRows}>
              <summary onClick={(e) => { e.preventDefault(); setShowRows(!showRows); }}>
                {showRows ? '▼' : '▶'} 数据预览（前 {step.rows_preview.length} / {step.row_count} 行）
              </summary>
              <TablePreview rows={step.rows_preview} columns={step.columns ?? []} />
            </details>
          )}
        </>
      )}

      {/* STAT 步骤 */}
      {step.step_type === 'STAT' && step.stats && (
        <StatsSummary stats={step.stats} />
      )}

      {/* 错误 */}
      {step.error && (
        <div className={styles.errorBox}>⚠ {step.error}</div>
      )}
    </div>
  );
}

function statusIcon(s: string): string {
  switch (s) {
    case 'pending': return '○';
    case 'running': return '⏳';
    case 'sql_attempt': return '⚙';
    case 'done': return '✓';
    case 'error': return '✗';
    default: return '·';
  }
}

function TablePreview({ rows, columns }: { rows: Record<string, unknown>[]; columns: string[] }) {
  const cols = columns.length > 0 ? columns : Object.keys(rows[0] ?? {});
  return (
    <div className={styles.tableWrap}>
      <table className={styles.table}>
        <thead>
          <tr>{cols.map((c) => <th key={c}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>
              {cols.map((c) => (
                <td key={c}>{formatCell(r[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatCell(v: unknown): string {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'number') return v.toLocaleString();
  return String(v);
}

function StatsSummary({ stats }: { stats: any }) {
  // 不同算法不同显示
  if (stats?.series) {
    // mom_yoy
    const latest = stats.latest;
    return (
      <div className={styles.statsCompact}>
        <span className={styles.statItem}>趋势：<b>{stats.trend}</b></span>
        {latest && (
          <>
            <span className={styles.statItem}>
              最新 {latest.period}：<b>{(latest.value ?? 0).toLocaleString()}</b>
            </span>
            {latest.mom_pct !== null && (
              <span className={styles.statItem}>
                MoM：<b style={{ color: latest.mom_pct >= 0 ? '#22C55E' : '#EF4444' }}>
                  {latest.mom_pct > 0 ? '+' : ''}{latest.mom_pct}%
                </b>
              </span>
            )}
            {latest.yoy_pct !== null && (
              <span className={styles.statItem}>
                YoY：<b style={{ color: latest.yoy_pct >= 0 ? '#22C55E' : '#EF4444' }}>
                  {latest.yoy_pct > 0 ? '+' : ''}{latest.yoy_pct}%
                </b>
              </span>
            )}
          </>
        )}
      </div>
    );
  }
  if (stats?.anomalies) {
    return (
      <div className={styles.statsCompact}>
        <span className={styles.statItem}>均值 <b>{stats.mean}</b></span>
        <span className={styles.statItem}>σ <b>{stats.std}</b></span>
        <span className={styles.statItem}>
          异常 <b>{stats.anomalies.length}</b> 个
        </span>
      </div>
    );
  }
  if (stats?.segment_counts) {
    return (
      <div className={styles.statsCompact}>
        {Object.entries(stats.segment_counts).map(([k, v]) => (
          <span key={k} className={styles.statItem}>{k}: <b>{v as number}</b></span>
        ))}
      </div>
    );
  }
  return <pre className={styles.statsRaw}>{JSON.stringify(stats, null, 2).slice(0, 300)}</pre>;
}
