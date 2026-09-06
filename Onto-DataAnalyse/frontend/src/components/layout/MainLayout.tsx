import { Outlet } from 'react-router-dom';
import { useApp } from '../../store/AppContext';
import StageProgress from './StageProgress';
import styles from './MainLayout.module.css';

export default function MainLayout() {
  const { health } = useApp();
  const apiOk = !!health;
  const aiOk = !!health?.deepseek_configured;

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <div className={styles.brand}>
          <div className={styles.logo}>本</div>
          <div className={styles.brandText}>
            <div className={styles.brandTitle}>本体驱动电商数据智能分析</div>
            <div className={styles.brandSub}>Ontology-Driven E-commerce Analytics</div>
          </div>
        </div>
        <StageProgress />
        <div className={styles.status}>
          <span className={`${styles.dot} ${apiOk ? styles.dotOk : styles.dotErr}`} />
          <span>{apiOk ? `后端已连接 · 模型 ${health?.model}` : '后端未连接'}</span>
          {apiOk && !aiOk && (
            <span className={styles.warn}>⚠ DeepSeek API Key 未配置（请填写 .env）</span>
          )}
        </div>
      </header>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}
