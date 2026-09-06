import React, { useEffect } from 'react';
import { Form, Input, Select, Tag, Space } from 'antd';
import { Behavior } from '../../types/models';

interface BehaviorEditorProps {
  behavior: Behavior;
  onChange: (behavior: Behavior) => void;
  availableRules?: string[];
}

const BehaviorEditor: React.FC<BehaviorEditorProps> = ({ 
  behavior, 
  onChange,
  availableRules = []
}) => {
  const [form] = Form.useForm();

  useEffect(() => {
    form.setFieldsValue(behavior);
  }, [behavior, form]);

  const handleFormChange = () => {
    const values = form.getFieldsValue();
    onChange({
      ...behavior,
      ...values
    });
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>编辑行为: {behavior.name}</h2>
      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleFormChange}
      >
        <Form.Item label="行为ID" name="id">
          <Input disabled />
        </Form.Item>
        <Form.Item label="行为名称" name="name" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="所属实体" name="ownerEntity">
          <Input disabled />
        </Form.Item>
        <Form.Item label="行为类型" name="behaviorType">
          <Select>
            <Select.Option value="COMMAND">COMMAND</Select.Option>
            <Select.Option value="QUERY">QUERY</Select.Option>
            <Select.Option value="EVENT_HANDLER">EVENT_HANDLER</Select.Option>
          </Select>
        </Form.Item>
        <Form.Item label="触发类型" name="triggerType">
          <Select>
            <Select.Option value="USER_ACTION">USER_ACTION</Select.Option>
            <Select.Option value="SYSTEM">SYSTEM</Select.Option>
            <Select.Option value="EVENT">EVENT</Select.Option>
            <Select.Option value="EXTERNAL">EXTERNAL</Select.Option>
          </Select>
        </Form.Item>
        <Form.Item label="描述" name="description">
          <Input.TextArea rows={4} />
        </Form.Item>
        <Form.Item label="应用规则" name="appliedRules">
          <Select mode="multiple" placeholder="选择规则">
            {availableRules.map(ruleId => (
              <Select.Option key={ruleId} value={ruleId}>{ruleId}</Select.Option>
            ))}
          </Select>
        </Form.Item>
      </Form>

      {behavior.preconditions && behavior.preconditions.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <h3>前置条件</h3>
          <Space direction="vertical">
            {behavior.preconditions.map((cond, idx) => (
              <Tag key={idx}>{cond}</Tag>
            ))}
          </Space>
        </div>
      )}
    </div>
  );
};

export default BehaviorEditor;
