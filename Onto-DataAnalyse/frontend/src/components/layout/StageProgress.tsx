import { NavLink } from 'react-router-dom';
import styles from './StageProgress.module.css';

const STAGES = [
  { id: 1, key: 'phase1', title: '需求探索', subtitle: '上传文档 · AI 解析' },
  { id: 2, key: 'phase2', title: '本体建模', subtitle: '知识图谱 · 字段映射' },
  { id: 3, key: 'phase3', title: '场景执行', subtitle: '采集 · 统计 · AI 推理' },
  { id: 4, key: 'phase4', title: '对话报告', subtitle: '自然语言 · 可视化报告' },
];

export default function StageProgress() {
  return (
    <ol className={styles.steps}>
      {STAGES.map((s, idx) => (
        <li key={s.id} className={styles.item}>
          <NavLink
            to={`/${s.key}`}
            className={({ isActive }) => `${styles.link} ${isActive ? styles.active : ''}`}
          >
            <span className={styles.index}>{s.id}</span>
            <span className={styles.body}>
              <span className={styles.title}>{s.title}</span>
              <span className={styles.subtitle}>{s.subtitle}</span>
            </span>
          </NavLink>
          {idx < STAGES.length - 1 && <span className={styles.divider} aria-hidden="true" />}
        </li>
      ))}
    </ol>
  );
}
