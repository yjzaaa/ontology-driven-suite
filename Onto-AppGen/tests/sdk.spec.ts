/**
 * SDK 单元测试（第一阶段）：校验器 + 生成器产数据。
 * 核心断言：产物 = 数据（tables/behaviors/schema JSON），不是代码。
 */
import { describe, expect, it } from 'vitest'
import { mkdtempSync, rmSync, readFileSync, existsSync, readdirSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { buildModelIndex, validateSchema } from '../src/validator.js'
import { generateData } from '../src/generator.js'
import type { AppSchema } from '../src/types.js'

const m1 = {
  aggregates: [
    { id: 'AGG-W', rootEntity: { alias: 'RepairOrder', attributes: [
      { name: 'orderNo', type: 'String', required: true, unique: true },
      { name: 'status', type: 'Enum', enumValues: ['待派单', '维修中', '已维修'], required: true },
    ] } },
  ],
  masterEntities: [ { alias: 'FaultType', attributes: ['faultTypeCode', 'faultTypeName'] } ],
}
const m2 = { behaviors: [
  { id: 'RepairOrder_Create', name: '报修登记', ownerEntity: 'RepairOrder', postconditions: [{ field: 'status', setValue: '待派单' }] },
  { id: 'RepairOrder_Assign', name: '派单', ownerEntity: 'RepairOrder', preconditions: ["repairOrder.status == '待派单'"], postconditions: [{ field: 'status', setValue: '维修中' }] },
] }

function schema(): AppSchema {
  return {
    name: 'd', version: '1', sourceProject: 'd',
    pages: [
      { id: 'form', title: '报修', blocks: [{ type: 'form', title: '报修登记', entity: 'RepairOrder', behavior: 'RepairOrder_Create', fields: [
        { name: 'faultTypeId', label: '故障类型', control: 'select', refTable: 'FaultType' },
      ] }] },
      { id: 'list', title: '列表', blocks: [{ type: 'table', title: '工单', entity: 'RepairOrder', columns: [{ name: 'status', label: '状态', render: 'tag', tagMap: { 待派单: 'orange' } }], actions: [{ label: '派单', behavior: 'RepairOrder_Assign', visibleWhen: { status: '待派单' } }] }] },
    ],
  }
}

describe('校验器 validateSchema', () => {
  it('合法 schema → 0 issue', () => {
    expect(validateSchema(schema(), buildModelIndex(m1, m2))).toEqual([])
  })
  it('非法控件 → RULE-CONTROL-LEGAL', () => {
    const s = schema(); s.pages[0].blocks[0].fields![0].control = 'slider' as any
    expect(validateSchema(s, buildModelIndex(m1, m2)).some(i => i.code === 'RULE-CONTROL-LEGAL')).toBe(true)
  })
  it('引用行为不存在 → RULE-BEHAVIOR-EXISTS', () => {
    const s = schema(); s.pages[1].blocks[0].actions![0].behavior = 'Nope'
    expect(validateSchema(s, buildModelIndex(m1, m2)).some(i => i.code === 'RULE-BEHAVIOR-EXISTS')).toBe(true)
  })
})

describe('生成器 generateData：产物=数据', () => {
  it('只产 tables/behaviors/schema JSON，无代码副本', () => {
    const dir = mkdtempSync(join(tmpdir(), 'oag-data-'))
    const r = generateData(dir, schema(), m1, m2)
    expect(r.files.sort()).toEqual(['app.schema.json', 'behaviors.json', 'tables.json'])
    const files = readdirSync(join(dir, 'app'))
    expect(files.find(f => f.endsWith('.cjs') || f.endsWith('.html'))).toBeUndefined()
    rmSync(dir, { recursive: true, force: true })
  })
  it('主数据被 schema 引用 → 补建表；行为规格含前置/后置条件', () => {
    const dir = mkdtempSync(join(tmpdir(), 'oag-data-'))
    generateData(dir, schema(), m1, m2)
    const tables = JSON.parse(readFileSync(join(dir, 'app', 'tables.json'), 'utf-8'))
    expect(tables.map((t: any) => t.table)).toContain('FaultType')
    const behaviors = JSON.parse(readFileSync(join(dir, 'app', 'behaviors.json'), 'utf-8'))
    const assign = behaviors.find((b: any) => b.id === 'RepairOrder_Assign')
    expect(assign.preconditions[0]).toContain('待派单')
    expect(assign.postconditions[0].setValue).toBe('维修中')
    rmSync(dir, { recursive: true, force: true })
  })
})