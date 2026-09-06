/**
 * 把一个 React 渲染出来的报告 DOM 子树导出为独立 HTML 文件
 *
 * 三大关键步骤：
 *  1. 深克隆目标 DOM
 *  2. 把 ECharts canvas 替换为 PNG dataURL 内嵌 <img>
 *  3. 收集 document 中所有相关 CSS 规则并内联进 <style>
 *
 * 输出的 HTML 自包含、可独立打开、保留全部样式与图表。
 */
import * as echarts from 'echarts/core';

export interface ExportOptions {
  title: string;
  filename?: string;
  /** 可选：报告头部的元信息（生成时间、场景名等） */
  subtitle?: string;
}

export async function exportReportToHtml(
  rootEl: HTMLElement,
  options: ExportOptions,
): Promise<void> {
  // 等待一帧确保最新渲染已完成
  await new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));

  // 1. 把所有 ECharts 实例转 PNG（在克隆之前先拿到 dataURL，因为克隆后 echarts instance 会丢失关联）
  const echartsContainers = Array.from(rootEl.querySelectorAll<HTMLElement>('[_echarts_instance_]'));
  const echartsDataUrls = new Map<number, { dataUrl: string; width: number; height: number }>();
  echartsContainers.forEach((el, idx) => {
    try {
      const instance = echarts.getInstanceByDom(el);
      if (!instance) return;
      const dataUrl = instance.getDataURL({
        type: 'png',
        pixelRatio: 2,
        backgroundColor: '#ffffff',
      });
      const rect = el.getBoundingClientRect();
      echartsDataUrls.set(idx, {
        dataUrl,
        width: Math.round(rect.width),
        height: Math.round(rect.height),
      });
    } catch (e) {
      console.warn(`导出图表 ${idx} 失败`, e);
    }
  });

  // 2. 克隆 DOM
  const clone = rootEl.cloneNode(true) as HTMLElement;

  // 2.1 移除标记为"导出时隐藏"的元素（如导出按钮本身）
  clone.querySelectorAll('[data-export-hide]').forEach((el) => el.remove());

  // 3. 把克隆里的 ECharts 容器替换为 <img>
  const cloneEchartsContainers = Array.from(clone.querySelectorAll<HTMLElement>('[_echarts_instance_]'));
  cloneEchartsContainers.forEach((el, idx) => {
    const data = echartsDataUrls.get(idx);
    if (!data) return;
    // 清空容器内的 canvas，替换为内嵌图片
    el.innerHTML = `<img src="${data.dataUrl}" style="display:block;width:100%;height:auto;max-width:${data.width}px;" alt="chart" />`;
    el.removeAttribute('_echarts_instance_');
    el.style.height = 'auto';
  });

  // 4. 收集所有 CSS 规则
  const allCss = collectAllStyles();

  // 5. 把所有 <details> 展开（导出后用户看不到交互，先展开方便阅读）
  clone.querySelectorAll('details').forEach((d) => d.setAttribute('open', ''));

  // 6. 组装完整 HTML 文档
  const html = buildStandaloneHtml({
    title: options.title,
    subtitle: options.subtitle,
    bodyHtml: clone.outerHTML,
    css: allCss,
  });

  // 7. 触发下载
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = options.filename ?? `${sanitizeFilename(options.title)}.html`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// ============================================================
// 收集所有 stylesheet 中的 CSS 规则
// 同源（含 link/style/CSS Modules 内联）都能读到 cssRules
// ============================================================
function collectAllStyles(): string {
  const parts: string[] = [];
  const sheets = Array.from(document.styleSheets);
  for (const sheet of sheets) {
    try {
      const rules = Array.from((sheet as CSSStyleSheet).cssRules || []);
      for (const rule of rules) {
        parts.push(rule.cssText);
      }
    } catch (e) {
      // 跨域 stylesheet（不太可能在 dev/build 出现）会抛 SecurityError，跳过
    }
  }
  return parts.join('\n');
}

// ============================================================
// 文件名安全化
// ============================================================
function sanitizeFilename(name: string): string {
  return name
    .replace(/[\\/:*?"<>|]+/g, '_')
    .replace(/\s+/g, '_')
    .substring(0, 120);
}

// ============================================================
// 拼装独立 HTML 文档
// ============================================================
interface BuildHtmlArgs {
  title: string;
  subtitle?: string;
  bodyHtml: string;
  css: string;
}

function buildStandaloneHtml({ title, subtitle, bodyHtml, css }: BuildHtmlArgs): string {
  const safeTitle = escapeHtml(title);
  const safeSubtitle = subtitle ? escapeHtml(subtitle) : '';
  const generatedTime = new Date().toLocaleString('zh-CN', { hour12: false });

  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${safeTitle}</title>
<style>
/* 重置 & 基础排版 */
* { box-sizing: border-box; }
html, body {
  margin: 0;
  padding: 0;
  background: #F4F6F9;
  color: #1A202C;
  font-family: 'Inter', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
  font-size: 14px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
.export-wrapper {
  max-width: 1100px;
  margin: 24px auto;
  padding: 0 16px;
}
.export-banner {
  background: linear-gradient(135deg, #1B3A6B 0%, #2952A3 100%);
  color: #fff;
  padding: 16px 24px;
  border-radius: 8px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(27, 58, 107, 0.18);
}
.export-banner h1 {
  font-size: 18px;
  margin: 0;
  font-weight: 700;
}
.export-banner small {
  font-size: 12px;
  opacity: 0.85;
}
.export-footer {
  margin-top: 24px;
  padding: 16px;
  text-align: center;
  font-size: 12px;
  color: #718096;
  border-top: 1px solid #E2E8F0;
}

/* 全局打印优化 */
@media print {
  body { background: #fff; }
  .export-banner { box-shadow: none; }
}

/* === 应用复制的页面 CSS === */
${css}
</style>
</head>
<body>
<div class="export-wrapper">
  <div class="export-banner">
    <div>
      <h1>${safeTitle}</h1>
      ${safeSubtitle ? `<small>${safeSubtitle}</small>` : ''}
    </div>
    <small>导出于 ${generatedTime}</small>
  </div>
  ${bodyHtml}
  <div class="export-footer">
    本报告由"本体驱动电商数据智能分析系统"导出 · 数据基于本地演示库 · 单文件离线可读
  </div>
</div>
</body>
</html>`;
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}
