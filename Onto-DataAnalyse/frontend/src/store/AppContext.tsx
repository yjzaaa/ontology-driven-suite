import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { apiClient } from '../api/client';
import type { ApiResponse, HealthInfo, Stage } from '../types/api';

interface AppState {
  projectId: string;
  currentStage: Stage;
  health: HealthInfo | null;
  setCurrentStage: (s: Stage) => void;
  refreshHealth: () => Promise<void>;
}

const AppContext = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [currentStage, setCurrentStage] = useState<Stage>(1);
  const [health, setHealth] = useState<HealthInfo | null>(null);

  const refreshHealth = useCallback(async () => {
    try {
      const { data } = await apiClient.get<ApiResponse<HealthInfo>>('/system/health');
      if (data.success && data.data) {
        setHealth(data.data);
      }
    } catch (err) {
      // 后端未启动也允许前端展示
      console.warn('健康检查失败:', err);
    }
  }, []);

  useEffect(() => {
    refreshHealth();
  }, [refreshHealth]);

  const value = useMemo<AppState>(
    () => ({
      projectId: health?.project_id ?? 'default',
      currentStage,
      health,
      setCurrentStage,
      refreshHealth,
    }),
    [currentStage, health, refreshHealth],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp(): AppState {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp 必须在 AppProvider 内使用');
  return ctx;
}
