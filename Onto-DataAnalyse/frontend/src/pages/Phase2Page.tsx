import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { phase1Api } from '../api/phase1Api';
import { phase2Api } from '../api/phase2Api';
import { sseRequest } from '../api/sseClient';
import GraphControls from '../components/phase2/GraphControls';
import MappingView from '../components/phase2/MappingView';
import NodeDetail from '../components/phase2/NodeDetail';
import OntologyGraph from '../components/phase2/OntologyGraph';
import StageHint from '../components/shared/StageHint';
import type { GraphEdge, GraphNode, NodeType } from '../types/graph';
import type {
  MappingFieldLink,
  MappingVisualization,
  ModelKey,
  Phase2State,
} from '../types/ontology';
import styles from './Phase2Page.module.css';

const PHASES: { key: ModelKey | 'mapping'; label: string }[] = [
  { key: 'M1', label: 'M1 对象模型' },
  { key: 'M3', label: 'M3 规则模型' },
  { key: 'M_Metric', label: 'M_Metric 指标模型' },
  { key: 'M2', label: 'M2 行为模型（分析）' },
  { key: 'M4', label: 'M4 场景模型（分析）' },
  { key: 'mapping', label: '数据库映射' },
];

type Status = 'pending' | 'running' | 'retry' | 'done' | 'error';

interface PhaseProgress {
  status: Status;
  attempt?: number;
  summary?: { count: number; relations?: number };
  warnings?: string[];
  errorMsg?: string;
}

export default function Phase2Page() {
  const navigate = useNavigate();
  const [view, setView] = useState<'graph' | 'mapping'>('graph');
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [recentNodeIds, setRecentNodeIds] = useState<string[]>([]);
  const [mapping, setMapping] = useState<MappingVisualization | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedLink, setSelectedLink] = useState<MappingFieldLink | null>(null);
  const [enabledTypes, setEnabledTypes] = useState<Set<NodeType>>(
    () => new Set(['entity', 'behavior', 'rule', 'scenario', 'metric']),
  );

  const [phaseProgress, setPhaseProgress] = useState<Record<string, PhaseProgress>>({});
  const [globalErr, setGlobalErr] = useState('');
  const [generating, setGenerating] = useState(false);
  const [streamSummary, setStreamSummary] = useState<{ phase: string; chars: number; batchInfo?: string } | null>(null);
  const [phase1Ready, setPhase1Ready] = useState(true);
  const abortRef = useRef<AbortController | null>(null);

  // 初始加载已生成内容
  useEffect(() => {
    (async () => {
      try {
        // 检查阶段一是否已完成（需要解析后的需求文档）
        try {
          const p1 = await phase1Api.getState();
          setPhase1Ready(!!p1.parsed_requirement);
        } catch {
          setPhase1Ready(false);
        }
        const state: Phase2State = await phase2Api.getState();
        const progress: Record<string, PhaseProgress> = {};
        for (const p of PHASES) {
          if (p.key === 'mapping') {
            progress[p.key] = { status: state.has_mapping ? 'done' : 'pending' };
          } else {
            const item = state.models[p.key as ModelKey];
            progress[p.key] = {
              status: item?.ready ? 'done' : 'pending',
              summary: item?.summary ? { count: item.summary.count, relations: item.summary.relations } : undefined,
            };
          }
        }
        setPhaseProgress(progress);
        const g = await phase2Api.getGraph();
        if (g.nodes.length > 0) {
          setNodes(g.nodes);
          setEdges(g.edges);
        }
        if (state.has_mapping) {
          const m = await phase2Api.getMapping();
          setMapping(m);
        }
      } catch {
        /* 忽略 */
      }
    })();
  }, []);

  const handleSse = useCallback((msg: any) => {
    switch (msg.type) {
      case 'phase': {
        setPhaseProgress((p) => ({ ...p, [msg.phase]: { status: 'running' } }));
        setStreamSummary({ phase: msg.phase, chars: 0 });
        break;
      }
      case 'phase_delta': {
        setStreamSummary((s) =>
          s && s.phase === msg.phase
            ? { phase: msg.phase, chars: s.chars + (msg.delta?.length ?? 0) }
            : { phase: msg.phase, chars: msg.delta?.length ?? 0 },
        );
        break;
      }
      case 'phase_retry': {
        setPhaseProgress((p) => ({
          ...p,
          [msg.phase]: { status: 'retry', attempt: msg.attempt, errorMsg: msg.reason },
        }));
        break;
      }
      case 'phase_done': {
        setPhaseProgress((p) => ({
          ...p,
          [msg.phase]: { status: 'done', summary: msg.summary, warnings: msg.warnings ?? [] },
        }));
        break;
      }
      case 'graph_delta': {
        const newN: GraphNode[] = msg.added_nodes ?? [];
        const newE: GraphEdge[] = msg.added_edges ?? [];
        setNodes((prev) => [...prev, ...newN]);
        setEdges((prev) => [...prev, ...newE]);
        setRecentNodeIds(newN.map((n) => n.id));
        setTimeout(() => setRecentNodeIds([]), 2000);
        break;
      }
      case 'mapping_plan': {
        setStreamSummary({
          phase: 'mapping', chars: 0,
          batchInfo: `计划 ${msg.total_batches} 批 · ${msg.total_entities} 实体`,
        });
        break;
      }
      case 'mapping_batch_start': {
        setStreamSummary({
          phase: 'mapping', chars: 0,
          batchInfo: `批次 ${msg.batch_idx}/${msg.total_batches} · ${msg.entity_ids?.length ?? 0} 实体`,
        });
        break;
      }
      case 'mapping_batch_done': {
        setStreamSummary((s) => ({
          phase: 'mapping', chars: 0,
          batchInfo: `${s?.batchInfo ?? ''} ✓ ${msg.mapped_count} 完成`,
        }));
        break;
      }
      case 'mapping_batch_failed': {
        setStreamSummary((s) => ({
          phase: 'mapping', chars: 0,
          batchInfo: `${s?.batchInfo ?? ''} ✗ 跳过`,
        }));
        break;
      }
      case 'mapping_ready': {
        setPhaseProgress((p) => ({ ...p, mapping: { status: 'done', summary: msg.stats } }));
        // 拉一次完整 mapping
        phase2Api.getMapping().then(setMapping).catch(() => {});
        break;
      }
      case 'error': {
        setGlobalErr(msg.message ?? '生成失败');
        if (msg.phase) {
          setPhaseProgress((p) => ({
            ...p,
            [msg.phase]: { ...(p[msg.phase] ?? { status: 'error' }), status: 'error', errorMsg: msg.message },
          }));
        }
        break;
      }
      case 'done': {
        setGenerating(false);
        break;
      }
    }
  }, []);

  const startGenerate = useCallback(async () => {
    setGlobalErr('');
    setNodes([]);
    setEdges([]);
    setMapping(null);
    setSelectedNode(null);
    setSelectedLink(null);
    setRecentNodeIds([]);
    const fresh: Record<string, PhaseProgress> = {};
    PHASES.forEach((p) => (fresh[p.key] = { status: 'pending' }));
    setPhaseProgress(fresh);
    setGenerating(true);

    const ac = new AbortController();
    abortRef.current = ac;
    await sseRequest(
      '/api/phase2/generate',
      { method: 'POST', body: {}, signal: ac.signal },
      {
        onMessage: handleSse,
        onError: (err) => {
          setGlobalErr(err.message);
          setGenerating(false);
        },
        onDone: () => setGenerating(false),
      },
    );
  }, [handleSse]);

  const goToPhase3 = useCallback(async () => {
    try {
      await phase2Api.confirm();
      navigate('/phase3');
    } catch (err) {
      setGlobalErr((err as Error).message);
    }
  }, [navigate]);

  const nodesByType = useMemo(() => {
    const c: Record<string, number> = {};
    for (const n of nodes) c[n.type] = (c[n.type] ?? 0) + 1;
    return c;
  }, [nodes]);

  const allDone = useMemo(
    () => PHASES.every((p) => phaseProgress[p.key]?.status === 'done'),
    [phaseProgress],
  );

  const toggleType = useCallback((t: NodeType) => {
    setEnabledTypes((prev) => {
      const next = new Set(prev);
      if (next.has(t)) next.delete(t);
      else next.add(t);
      return next;
    });
  }, []);

  return (
    <div>
      {!phase1Ready && (
        <StageHint
          type="warn"
          message="阶段一的需求解析尚未完成 — 直接生成本体会失败，请先到阶段一上传文档并执行 AI 解析"
          linkTo="/phase1"
          linkText="去阶段一"
        />
      )}
    <div className={styles.layout}>
      {/* 左侧：流程面板 */}
      <aside className={styles.sidebar}>
        <div className={styles.sidebarHead}>
          <div className={styles.sidebarTitle}>生成流程</div>
          <button
            className="btn-primary"
            onClick={startGenerate}
            disabled={generating}
            type="button"
            style={{ width: '100%' }}
          >
            {generating ? '生成中...' : allDone ? '重新生成' : '开始生成本体'}
          </button>
        </div>
        <ol className={styles.phaseList}>
          {PHASES.map((p) => {
            const prog = phaseProgress[p.key] ?? { status: 'pending' };
            return (
              <li key={p.key} className={`${styles.phaseItem} ${styles[`s_${prog.status}`]}`}>
                <span className={styles.phaseIcon}>
                  {prog.status === 'pending' && '○'}
                  {prog.status === 'running' && '⏳'}
                  {prog.status === 'retry' && '↻'}
                  {prog.status === 'done' && '✓'}
                  {prog.status === 'error' && '✗'}
                </span>
                <div className={styles.phaseBody}>
                  <div className={styles.phaseLabel}>{p.label}</div>
                  {prog.summary && (
                    <div className={styles.phaseSummary}>
                      {prog.summary.count} 项
                      {prog.summary.relations !== undefined && prog.summary.relations !== null && ` · ${prog.summary.relations} 关系`}
                    </div>
                  )}
                  {prog.status === 'retry' && prog.attempt && (
                    <div className={styles.phaseRetry}>
                      第 {prog.attempt} 次重试 — {prog.errorMsg?.slice(0, 60)}
                    </div>
                  )}
                  {prog.status === 'error' && (
                    <div className={styles.phaseError}>{prog.errorMsg?.slice(0, 80)}</div>
                  )}
                  {prog.warnings && prog.warnings.length > 0 && (
                    <div className={styles.phaseWarn}>⚠ {prog.warnings.join('; ')}</div>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
        {streamSummary && generating && (
          <div className={styles.streamHint}>
            <span className={styles.spinner} />
            {streamSummary.batchInfo
              ? <>{streamSummary.phase} · {streamSummary.batchInfo}</>
              : <>{streamSummary.phase} · 接收 {streamSummary.chars.toLocaleString()} 字</>}
          </div>
        )}
        {globalErr && <div className={styles.globalErr}>{globalErr}</div>}

        {allDone && (
          <button
            className="btn-primary"
            onClick={goToPhase3}
            type="button"
            style={{ width: '100%', marginTop: 12 }}
          >
            确认本体 → 进入阶段三
          </button>
        )}
      </aside>

      {/* 右侧：图谱 / 映射切换 */}
      <main className={styles.main}>
        <div className={styles.toolbar}>
          <div className={styles.tabs}>
            <button
              className={`${styles.tab} ${view === 'graph' ? styles.tabActive : ''}`}
              onClick={() => setView('graph')}
              type="button"
            >
              🧠 知识图谱 ({nodes.length})
            </button>
            <button
              className={`${styles.tab} ${view === 'mapping' ? styles.tabActive : ''}`}
              onClick={() => setView('mapping')}
              type="button"
              disabled={!mapping}
            >
              🔗 数据库映射 ({mapping?.stats.link_count ?? 0})
            </button>
          </div>
          {view === 'graph' && (
            <GraphControls
              enabledTypes={enabledTypes}
              onToggle={toggleType}
              stats={nodesByType}
            />
          )}
        </div>

        <div className={styles.canvas}>
          {view === 'graph' ? (
            nodes.length === 0 ? (
              <div className={styles.placeholder}>
                <div className={styles.placeholderIcon}>🧭</div>
                <div className={styles.placeholderText}>
                  尚未生成本体。点击左侧「开始生成本体」按钮，AI 将基于阶段一的需求文档
                  和数据库 Schema 流式生成 5 个本体模型，知识图谱会随生成过程动态演进。
                </div>
              </div>
            ) : (
              <OntologyGraph
                nodes={nodes}
                edges={edges}
                highlightedNodeIds={recentNodeIds}
                enabledTypes={enabledTypes}
                onNodeClick={setSelectedNode}
              />
            )
          ) : mapping ? (
            <MappingView data={mapping} onLinkClick={setSelectedLink} />
          ) : (
            <div className={styles.placeholder}>
              <div className={styles.placeholderText}>映射尚未生成。</div>
            </div>
          )}

          {selectedNode && view === 'graph' && (
            <NodeDetail node={selectedNode} onClose={() => setSelectedNode(null)} />
          )}
        </div>
      </main>

      {/* 映射详情底部抽屉 */}
      {selectedLink && (
        <div className={styles.linkDetail}>
          <div className={styles.linkDetailHead}>
            <strong>映射详情</strong>
            <button onClick={() => setSelectedLink(null)} type="button" className={styles.closeBtn}>✕</button>
          </div>
          <div className={styles.linkDetailBody}>
            <div className={styles.detailLine}>
              <span className={styles.detailKey}>本体字段</span>
              <span className={styles.detailVal}>{selectedLink.entity_id}.<b>{selectedLink.ontology_field}</b></span>
            </div>
            <div className={styles.detailLine}>
              <span className={styles.detailKey}>数据库</span>
              <span className={styles.detailVal}>{selectedLink.table}.<b>{selectedLink.db_column}</b></span>
            </div>
            <div className={styles.detailLine}>
              <span className={styles.detailKey}>置信度</span>
              <span className={styles.detailVal}>
                <span className={styles.confBadge} style={{ background: selectedLink.color }}>
                  {(selectedLink.confidence * 100).toFixed(0)}%
                </span>
              </span>
            </div>
            {selectedLink.db_expression && (
              <div className={styles.detailLine}>
                <span className={styles.detailKey}>表达式</span>
                <code className={styles.detailVal}>{selectedLink.db_expression}</code>
              </div>
            )}
            {selectedLink.note && (
              <div className={styles.detailLine}>
                <span className={styles.detailKey}>说明</span>
                <span className={styles.detailVal}>{selectedLink.note}</span>
              </div>
            )}
            {selectedLink.value_mapping && (
              <div className={styles.detailLine}>
                <span className={styles.detailKey}>枚举映射</span>
                <span className={styles.detailVal}>
                  {Object.entries(selectedLink.value_mapping).map(([k, v]) => (
                    <span key={k} className={styles.enumTag}>{k}→{v}</span>
                  ))}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
    </div>
  );
}
