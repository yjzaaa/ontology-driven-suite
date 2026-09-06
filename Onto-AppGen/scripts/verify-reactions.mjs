// 联动验证：Formily x-reactions 控件联动显隐实测（用临时目录，不污染主 app/）
// schema：故障类型（下拉） + 故障描述（visibleWhen：仅当故障类型=硬件故障时显示）
import { readFileSync, mkdtempSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { tmpdir } from 'node:os'
import { load as yaml } from 'js-yaml'
import { spawn } from 'node:child_process'
import { buildModelIndex, validateSchema } from '../src/validator.ts'
import { generateData } from '../src/generator.ts'

const here = dirname(fileURLToPath(import.meta.url))
const projectDir = join(here, '..')
const m1 = yaml(readFileSync(join(projectDir, 'model', 'm1-object-model.yaml'), 'utf-8'))
const m2 = yaml(readFileSync(join(projectDir, 'model', 'm2-behavior-model.yaml'), 'utf-8'))
const idx = buildModelIndex(m1, m2)

// 带联动的 schema：故障描述仅当故障类型='硬件故障' 时显示
const schema = {
  name: '联动验证', version: '1.0', sourceProject: 'workbench-v3',
  pages: [
    { id: 'p1', title: '联动表单', blocks: [
      { type: 'form', title: '报修登记', entity: 'AppSchema', behavior: 'Schema_Generate', fields: [
        { name: 'faultType', label: '故障类型', control: 'select', options: ['硬件故障', '软件故障', '网络故障'], required: true },
        { name: 'faultDesc', label: '故障描述', control: 'textarea', visibleWhen: { faultType: '硬件故障' } },
        { name: 'name', label: '应用名', control: 'input', required: true },
        { name: 'version', label: '版本', control: 'input', required: true },
        { name: 'sourceProject', label: '来源项目', control: 'input', required: true },
      ] },
    ] },
  ],
}

const issues = validateSchema(schema, idx)
console.log('校验:', issues.length === 0 ? '通过 ✅' : '失败 ❌')
if (issues.length) process.exit(1)

const tmp = mkdtempSync(join(tmpdir(), 'oag-react-'))
generateData(tmp, schema, m1, m2)
console.log('数据产物（临时）:', tmp)

const engineJs = join(projectDir, 'engine', 'engine.cjs')
const child = spawn(process.execPath, [engineJs, '--project', join(tmp, 'app'), '--port', '4411'], { stdio: ['ignore', 'pipe', 'pipe'] })
let buf = ''
child.stdout.on('data', d => {
  buf += d.toString()
  const m = buf.match(/APP_READY (\S+)/)
  if (m) { console.log('ENGINE_URL=' + m[1]); }
})
child.stderr.on('data', d => process.stderr.write(String(d)))
child.on('error', e => { console.error('启动失败:', e.message); process.exit(1) })
// 保持运行（供后续 Puppeteer 验证），由外层命令管理生命周期
process.on('SIGINT', () => { child.kill(); process.exit(0) })