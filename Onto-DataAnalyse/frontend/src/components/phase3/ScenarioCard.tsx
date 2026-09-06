import type { ScenarioSummary } from '../../types/scenario';
import styles from './ScenarioCard.module.css';

interface Props {
  scenario: ScenarioSummary;
  active?: boolean;
  onSelect: (id: string) => void;
  disabled?: boolean;
}

export default function ScenarioCard({ scenario, active, onSelect, disabled }: Props) {
  return (
    <div
      className={`${styles.card} ${active ? styles.active : ''} ${disabled ? styles.disabled : ''}`}
      onClick={() => !disabled && onSelect(scenario.id)}
    >
      <div className={styles.icon}>{scenario.icon}</div>
      <div className={styles.title}>{scenario.name}</div>
      <div className={styles.desc}>{scenario.description}</div>
      <div className={styles.metaRow}>
        <span className={styles.metaTag}>{scenario.step_count} 步</span>
        <span className={styles.metaTag}>{scenario.key_metrics.length} 指标</span>
      </div>
      <div className={styles.triggers}>
        触发词：{scenario.triggers.slice(0, 3).map((t, i) => (
          <code key={t} className={styles.trigger}>{t}{i < Math.min(scenario.triggers.length, 3) - 1 ? '' : ''}</code>
        ))}
      </div>
      <button
        type="button"
        className={`btn-primary ${styles.btn}`}
        disabled={disabled}
        onClick={(e) => {
          e.stopPropagation();
          if (!disabled) onSelect(scenario.id);
        }}
      >
        {active ? '执行中...' : '执行此场景'}
      </button>
    </div>
  );
}
