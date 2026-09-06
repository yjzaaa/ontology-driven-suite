import React, { useEffect } from 'react';
import { Form, Input, Select, Tag, Space, Descriptions } from 'antd';
import { Rule } from '../../types/models';

interface RuleEditorProps {
  rule: Rule;
  onChange: (rule: Rule) => void;
}

const RuleEditor: React.FC<RuleEditorProps> = ({ rule, onChange }) => {
  const [form] = Form.useForm();

  useEffect(() => {
    form.setFieldsValue(rule);
  }, [rule, form]);

  const handleFormChange = () => {
    const values = form.getFieldsValue();
    onChange({
      ...rule,
      ...values
    });
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>规则详情: {rule.name}</h2>
      
      <Descriptions bordered column={1} style={{ marginBottom: 24 }}>
        <Descriptions.Item label="规则ID">{rule.id}</Descriptions.Item>
        <Descriptions.Item label="规则类型">
          <Tag color="blue">{rule.ruleType}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="版本">{rule.version || '1.0'}</Descriptions.Item>
        <Descriptions.Item label="输出类型">{rule.outputType || 'Boolean'}</Descriptions.Item>
      </Descriptions>

      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleFormChange}
      >
        <Form.Item label="规则名称" name="name" rules={[{ required: true }]}>
          <Input />
        </Form.Item>

        <Form.Item label="规则类型" name="ruleType">
          <Select>
            <Select.Option value="VALIDATION">VALIDATION（验证规则）</Select.Option>
            <Select.Option value="CALCULATION">CALCULATION（计算规则）</Select.Option>
            <Select.Option value="DERIVATION">DERIVATION（推导规则）</Select.Option>
            <Select.Option value="TRANSFORMATION">TRANSFORMATION（转换规则）</Select.Option>
            <Select.Option value="RISK">RISK（风控规则）</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item label="描述" name="description">
          <Input.TextArea rows={4} />
        </Form.Item>

        <Form.Item label="规则表达式" name="expression">
          <Input.TextArea 
            rows={8} 
            placeholder="输入规则表达式，如：totalAmount > 0 AND externalPurchaseAmount <= totalAmount"
            style={{ fontFamily: 'monospace' }}
          />
        </Form.Item>

        <Form.Item label="违规提示消息" name="violationMessage">
          <Input.TextArea rows={2} />
        </Form.Item>

        <Form.Item label="输出类型" name="outputType">
          <Input placeholder="如：Boolean, Decimal, ValidationResult" />
        </Form.Item>

        <Form.Item label="版本" name="version">
          <Input placeholder="如：1.0, 2.1" />
        </Form.Item>
      </Form>

      {rule.inputParams && rule.inputParams.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h3>输入参数</h3>
          <Space direction="vertical" style={{ width: '100%' }}>
            {rule.inputParams.map((param: any, idx: number) => (
              <div key={idx} style={{ 
                padding: 12, 
                background: '#f5f5f5', 
                borderRadius: 4,
                border: '1px solid #d9d9d9'
              }}>
                <div><strong>参数名:</strong> {param.name}</div>
                <div><strong>类型:</strong> {param.type}</div>
                {param.sourceField && (
                  <div><strong>来源字段:</strong> {param.sourceField}</div>
                )}
              </div>
            ))}
          </Space>
        </div>
      )}

      {rule.reusedBy && rule.reusedBy.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h3>被以下行为引用</h3>
          <Space wrap>
            {rule.reusedBy.map((behaviorId: string) => (
              <Tag key={behaviorId} color="green">{behaviorId}</Tag>
            ))}
          </Space>
        </div>
      )}
    </div>
  );
};

export default RuleEditor;
