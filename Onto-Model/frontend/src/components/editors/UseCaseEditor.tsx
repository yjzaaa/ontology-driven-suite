import React from 'react';
import { Descriptions, Tag, Space, Timeline, Card, Divider } from 'antd';
import { 
  FunctionOutlined, 
  ThunderboltOutlined, 
  ApartmentOutlined,
  ClockCircleOutlined 
} from '@ant-design/icons';
import { UseCase } from '../../types/models';

interface UseCaseEditorProps {
  useCase: UseCase;
  workspace: any;
}

const UseCaseEditor: React.FC<UseCaseEditorProps> = ({ useCase, workspace }) => {
  const getStepIcon = (step: any) => {
    if (step.stepType === 'BEHAVIOR_CALL') {
      return <FunctionOutlined style={{ color: '#1890ff' }} />;
    } else if (step.stepType === 'EVENT_WAIT' || step.stepType === 'EVENT_EMIT') {
      return <ThunderboltOutlined style={{ color: '#faad14' }} />;
    } else if (step.stepType === 'GATEWAY') {
      return <ApartmentOutlined style={{ color: '#52c41a' }} />;
    }
    return <ClockCircleOutlined />;
  };

  const getStepTitle = (step: any) => {
    if (step.stepType === 'BEHAVIOR_CALL' && step.behaviorRef) {
      const behavior = workspace?.models?.behaviorModel?.behaviors?.find(
        (b: any) => b.id === step.behaviorRef
      );
      return (
        <div>
          <Tag color="blue">行为调用</Tag>
          <strong>{behavior?.name || step.behaviorRef}</strong>
        </div>
      );
    } else if (step.stepType === 'EVENT_WAIT' && step.waitForEvent) {
      const event = workspace?.models?.eventModel?.events?.find(
        (e: any) => e.eventId === step.waitForEvent
      );
      return (
        <div>
          <Tag color="orange">等待事件</Tag>
          <strong>{event?.eventName || step.waitForEvent}</strong>
          {step.timeout && <Tag color="red">超时: {step.timeout}</Tag>}
        </div>
      );
    } else if (step.stepType === 'EVENT_EMIT' && step.eventRef) {
      const event = workspace?.models?.eventModel?.events?.find(
        (e: any) => e.eventId === step.eventRef
      );
      return (
        <div>
          <Tag color="gold">发出事件</Tag>
          <strong>{event?.eventName || step.eventRef}</strong>
        </div>
      );
    } else if (step.stepType === 'GATEWAY') {
      return (
        <div>
          <Tag color="green">网关</Tag>
          <strong>{step.gatewayType}</strong>
          {step.condition && <div style={{ fontSize: 12, color: '#666' }}>条件: {step.condition}</div>}
        </div>
      );
    }
    return <Tag>{step.stepType}</Tag>;
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>{useCase.name}</h2>
      
      <Descriptions bordered column={1} style={{ marginBottom: 24 }}>
        <Descriptions.Item label="用例ID">{useCase.id}</Descriptions.Item>
        <Descriptions.Item label="描述">
          <div style={{ whiteSpace: 'pre-wrap' }}>{useCase.description}</div>
        </Descriptions.Item>
        {useCase.actors && useCase.actors.length > 0 && (
          <Descriptions.Item label="参与者">
            <Space wrap>
              {useCase.actors.map((actor: string) => (
                <Tag key={actor} color="purple">{actor}</Tag>
              ))}
            </Space>
          </Descriptions.Item>
        )}
      </Descriptions>

      {useCase.preconditions && useCase.preconditions.length > 0 && (
        <Card 
          title="前置条件" 
          size="small" 
          style={{ marginBottom: 16 }}
          headStyle={{ background: '#f0f5ff' }}
        >
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {useCase.preconditions.map((condition: string, idx: number) => (
              <li key={idx}>{condition}</li>
            ))}
          </ul>
        </Card>
      )}

      {useCase.postconditions && useCase.postconditions.length > 0 && (
        <Card 
          title="后置条件" 
          size="small" 
          style={{ marginBottom: 16 }}
          headStyle={{ background: '#f6ffed' }}
        >
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {useCase.postconditions.map((condition: string, idx: number) => (
              <li key={idx}>{condition}</li>
            ))}
          </ul>
        </Card>
      )}

      <Divider orientation="left">主流程 (Primary Flow)</Divider>
      
      {useCase.primaryFlow && useCase.primaryFlow.length > 0 ? (
        <Timeline mode="left" style={{ marginTop: 24 }}>
          {useCase.primaryFlow.map((step: any, index: number) => (
            <Timeline.Item 
              key={step.stepId}
              dot={getStepIcon(step)}
              label={<strong>步骤 {index + 1}</strong>}
            >
              <Card size="small" style={{ marginBottom: 8 }}>
                <div style={{ marginBottom: 8 }}>
                  {getStepTitle(step)}
                </div>
                {step.description && (
                  <div style={{ fontSize: 13, color: '#666', marginTop: 8 }}>
                    {step.description}
                  </div>
                )}
                {step.nextSteps && step.nextSteps.length > 0 && (
                  <div style={{ fontSize: 12, color: '#999', marginTop: 8 }}>
                    → 下一步: {step.nextSteps.join(', ')}
                  </div>
                )}
              </Card>
            </Timeline.Item>
          ))}
        </Timeline>
      ) : (
        <div style={{ color: '#999', textAlign: 'center', padding: 24 }}>
          暂无主流程定义
        </div>
      )}

      {useCase.alternativeFlows && useCase.alternativeFlows.length > 0 && (
        <>
          <Divider orientation="left">替代流程 (Alternative Flows)</Divider>
          <Space direction="vertical" style={{ width: '100%' }}>
            {useCase.alternativeFlows.map((flow: any) => (
              <Card 
                key={flow.id} 
                title={flow.name}
                size="small"
                headStyle={{ background: '#fffbe6' }}
              >
                <div><strong>触发点:</strong> {flow.triggerAt}</div>
                <div><strong>条件:</strong> {flow.condition}</div>
                {flow.steps && flow.steps.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <strong>步骤:</strong>
                    <ul style={{ marginTop: 4, paddingLeft: 20 }}>
                      {flow.steps.map((step: any, idx: number) => (
                        <li key={idx}>{step.description || step.stepType}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </Card>
            ))}
          </Space>
        </>
      )}

      {useCase.exceptionFlows && useCase.exceptionFlows.length > 0 && (
        <>
          <Divider orientation="left">异常流程 (Exception Flows)</Divider>
          <Space direction="vertical" style={{ width: '100%' }}>
            {useCase.exceptionFlows.map((flow: any) => (
              <Card 
                key={flow.id || flow.flowId} 
                title={flow.name || flow.flowId}
                size="small"
                headStyle={{ background: '#fff1f0' }}
              >
                <div><strong>触发点:</strong> {flow.triggerAt}</div>
                <div><strong>条件:</strong> {flow.condition}</div>
                <div><strong>处理:</strong> {flow.description || flow.compensationRef}</div>
              </Card>
            ))}
          </Space>
        </>
      )}
    </div>
  );
};

export default UseCaseEditor;
