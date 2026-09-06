import React, { useState } from 'react'
import ReactDOM from 'react-dom/client'
import { Layout, Menu, Typography, ConfigProvider, theme as antdTheme } from 'antd'
import type { AppSchema, Block } from './schema'
import { FormBlock } from './FormBlock'
import { TableBlock } from './TableBlock'
import { themeToken, themeComponents } from './theme'

const { Sider, Content } = Layout

declare global {
  interface Window { __SCHEMA__?: AppSchema }
}
const SCHEMA: AppSchema = window.__SCHEMA__ ?? { name: '应用', version: '1.0', sourceProject: '', pages: [] }

function BlockView({ block }: { block: Block }) {
  if (block.type === 'form') return <FormBlock block={block} />
  if (block.type === 'table') return <TableBlock block={block} />
  return <div className="block-card">暂未支持的 Block: {block.type}</div>
}

function App() {
  const [active, setActive] = useState(SCHEMA.pages[0]?.id)
  const current = SCHEMA.pages.find(p => p.id === active) ?? SCHEMA.pages[0]
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider className="app-sider" width={200}>
        <div className="app-logo">{SCHEMA.name}</div>
        <Menu theme="dark" mode="inline" selectedKeys={current ? [current.id] : []}
          onClick={e => setActive(e.key)}
          items={SCHEMA.pages.map(p => ({ key: p.id, label: p.title }))} />
      </Sider>
      <Layout>
        <Content className="app-content">
          <Typography.Title level={4} style={{ marginTop: 0 }}>{current?.title}</Typography.Title>
          {(current?.blocks ?? []).map((b, i) => <BlockView key={i} block={b} />)}
        </Content>
      </Layout>
    </Layout>
  )
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <ConfigProvider theme={{ algorithm: antdTheme.defaultAlgorithm, token: themeToken, components: themeComponents }}>
    <App />
  </ConfigProvider>
)