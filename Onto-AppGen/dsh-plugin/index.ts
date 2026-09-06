/**
 * Onto-AppGen DSH 插件层（薄适配层）
 *
 * 核心机制（协议/校验器/生成器/固定引擎/渲染器）留在独立项目 Onto-AppGen；
 * 本模块只是把 Onto-AppGen 的能力封装成 DSH 可调用的工具：
 *   - ontology_app：LLM 读本体模型 → 生成 App Schema → 校验 → 生成数据产物 → 启动固定引擎运行
 *
 * 通过 DSH 的 cordis.yml 覆盖层以本地绝对路径插件加载（见 dsh-plugin/cordis.yml）。
 * 不修改 DSH 源码，不改动 packages/。
 */

import type { Context } from '@deepseek-ai/cordis'
import type {} from '@deepseek-ai/dsh-system-prompt'
import type { ContentBlock } from '@deepseek-ai/dsh-llm'
import { defineTool } from '@deepseek-ai/dsh-tools'
import { join, dirname } from 'node:path'
import { existsSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { spawn } from 'node:child_process'
import { load as yaml } from 'js-yaml'
import { buildModelIndex, validateSchema } from '../src/validator.js'
import { generateData } from '../src/generator.js'
import type { AppSchema } from '../src/types.js'

/** Cordis 插件名。 */
export const name = 'onto-appgen'
/** 需要的服务：工具注册 + 系统提示组装。 */
export const inject = ['tools', 'systemPrompt']

/** 本项目根目录（dsh-plugin/ 的上级） */
const here = dirname(fileURLToPath(import.meta.url))
const projectRoot = join(here, '..')
const modelDir = join(projectRoot, 'model')
const engineJs = join(projectRoot, 'engine', 'engine.cjs')

/** 统一 output：schema 用无约束 JSON，render 序列化为文本块。 */
const jsonOutput = {
  schema: { type: 'json' } as const,
  render: (_args: any, value: any): ContentBlock[] => [{ type: 'text', text: JSON.stringify(value, null, 2) }],
}

function requireString(v: unknown, label: string): string {
  if (typeof v !== 'string' || v.trim().length === 0) throw new Error(`invalid ${label}: expected a non-empty string`)
  return v.trim()
}

/** 读取项目模型（M1 + M2），供校验/生成。 */
function loadModels(): { m1: any; m2: any } {
  const read = (f: string) => yaml(readFileSync(join(modelDir, f), 'utf-8'))
  return { m1: read('m1-object-model.yaml'), m2: read('m2-behavior-model.yaml') }
}

/** 读取前端设计规范（skills/frontend-design/SKILL.md，去掉 frontmatter）。 */
function loadDesignSpec(): string {
  const p = join(projectRoot, 'skills', 'frontend-design', 'SKILL.md')
  if (!existsSync(p)) return ''
  const raw = readFileSync(p, 'utf-8')
  // 去掉 --- frontmatter --- 头，只留正文
  return raw.replace(/^---[\s\S]*?---\s*/, '').trim()
}

export function apply(ctx: Context): void {
  const designSpec = loadDesignSpec()
  ctx.systemPrompt.section({
    name: 'tool:onto-appgen',
    order: 116,
    text:
      '使用 `ontology_app` 生成应用：让 LLM 读取本体模型后生成 App Schema（页面组织决议），校验后生成数据产物（tables/behaviors/schema JSON），再用固定引擎运行（数据是唯一真相源，不生成代码）。'
      + '\n\n【前端设计规范 — 生成 UI Schema 时必须遵循】\n' + designSpec,
  })

  ctx.tools.register(defineTool({
    name: 'ontology_app',
    description:
      '基于 Onto-AppGen 从本体模型生成并运行应用（产物 = 数据，非代码）。'
      + '`validate`：校验 LLM 输出的 App Schema（引用 entity/behavior/refTable 指回模型、控件合法、页面 id 唯一、跳转目标存在）。'
      + '`generate`：校验通过后生成数据产物到 <projectDir>/app/（tables.json + behaviors.json + app.schema.json）。'
      + '`run`：用固定引擎 engine.cjs 启动该数据产物，返回可打开的 URL。'
      + '`read`：读取已落盘的 App Schema。',
    parameters: {
      action: { type: 'string', required: true, description: "'validate' | 'generate' | 'run' | 'read'" },
      schema: { type: 'object', additionalProperties: true, description: 'validate/generate 时的 App Schema 对象' },
      projectDir: { type: 'string', description: '目标项目目录（其 app/ 存数据产物）；默认 Onto-AppGen 自身项目' },
      port: { type: 'integer', description: 'run 时指定端口（默认随机）' },
    },
    output: jsonOutput,
    async execute(args: any) {
      const action = requireString(args.action, 'action')
      const target = args.projectDir ? requireString(args.projectDir, 'projectDir') : projectRoot
      const { m1, m2 } = loadModels()
      const idx = buildModelIndex(m1, m2)

      if (action === 'read') {
        const p = join(target, 'app', 'app.schema.json')
        if (!existsSync(p)) return { error: '未找到 app.schema.json，先调用 generate' }
        const schema = JSON.parse(readFileSync(p, 'utf-8'))
        return { schema }
      }

      if (action === 'validate') {
        const schema = args.schema as AppSchema
        if (!schema || typeof schema !== 'object') throw new Error('invalid schema: validate 需要 schema 对象')
        const issues = validateSchema(schema, idx)
        return {
          valid: issues.length === 0, issues,
          hint: issues.length ? '按 issues 修正 schema 后重新 validate' : '校验通过，可调用 generate',
        }
      }

      if (action === 'generate') {
        const schema = args.schema as AppSchema
        if (!schema || typeof schema !== 'object') throw new Error('invalid schema: generate 需要 schema 对象')
        const issues = validateSchema(schema, idx)
        if (issues.length > 0) {
          return { generated: false, issues, hint: 'Schema 未通过校验，禁止生成' }
        }
        const data = generateData(target, schema, m1, m2)
        return {
          generated: true, projectDir: data.projectDir, files: data.files,
          tables: data.tables, behaviors: data.behaviors,
          next: '调用 run 启动应用',
        }
      }

      if (action === 'run') {
        const appDir = join(target, 'app')
        if (!existsSync(join(appDir, 'tables.json'))) return { error: '数据产物不存在，先调用 generate' }
        const port = typeof args.port === 'number' ? args.port : 0
        return new Promise<{ running: boolean; url: string; pid: number | null }>((resolve, reject) => {
          const child = spawn(process.execPath, [engineJs, '--project', appDir, '--port', String(port)], { stdio: ['ignore', 'pipe', 'pipe'] })
          const timer = setTimeout(() => { try { child.kill() } catch { /* noop */ } ; reject(new Error('应用启动超时（10s）')) }, 10000)
          let buf = ''
          child.stdout.on('data', (d: Buffer) => {
            buf += d.toString()
            const m = buf.match(/APP_READY (\S+)/)
            if (m) {
              clearTimeout(timer)
              // unref：让引擎子进程独立运行，不阻塞父进程退出
              child.unref()
              resolve({ running: true, url: m[1]!, pid: child.pid ?? null })
            }
          })
          child.on('error', (e) => { clearTimeout(timer); reject(e) })
          child.stderr.on('data', (d: Buffer) => console.error('[ontology_app run]', d.toString()))
        })
      }

      throw new Error(`invalid action: ${action} (expect validate|generate|run|read)`)
    },
  }))
}