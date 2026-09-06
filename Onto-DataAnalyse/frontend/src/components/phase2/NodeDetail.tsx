import { useEffect, useState } from 'react';
import { phase2Api } from '../../api/phase2Api';
import type { GraphNode } from '../../types/graph';
import type { ModelKey, ModelYamlPayload } from '../../types/ontology';
import YamlViewer from '../shared/YamlViewer';
import styles from './NodeDetail.module.css';

interface Props {
  node: GraphNode | null;
  onClose: () => void;
}

const TYPE_LABEL: Record<string, string> = {
  entity: '实体',
  behavior: '分析行为',
  rule: '业务规则',
  scenario: '分析场景',
  metric: '指标',
};

export default function NodeDetail({ node, onClose }: Props) {
  const [payload, setPayload] = useState<ModelYamlPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');

  useEffect(() => {
    if (!node) return;
    setErr('');
    setPayload(null);
    const modelKey = node.raw_ref?.model as ModelKey | undefined;
    if (!modelKey) return;
    setLoading(true);
    phase2Api.getYaml(modelKey)
      .then((p) => setPayload(p))
      .catch((e) => setErr((e as Error).message))
      .finally(() => setLoading(false));
  }, [node]);

  if (!node) return null;

  // 从 YAML 文本中尝试提取该节点对应的片段（通过 ID 匹配）
  const fragment = payload ? extractFragment(payload.yaml_text, node.id) : '';

  return (
    <div className={styles.drawer}>
      <div className={styles.head}>
        <div>
          <div className={styles.typeTag} style={{ background: node.color }}>
            {TYPE_LABEL[node.type] ?? node.type}
          </div>
          <div className={styles.title}>{node.label}</div>
          <div className={styles.id}>{node.id}</div>
        </div>
        <button className={styles.close} onClick={onClose} type="button">✕</button>
      </div>

      {node.description && <div className={styles.desc}>{node.description}</div>}

      <div className={styles.meta}>
        {node.subtype && <Meta label="子类型" value={node.subtype} />}
        {node.domain && <Meta label="业务域" value={node.domain} />}
        {node.unit && <Meta label="单位" value={node.unit} />}
        {node.raw_ref && <Meta label="所属模型" value={node.raw_ref.model} />}
      </div>

      <div className={styles.section}>
        <div className={styles.sectionTitle}>YAML 片段</div>
        {loading && <div className={styles.muted}>加载中...</div>}
        {err && <div className={styles.error}>{err}</div>}
        {fragment ? (
          <YamlViewer yamlText={fragment} />
        ) : payload ? (
          <div className={styles.muted}>未能在 YAML 中定位该节点的片段（可能是衍生节点）</div>
        ) : null}
      </div>

      {payload && (
        <details className={styles.full}>
          <summary>查看完整 {payload.filename}</summary>
          <YamlViewer yamlText={payload.yaml_text} filename={payload.filename} />
        </details>
      )}
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className={styles.metaItem}>
      <span className={styles.metaLabel}>{label}</span>
      <span className={styles.metaValue}>{value}</span>
    </div>
  );
}

/**
 * 从 YAML 文本中提取以 `- id: <nodeId>` 开头的一段（直到下一条 `- id:` 或文件末尾）
 */
function extractFragment(yamlText: string, nodeId: string): string {
  const lines = yamlText.split('\n');
  let start = -1;
  let baseIndent = 0;
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const m = line.match(/^(\s*)-\s+id\s*:\s*['"]?([\w-]+)['"]?/);
    if (m && m[2] === nodeId) {
      start = i;
      baseIndent = m[1].length;
      break;
    }
  }
  if (start < 0) return '';
  let end = lines.length;
  for (let i = start + 1; i < lines.length; i++) {
    const line = lines[i];
    if (/^\s*$/.test(line)) continue;
    const indent = line.match(/^(\s*)/)?.[1].length ?? 0;
    if (indent <= baseIndent && /^\s*-\s+id/.test(line)) {
      end = i;
      break;
    }
    if (indent < baseIndent && line.trim() && !line.startsWith('-')) {
      end = i;
      break;
    }
  }
  return lines.slice(start, end).join('\n');
}
