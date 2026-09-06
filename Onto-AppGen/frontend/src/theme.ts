/**
 * 设计 token：对应 skills/frontend-design/SKILL.md 第八节。
 * 渲染器经 ConfigProvider theme 应用，让产出界面遵循设计规范（低饱和靛蓝主色、浅色专业风）。
 */

export const themeToken = {
  colorPrimary: '#4F46E5',
  colorInfo: '#4F46E5',
  colorSuccess: '#10B981',
  colorWarning: '#F59E0B',
  colorError: '#EF4444',
  colorTextBase: '#0F172A',
  colorText: '#334155',
  colorTextSecondary: '#64748B',
  colorBgLayout: '#F5F6FA',
  colorBgContainer: '#FFFFFF',
  colorBorder: '#E2E8F0',
  colorBorderSecondary: '#EEF2F7',
  borderRadius: 8,
  fontSize: 14,
  fontFamily: "-apple-system, 'PingFang SC', 'Microsoft YaHei', 'Segoe UI', sans-serif",
} as const

/** 语义状态色（Tag 用），对应设计规范的语义色 */
export const statusColor = {
  success: '#10B981',
  processing: '#3B82F6',
  warning: '#F59E0B',
  error: '#EF4444',
  default: '#64748B',
} as const

/** 组件级覆盖（ConfigProvider components） */
export const themeComponents = {
  Layout: {
    siderBg: '#0F172A',
    headerBg: '#FFFFFF',
  },
  Menu: {
    darkItemBg: '#0F172A',
    darkItemColor: '#94A3B8',
    darkItemSelectedBg: '#4F46E5',
    darkItemSelectedColor: '#FFFFFF',
  },
  Card: {
    borderRadiusLG: 10,
    boxShadowTertiary: '0 1px 2px rgba(15,23,42,.04), 0 4px 12px rgba(15,23,42,.04)',
  },
  Table: {
    headerBg: '#F8FAFC',
    borderColor: '#EEF2F7',
  },
} as const
