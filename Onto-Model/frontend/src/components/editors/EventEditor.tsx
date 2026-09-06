import React, { useEffect } from 'react';
import { Form, Input, Select } from 'antd';
import { Event } from '../../types/models';

interface EventEditorProps {
  event: Event;
  onChange: (event: Event) => void;
  availableBehaviors?: string[];
}

const EventEditor: React.FC<EventEditorProps> = ({ 
  event, 
  onChange,
  availableBehaviors = []
}) => {
  const [form] = Form.useForm();

  useEffect(() => {
    form.setFieldsValue(event);
  }, [event, form]);

  const handleFormChange = () => {
    const values = form.getFieldsValue();
    onChange({
      ...event,
      ...values
    });
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>编辑事件: {event.eventName}</h2>
      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleFormChange}
      >
        <Form.Item label="事件ID" name="eventId">
          <Input disabled />
        </Form.Item>
        <Form.Item label="事件名称" name="eventName" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item label="描述" name="description">
          <Input.TextArea rows={4} />
        </Form.Item>
        <Form.Item label="生产者行为" name="producerBehaviorRef" rules={[{ required: true }]}>
          <Select placeholder="选择生产者行为">
            {availableBehaviors.map(behaviorId => (
              <Select.Option key={behaviorId} value={behaviorId}>{behaviorId}</Select.Option>
            ))}
          </Select>
        </Form.Item>
        <Form.Item label="订阅者行为" name="subscriberBehaviorRefs">
          <Select mode="multiple" placeholder="选择订阅者行为">
            {availableBehaviors.map(behaviorId => (
              <Select.Option key={behaviorId} value={behaviorId}>{behaviorId}</Select.Option>
            ))}
          </Select>
        </Form.Item>
        <Form.Item label="触发条件" name="triggerCondition">
          <Input.TextArea rows={2} />
        </Form.Item>
        <Form.Item label="事件顺序" name="ordering">
          <Select>
            <Select.Option value="AT_LEAST_ONCE">AT_LEAST_ONCE</Select.Option>
            <Select.Option value="EXACTLY_ONCE">EXACTLY_ONCE</Select.Option>
            <Select.Option value="BEST_EFFORT">BEST_EFFORT</Select.Option>
          </Select>
        </Form.Item>
      </Form>
    </div>
  );
};

export default EventEditor;
