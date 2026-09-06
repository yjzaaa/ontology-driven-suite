// 从 DSH 仓库根运行：npx tsx D:/sharptoolbox/Onto-AppGen/scripts/verify-plugin.mjs
// 验证 DSH 插件层（ontology_app 工具）可加载并正确工作
import { apply } from 'file:///D:/sharptoolbox/Onto-AppGen/dsh-plugin/index.ts'

const tools = new Map()
const ctx = {
  tools: { register: (d) => tools.set(d.name, d) },
  systemPrompt: { section: () => {} },
  on: () => {}, get: () => undefined, inject: () => {},
}
apply(ctx)

console.log('插件名:', 'onto-appgen (via apply)')
console.log('注册工具:', [...tools.keys()].join(', '))

const tool = tools.get('ontology_app')

// 1. validate 合法 schema
const schema = {
  name: '工作台', version: '1.0', sourceProject: 'workbench-v3',
  pages: [
    { id: 'p1', title: '模型', blocks: [{ type: 'table', title: '清单', entity: 'AppSchema', columns: [{ name: 'name', label: '应用名' }] }] },
    { id: 'p2', title: '登记', blocks: [{ type: 'form', title: '登记', entity: 'Page', behavior: 'Schema_Generate', fields: [{ name: 'id', label: 'id', control: 'input', required: true }] }] },
  ],
}
const v = await tool.execute({ action: 'validate', schema }, {})
console.log('\nvalidate 合法 schema:', v.valid ? '通过 ✅' : '失败 ❌', 'issues:', JSON.stringify(v.issues))

// 2. validate 非法控件
const bad = { ...schema, pages: [{ id: 'p1', title: 'P', blocks: [{ type: 'form', title: 'F', entity: 'Page', fields: [{ name: 'a', label: 'A', control: 'slider' }] }] }] }
const vb = await tool.execute({ action: 'validate', schema: bad }, {})
console.log('validate 非法控件:', vb.valid ? '（漏检）' : '拦截 ✅', vb.issues?.[0]?.code)

// 3. generate（产物=数据）
const g = await tool.execute({ action: 'generate', schema }, {})
console.log('\ngenerate:', g.generated ? '成功 ✅' : '失败')
console.log('  projectDir:', g.projectDir)
console.log('  files:', g.files.join(', '))
console.log('  tables:', g.tables.map(t => t.table).join(', '))
console.log('  behaviors:', g.behaviors.map(b => b.id).join(', '))

// 4. run（spawn 固定引擎 + 行为 API）
const r = await tool.execute({ action: 'run', projectDir: g.projectDir, port: 4404 }, {})
console.log('\nrun:', r.running ? '启动 ✅' : '失败')
if (r.running && r.url) {
  const create = await (await fetch(r.url + '/api/behavior/Schema_Generate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: 'X', version: '1', sourceProject: 'demo', pages: [] }) })).json()
  console.log('  run 后行为 API:', create.ok ? '可用 ✅' : '不可用 ❌', create.ok ? ('row=' + JSON.stringify(create.row)) : JSON.stringify(create))
  const html = await (await fetch(r.url + '/')).text()
  // 本地构建版渲染器：检查 schema 注入 + renderer.js 引用（不再是 CDN antd 字符串）
  console.log('  run 后渲染器:', (html.includes('__SCHEMA__') && html.includes('renderer.js')) ? '加载 ✅' : '❌')
  // 收尾：杀掉引擎子进程，避免阻塞脚本退出
  if (r.pid) { try { process.kill(r.pid) } catch { /* noop */ } }
}
console.log('\n全部验证完成')
process.exit(0)
