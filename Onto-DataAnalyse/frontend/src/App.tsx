import { Suspense, lazy } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';

// 路由级代码分割：每个阶段单独 chunk
const Phase1Page = lazy(() => import('./pages/Phase1Page'));
const Phase2Page = lazy(() => import('./pages/Phase2Page'));
const Phase3Page = lazy(() => import('./pages/Phase3Page'));
const Phase4Page = lazy(() => import('./pages/Phase4Page'));

function PageLoading() {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      height: 'calc(100vh - 110px)', color: 'var(--text-muted)',
      fontSize: 13,
    }}>
      <span style={{
        display: 'inline-block', width: 12, height: 12, borderRadius: '50%',
        background: 'var(--color-accent)', marginRight: 8,
        animation: 'pulse 1s ease-in-out infinite',
      }} />
      加载中...
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<MainLayout />}>
        <Route index element={<Navigate to="/phase1" replace />} />
        <Route path="phase1" element={
          <Suspense fallback={<PageLoading />}><Phase1Page /></Suspense>
        } />
        <Route path="phase2" element={
          <Suspense fallback={<PageLoading />}><Phase2Page /></Suspense>
        } />
        <Route path="phase3" element={
          <Suspense fallback={<PageLoading />}><Phase3Page /></Suspense>
        } />
        <Route path="phase4" element={
          <Suspense fallback={<PageLoading />}><Phase4Page /></Suspense>
        } />
      </Route>
    </Routes>
  );
}
