import React, { useEffect } from 'react';
import { Descriptions, Form, Input, Select, Table, Tag } from 'antd';

interface ActorEditorProps {
  itemType: 'actor' | 'role' | 'permission';
  data: any;
  onChange: (data: any) => void;
  availableRoles?: string[];
  availablePermissions?: string[];
  availableBehaviors?: string[];
}

const ActorEditor: React.FC<ActorEditorProps> = ({
  itemType,
  data,
  onChange,
  availableRoles = [],
  availablePermissions = [],
  availableBehaviors = []
}) => {
  const [form] = Form.useForm();

  useEffect(() => {
    form.setFieldsValue({
      ...data,
      targetRef: itemType === 'permission' && typeof data?.targetRef === 'string'
        ? [data.targetRef]
        : data?.targetRef
    });
  }, [data, form, itemType]);

  const handleFormChange = () => {
    const values = form.getFieldsValue();
    const targetRef = itemType === 'permission' && Array.isArray(values.targetRef)
      ? (values.targetRef.length === 1 ? values.targetRef[0] : values.targetRef)
      : values.targetRef;

    onChange({
      ...data,
      ...values,
      targetRef
    });
  };

  const titleMap = {
    actor: '主体',
    role: '角色',
    permission: '权限'
  };

  const renderAttributes = () => {
    if (!data?.attributes || itemType !== 'actor') return null;
    const rows = Object.entries(data.attributes).map(([key, value]) => ({ key, value }));
    return (
      <>
        <h3 style={{ marginTop: 24 }}>主体属性</h3>
        <Table
          dataSource={rows}
          columns={[
            { title: '属性', dataIndex: 'key', key: 'key' },
            { title: '值', dataIndex: 'value', key: 'value', render: (value: any) => `${value}` }
          ]}
          rowKey="key"
          pagination={false}
        />
      </>
    );
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>{titleMap[itemType]}维护: {data?.name || data?.actorId || data?.roleId || data?.permissionId}</h2>

      <Descriptions bordered column={1} style={{ marginBottom: 24 }}>
        <Descriptions.Item label="模型类型">
          <Tag color={itemType === 'permission' ? 'red' : itemType === 'role' ? 'purple' : 'blue'}>
            {titleMap[itemType]}
          </Tag>
        </Descriptions.Item>
      </Descriptions>

      <Form form={form} layout="vertical" onValuesChange={handleFormChange}>
        {itemType === 'actor' && (
          <>
            <Form.Item label="主体ID" name="actorId">
              <Input disabled />
            </Form.Item>
            <Form.Item label="主体名称" name="name" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item label="主体类型" name="actorType">
              <Select>
                <Select.Option value="HUMAN">HUMAN</Select.Option>
                <Select.Option value="SYSTEM">SYSTEM</Select.Option>
                <Select.Option value="EXTERNAL_SYSTEM">EXTERNAL_SYSTEM</Select.Option>
                <Select.Option value="SERVICE">SERVICE</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item label="关联角色" name="roles">
              <Select mode="multiple" placeholder="选择角色">
                {availableRoles.map(roleId => (
                  <Select.Option key={roleId} value={roleId}>{roleId}</Select.Option>
                ))}
              </Select>
            </Form.Item>
          </>
        )}

        {itemType === 'role' && (
          <>
            <Form.Item label="角色ID" name="roleId">
              <Input disabled />
            </Form.Item>
            <Form.Item label="角色名称" name="name" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item label="继承角色" name="inheritsFrom">
              <Select mode="multiple" placeholder="选择继承角色">
                {availableRoles.filter(roleId => roleId !== data?.roleId).map(roleId => (
                  <Select.Option key={roleId} value={roleId}>{roleId}</Select.Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item label="权限" name="permissions">
              <Select mode="multiple" placeholder="选择权限">
                {availablePermissions.map(permissionId => (
                  <Select.Option key={permissionId} value={permissionId}>{permissionId}</Select.Option>
                ))}
              </Select>
            </Form.Item>
          </>
        )}

        {itemType === 'permission' && (
          <>
            <Form.Item label="权限ID" name="permissionId">
              <Input disabled />
            </Form.Item>
            <Form.Item label="目标类型" name="targetType">
              <Select>
                <Select.Option value="BEHAVIOR">BEHAVIOR</Select.Option>
                <Select.Option value="OBJECT">OBJECT</Select.Option>
                <Select.Option value="SCENARIO">SCENARIO</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item label="目标引用" name="targetRef">
              <Select mode="tags" showSearch placeholder="选择目标行为">
                {availableBehaviors.map(behaviorId => (
                  <Select.Option key={behaviorId} value={behaviorId}>{behaviorId}</Select.Option>
                ))}
              </Select>
            </Form.Item>
            <Form.Item label="数据范围" name="dataScope">
              <Select>
                <Select.Option value="OWN">OWN</Select.Option>
                <Select.Option value="DEPT">DEPT</Select.Option>
                <Select.Option value="ALL">ALL</Select.Option>
              </Select>
            </Form.Item>
            <Form.Item label="ABAC条件" name="abacCondition">
              <Input.TextArea rows={4} />
            </Form.Item>
          </>
        )}
      </Form>

      {renderAttributes()}
    </div>
  );
};

export default ActorEditor;
