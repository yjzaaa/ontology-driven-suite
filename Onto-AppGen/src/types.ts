/**
 * App Schema 协议（meta-schema）：LLM 读本体模型后输出的「页面组织决议」契约。
 * 由本项目本体建模（model/m1-object-model.yaml 的 AppSchema/Block/Field/Column/Action）驱动。
 */

/** 合法控件枚举（对应 M1 Field.control 的 enumValues） */
export const CONTROL_TYPES = ['select', 'input', 'textarea', 'date', 'datetime', 'radio', 'number'] as const
export type ControlType = typeof CONTROL_TYPES[number]

/** Block 类型（对应 M1 Block.type 的 enumValues） */
export const BLOCK_TYPES = ['form', 'table', 'stat', 'detail'] as const
export type BlockType = typeof BLOCK_TYPES[number]

/** 列渲染方式 */
export const RENDER_TYPES = ['text', 'tag'] as const
export type RenderType = typeof RENDER_TYPES[number]

/** 表单字段（对应 M1 Field） */
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

/** 列表列（对应 M1 Column） */
export interface Column {
  name: string
  label: string
  render?: RenderType
  tagMap?: Record<string, string>
  refTable?: string
  refLabel?: string
}

/** 顶部筛选 */
export interface Filter {
  name: string
  label: string
  options?: string[]
}

/** 行内操作（对应 M1 Action） */
export interface Action {
  label: string
  behavior: string
  params?: Field[]
  confirm?: string
  visibleWhen?: Record<string, string>
  rowClick?: string
}

/** 页面组成单元（对应 M1 Block） */
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

/** 页面（对应 M1 Page） */
export interface Page {
  id: string
  title: string
  icon?: string
  blocks: Block[]
}

/** App Schema（对应 M1 AppSchema 主单据） */
export interface AppSchema {
  name: string
  version: string
  sourceProject: string
  pages: Page[]
}

/** 校验问题（对应 M3 规则违规） */
export interface SchemaIssue {
  code: string
  message: string
  pageId?: string
  path?: string
}
