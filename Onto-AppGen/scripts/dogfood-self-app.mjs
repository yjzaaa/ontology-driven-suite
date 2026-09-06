// Dogfood 端到端：Onto-AppGen 用自身本体模型（workbench-v3）生成它自己的应用
// 证明：工作台 V3 首先是一个应用（由本体模型生成），之后才作为插件被引用
import { readFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { load as yaml } from 'js-yaml'
import { buildModelIndex, validateSchema } from '../src/validator.ts'
import { generateSchemaApp } from '../src/generator.ts'

const here = dirname(fileURLToPath(import.meta.url))
const projectDir = join(here, '..')

// 1. 读自身本体模型（M1 + M2）
const m1 = yaml(readFileSync(join(projectDir, 'model', 'm1-object-model.yaml'), 'utf-8'))
const m2 = yaml(readFileSync(join(projectDir, 'model', 'm2-behavior-model.yaml'), 'utf-8'))
const idx = buildModelIndex(m1, m2)
console.log('自身 M1 表:', [...idx.tables].join(', '))
console.log('自身 M2 行为:', [...idx.behaviors].join(', '))

// 2. LLM 风格 App Schema：本体工作台 V3 自己的页面（模型视图/图谱/编辑/应用生成）
const schema = {
  name: '本体工作台 V3', version: '1.0', sourceProject: 'workbench-v3',
  pages: [
    {
      id: 'models', title: '本体模型', icon: 'ApartmentOutlined',
      blocks: [
        { type: 'table', title: '本体模型清单', entity: 'AppSchema',
          columns: [
            { name: 'name', label: '应用名' },
            { name: 'version', label: '版本' },
            { name: 'sourceProject', label: '来源项目' },
          ] },
      ],
    },
    {
      id: 'pages', title: '页面组织', icon: 'LayoutOutlined',
      blocks: [
        { type: 'table', title: '页面清单', entity: 'Page',
          columns: [
            { name: 'id', label: '页面 id' },
            { name: 'title', label: '标题' },
          ] },
        { type: 'form', title: '登记页面', entity: 'Page', behavior: 'Schema_Generate',
          fields: [
            { name: 'id', label: '页面 id', control: 'input', required: true },
            { name: 'title', label: '标题', control: 'input', required: true },
          ] },
      ],
    },
    {
      id: 'validate', title: 'Schema 校验', icon: 'CheckCircleOutlined',
      blocks: [
        { type: 'table', title: '校验问题清单', entity: 'Block',
          columns: [
            { name: 'type', label: 'Block 类型' },
            { name: 'title', label: '标题' },
          ] },
      ],
    },
  ],
}

// 3. 校验（引用自身模型）
const issues = validateSchema(schema, idx)
console.log('\n校验:', issues.length === 0 ? '通过 ✅' : '失败 ❌')
if (issues.length) { console.log(issues); process.exit(1) }

// 4. 生成应用（Onto-AppGen 自己的 app/）
const app = generateSchemaApp(projectDir, schema, m1, m2)
console.log('生成应用:', app.appDir)
console.log('tables:', app.tables.map(t => t.table).join(', '))
console.log('behaviors:', app.behaviors.map(b => b.id).join(', '))
console.log('files:', app.files.join(', '))
