/**
 * 把场景报告中 AI 给出的 chart 配置 + SQL 数据，构建成 ECharts option。
 *
 * Chart 配置形如：
 *   {type:'line', title:'GMV 月度趋势', x_field:'period', y_field:'gmv', data_step:'S1'}
 */

export interface ChartHint {
  type?: string;
  title?: string;
  x_field?: string;
  y_field?: string;
  data_step?: string;
  series_field?: string;     // 分组字段（多 series）
  note?: string;
}

const PALETTE = ['#1E3A5F', '#2E6DB4', '#5BA3D9', '#A8CDF0', '#E8623A', '#27A86A', '#FBBF24'];

export function buildEChartsOption(
  hint: ChartHint,
  rows: Record<string, any>[],
): any | null {
  if (!rows || rows.length === 0) return null;
  const xField = hint.x_field ?? Object.keys(rows[0])[0];
  const yField = hint.y_field ?? Object.keys(rows[0])[1];
  const type = (hint.type ?? 'line').toLowerCase();

  // 多 series 情况（按 series_field 分组）
  if (hint.series_field) {
    const groups = new Map<string, Record<string, any>[]>();
    const xs = new Set<string>();
    for (const r of rows) {
      const sk = String(r[hint.series_field]);
      if (!groups.has(sk)) groups.set(sk, []);
      groups.get(sk)!.push(r);
      xs.add(String(r[xField]));
    }
    const xArr = Array.from(xs).sort();
    const seriesArr = Array.from(groups.entries()).map(([name, items], i) => ({
      name,
      type: type === 'pie' ? 'bar' : type,
      smooth: type === 'line',
      symbolSize: 6,
      itemStyle: { color: PALETTE[i % PALETTE.length] },
      data: xArr.map((x) => {
        const r = items.find((rr) => String(rr[xField]) === x);
        return r ? Number(r[yField]) : null;
      }),
    }));
    return {
      title: hint.title ? { text: hint.title, left: 'left' } : undefined,
      legend: { data: Array.from(groups.keys()), top: hint.title ? 30 : 8 },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: xArr, boundaryGap: type === 'bar' },
      yAxis: { type: 'value' },
      series: seriesArr,
    };
  }

  // 饼图
  if (type === 'pie') {
    return {
      title: hint.title ? { text: hint.title, left: 'left' } : undefined,
      tooltip: { trigger: 'item', formatter: '{a}<br>{b}: {c} ({d}%)' },
      legend: { orient: 'vertical', right: 8, top: 'middle', textStyle: { fontSize: 11 } },
      series: [{
        name: hint.title || '占比',
        type: 'pie',
        radius: ['38%', '68%'],
        center: ['40%', '52%'],
        label: { fontSize: 11 },
        data: rows.map((r) => ({ name: String(r[xField]), value: Number(r[yField]) })),
      }],
    };
  }

  // 单 series（line / bar / scatter）
  const x = rows.map((r) => String(r[xField]));
  const y = rows.map((r) => Number(r[yField]));
  return {
    title: hint.title ? { text: hint.title, left: 'left' } : undefined,
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: x, boundaryGap: type === 'bar' },
    yAxis: { type: 'value' },
    series: [{
      name: hint.y_field,
      type,
      smooth: type === 'line',
      symbolSize: 6,
      itemStyle: { color: PALETTE[0] },
      areaStyle: type === 'line' ? { color: 'rgba(46,109,180,0.08)' } : undefined,
      data: y,
    }],
  };
}

/**
 * 从 stat_steps 的 mom_yoy 输出生成趋势图配置
 */
export function buildMomYoyChart(stats: any, title = '趋势分析'): any | null {
  const series = stats?.series;
  if (!series || series.length === 0) return null;
  const x = series.map((s: any) => s.period);
  return {
    title: { text: title, left: 'left' },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any[]) => {
        const items = params.map((p) => {
          const v = (p.value ?? 0).toLocaleString();
          return `${p.marker} ${p.seriesName}: <b>${v}</b>`;
        }).join('<br>');
        return `${params[0]?.axisValue}<br>${items}`;
      },
    },
    legend: { data: ['值', '环比变化'], top: 28 },
    grid: { top: 70, right: 60, bottom: 30, left: 50 },
    xAxis: { type: 'category', data: x },
    yAxis: [
      { type: 'value', name: '值', position: 'left' },
      { type: 'value', name: '环比 %', position: 'right', axisLabel: { formatter: '{value}%' } },
    ],
    series: [
      {
        name: '值', type: 'line', smooth: true, symbolSize: 6,
        itemStyle: { color: '#2E6DB4' },
        areaStyle: { color: 'rgba(46,109,180,0.10)' },
        data: series.map((s: any) => s.value),
      },
      {
        name: '环比变化', type: 'bar', yAxisIndex: 1, barWidth: 12,
        itemStyle: {
          color: (p: any) => (p.value ?? 0) >= 0 ? '#27A86A' : '#E8623A',
        },
        data: series.map((s: any) => s.mom_pct),
      },
    ],
  };
}

/**
 * 自动从 sql_steps 推断"需要图表化"的步骤，并生成默认图表
 */
export function inferAutoCharts(sqlSteps: any[]): { hint: ChartHint; rows: any[] }[] {
  const out: { hint: ChartHint; rows: any[] }[] = [];
  for (const step of sqlSteps) {
    const rows = step.rows_preview ?? [];
    if (rows.length < 2) continue;
    const cols = step.columns ?? Object.keys(rows[0] ?? {});
    if (cols.length < 2) continue;
    // 启发：第一列像 period（YYYY-MM）→ 折线；含两个分类列 → 堆叠柱图
    const firstCol = cols[0];
    const isPeriod = /period|month|date|day|week/i.test(firstCol);
    const numericCols = cols.slice(1).filter((c: string) =>
      rows.some((r: any) => typeof r[c] === 'number'),
    );
    if (numericCols.length === 0) continue;
    out.push({
      hint: {
        type: isPeriod ? 'line' : 'bar',
        title: step.description ?? step.step_id,
        x_field: firstCol,
        y_field: numericCols[0],
        data_step: step.step_id,
      },
      rows,
    });
  }
  return out;
}
