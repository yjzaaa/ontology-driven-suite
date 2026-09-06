import type { NodeType } from '../../types/graph';
import styles from './GraphControls.module.css';

interface Props {
  enabledTypes: Set<NodeType>;
  onToggle: (t: NodeType) => void;
  stats?: Record<string, number>;
}

const ALL_TYPES: { key: NodeType; label: string; color: string }[] = [
  { key: 'entity', label: '实体', color: '#5B4FBB' },
  { key: 'behavior', label: '行为', color: '#CB6A2A' },
  { key: 'rule', label: '规则', color: '#BA7517' },
  { key: 'scenario', label: '场景', color: '#3B78C0' },
  { key: 'metric', label: '指标', color: '#3B9A80' },
];

export default function GraphControls({ enabledTypes, onToggle, stats }: Props) {
  return (
    <div className={styles.bar}>
      <span className={styles.label}>显示：</span>
      {ALL_TYPES.map((t) => {
        const active = enabledTypes.has(t.key);
        const count = stats?.[t.key] ?? 0;
        return (
          <button
            key={t.key}
            type="button"
            className={`${styles.chip} ${active ? styles.chipActive : ''}`}
            onClick={() => onToggle(t.key)}
            style={{
              borderColor: active ? t.color : 'var(--border-color)',
              background: active ? `${t.color}15` : 'transparent',
              color: active ? t.color : 'var(--text-muted)',
            }}
          >
            <span className={styles.dot} style={{ background: t.color }} />
            {t.label}
            {count > 0 && <span className={styles.count}>{count}</span>}
          </button>
        );
      })}
    </div>
  );
}
