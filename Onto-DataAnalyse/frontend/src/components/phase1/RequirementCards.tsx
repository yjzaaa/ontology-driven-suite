import type { ParsedRequirement } from '../../types/requirement';
import styles from './RequirementCards.module.css';

const PRIORITY_LABEL: Record<string, string> = {
  high: '高优',
  medium: '中',
  low: '低',
};

interface Props {
  data: ParsedRequirement;
}

export default function RequirementCards({ data }: Props) {
  return (
    <div className={styles.wrap}>
      {/* 概要 */}
      <div className={styles.overview}>
        <div className={styles.overviewItem}>
          <div className={styles.overviewLabel}>时间范围</div>
          <div className={styles.overviewValue}>{data.time_range || '—'}</div>
        </div>
        <div className={styles.overviewItem}>
          <div className={styles.overviewLabel}>分析目标</div>
          <div className={styles.overviewValue}>{data.analysis_goals?.length ?? 0} 项</div>
        </div>
        <div className={styles.overviewItem}>
          <div className={styles.overviewLabel}>数据对象</div>
          <div className={styles.overviewValue}>{data.data_objects?.length ?? 0} 个</div>
        </div>
        <div className={styles.overviewItem}>
          <div className={styles.overviewLabel}>核心指标</div>
          <div className={styles.overviewValue}>{data.metrics?.length ?? 0} 个</div>
        </div>
      </div>

      {/* 分析目标 */}
      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>分析目标</h3>
        <div className={styles.goalGrid}>
          {data.analysis_goals?.map((g) => (
            <div key={g.id} className={styles.goalCard}>
              <div className={styles.goalHead}>
                <span className={styles.goalId}>{g.id}</span>
                <span className={styles.goalTitle}>{g.title}</span>
                <span className={`${styles.priorityBadge} ${styles[`p_${g.priority}`]}`}>
                  {PRIORITY_LABEL[g.priority] || g.priority}
                </span>
              </div>
              <div className={styles.goalDesc}>{g.description}</div>
              {g.related_metrics && g.related_metrics.length > 0 && (
                <div className={styles.tagRow}>
                  {g.related_metrics.map((m) => (
                    <span key={m} className={styles.tag}>{m}</span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* 数据对象 */}
      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>数据对象识别</h3>
        <div className={styles.objGrid}>
          {data.data_objects?.map((o) => (
            <div key={o.alias} className={styles.objCard}>
              <div className={styles.objName}>
                {o.name} <span className={styles.objAlias}>{o.alias}</span>
              </div>
              <div className={styles.objMeta}>
                <span className={styles.objMetaLabel}>对应表：</span>
                {o.hint_tables.map((t) => (
                  <span key={t} className={styles.tableTag}>{t}</span>
                ))}
              </div>
              <div className={styles.objMeta}>
                <span className={styles.objMetaLabel}>关键字段：</span>
                {o.key_attributes.slice(0, 6).map((a) => (
                  <span key={a} className={styles.tag}>{a}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 指标 */}
      <section className={styles.section}>
        <h3 className={styles.sectionTitle}>核心指标清单</h3>
        <div className={styles.metricsTable}>
          <div className={styles.metricsHead}>
            <span>指标</span>
            <span>分类</span>
            <span>计算口径</span>
          </div>
          {data.metrics?.map((m) => (
            <div key={m.name} className={styles.metricsRow}>
              <span className={styles.metricName}>{m.name}</span>
              <span className={`${styles.tag} ${styles.tagPrimary}`}>{m.category}</span>
              <span className={styles.metricDef}>{m.definition}</span>
            </div>
          ))}
        </div>
      </section>

      {/* AI 追问 */}
      {data.ai_questions && data.ai_questions.length > 0 && (
        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>AI 追问 · 需进一步澄清</h3>
          <ul className={styles.questionList}>
            {data.ai_questions.map((q, i) => (
              <li key={i} className={styles.questionItem}>{q}</li>
            ))}
          </ul>
        </section>
      )}

      {/* 关注点 */}
      {data.focus_areas && data.focus_areas.length > 0 && (
        <section className={styles.section}>
          <h3 className={styles.sectionTitle}>特别关注</h3>
          <div className={styles.tagRow}>
            {data.focus_areas.map((f) => (
              <span key={f} className={`${styles.tag} ${styles.tagAccent}`}>{f}</span>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
