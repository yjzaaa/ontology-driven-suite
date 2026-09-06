import { useRef, useState } from 'react';
import EChartsWrapper from '../shared/EChartsWrapper';
import ConfidenceBadge from '../shared/ConfidenceBadge';
import { buildEChartsOption, buildMomYoyChart, inferAutoCharts } from './chartBuilder';
import { exportReportToHtml } from '../../utils/exportHtml';
import styles from './ReportContainer.module.css';

interface ReportSqlStep {
  step_id: string;
  description: string;
  sql: string;
  source: string;
  row_count: number;
  columns: string[];
  rows_preview: Record<string, any>[];
  ok: boolean;
}

interface ReportStatStep {
  step_id: string;
  description: string;
  algorithm: string;
  stats: any;
}

interface ReportAiStep {
  step_id: string;
  description: string;
  ai_output: {
    thinking?: string;
    conclusion?: string;
    recommendations?: string;
    charts_parsed?: any[];
    confidence?: { avg: number; values: number[] };
  };
}

interface Report {
  scenario: { id: string; name: string; icon?: string; description?: string };
  sql_steps: ReportSqlStep[];
  stat_steps: ReportStatStep[];
  ai_steps: ReportAiStep[];
  generated_at: string;
}

interface Props {
  report: Report;
}

export default function ReportContainer({ report }: Props) {
  const rootRef = useRef<HTMLDivElement>(null);
  const [exporting, setExporting] = useState(false);

  const handleExport = async () => {
    if (!rootRef.current || exporting) return;
    setExporting(true);
    try {
      await exportReportToHtml(rootRef.current, {
        title: `${report.scenario.icon ?? ''} ${report.scenario.name} 分析报告`.trim(),
        subtitle: `生成于 ${report.generated_at}`,
        filename: `report_${report.scenario.id}_${report.generated_at.replace(/[: -]/g, '')}.html`,
      });
    } catch (err) {
      // eslint-disable-next-line no-alert
      alert(`导出失败：${(err as Error).message}`);
    } finally {
      setExporting(false);
    }
  };

  const sqlByStepId: Record<string, ReportSqlStep> = {};
  for (const s of report.sql_steps) sqlByStepId[s.step_id] = s;

  const ai = report.ai_steps[0]?.ai_output;
  const confidence = ai?.confidence?.avg;

  // AI 指定的图表（优先）
  const aiCharts: { hint: any; rows: any[] }[] = [];
  for (const ch of ai?.charts_parsed ?? []) {
    const target = sqlByStepId[ch.data_step];
    if (target?.rows_preview) {
      aiCharts.push({ hint: ch, rows: target.rows_preview });
    }
  }

  // 自动推断图表（fallback / 补充）
  const autoCharts = inferAutoCharts(report.sql_steps);

  // 同环比统计步骤的双轴图
  const momYoyCharts: { title: string; option: any }[] = [];
  for (const s of report.stat_steps) {
    if (s.algorithm === 'mom_yoy' && s.stats?.series) {
      const opt = buildMomYoyChart(s.stats, s.description);
      if (opt) momYoyCharts.push({ title: s.description, option: opt });
    }
  }

  // 核心 KPI 卡片：从 mom_yoy 的 latest 提取
  const kpiCards = report.stat_steps
    .filter((s) => s.algorithm === 'mom_yoy' && s.stats?.latest)
    .map((s) => ({
      title: s.description.replace(/计算\s*/, '').replace(/同环比.*$/, '').trim() || '指标',
      latest: s.stats.latest,
    }));

  return (
    <div className={styles.report} ref={rootRef}>
      {/* 封面 */}
      <div className={styles.cover}>
        <div className={styles.coverIcon}>{report.scenario.icon}</div>
        <div className={styles.coverMain}>
          <h1 className={styles.coverTitle}>{report.scenario.name}</h1>
          <div className={styles.coverMeta}>
            <span>生成于 {report.generated_at}</span>
            {confidence != null && (
              <ConfidenceBadge value={confidence} size="md" label="平均置信度" />
            )}
          </div>
        </div>
        {/* data-export-hide 标记 — 导出 HTML 时该按钮会被自动移除 */}
        <button
          type="button"
          className={styles.exportBtn}
          onClick={handleExport}
          disabled={exporting}
          title="导出为单文件 HTML（含全部样式与图表）"
          data-export-hide=""
        >
          {exporting ? '导出中...' : '📥 导出 HTML'}
        </button>
      </div>

      {/* 执行摘要 */}
      {ai?.conclusion && (
        <section className={styles.section}>
          <div className={styles.sectionTitle}>📊 执行摘要</div>
          <div className={styles.summaryBox}>
            <FormattedText text={ai.conclusion.split('\n').slice(0, 6).join('\n')} />
          </div>
        </section>
      )}

      {/* 核心指标卡片 */}
      {kpiCards.length > 0 && (
        <section className={styles.section}>
          <div className={styles.sectionTitle}>核心指标</div>
          <div className={styles.kpiGrid}>
            {kpiCards.map((k, i) => (
              <KPICard key={i} {...k} />
            ))}
          </div>
        </section>
      )}

      {/* AI 指定图表 */}
      {aiCharts.length > 0 && (
        <section className={styles.section}>
          <div className={styles.sectionTitle}>📈 关键趋势</div>
          <div className={styles.chartGrid}>
            {aiCharts.map((c, i) => {
              const opt = buildEChartsOption(c.hint, c.rows);
              if (!opt) return null;
              return (
                <div key={i} className={styles.chartCard}>
                  <EChartsWrapper option={opt} height={280} />
                  {c.hint.note && <div className={styles.chartNote}>{c.hint.note}</div>}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* 同环比双轴图 */}
      {momYoyCharts.length > 0 && (
        <section className={styles.section}>
          <div className={styles.sectionTitle}>📐 同环比分析</div>
          <div className={styles.chartGrid}>
            {momYoyCharts.map((c, i) => (
              <div key={i} className={styles.chartCard}>
                <EChartsWrapper option={c.option} height={280} />
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 自动图表（fallback） */}
      {aiCharts.length === 0 && autoCharts.length > 0 && (
        <section className={styles.section}>
          <div className={styles.sectionTitle}>数据可视化</div>
          <div className={styles.chartGrid}>
            {autoCharts.slice(0, 4).map((c, i) => {
              const opt = buildEChartsOption(c.hint, c.rows);
              if (!opt) return null;
              return (
                <div key={i} className={styles.chartCard}>
                  <EChartsWrapper option={opt} height={260} />
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* AI 推理结论 */}
      {ai?.conclusion && (
        <section className={styles.section}>
          <div className={styles.sectionTitle}>🧠 AI 推理结论</div>
          <div className={styles.insightBox}>
            <FormattedText text={ai.conclusion} />
          </div>
        </section>
      )}

      {/* 行动建议 */}
      {ai?.recommendations && (
        <section className={styles.section}>
          <div className={styles.sectionTitle}>🎯 行动建议</div>
          <div className={styles.recommendBox}>
            <FormattedText text={ai.recommendations} />
          </div>
        </section>
      )}

      {/* 数据表 */}
      <section className={styles.section}>
        <div className={styles.sectionTitle}>📋 数据表</div>
        {report.sql_steps.slice(0, 3).map((s) => (
          <details key={s.step_id} className={styles.tableDetails}>
            <summary>
              <strong>{s.step_id}</strong> · {s.description}
              <span className={styles.tableSummaryMeta}>
                {s.row_count} 行 · {s.source === 'ai' ? 'AI 生成' : 'Fallback'}
              </span>
            </summary>
            <DataTable rows={s.rows_preview} columns={s.columns} />
          </details>
        ))}
      </section>

      {/* 推理思维链（折叠） */}
      {ai?.thinking && (
        <section className={styles.section}>
          <details>
            <summary className={styles.foldHead}>查看 AI 推理思维链</summary>
            <pre className={styles.thinkBox}>{ai.thinking}</pre>
          </details>
        </section>
      )}

      {/* 数据溯源（折叠） */}
      <section className={styles.section}>
        <details>
          <summary className={styles.foldHead}>查看数据溯源（共 {report.sql_steps.length} 个 SQL）</summary>
          <div className={styles.lineage}>
            {report.sql_steps.map((s) => (
              <div key={s.step_id} className={styles.lineageItem}>
                <div className={styles.lineageHead}>
                  <strong>{s.step_id}</strong> · {s.description}
                  <span className={styles.lineageMeta}>{s.row_count} 行 · {s.source === 'ai' ? 'AI 生成' : 'Fallback'}</span>
                </div>
                <pre className={styles.lineageSql}>{s.sql}</pre>
              </div>
            ))}
          </div>
        </details>
      </section>
    </div>
  );
}

function KPICard({ title, latest }: { title: string; latest: any }) {
  const value = latest?.value ?? 0;
  const momPct = latest?.mom_pct;
  const yoyPct = latest?.yoy_pct;
  return (
    <div className={styles.kpiCard}>
      <div className={styles.kpiTitle}>{title}</div>
      <div className={styles.kpiValue}>{Number(value).toLocaleString()}</div>
      <div className={styles.kpiCompare}>
        {momPct != null && (
          <span className={`${styles.compareItem} ${momPct >= 0 ? styles.cmpUp : styles.cmpDown}`}>
            {momPct >= 0 ? '▲' : '▼'} {Math.abs(momPct).toFixed(1)}% MoM
          </span>
        )}
        {yoyPct != null && (
          <span className={`${styles.compareItem} ${yoyPct >= 0 ? styles.cmpUp : styles.cmpDown}`}>
            {yoyPct >= 0 ? '▲' : '▼'} {Math.abs(yoyPct).toFixed(1)}% YoY
          </span>
        )}
      </div>
      <div className={styles.kpiPeriod}>{latest?.period}</div>
    </div>
  );
}

function DataTable({ rows, columns }: { rows: Record<string, any>[]; columns: string[] }) {
  if (!rows || rows.length === 0) return <div className={styles.empty}>无数据</div>;
  const cols = columns?.length ? columns : Object.keys(rows[0]);
  return (
    <div className={styles.tableWrap}>
      <table className={styles.dataTable}>
        <thead>
          <tr>{cols.map((c) => <th key={c}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>{cols.map((c) => <td key={c}>{format(r[c])}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function format(v: any): string {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'number') return v.toLocaleString();
  return String(v);
}

function FormattedText({ text }: { text: string }) {
  const lines = text.split('\n');
  return (
    <div className={styles.formatted}>
      {lines.map((l, i) => (
        <div key={i} className={styles.formattedLine}
             dangerouslySetInnerHTML={{ __html: applyInlineFormatting(l) }} />
      ))}
    </div>
  );
}

function applyInlineFormatting(line: string): string {
  let s = line.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  s = s.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
  s = s.replace(/\[(P0)\]/g, '<span class="prio-high">[P0]</span>');
  s = s.replace(/\[(P1)\]/g, '<span class="prio-mid">[P1]</span>');
  s = s.replace(/\[(P2)\]/g, '<span class="prio-low">[P2]</span>');
  s = s.replace(/\[置信度[:：]\s*(\d+)%\]/g, '<span class="conf-tag">置信度 $1%</span>');
  return s;
}
