import { Link } from 'react-router-dom';
import styles from './StageHint.module.css';

interface Props {
  message: string;
  linkTo?: string;
  linkText?: string;
  type?: 'info' | 'warn';
}

/**
 * 阶段衔接提示条：用于在用户跳过前置阶段时给出温和提示
 */
export default function StageHint({ message, linkTo, linkText, type = 'info' }: Props) {
  return (
    <div className={`${styles.hint} ${styles[type]}`}>
      <span className={styles.icon}>{type === 'warn' ? '⚠' : 'ℹ'}</span>
      <span className={styles.text}>{message}</span>
      {linkTo && linkText && (
        <Link to={linkTo} className={styles.link}>
          {linkText} →
        </Link>
      )}
    </div>
  );
}
