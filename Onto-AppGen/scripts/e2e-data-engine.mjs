// 端到端验证：数据产物 + 固定引擎（第一阶段「平台内跑」）
// 流程：读本体模型 → schema → 校验 → 产数据(tables/behaviors/schema JSON) → 固定引擎启动 → 行为 API + 渲染验证
import { readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { load as yaml } from 'js-yaml'
import { spawn } from 'node:child_process'
import { buildModelIndex, validateSchema } from '../src/validator.ts'
import { generateData } from '../src/generator.ts'

const here = dirname(fileURLToPath(import.meta.url))
const projectDir = join(here, '..')

// 1. 读本体模型
const m1 = yaml(readFileSync(join(projectDir, 'model', 'm1-object-model.yaml'), 'utf-8'))
const m2 = yaml(readFileSync(join(projectDir, 'model', 'm2-behavior-model.yaml'), 'utf-8'))
const idx = buildModelIndex(m1, m2)
console.log('M1 表:', [...idx.tables].join(', '))
console.log('M2 行为:', [...idx.behaviors].join(', '))

// 2. schema（LLM 生成的页面组织）
const schema = {
  name: '本体工作台 V3', version: '1.0', sourceProject: 'workbench-v3',
  pages: [
    { id: 'models', title: '本体模型', blocks: [
      { type: 'form', title: '登记应用', entity: 'AppSchema', behavior: 'Schema_Generate', fields: [
        { name: 'name', label: '应用名', control: 'input', required: true },
        { name: 'version', label: '版本', control: 'input', required: true },
        { name: 'sourceProject', label: '来源项目', control: 'input', required: true },
      ] },
      { type: 'table', title: '本体模型清单', entity: 'AppSchema', columns: [
        { name: 'name', label: '应用名' }, { name: 'version', label: '版本' },
      ] },
    ] },
  ],
}

// 3. 校验
const issues = validateSchema(schema, idx)
console.log('校验:', issues.length === 0 ? '通过 ✅' : '失败 ❌')
if (issues.length) { console.log(issues); process.exit(1) }

// 4. 生成数据产物（不生成代码）
const data = generateData(projectDir, schema, m1, m2)
console.log('数据产物:', data.files.join(', '))
console.log('tables:', data.tables.map(t => t.table).join(', '))

// 5. 固定引擎启动（读数据产物）
const engineJs = join(projectDir, 'engine', 'engine.cjs')
const appDir = join(projectDir, 'app')
const child = spawn(process.execPath, [engineJs, '--project', appDir, '--port', '4402'], { stdio: ['ignore', 'pipe', 'pipe'] })
let buf = ''
child.stdout.on('data', d => { buf += d.toString(); const m = buf.match(/APP_READY (\S+)/); if (m) test(m[1]) })
child.stderr.on('data', d => process.stderr.write(String(d)))
child.on('error', e => { console.error('启动失败:', e.message); process.exit(1) })

async function test(url) {
  try {
    // 行为 API：新建（Schema_Generate，主键自动编号 + postconditions）
    const create = await (await fetch(url + '/api/behavior/Schema_Generate', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: '测试应用', version: '1.0', sourceProject: 'demo', pages: [] }) })).json()
    console.log('行为 API 新建:', JSON.stringify(create))
    // 列表查询
    const list = await (await fetch(url + '/api/entity/AppSchema')).json()
    console.log('列表 count:', list.count, '| 首行 name:', list.rows[0]?.name)
    // 渲染器页面
    const html = await (await fetch(url + '/')).text()
    console.log('渲染器:', html.includes('本体工作台 V3') ? '含应用名 ✅' : '缺应用名 ❌', '| antd:', html.includes('antd') ? '✅' : '❌')
    // 确认产物目录里没有代码文件（只有数据）
    const { readdirSync } = await import('node:fs')
    const files = readdirSync(appDir)
    console.log('app/ 目录内容:', files.join(', '))
    console.log('只有数据无代码:', !files.includes('app.cjs') && !files.includes('renderer.html') ? '✅' : '❌（还有代码副本）')
  } catch (e) { console.error('测试失败:', e.message) }
  finally { child.kill(); process.exit(0) }
}