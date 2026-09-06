import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import type { MappingFieldLink, MappingVisualization } from '../../types/ontology';
import styles from './MappingView.module.css';

interface Props {
  data: MappingVisualization;
  onLinkClick?: (link: MappingFieldLink) => void;
}

/**
 * 三列布局：
 *  - 左：本体实体 + 字段树
 *  - 中：SVG 连线层（贝塞尔曲线，颜色映射置信度）
 *  - 右：数据库表 + 字段树
 *
 * 每个字段是一个 DOM 节点；连线由其在容器中的相对位置计算。
 */
export default function MappingView({ data, onLinkClick }: Props) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [expandedEntities, setExpandedEntities] = useState<Set<string>>(() => new Set());
  const [expandedTables, setExpandedTables] = useState<Set<string>>(() => new Set());
  const [hoverLink, setHoverLink] = useState<MappingFieldLink | null>(null);
  const [highlightKey, setHighlightKey] = useState<string | null>(null);

  // 默认全部展开
  useEffect(() => {
    setExpandedEntities(new Set(data.entities.map((e) => e.entity_id)));
    setExpandedTables(new Set(data.tables.map((t) => t.table)));
  }, [data.entities, data.tables]);

  // 元素 DOM id 约定（便于查 BoundingRect）
  const entityFieldId = (eid: string, field: string) => `mp-ef-${eid}__${field}`;
  const tableColId = (table: string, col: string) => `mp-tc-${table}__${col}`;

  // 计算连线坐标（每次 layout 后）
  const [linePaths, setLinePaths] = useState<{ link: MappingFieldLink; d: string }[]>([]);
  useLayoutEffect(() => {
    const wrap = wrapRef.current;
    if (!wrap) return;
    const wrapRect = wrap.getBoundingClientRect();
    const items: { link: MappingFieldLink; d: string }[] = [];

    for (const link of data.links) {
      const leftEl = document.getElementById(entityFieldId(link.entity_id, link.ontology_field));
      const rightEl = document.getElementById(tableColId(link.table, link.db_column));
      if (!leftEl || !rightEl) continue;
      const lRect = leftEl.getBoundingClientRect();
      const rRect = rightEl.getBoundingClientRect();
      const x1 = lRect.right - wrapRect.left;
      const y1 = lRect.top + lRect.height / 2 - wrapRect.top;
      const x2 = rRect.left - wrapRect.left;
      const y2 = rRect.top + rRect.height / 2 - wrapRect.top;
      const cx1 = x1 + (x2 - x1) * 0.4;
      const cx2 = x1 + (x2 - x1) * 0.6;
      const d = `M${x1},${y1} C${cx1},${y1} ${cx2},${y2} ${x2},${y2}`;
      items.push({ link, d });
    }
    setLinePaths(items);
  }, [data, expandedEntities, expandedTables]);

  const stats = data.stats;

  return (
    <div className={styles.wrap} ref={wrapRef}>
      {/* SVG 连线层 */}
      <svg className={styles.svg} ref={svgRef}>
        {linePaths.map(({ link, d }, idx) => {
          const k = `${link.entity_id}.${link.ontology_field}->${link.table}.${link.db_column}`;
          const highlighted = highlightKey === k || hoverLink === link;
          return (
            <path
              key={idx}
              d={d}
              stroke={link.color}
              strokeWidth={highlighted ? 2.5 : 1.5}
              fill="none"
              opacity={highlightKey && !highlighted ? 0.18 : 0.85}
              strokeDasharray={link.db_expression ? '4 3' : undefined}
              style={{ cursor: 'pointer' }}
              onMouseEnter={() => setHoverLink(link)}
              onMouseLeave={() => setHoverLink(null)}
              onClick={() => onLinkClick?.(link)}
            />
          );
        })}
      </svg>

      {/* 左：本体实体 */}
      <div className={`${styles.column} ${styles.leftCol}`}>
        <div className={styles.colHead}>
          本体实体
          <span className={styles.colCount}>{stats.entity_count}</span>
        </div>
        {data.entities.map((ent) => {
          const open = expandedEntities.has(ent.entity_id);
          return (
            <div key={ent.entity_id} className={styles.entCard}>
              <div
                className={styles.entHead}
                onClick={() => toggle(expandedEntities, setExpandedEntities, ent.entity_id)}
              >
                <span className={styles.expander}>{open ? '▼' : '▶'}</span>
                <span className={styles.entName}>{ent.entity_name}</span>
                <span className={styles.entId}>{ent.entity_id}</span>
              </div>
              {open && (
                <div className={styles.fieldList}>
                  {ent.fields.map((f) => {
                    const hasLink = data.links.some(
                      (l) => l.entity_id === ent.entity_id && l.ontology_field === f.name,
                    );
                    return (
                      <div
                        key={f.name}
                        id={entityFieldId(ent.entity_id, f.name)}
                        className={`${styles.field} ${styles.fieldLeft} ${hasLink ? '' : styles.fieldUnmapped}`}
                        onMouseEnter={() => setHighlightKey(buildKeyFromField(data.links, ent.entity_id, f.name, 'left'))}
                        onMouseLeave={() => setHighlightKey(null)}
                      >
                        <span className={styles.fieldName}>{f.name}</span>
                        {f.label && <span className={styles.fieldLabel}>{f.label}</span>}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 中：连线提示区 */}
      <div className={styles.midCol}>
        <div className={styles.midLegend}>
          <div className={styles.legendRow}>
            <span className={styles.dotG} /> 高 ≥0.90
          </div>
          <div className={styles.legendRow}>
            <span className={styles.dotO} /> 中 0.70-0.89
          </div>
          <div className={styles.legendRow}>
            <span className={styles.dotR} /> 低 &lt;0.70
          </div>
          <div className={styles.legendNote}>
            虚线 = 含表达式/转换
          </div>
        </div>
        {hoverLink && (
          <div className={styles.tooltip}>
            <div className={styles.tooltipTitle}>
              {hoverLink.entity_id}.<b>{hoverLink.ontology_field}</b>
              <br />→ {hoverLink.table}.<b>{hoverLink.db_column}</b>
            </div>
            <div className={styles.tooltipMeta}>
              置信度 <b>{(hoverLink.confidence * 100).toFixed(0)}%</b>
              {hoverLink.note && <div className={styles.tooltipNote}>{hoverLink.note}</div>}
            </div>
          </div>
        )}
      </div>

      {/* 右：数据库表 */}
      <div className={`${styles.column} ${styles.rightCol}`}>
        <div className={styles.colHead}>
          数据库表
          <span className={styles.colCount}>{stats.table_count}</span>
        </div>
        {data.tables.map((tbl) => {
          const open = expandedTables.has(tbl.table);
          return (
            <div key={tbl.table} className={styles.entCard}>
              <div
                className={styles.entHead}
                onClick={() => toggle(expandedTables, setExpandedTables, tbl.table)}
              >
                <span className={styles.expander}>{open ? '▼' : '▶'}</span>
                <span className={styles.tableName}>{tbl.table}</span>
                <span className={styles.entId}>{tbl.columns.length} 列</span>
              </div>
              {open && (
                <div className={styles.fieldList}>
                  {tbl.columns.map((c) => (
                    <div
                      key={c.name}
                      id={tableColId(tbl.table, c.name)}
                      className={`${styles.field} ${styles.fieldRight}`}
                      onMouseEnter={() => setHighlightKey(buildKeyFromField(data.links, tbl.table, c.name, 'right'))}
                      onMouseLeave={() => setHighlightKey(null)}
                    >
                      <span className={styles.fieldName}>{c.name}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function toggle(set: Set<string>, setter: (s: Set<string>) => void, key: string) {
  const next = new Set(set);
  if (next.has(key)) next.delete(key);
  else next.add(key);
  setter(next);
}

function buildKeyFromField(
  links: MappingFieldLink[],
  parent: string,
  field: string,
  side: 'left' | 'right',
): string | null {
  const found = links.find((l) =>
    side === 'left'
      ? l.entity_id === parent && l.ontology_field === field
      : l.table === parent && l.db_column === field,
  );
  if (!found) return null;
  return `${found.entity_id}.${found.ontology_field}->${found.table}.${found.db_column}`;
}
