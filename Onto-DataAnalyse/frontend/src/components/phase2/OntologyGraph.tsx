import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { GraphEdge, GraphNode, NodeType } from '../../types/graph';
import styles from './OntologyGraph.module.css';

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
  highlightedNodeIds?: string[];   // 最近新增的节点（高亮入场动画）
  onNodeClick?: (node: GraphNode) => void;
  enabledTypes?: Set<NodeType>;    // 过滤器
}

const EDGE_DISTANCE_BY_TYPE: Record<string, number> = {
  composition: 70,
  aggregation: 85,
  association: 110,
  dependency: 100,
  rule_ref: 75,
  metric_dep: 100,
  scenario_call: 95,
  behavior_call: 80,
};

const EDGE_STRENGTH_BY_TYPE: Record<string, number> = {
  composition: 0.85,
  aggregation: 0.65,
  association: 0.4,
  dependency: 0.3,
  rule_ref: 0.5,
  metric_dep: 0.3,
  scenario_call: 0.45,
  behavior_call: 0.55,
};

const CHARGE_BY_TYPE: Record<string, number> = {
  entity: -380,
  scenario: -260,
  behavior: -180,
  rule: -140,
  metric: -130,
};

export default function OntologyGraph({
  nodes, edges, highlightedNodeIds = [], onNodeClick, enabledTypes,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  // 持久化 D3 状态（避免 React rerender 重建）
  const stateRef = useRef<{
    simulation: d3.Simulation<GraphNode, GraphEdge> | null;
    nodes: GraphNode[];
    edges: GraphEdge[];
    g: d3.Selection<SVGGElement, unknown, null, undefined> | null;
    zoom: d3.ZoomBehavior<SVGSVGElement, unknown> | null;
  }>({ simulation: null, nodes: [], edges: [], g: null, zoom: null });

  const [tooltip, setTooltip] = useState<{ x: number; y: number; text: string } | null>(null);
  const [size, setSize] = useState({ w: 800, h: 600 });

  // 监听容器尺寸
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      const rect = entries[0].contentRect;
      setSize({ w: Math.floor(rect.width), h: Math.floor(rect.height) });
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // 初始化 SVG（一次）
  useEffect(() => {
    if (!svgRef.current || stateRef.current.g) return;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // 箭头标记
    const defs = svg.append('defs');
    ['composition', 'aggregation', 'association', 'dependency',
      'rule_ref', 'metric_dep', 'scenario_call', 'behavior_call'].forEach((t) => {
      defs.append('marker')
        .attr('id', `arrow-${t}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 24)
        .attr('refY', 0)
        .attr('markerWidth', 7)
        .attr('markerHeight', 7)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', _edgeColor(t));
    });

    const zoomG = svg.append('g').attr('class', 'zoom-layer');
    zoomG.append('g').attr('class', 'edges');
    zoomG.append('g').attr('class', 'nodes');

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => {
        zoomG.attr('transform', event.transform.toString());
      });
    svg.call(zoom).on('dblclick.zoom', null);   // 禁用双击缩放（让位给节点取消固定）

    stateRef.current.g = zoomG as d3.Selection<SVGGElement, unknown, null, undefined>;
    stateRef.current.zoom = zoom;

    // 初始化 simulation
    const sim = d3.forceSimulation<GraphNode>([])
      .force('link', d3.forceLink<GraphNode, GraphEdge>([])
        .id((d) => d.id)
        .distance((d) => EDGE_DISTANCE_BY_TYPE[d.type] ?? 100)
        .strength((d) => EDGE_STRENGTH_BY_TYPE[d.type] ?? 0.4))
      .force('charge', d3.forceManyBody<GraphNode>()
        .strength((d) => CHARGE_BY_TYPE[d.type] ?? -150))
      .force('center', d3.forceCenter(size.w / 2, size.h / 2))
      .force('collide', d3.forceCollide<GraphNode>().radius((d) => (d.radius ?? 18) + 4))
      .alphaDecay(0.03)
      .velocityDecay(0.42)
      .on('tick', () => _tick(stateRef.current));

    stateRef.current.simulation = sim;
  }, [size.w, size.h]);

  // 每当外部 nodes / edges 变化时同步到 simulation
  useEffect(() => {
    const sim = stateRef.current.simulation;
    if (!sim || !stateRef.current.g) return;

    // === 合并新节点（保留已有位置）===
    const existingById = new Map(stateRef.current.nodes.map((n) => [n.id, n]));
    const mergedNodes: GraphNode[] = nodes.map((n) => {
      const old = existingById.get(n.id);
      if (old) {
        return { ...n, x: old.x, y: old.y, vx: old.vx, vy: old.vy, fx: old.fx, fy: old.fy };
      }
      // 新节点：从画布中心附近随机位置入场
      return {
        ...n,
        x: size.w / 2 + (Math.random() - 0.5) * 80,
        y: size.h / 2 + (Math.random() - 0.5) * 80,
      };
    });
    stateRef.current.nodes = mergedNodes;
    stateRef.current.edges = edges.map((e) => ({ ...e }));

    sim.nodes(mergedNodes);
    (sim.force('link') as d3.ForceLink<GraphNode, GraphEdge>).links(stateRef.current.edges);
    sim.alpha(0.6).restart();

    _render(stateRef.current, { highlightedNodeIds, onNodeClick, setTooltip, enabledTypes });
  }, [nodes, edges, highlightedNodeIds, onNodeClick, enabledTypes]);

  // 中心力随尺寸变化
  useEffect(() => {
    const sim = stateRef.current.simulation;
    if (!sim) return;
    sim.force('center', d3.forceCenter(size.w / 2, size.h / 2));
    sim.alpha(0.3).restart();
  }, [size.w, size.h]);

  return (
    <div ref={containerRef} className={styles.container}>
      <svg ref={svgRef} width={size.w} height={size.h} className={styles.svg} />
      {tooltip && (
        <div
          className={styles.tooltip}
          style={{ left: tooltip.x + 12, top: tooltip.y + 12 }}
        >
          {tooltip.text}
        </div>
      )}
    </div>
  );
}

// ============================================================
// 辅助：边颜色查表（用于 marker 定义）
// ============================================================
function _edgeColor(t: string): string {
  switch (t) {
    case 'composition': return '#D05538';
    case 'aggregation': return '#CB6A2A';
    case 'association': return '#5B78C0';
    case 'dependency': return '#888780';
    case 'rule_ref': return '#BA7517';
    case 'metric_dep': return '#3B9A80';
    case 'scenario_call': return '#3B78C0';
    case 'behavior_call': return '#CB6A2A';
    default: return '#888';
  }
}

// ============================================================
// 渲染节点和边（enter/update/exit）
// ============================================================
function _render(
  state: { g: d3.Selection<SVGGElement, unknown, null, undefined> | null; nodes: GraphNode[]; edges: GraphEdge[]; simulation: d3.Simulation<GraphNode, GraphEdge> | null },
  opts: {
    highlightedNodeIds: string[];
    onNodeClick?: (n: GraphNode) => void;
    setTooltip: (t: { x: number; y: number; text: string } | null) => void;
    enabledTypes?: Set<NodeType>;
  }
) {
  if (!state.g || !state.simulation) return;
  const g = state.g;
  const enabled = opts.enabledTypes;

  // === edges ===
  const edgeSel = g.select<SVGGElement>('g.edges').selectAll<SVGLineElement, GraphEdge>('line')
    .data(state.edges, (d) => d.id);

  edgeSel.exit().remove();

  const edgeEnter = edgeSel.enter().append('line')
    .attr('stroke', (d) => d.color)
    .attr('stroke-width', (d) => d.width)
    .attr('stroke-dasharray', (d) => d.dashArray ?? null)
    .attr('opacity', 0)
    .attr('marker-end', (d) => `url(#arrow-${d.type})`);

  edgeEnter.transition().duration(300).attr('opacity', 1);

  edgeSel.merge(edgeEnter)
    .attr('opacity', (d) => _isEdgeEnabled(d, state.nodes, enabled) ? 0.85 : 0.08);

  // === nodes ===
  const nodeSel = g.select<SVGGElement>('g.nodes').selectAll<SVGGElement, GraphNode>('g.node')
    .data(state.nodes, (d) => d.id);

  nodeSel.exit().remove();

  const enter = nodeSel.enter().append('g')
    .attr('class', 'node')
    .style('cursor', 'pointer')
    .on('click', (_e, d) => opts.onNodeClick?.(d))
    .on('mouseover', (event, d) => {
      const sub = d.subtype ? ` · ${d.subtype}` : '';
      opts.setTooltip({
        x: event.clientX,
        y: event.clientY,
        text: `${d.label} (${d.type}${sub})\n${d.description ?? ''}`,
      });
    })
    .on('mouseout', () => opts.setTooltip(null))
    .on('dblclick', (_e, d) => {
      d.fx = null;
      d.fy = null;
      state.simulation?.alpha(0.3).restart();
    })
    .call(_drag(state.simulation));

  // 节点形状：菱形（metric）/ 圆形（其他）
  enter.each(function (d) {
    const sel = d3.select(this);
    if (d.shape === 'diamond') {
      sel.append('path')
        .attr('d', _diamondPath(d.radius))
        .attr('fill', d.color)
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);
    } else {
      sel.append('circle')
        .attr('r', d.radius)
        .attr('fill', d.color)
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);
    }
  });

  enter.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', (d) => d.radius + 14)
    .attr('font-size', 11)
    .attr('font-weight', 600)
    .attr('fill', '#1A202C')
    .attr('pointer-events', 'none')
    .text((d) => d.label.length > 10 ? d.label.slice(0, 9) + '…' : d.label);

  // 入场动画（缩放从 0 到 1）
  enter.attr('transform', (d) => `translate(${d.x},${d.y}) scale(0)`)
    .transition().duration(380).ease(d3.easeBackOut)
    .attr('transform', (d) => `translate(${d.x},${d.y}) scale(1)`);

  // 高亮 ring（最近添加的节点）
  enter.filter((d) => opts.highlightedNodeIds.includes(d.id))
    .append('circle')
    .attr('class', 'highlight-ring')
    .attr('r', (d) => d.radius + 6)
    .attr('fill', 'none')
    .attr('stroke', '#0EA5E9')
    .attr('stroke-width', 2)
    .attr('opacity', 1)
    .transition().duration(1600).attr('opacity', 0).attr('r', (d) => d.radius + 16)
    .remove();

  // 节点过滤（淡出未启用类型）
  nodeSel.merge(enter)
    .style('opacity', (d) => (enabled && !enabled.has(d.type)) ? 0.15 : 1);
}

function _tick(state: { g: d3.Selection<SVGGElement, unknown, null, undefined> | null; nodes: GraphNode[]; edges: GraphEdge[] }) {
  if (!state.g) return;
  state.g.select('g.edges').selectAll<SVGLineElement, GraphEdge>('line')
    .attr('x1', (d) => (d.source as GraphNode).x ?? 0)
    .attr('y1', (d) => (d.source as GraphNode).y ?? 0)
    .attr('x2', (d) => (d.target as GraphNode).x ?? 0)
    .attr('y2', (d) => (d.target as GraphNode).y ?? 0);
  state.g.select('g.nodes').selectAll<SVGGElement, GraphNode>('g.node')
    .attr('transform', (d) => `translate(${d.x ?? 0},${d.y ?? 0})`);
}

function _drag(sim: d3.Simulation<GraphNode, GraphEdge> | null) {
  function started(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) {
    if (!event.active) sim?.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }
  function dragged(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) {
    d.fx = event.x;
    d.fy = event.y;
  }
  function ended(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>, d: GraphNode) {
    if (!event.active) sim?.alphaTarget(0);
    // 拖拽后固定（双击解除）
  }
  return d3.drag<SVGGElement, GraphNode>()
    .on('start', started)
    .on('drag', dragged)
    .on('end', ended);
}

function _diamondPath(r: number): string {
  return `M0,${-r} L${r},0 L0,${r} L${-r},0 Z`;
}

function _isEdgeEnabled(edge: GraphEdge, nodes: GraphNode[], enabled?: Set<NodeType>): boolean {
  if (!enabled) return true;
  const sid = typeof edge.source === 'string' ? edge.source : edge.source.id;
  const tid = typeof edge.target === 'string' ? edge.target : edge.target.id;
  const s = nodes.find((n) => n.id === sid);
  const t = nodes.find((n) => n.id === tid);
  if (!s || !t) return false;
  return enabled.has(s.type) && enabled.has(t.type);
}
