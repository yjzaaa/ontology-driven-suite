import { useEffect, useRef } from 'react';
import * as echarts from 'echarts/core';
import { LineChart, BarChart, PieChart, ScatterChart, HeatmapChart } from 'echarts/charts';
import {
  GridComponent, TooltipComponent, LegendComponent, TitleComponent,
  DataZoomComponent, MarkLineComponent, MarkAreaComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([
  LineChart, BarChart, PieChart, ScatterChart, HeatmapChart,
  GridComponent, TooltipComponent, LegendComponent, TitleComponent,
  DataZoomComponent, MarkLineComponent, MarkAreaComponent,
  CanvasRenderer,
]);

// 全局咨询公司风格主题（麦肯锡蓝系）
const REPORT_THEME = {
  color: ['#1E3A5F', '#2E6DB4', '#5BA3D9', '#A8CDF0', '#E8623A', '#27A86A', '#8C9BAB', '#FBBF24'],
  backgroundColor: 'transparent',
  textStyle: { fontFamily: 'system-ui, -apple-system, sans-serif', color: '#1A202C', fontSize: 12 },
  title: { textStyle: { fontSize: 14, fontWeight: 600, color: '#1B3A6B' } },
  legend: { textStyle: { color: '#4A5568', fontSize: 11 }, itemWidth: 12, itemHeight: 12 },
  grid: { containLabel: true, top: 50, right: 30, bottom: 40, left: 30 },
  xAxis: {
    axisLine: { lineStyle: { color: '#CBD5E0' } },
    axisLabel: { color: '#4A5568' },
    splitLine: { show: false },
  },
  yAxis: {
    axisLine: { show: false },
    axisLabel: { color: '#4A5568' },
    splitLine: { lineStyle: { color: '#E2E8F0', type: 'dashed' } },
  },
  tooltip: {
    backgroundColor: 'rgba(26, 32, 44, 0.94)',
    borderWidth: 0,
    textStyle: { color: '#FFFFFF', fontSize: 12 },
    extraCssText: 'box-shadow: 0 4px 12px rgba(0,0,0,0.2);',
  },
};

interface Props {
  option: any;
  height?: number;
  className?: string;
  onChartReady?: (chart: any) => void;
}

export default function EChartsWrapper({ option, height = 320, className, onChartReady }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = echarts.init(containerRef.current, undefined, { renderer: 'canvas' });
    chartRef.current = chart;
    if (onChartReady) onChartReady(chart);
    const resize = () => chart.resize();
    window.addEventListener('resize', resize);
    return () => {
      window.removeEventListener('resize', resize);
      chart.dispose();
      chartRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (!chartRef.current || !option) return;
    // 合并主题
    const merged = {
      ...REPORT_THEME,
      ...option,
      color: option.color || REPORT_THEME.color,
      grid: { ...REPORT_THEME.grid, ...(option.grid || {}) },
      xAxis: Array.isArray(option.xAxis)
        ? option.xAxis.map((x: any) => ({ ...REPORT_THEME.xAxis, ...x }))
        : (option.xAxis ? { ...REPORT_THEME.xAxis, ...option.xAxis } : undefined),
      yAxis: Array.isArray(option.yAxis)
        ? option.yAxis.map((y: any) => ({ ...REPORT_THEME.yAxis, ...y }))
        : (option.yAxis ? { ...REPORT_THEME.yAxis, ...option.yAxis } : undefined),
      tooltip: { ...REPORT_THEME.tooltip, ...(option.tooltip || {}) },
    };
    chartRef.current.setOption(merged, true);
  }, [option]);

  return <div ref={containerRef} className={className} style={{ width: '100%', height }} />;
}
