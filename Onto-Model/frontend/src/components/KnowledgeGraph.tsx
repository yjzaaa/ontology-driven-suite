import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { GraphData, GraphNode, GraphEdge } from '../services/graphBuilder';

interface KnowledgeGraphProps {
  graphData: GraphData;
}

const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({ graphData }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [activeFilter, setActiveFilter] = useState<string>('all');
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });
  const transformRef = useRef(transform);
  transformRef.current = transform;
  const drawRef = useRef<() => void>(() => {});
  const fitRef = useRef<() => void>(() => {});
  const fitDoneRef = useRef(false);
  const simulationRef = useRef<any>(null);

  const DARK = window.matchMedia('(prefers-color-scheme: dark)').matches;

  const COLORS = {
    entity_core: DARK ? '#8B7FE8' : '#5B4FBB',
    entity_support: DARK ? '#5DC9A8' : '#3B9A80',
    behavior: DARK ? '#F4A06A' : '#CB6A2A',
    rule: DARK ? '#F0C060' : '#BA7517',
    scenario: DARK ? '#6AAEE8' : '#3B78C0',
    event: DARK ? '#5DC9A8' : '#3B9A80',
    actor: DARK ? '#D98CE8' : '#9A4FB3',
    role: DARK ? '#C7A5F5' : '#7A5FB8',
    permission: DARK ? '#F08A8A' : '#C24A4A',
    flow: DARK ? '#8AC7F0' : '#2E86C1',
    report: DARK ? '#A8D5A2' : '#4C8C4A',
    ui: DARK ? '#F2C94C' : '#B8860B',
    compensation: DARK ? '#F08A8A' : '#C0392B',
    quality: DARK ? '#B39DDB' : '#7D5BA6',
    metric: DARK ? '#80CBC4' : '#00897B',
  };

  const EDGE_COLORS: Record<string, string> = {
    composition: '#D05538',
    aggregation: '#CB6A2A',
    association: '#8B87B0',
    event: '#5DC9A8',
    applies_rule: '#F0C060',
    authorization: '#9A4FB3',
    triggers: '#6AAEE8',
    default: DARK ? '#555' : '#ccc',
  };

  useEffect(() => {
    if (!containerRef.current || !canvasRef.current || !graphData.nodes.length) return;

    const container = containerRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let W = container.offsetWidth;
    let H = container.offsetHeight;
    canvas.width = W * devicePixelRatio;
    canvas.height = H * devicePixelRatio;
    ctx.scale(devicePixelRatio, devicePixelRatio);

    interface SimNode extends GraphNode {
      x: number;
      y: number;
      fx?: number | null;
      fy?: number | null;
    }

    const nodes: SimNode[] = graphData.nodes.map(n => ({ ...n, x: W / 2, y: H / 2 }));
    const nodeMap: Record<string, SimNode> = {};
    nodes.forEach(n => nodeMap[n.id] = n);

    const linkData = graphData.edges
      .filter(e => nodeMap[e.s] && nodeMap[e.t])
      .map(e => ({
        source: e.s,
        target: e.t,
        type: e.type,
        label: e.label,
        dash: e.dash
      }));

    const isVisible = (n: GraphNode) => {
      if (activeFilter === 'all') return true;
      return n.cat === activeFilter;
    };

    const edgeVisible = (e: any) => {
      if (activeFilter === 'all') return true;
      const src = nodeMap[typeof e.source === 'string' ? e.source : e.source.id];
      const tgt = nodeMap[typeof e.target === 'string' ? e.target : e.target.id];
      return (src && isVisible(src)) || (tgt && isVisible(tgt));
    };

    const nodeAlpha = (n: GraphNode) => {
      if (activeFilter === 'all') return 1;
      return n.cat === activeFilter ? 1 : 0.15;
    };

    const edgeAlpha = (e: any) => {
      if (activeFilter === 'all') return 0.6;
      const src = nodeMap[typeof e.source === 'string' ? e.source : e.source.id];
      const tgt = nodeMap[typeof e.target === 'string' ? e.target : e.target.id];
      const sv = src && src.cat === activeFilter;
      const tv = tgt && tgt.cat === activeFilter;
      if (sv || tv) return 0.7;
      return 0.05;
    };

    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      ctx.save();
      ctx.translate(transformRef.current.x, transformRef.current.y);
      ctx.scale(transformRef.current.k, transformRef.current.k);

      // Draw edges
      linkData.forEach(e => {
        if (!edgeVisible(e)) return;
        const source = typeof e.source === 'string' ? nodeMap[e.source] : e.source;
        const target = typeof e.target === 'string' ? nodeMap[e.target] : e.target;
        if (!source || !target) return;

        const sx = source.x, sy = source.y;
        const tx = target.x, ty = target.y;
        const dx = tx - sx, dy = ty - sy;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const ux = dx / dist, uy = dy / dist;
        const x1 = sx + ux * source.r;
        const y1 = sy + uy * source.r;
        const x2 = tx - ux * (target.r + 8);
        const y2 = ty - uy * (target.r + 8);

        const col = EDGE_COLORS[e.type] || EDGE_COLORS.default;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        const mx = (x1 + x2) / 2 - dy * 0.08, my = (y1 + y2) / 2 + dx * 0.08;
        ctx.quadraticCurveTo(mx, my, x2, y2);
        ctx.strokeStyle = col;
        ctx.lineWidth = e.type === 'composition' ? 1.5 : 0.8;
        ctx.globalAlpha = edgeAlpha(e);
        if (e.dash) ctx.setLineDash([4, 3]);
        else ctx.setLineDash([]);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.globalAlpha = 1;

        // Arrowhead
        const angle = Math.atan2(y2 - my, x2 - mx);
        ctx.save();
        ctx.translate(x2, y2);
        ctx.rotate(angle);
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(-7, -4);
        ctx.lineTo(-7, 4);
        ctx.closePath();
        ctx.fillStyle = col;
        ctx.globalAlpha = edgeAlpha(e);
        ctx.fill();
        ctx.restore();
        ctx.globalAlpha = 1;
      });

      // Draw nodes
      nodes.forEach(n => {
        const alpha = nodeAlpha(n);
        ctx.globalAlpha = alpha;
        const col = COLORS[n.sub as keyof typeof COLORS] || COLORS.entity_core;

        if (n.sub === 'entity_core') {
          ctx.beginPath();
          ctx.arc(n.x, n.y, n.r + 5, 0, Math.PI * 2);
          ctx.strokeStyle = col;
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = col;
        ctx.fill();
        ctx.strokeStyle = DARK ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.12)';
        ctx.lineWidth = 0.5;
        ctx.stroke();

        ctx.fillStyle = '#fff';
        const fontSize = n.r > 20 ? 12 : n.r > 15 ? 11 : 10;
        ctx.font = `500 ${fontSize}px sans-serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const maxW = n.r * 1.7;
        if (ctx.measureText(n.label).width <= maxW) {
          ctx.fillText(n.label, n.x, n.y);
        } else {
          const half = Math.ceil(n.label.length / 2);
          const line1 = n.label.slice(0, half);
          const line2 = n.label.slice(half);
          ctx.fillText(line1, n.x, n.y - 7);
          ctx.fillText(line2, n.x, n.y + 7);
        }
        ctx.globalAlpha = 1;
      });

      ctx.restore();
    };

    const viewBase = Math.min(W, H);
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(linkData).id((d: any) => d.id).distance((d: any) => {
        // 理想边距随画布短边等比缩放（响应式，非固定 px）
        if (d.type === 'composition' || d.type === 'aggregation') return viewBase * 0.12;
        if (d.type === 'event') return viewBase * 0.10;
        if (d.type === 'triggers') return viewBase * 0.13;
        return viewBase * 0.15;
      }).strength((d: any) => {
        if (d.type === 'composition') return 0.9;
        if (d.type === 'aggregation') return 0.7;
        if (d.type === 'applies_rule') return 0.3;
        return 0.5;
      }))
      .force('charge', d3.forceManyBody().strength((d: any) => -viewBase * 0.5 - d.r * 5))
      .force('center', d3.forceCenter(W / 2, H / 2).strength(0.05))
      .force('collision', d3.forceCollide((d: any) => d.r + Math.max(6, viewBase * 0.012)))
      .force('x', d3.forceX(W / 2).strength(0.04))
      .force('y', d3.forceY(H / 2).strength(0.04))
      .alphaDecay(0.02)
      .on('tick', draw);

    simulationRef.current = simulation;

    // 自适应视口：布局稳定后按节点包围盒自动缩放/平移，让图填满画布（数据驱动，不针对具体工作区写死）
    fitDoneRef.current = false;
    const fit = () => {
      if (!nodes.length) return;
      // 边距随画布尺寸等比缩放（响应式，非固定 px）
      const pad = Math.min(W, H) * 0.06;
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      nodes.forEach((n) => {
        if (n.x < minX) minX = n.x;
        if (n.y < minY) minY = n.y;
        if (n.x > maxX) maxX = n.x;
        if (n.y > maxY) maxY = n.y;
      });
      const bw = Math.max(maxX - minX, 1);
      const bh = Math.max(maxY - minY, 1);
      // 缩放上限由数据推导：保证最大节点直径不超过画布短边的 1/4（数据驱动，非固定值）
      const maxNodeR = nodes.reduce((m, n) => Math.max(m, n.r), 0) || 1;
      const kMax = Math.max(Math.min(W, H) / (maxNodeR * 4), 0.1);
      const kk = Math.min((W - pad * 2) / bw, (H - pad * 2) / bh, kMax);
      const cx = (minX + maxX) / 2;
      const cy = (minY + maxY) / 2;
      const next = { x: W / 2 - cx * kk, y: H / 2 - cy * kk, k: kk };
      setTransform(next);
      transformRef.current = next;
      drawRef.current();
    };
    fitRef.current = fit;

    simulation.on('tick', () => {
      draw();
      // 布局接近稳定后执行一次自适应视图
      if (!fitDoneRef.current && simulation.alpha() < 0.03) {
        fitDoneRef.current = true;
        fit();
      }
    });

    // Interaction
    let dragging: SimNode | null = null;
    let dragOffX = 0, dragOffY = 0;
    let panStart: any = null;

    const screenToWorld = (px: number, py: number) => {
      const t = transformRef.current;
      return {
        x: (px - t.x) / t.k,
        y: (py - t.y) / t.k,
      };
    };

    const hitNode = (wx: number, wy: number): SimNode | null => {
      let best: SimNode | null = null;
      let bestDist = Infinity;
      nodes.forEach(n => {
        const d = Math.hypot(n.x - wx, n.y - wy);
        if (d < n.r + 4 && d < bestDist) {
          bestDist = d;
          best = n;
        }
      });
      return best;
    };

    const handleMouseDown = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const px = e.clientX - rect.left;
      const py = e.clientY - rect.top;
      const w = screenToWorld(px, py);
      const hit = hitNode(w.x, w.y);
      if (hit) {
        dragging = hit;
        dragOffX = w.x - hit.x;
        dragOffY = w.y - hit.y;
        hit.fx = hit.x;
        hit.fy = hit.y;
        simulation.alphaTarget(0.3).restart();
      } else {
        panStart = { x: e.clientX - transformRef.current.x, y: e.clientY - transformRef.current.y };
      }
    };

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const px = e.clientX - rect.left;
      const py = e.clientY - rect.top;
      const w = screenToWorld(px, py);

      if (dragging) {
        dragging.fx = w.x - dragOffX;
        dragging.fy = w.y - dragOffY;
        return;
      }
      if (panStart) {
        const t = transformRef.current;
        const next = { x: e.clientX - panStart.x, y: e.clientY - panStart.y, k: t.k };
        setTransform(next);
        transformRef.current = next;
        drawRef.current();
        return;
      }
      const hit = hitNode(w.x, w.y);
      canvas.style.cursor = hit ? 'pointer' : 'default';
    };

    const handleMouseUp = () => {
      if (dragging) {
        dragging.fx = null;
        dragging.fy = null;
        dragging = null;
        simulation.alphaTarget(0);
      }
      panStart = null;
    };

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const px = e.clientX - rect.left;
      const py = e.clientY - rect.top;
      const t = transformRef.current;
      const delta = e.deltaY > 0 ? 0.85 : 1.18;
      const newK = Math.max(0.3, Math.min(4, t.k * delta));
      const next = {
        x: px - (px - t.x) * (newK / t.k),
        y: py - (py - t.y) * (newK / t.k),
        k: newK
      };
      setTransform(next);
      transformRef.current = next;
      drawRef.current();
    };

    canvas.addEventListener('mousedown', handleMouseDown);
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseup', handleMouseUp);
    canvas.addEventListener('mouseleave', handleMouseUp);
    canvas.addEventListener('wheel', handleWheel, { passive: false });

    const resizeObserver = new ResizeObserver(() => {
      W = container.offsetWidth;
      H = container.offsetHeight;
      canvas.width = W * devicePixelRatio;
      canvas.height = H * devicePixelRatio;
      ctx.scale(devicePixelRatio, devicePixelRatio);
      simulation.force('center', d3.forceCenter(W / 2, H / 2));
      simulation.force('x', d3.forceX(W / 2).strength(0.04));
      simulation.force('y', d3.forceY(H / 2).strength(0.04));
      draw();
    });
    resizeObserver.observe(container);

    drawRef.current = draw;

    return () => {
      canvas.removeEventListener('mousedown', handleMouseDown);
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('mouseup', handleMouseUp);
      canvas.removeEventListener('mouseleave', handleMouseUp);
      canvas.removeEventListener('wheel', handleWheel);
      resizeObserver.disconnect();
      simulation.stop();
    };
  }, [graphData, activeFilter]);

  // transform 变化时仅重绘（缩放/平移），不重建力导向模拟，避免布局闪跳
  useEffect(() => {
    drawRef.current();
  }, [transform]);

  const handleReset = () => {
    // 重置 = 重新布局 + 自动适配视口
    fitDoneRef.current = false;
    if (simulationRef.current) {
      simulationRef.current.alpha(0.5).restart();
    }
    fitRef.current();
  };

  return (
    <div ref={containerRef} style={{ width: '100%', height: '100%', position: 'relative' }}>
      <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block' }} />
      
      {/* Legend */}
      <div style={{
        position: 'absolute', top: 12, left: 12,
        background: '#fff', border: '0.5px solid #d9d9d9',
        borderRadius: 8, padding: '10px 14px', fontSize: 12
      }}>
        <div style={{ fontWeight: 500, marginBottom: 6 }}>图例</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '4px 0' }}>
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: COLORS.entity_core }} />
          <span>核心对象</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '4px 0' }}>
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: COLORS.entity_support }} />
          <span>支撑域对象</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '4px 0' }}>
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: COLORS.behavior }} />
          <span>行为</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '4px 0' }}>
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: COLORS.rule }} />
          <span>规则</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '4px 0' }}>
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: COLORS.event }} />
          <span>事件</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '4px 0' }}>
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: COLORS.scenario }} />
          <span>场景/流程</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, margin: '4px 0' }}>
          <div style={{ width: 12, height: 12, borderRadius: '50%', background: COLORS.actor }} />
          <span>主体</span>
        </div>
      </div>

      {/* Filter buttons */}
      <div style={{
        position: 'absolute', top: 12, right: 12,
        display: 'flex', gap: 6, flexWrap: 'wrap',
        justifyContent: 'flex-end', maxWidth: 340
      }}>
        {[
          { key: 'all', label: '全部' },
          { key: 'entity', label: '对象' },
          { key: 'behavior', label: '行为' },
          { key: 'rule', label: '规则' },
          { key: 'event', label: '事件' },
          { key: 'scenario', label: '场景' },
          { key: 'actor', label: '主体' },
          { key: 'flow', label: '流程' },
          { key: 'report', label: '报表' },
          { key: 'ui', label: '界面' },
          { key: 'metric', label: '度量' }
        ].map(filter => (
          <button
            key={filter.key}
            onClick={() => setActiveFilter(filter.key)}
            style={{
              background: activeFilter === filter.key ? '#f0f0f0' : '#fff',
              border: '0.5px solid #d9d9d9',
              borderRadius: 20,
              padding: '4px 10px',
              fontSize: 11,
              cursor: 'pointer',
              color: activeFilter === filter.key ? '#000' : '#666'
            }}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {/* Controls */}
      <div style={{
        position: 'absolute', bottom: 12, right: 12,
        display: 'flex', gap: 6
      }}>
        <button
          onClick={handleReset}
          style={{
            background: '#fff',
            border: '0.5px solid #d9d9d9',
            borderRadius: 8,
            padding: '5px 10px',
            fontSize: 12,
            cursor: 'pointer'
          }}
        >
          重置视图
        </button>
      </div>
    </div>
  );
};

export default KnowledgeGraph;
