/**
 * TableBlock：列表 + 筛选 + 行内操作（antd Table + Formily 弹窗表单）。
 */
import React, { useEffect, useState } from 'react'
import { createForm } from '@formily/core'
import { Table, Tag, Button, Modal, Space, message, Select } from 'antd'
import type { Block, Action } from './schema'
import { ActionParamsForm } from './FormBlock'

async function api(path: string, opts?: RequestInit) {
  const r = await fetch(path, opts)
  const j = await r.json()
  if (!r.ok) throw new Error(j.error || JSON.stringify(j))
  return j
}

export function TableBlock({ block, onRefresh }: { block: Block; onRefresh?: () => void }) {
  const [rows, setRows] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState<Record<string, any>>({})
  const [modal, setModal] = useState<{ action: Action; row: any } | null>(null)
  const [detail, setDetail] = useState<any>(null)
  const [modalForm] = useState(() => createForm())

  const load = async () => {
    setLoading(true)
    try {
      const qs = Object.entries(filters).filter(([, v]) => v).map(([k, v]) => k + '=' + encodeURIComponent(v)).join('&')
      const j = await api('/api/entity/' + block.entity + (qs ? '?' + qs : ''))
      setRows(j.rows || [])
    } catch (e: any) { message.error(String(e.message || e)) }
    finally { setLoading(false) }
  }
  useEffect(() => { load() }, [block, JSON.stringify(filters)])

  const colTag = (val: any, tagMap?: Record<string, string>) =>
    tagMap && tagMap[val] ? <Tag color={tagMap[val]}>{val}</Tag> : <Tag>{String(val ?? '-')}</Tag>

  const runAction = async (action: Action, row: any) => {
    try {
      if (action.params && action.params.length) await modalForm.validate()
      const payload = { ...modalForm.values, ...row }
      await api('/api/behavior/' + action.behavior, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
      message.success('操作成功')
      setModal(null); modalForm.reset(); load(); onRefresh && onRefresh()
    } catch (e: any) {
      if (!(e?.errorFields)) message.error(String(e.message || e))
    }
  }

  const columns = [
    ...(block.columns ?? []).map(c => ({
      title: c.label, dataIndex: c.name, key: c.name,
      render: (v: any) => c.render === 'tag' ? colTag(v, c.tagMap) : (v ?? '-'),
    })),
    ...((block.actions ?? []).length ? [{
      title: '操作', key: '_actions', render: (_: any, row: any) => (
        <Space>
          {(block.actions ?? []).map(a => {
            const visible = !a.visibleWhen || Object.entries(a.visibleWhen).every(([k, v]) => row[k] === v)
            if (!visible) return null
            return (
              <Button key={a.label} size="small" type="link"
                onClick={() => {
                  if (a.confirm) Modal.confirm({ title: a.confirm, onOk: () => runAction(a, row) })
                  else if (a.params && a.params.length) { modalForm.reset(); setModal({ action: a, row }) }
                  else runAction(a, row)
                }}
              >{a.label}</Button>
            )
          })}
        </Space>
      ),
    }] : []),
  ]

  return (
    <div className="block-card">
      <div className="block-title">{block.title}</div>
      {(block.filters ?? []).length > 0 && (
        <Space style={{ marginBottom: 12 }} wrap>
          {(block.filters ?? []).map(f => (
            <Select key={f.name} placeholder={f.label} allowClear style={{ width: 160 }}
              value={filters[f.name]} onChange={v => setFilters(s => ({ ...s, [f.name]: v }))}>
              {(f.options ?? []).map(o => <Select.Option key={o} value={o}>{o}</Select.Option>)}
            </Select>
          ))}
        </Space>
      )}
      <Table rowKey={(block.entity ?? 'row') + '_id'} size="small" loading={loading} dataSource={rows} columns={columns as any}
        pagination={{ pageSize: 10, showSizeChanger: true }}
        onRow={r => ({ onClick: () => block.rowClick && setDetail(r) })} />
      <Modal title={modal?.action?.label} open={!!modal} onOk={() => modal && runAction(modal.action, modal.row)} onCancel={() => setModal(null)} destroyOnClose>
        {modal && <ActionParamsForm fields={modal.action.params ?? []} form={modalForm} />}
      </Modal>
      <Modal title="详情" open={!!detail} footer={null} onCancel={() => setDetail(null)}>
        {detail && <Table size="small" rowKey="k" pagination={false} dataSource={Object.entries(detail).map(([k, v]) => ({ k, v }))}
          columns={[{ title: '字段', dataIndex: 'k' }, { title: '值', dataIndex: 'v' }]} />}
      </Modal>
    </div>
  )
}