/**
 * App Schema Field → Formily Schema 转换器。
 * Formily Schema 用 JSON Schema 描述：type/title/required/x-component/x-component-props/enum。
 * @formily/antd 的组件经 SchemaField 的 components 映射按 x-component 字符串解析。
 */
import type { Field } from './schema'

/** control → Formily x-component 映射（@formily/antd-v5 组件名） */
const COMPONENT_MAP: Record<string, string> = {
  select: 'Select',
  input: 'Input',
  textarea: 'Input.TextArea',
  date: 'DatePicker',
  datetime: 'DatePicker',
  radio: 'Radio.Group',
  number: 'NumberPicker',
}

/** 引用数据（refTable → 后端拉取的行） */
export type RefData = Record<string, Array<Record<string, any>>>

/** 单字段 → Formily Schema */
export function fieldToFormily(field: Field, refData: RefData): Record<string, any> {
  const component = COMPONENT_MAP[field.control] ?? 'Input'
  const props: Record<string, any> = {}
  if (field.control === 'datetime') props.showTime = true
  if (field.control === 'textarea') props.rows = 3
  if (field.control === 'select') {
    props.placeholder = '请选择' + field.label
    props.allowClear = true
    props.style = { width: '100%' }
  } else if (field.control === 'input' || field.control === 'textarea') {
    props.placeholder = '请输入' + field.label
  }

  const schema: Record<string, any> = {
    type: 'string',
    title: field.label,
    'x-decorator': 'FormItem',
    'x-component': component,
    'x-component-props': props,
  }
  if (field.required) schema.required = true
  if (field.default !== undefined) schema.default = field.default

  // 枚举 options（下拉/单选共用）
  if (field.options && field.options.length) {
    schema.enum = field.options.map(v => ({ label: String(v), value: v }))
  }
  // 引用字段：用预拉数据生成 enum
  if (field.refTable && refData[field.refTable]) {
    schema.enum = refData[field.refTable].map(o => {
      const val = field.refValue ? o[field.refValue] : o[Object.keys(o)[0]]
      const lab = field.refLabel ? o[field.refLabel] : val
      return { label: String(lab), value: val }
    })
  }
  // 联动显隐：visibleWhen { depField: expectedValue } → Formily x-reactions（x-display 控制是否渲染）
  if (field.visibleWhen && Object.keys(field.visibleWhen).length) {
    const [depField, expected] = Object.entries(field.visibleWhen)[0]!
    schema['x-reactions'] = {
      dependencies: [depField],
      fulfill: {
        schema: {
          'x-display': `{{ $deps[0] === ${JSON.stringify(expected)} ? "visible" : "none" }}`,
        },
      },
    }
  }
  return schema
}

/** 字段列表 → Formily 表单 Schema（object 容器） */
export function buildFormilySchema(fields: Field[] | undefined, refData: RefData): Record<string, any> {
  const properties: Record<string, any> = {}
  for (const f of fields ?? []) properties[f.name] = fieldToFormily(f, refData)
  return { type: 'object', properties }
}