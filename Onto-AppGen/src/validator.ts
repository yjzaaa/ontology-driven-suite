/**
 * App Schema 校验器：对应本体模型 M2.Schema_Validate 行为 + M3 六条规则。
 * 校验 LLM 输出的 App Schema 引用完整性（entity/behavior/refTable 指回本体模型）、
 * 控件合法性、页面 id 唯一、跳转目标存在。
 */

import type { AppSchema, SchemaIssue } from './types.js'
import { CONTROL_TYPES, BLOCK_TYPES, RENDER_TYPES } from './types.js'

/** 本体模型引用索引：实体集 / 行为集 / 表名集 */
export interface ModelIndex {
  entities: Set<string>
  behaviors: Set<string>
  tables: Set<string>
}

/** 从归一化后的本体模型构建引用索引。 */
export function buildModelIndex(m1: any, m2: any): ModelIndex {
  const entities = new Set<string>()
  const tables = new Set<string>()
  for (const agg of m1?.aggregates ?? []) {
    if (agg?.rootEntity?.alias) { entities.add(agg.rootEntity.alias); tables.add(agg.rootEntity.alias) }
    for (const e of agg?.internalEntities ?? []) if (e?.alias) { entities.add(e.alias); tables.add(e.alias) }
  }
  for (const e of m1?.masterEntities ?? []) if (e?.alias) { entities.add(e.alias); tables.add(e.alias) }
  const behaviors = new Set<string>((m2?.behaviors ?? []).map((b: any) => b.id))
  return { entities, behaviors, tables }
}

/** 校验 App Schema，返回违规问题清单（空数组 = 通过）。 */
export function validateSchema(schema: AppSchema, idx: ModelIndex): SchemaIssue[] {
  const issues: SchemaIssue[] = []

  const seen = new Set<string>()
  for (const p of schema.pages) {
    if (!p.id || !p.id.trim()) {
      issues.push({ code: 'PAGE_ID_EMPTY', message: '页面缺少 id', path: `pages.${p.title}` })
    } else if (seen.has(p.id)) {
      issues.push({ code: 'RULE-PAGE-ID-UNIQUE', message: `页面 id 重复: ${p.id}`, pageId: p.id })
    }
    seen.add(p.id)
  }

  const pageIds = new Set(schema.pages.map(p => p.id))
  for (const p of schema.pages) {
    for (const b of p.blocks ?? []) {
      const base = `pages.${p.id}.${b.title ?? b.type}`

      if (!BLOCK_TYPES.includes(b.type)) {
        issues.push({ code: 'BLOCK_TYPE_ILLEGAL', message: `非法 Block 类型: ${b.type}`, pageId: p.id, path: base })
        continue
      }

      if (b.entity && !idx.entities.has(b.entity) && !idx.tables.has(b.entity)) {
        issues.push({ code: 'RULE-ENTITY-EXISTS', message: `Block 引用实体不存在于 M1: ${b.entity}`, pageId: p.id, path: base })
      }

      if (b.behavior && !idx.behaviors.has(b.behavior)) {
        issues.push({ code: 'RULE-BEHAVIOR-EXISTS', message: `Block 引用行为不存在于 M2: ${b.behavior}`, pageId: p.id, path: base })
      }

      for (const f of b.fields ?? []) {
        if (!CONTROL_TYPES.includes(f.control)) {
          issues.push({ code: 'RULE-CONTROL-LEGAL', message: `非法控件类型: ${f.control}`, pageId: p.id, path: `${base}.fields.${f.name}` })
        }
        if (f.refTable && !idx.tables.has(f.refTable)) {
          issues.push({ code: 'RULE-ENTITY-EXISTS', message: `字段引用表不存在: ${f.refTable}`, pageId: p.id, path: `${base}.fields.${f.name}` })
        }
      }

      for (const c of b.columns ?? []) {
        if (c.render && !RENDER_TYPES.includes(c.render)) {
          issues.push({ code: 'RULE-CONTROL-LEGAL', message: `非法列渲染方式: ${c.render}`, pageId: p.id, path: `${base}.columns.${c.name}` })
        }
      }

      for (const a of b.actions ?? []) {
        if (a.behavior && !idx.behaviors.has(a.behavior)) {
          issues.push({ code: 'RULE-BEHAVIOR-EXISTS', message: `行内操作引用行为不存在于 M2: ${a.behavior}`, pageId: p.id, path: `${base}.actions.${a.label}` })
        }
        if (a.rowClick && !pageIds.has(a.rowClick)) {
          issues.push({ code: 'RULE-ROWCLICK-EXISTS', message: `跳转目标页面不存在: ${a.rowClick}`, pageId: p.id, path: `${base}.actions.${a.label}` })
        }
        for (const f of a.params ?? []) {
          if (f.refTable && !idx.tables.has(f.refTable)) {
            issues.push({ code: 'RULE-ENTITY-EXISTS', message: `操作参数引用表不存在: ${f.refTable}`, pageId: p.id, path: `${base}.actions.${a.label}` })
          }
        }
      }
    }
  }

  return issues
}
