import styles from './ConfidenceBadge.module.css';

interface Props {
  value: number;          // 0-100
  size?: 'sm' | 'md';
  label?: string;
}

export default function ConfidenceBadge({ value, size = 'sm', label = '置信度' }: Props) {
  const cls = value >= 80 ? styles.high : value >= 60 ? styles.mid : styles.low;
  return (
    <span className={`${styles.badge} ${styles[size]} ${cls}`}>
      <span className={styles.dot} />
      {label} {value}%
    </span>
  );
}
