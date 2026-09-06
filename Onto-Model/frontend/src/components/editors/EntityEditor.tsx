import React, { useState, useEffect, useMemo } from 'react';
import { Descriptions, Form, Input, Select, Table, Tag } from 'antd';
import { Entity } from '../../types/models';
import { ObjectModelNode } from '../../services/modelIndex';

interface EntityEditorProps {
  entity: Entity | ObjectModelNode | any;
  onChange: (entity: any) => void;
}

const EntityEditor: React.FC<EntityEditorProps> = ({ entity, onChange }) => {
  const [form] = Form.useForm();
  const objectNode = entity?.raw ? entity as ObjectModelNode : null;
  const rawEntity = useMemo(() => objectNode?.raw || entity || {}, [entity, objectNode]);
  const [attributes, setAttributes] = useState<any[]>(rawEntity.attributes || []);

  const normalizeAttribute = (attr: any, index: number) => {
    if (typeof attr === 'string') {
      return {
        name: attr,
        label: attr,
        type: '-',
        required: false,
        key: `${attr}-${index}`
      };
    }
    return {
      ...attr,
      key: attr?.name || index
    };
  };

  const normalizedAttributes = attributes.map(normalizeAttribute);
  const constraints = [
    ...(Array.isArray(rawEntity.constraints) ? rawEntity.constraints : []),
    ...(Array.isArray(rawEntity.aggregateConstraints) ? rawEntity.aggregateConstraints : []),
    ...(Array.isArray(rawEntity.invariants) ? rawEntity.invariants : [])
  ];
  const compositions = Array.isArray(rawEntity.compositions) ? rawEntity.compositions : [];
  const internalEntities = [
    ...(Array.isArray(rawEntity.internalEntities) ? rawEntity.internalEntities : []),
    ...(Array.isArray(rawEntity.entities) ? rawEntity.entities : [])
  ];

  // antd 5.x 已废弃 rowKey 函数的 index 参数，这里给每条记录生成稳定的 key，
  // 避免依赖行索引（索引在数据变化时不稳定，会导致列表状态错乱）。
  const compositionRows = compositions.map((row: any, i: number) => ({
    ...row,
    rowKey: row?.alias || row?.targetEntity || row?.name || `composition-${i}`
  }));
  const internalEntityRows = internalEntities.map((row: any, i: number) => ({
    ...row,
    rowKey: row?.alias || row?.name || `internal-${i}`
  }));
  const constraintRows = constraints.map((row: any, i: number) => ({
    ...row,
    rowKey: row?.name || row?.constraintType || row?.expression || `constraint-${i}`
  }));

  useEffect(() => {
    form.setFieldsValue({
      id: rawEntity.id || objectNode?.id,
      name: rawEntity.name || objectNode?.name,
      alias: rawEntity.alias || objectNode?.alias,
      description: rawEntity.description,
      lifecycle: rawEntity.lifecycle || []
    });
    setAttributes(rawEntity.attributes || []);
  }, [entity, form, objectNode?.alias, objectNode?.id, objectNode?.name, rawEntity]);

  const handleFormChange = () => {
    const values = form.getFieldsValue();
    const updatedRaw = {
      ...rawEntity,
      ...values,
      attributes
    };

    if (!updatedRaw.id) {
      delete updatedRaw.id;
    }

    onChange({
      ...(objectNode || {}),
      raw: objectNode ? updatedRaw : undefined,
      ...(!objectNode ? updatedRaw : {})
    });
  };

  const attributeColumns = [
    { title: '属性名', dataIndex: 'name', key: 'name' },
    { title: '标签', dataIndex: 'label', key: 'label' },
    { title: '类型', dataIndex: 'type', key: 'type' },
    { title: '必填', dataIndex: 'required', key: 'required', render: (val: boolean) => val ? '是' : '否' },
  ];

  const constraintColumns = [
    { title: '名称/类型', key: 'name', render: (_: any, row: any) => row.name || row.constraintType || '-' },
    { title: '表达式', dataIndex: 'expression', key: 'expression' },
    { title: '执行时机', dataIndex: 'enforcedAt', key: 'enforcedAt' },
    { title: '提示', dataIndex: 'violationMessage', key: 'violationMessage' }
  ];

  const compositionColumns = [
    { title: '组合别名', dataIndex: 'alias', key: 'alias' },
    { title: '子对象', dataIndex: 'targetEntity', key: 'targetEntity' },
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '基数', dataIndex: 'cardinality', key: 'cardinality' },
    { title: '级联', key: 'cascade', render: (_: any, row: any) => row.cascade || (row.cascadeDelete ? 'ALL' : '-') }
  ];

  return (
    <div style={{ padding: 24 }}>
      <h2>对象编辑: {rawEntity.name || objectNode?.name}</h2>

      {objectNode && (
        <Descriptions bordered column={1} style={{ marginBottom: 24 }}>
          <Descriptions.Item label="对象类型">
            <Tag color={objectNode.kind === 'aggregate' ? 'purple' : 'blue'}>
              {objectNode.kind}
            </Tag>
          </Descriptions.Item>
          {objectNode.aggregateName && (
            <Descriptions.Item label="所属聚合">{objectNode.aggregateName}</Descriptions.Item>
          )}
        </Descriptions>
      )}

      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleFormChange}
      >
        <Form.Item label="对象ID" name="id">
          <Input disabled />
        </Form.Item>
        <Form.Item label="对象名称" name="name" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="别名" name="alias">
          <Input />
        </Form.Item>
        <Form.Item label="生命周期" name="lifecycle">
          <Select mode="tags" placeholder="输入生命周期状态" />
        </Form.Item>
        <Form.Item label="描述" name="description">
          <Input.TextArea rows={4} />
        </Form.Item>
      </Form>

      <h3>属性列表</h3>
      <Table
        dataSource={normalizedAttributes}
        columns={attributeColumns}
        rowKey="name"
        pagination={false}
      />

      {compositions.length > 0 && (
        <>
          <h3 style={{ marginTop: 24 }}>组合子对象</h3>
          <Table
            dataSource={compositionRows}
            columns={compositionColumns}
            rowKey="rowKey"
            pagination={false}
          />
        </>
      )}

      {internalEntities.length > 0 && (
        <>
          <h3 style={{ marginTop: 24 }}>聚合内子对象</h3>
          <Table
            dataSource={internalEntityRows}
            columns={[
              { title: '名称', dataIndex: 'name', key: 'name' },
              { title: '别名', dataIndex: 'alias', key: 'alias' },
              { title: '属性数', key: 'attributes', render: (_: any, row: any) => row.attributes?.length || 0 }
            ]}
            rowKey="rowKey"
            pagination={false}
          />
        </>
      )}

      {constraints.length > 0 && (
        <>
          <h3 style={{ marginTop: 24 }}>约束</h3>
          <Table
            dataSource={constraintRows}
            columns={constraintColumns}
            rowKey="rowKey"
            pagination={false}
          />
        </>
      )}
    </div>
  );
};

export default EntityEditor;
