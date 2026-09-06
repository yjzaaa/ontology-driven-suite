/**
 * FormBlock：用 Formily 渲染字段级表单（控件联动/校验/布局）。
 * 替换之前手写 Control 的方案。
 */
import React, { useEffect, useMemo, useState } from 'react'
import { createForm } from '@formily/core'
import { FormProvider, createSchemaField } from '@formily/react'
import {
  FormItem, Input, Select, DatePicker, Radio, NumberPicker, FormLayout, Submit,
} from '@formily/antd-v5'
import { message } from 'antd'
import type { Block, Field } from './schema'
import { buildFormilySchema, type RefData } from './toFormily'

/** Formily components 映射：x-component 字符串 → @formily/antd-v5 组件 */
const componentMap = {
  FormItem, FormLayout, Input, Select, DatePicker, Radio, NumberPicker, Submit,
  'Input.TextArea': Input.TextArea,
  'Radio.Group': Radio.Group,
}
/** 用工厂创建 SchemaField（Formily 的正确用法：组件映射在创建时注入） */
const SchemaField = createSchemaField({ components: componentMap })

async function api(path: string, opts?: RequestInit) {
  const r = await fetch(path, opts)
  const j = await r.json()
  if (!r.ok) throw new Error(j.error || JSON.stringify(j))
  return j
}
async function getOptions(table: string): Promise<Array<Record<string, any>>> {
  const j = await api('/api/entity/' + encodeURIComponent(table))
  return j.rows || []
}

export function FormBlock({ block, onDone }: { block: Block; onDone?: () => void }) {
  const [refData, setRefData] = useState<RefData>({})
  const [submitting, setSubmitting] = useState(false)
  const form = useMemo(() => createForm(), [block])

  // 预拉引用字段数据
  useEffect(() => {
    (block.fields ?? []).forEach(f => {
      if (f.refTable) {
        getOptions(f.refTable).then(rows => setRefData(o => ({ ...o, [f.refTable!]: rows })))
      }
    })
  }, [block])

  const schema = useMemo(() => buildFormilySchema(block.fields, refData), [block, refData])

  const submit = async () => {
    setSubmitting(true)
    try {
      await form.validate()  // Formily 校验
      const vals = form.values
      if (block.behavior) {
        await api('/api/behavior/' + block.behavior, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(vals) })
      } else if (block.entity) {
        await api('/api/entity/' + block.entity, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(vals) })
      }
      message.success('提交成功')
      form.reset()
      onDone && onDone()
    } catch (e: any) {
      if (e?.errorFields || String(e).includes('validate')) {
        // Formily 校验失败已在表单内联提示，不再弹错
      } else {
        message.error(String(e.message || e))
      }
    } finally { setSubmitting(false) }
  }

  return (
    <div className="block-card">
      <div className="block-title">{block.title}</div>
      <FormProvider form={form}>
        <FormLayout layout="vertical">
          <SchemaField schema={schema} />
        </FormLayout>
        <Submit loading={submitting} onSubmit={submit}>{block.title}</Submit>
      </FormProvider>
    </div>
  )
}

/** 行内操作弹窗里的参数字段（也用 Formily） */
export function ActionParamsForm({ fields, form }: { fields: Field[]; form: any }) {
  const [refData, setRefData] = useState<RefData>({})
  useEffect(() => {
    (fields ?? []).forEach(f => {
      if (f.refTable) getOptions(f.refTable).then(rows => setRefData(o => ({ ...o, [f.refTable!]: rows })))
    })
  }, [fields])
  const schema = useMemo(() => buildFormilySchema(fields, refData), [fields, refData])
  return (
    <FormProvider form={form}>
      <FormLayout layout="vertical">
        <SchemaField schema={schema} />
      </FormLayout>
    </FormProvider>
  )
}