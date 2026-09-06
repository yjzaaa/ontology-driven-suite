/**
 * App Schema 生成器（对应本体模型 M2.App_Generate 行为）。
 * 第一阶段收敛：产物 = 数据，不是代码。
 * 从本体模型（M1 表 + M2 行为）+ LLM 提供的 App Schema，生成三个数据文件到 <projectDir>/app/：
 *   tables.json      建表规格（M1 聚合根/子实体 + schema 引用的主数据，含主键自动编号元信息）
 *   behaviors.json   行为规格（M2 行为：前置/后置条件、ownerEntity）
 *   app.schema.json  App Schema（页面组织决议，落盘可审计）
 * 运行由固定引擎 engine/engine.cjs 读这些数据 -> 建库 -> 行为 API -> serve 固定渲染器。
 */

import { writeFileSync, mkdirSync } from 'node:fs'
import { join } from 'node:path'
import type { AppSchema } from './types.js'

/** M1 聚合根/子实体/主数据（被 schema 引用）→ 建表规格 */
function buildTables(m1: any, schema: AppSchema) {
  const specs: any[] = []
  const collect = (alias: string, attrs: any[]) => {
    const cols = attrs.map((a: any, i: number) => ({
      name: typeof a === 'string' ? a : (a?.name ?? `col_${i}`),
      type: (typeof a === 'string' ? 'TEXT' : (a.type === 'Decimal' || a.type === 'Money' ? 'REAL' : 'TEXT')),
      required: Boolean(typeof a === 'string' ? false : a?.required),
      unique: Boolean(typeof a === 'string' ? false : a?.unique),
    }))
    const pkAttr = attrs.find((a: any) => a?.unique && a?.required)
    const pk = pkAttr ? (pkAttr.name ?? `col_${attrs.indexOf(pkAttr)}`) : `${alias}_id`
    if (!cols.some((c: any) => c.name === pk)) cols.unshift({ name: pk, type: 'TEXT', required: true, unique: true })
    specs.push({ table: alias, pk, columns: cols })
  }
  for (const agg of m1?.aggregates ?? []) {
    if (!agg?.rootEntity?.alias) continue
    collect(agg.rootEntity.alias, agg.rootEntity.attributes ?? [])
    for (const e of agg?.internalEntities ?? []) if (e?.alias) collect(e.alias, e.attributes ?? [])
  }
  // schema 引用的主数据 → 补建表
  const referenced = new Set<string>()
  for (const p of schema.pages ?? []) {
    for (const b of p.blocks ?? []) {
      for (const f of b.fields ?? []) if (f.refTable) referenced.add(f.refTable)
      for (const c of b.columns ?? []) if (c.refTable) referenced.add(c.refTable)
      for (const a of b.actions ?? []) for (const f of a.params ?? []) if (f.refTable) referenced.add(f.refTable)
    }
  }
  const existing = new Set(specs.map(s => s.table))
  for (const me of m1?.masterEntities ?? []) {
    if (!me?.alias || !referenced.has(me.alias) || existing.has(me.alias)) continue
    collect(me.alias, me.attributes ?? [])
  }
  return specs
}

export interface GeneratedData {
  projectDir: string
  files: string[]
  schema: AppSchema
  tables: Array<{ table: string; pk: string; columns: string[] }>
  behaviors: Array<{ id: string; name: string }>
}

/**
 * 生成数据产物（不生成代码）。
 * @param projectDir 项目目录（数据写到 <projectDir>/app/）
 */
export function generateData(projectDir: string, schema: AppSchema, m1: any, m2: any): GeneratedData {
  const specs = buildTables(m1, schema).map(s => {
    const pkPrefix = s.pk.toLowerCase().includes('order') ? 'WO-' : (s.table + '-')
    return { ...s, pkPrefix, pkPad: 4 }
  })
  const behaviors = (m2?.behaviors ?? []).map((b: any) => ({
    id: b.id,
    name: b.name,
    ownerEntity: b.ownerEntity,
    preconditions: b.preconditions ?? [],
    postconditions: b.postconditions ?? [],
  }))

  const appDir = join(projectDir, 'app')
  mkdirSync(appDir, { recursive: true })
  writeFileSync(join(appDir, 'tables.json'), JSON.stringify(specs, null, 2), 'utf-8')
  writeFileSync(join(appDir, 'behaviors.json'), JSON.stringify(behaviors, null, 2), 'utf-8')
  writeFileSync(join(appDir, 'app.schema.json'), JSON.stringify(schema, null, 2), 'utf-8')

  return {
    projectDir,
    files: ['tables.json', 'behaviors.json', 'app.schema.json'],
    schema,
    tables: specs.map(s => ({ table: s.table, pk: s.pk, columns: s.columns.map((c: any) => c.name) })),
    behaviors: behaviors.map(b => ({ id: b.id, name: b.name })),
  }
}