/**
 * App Schema 类型（与 SDK src/types.ts 对齐，前端侧使用）。
 */

export type ControlType = 'select' | 'input' | 'textarea' | 'date' | 'datetime' | 'radio' | 'number'
export type BlockType = 'form' | 'table' | 'stat' | 'detail'
export type RenderType = 'text' | 'tag'

export interface Field {
  name: string
  label: string
  control: ControlType
  required?: boolean
  options?: string[]
  refTable?: string
  refValue?: string
  refLabel?: string
  default?: string | number
  /** 联动显隐：仅当指定字段等于给定值时本字段才显示（对应 Formily x-reactions） */
  visibleWhen?: Record<string, string>
}

export interface Column {
  name: string
  label: string
  render?: RenderType
  tagMap?: Record<string, string>
  refTable?: string
  refLabel?: string
}

export interface Filter {
  name: string
  label: string
  options?: string[]
}

export interface Action {
  label: string
  behavior: string
  params?: Field[]
  confirm?: string
  visibleWhen?: Record<string, string>
  rowClick?: string
}

export interface Block {
  type: BlockType
  title: string
  entity?: string
  behavior?: string
  fields?: Field[]
  columns?: Column[]
  filters?: Filter[]
  actions?: Action[]
}

export interface Page {
  id: string
  title: string
  icon?: string
  blocks: Block[]
}

export interface AppSchema {
  name: string
  version: string
  sourceProject: string
  pages: Page[]
}
