import React, { useState, useEffect } from 'react';
import { Layout, Button, message, Modal, Input, Select, Tabs, Badge } from 'antd';
import { 
  FolderOpenOutlined, 
  SaveOutlined, 
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ApartmentOutlined
} from '@ant-design/icons';
import ModelTree from './components/ModelTree';
import EntityEditor from './components/editors/EntityEditor';
import BehaviorEditor from './components/editors/BehaviorEditor';
import EventEditor from './components/editors/EventEditor';
import RuleEditor from './components/editors/RuleEditor';
import UseCaseEditor from './components/editors/UseCaseEditor';
import ActorEditor from './components/editors/ActorEditor';
import KnowledgeGraph from './components/KnowledgeGraph';
import { workspaceApi, validationApi } from './services/api';
import { Workspace, Behavior, Event, Rule, UseCase, Actor, Role, Permission } from './types/models';
import { buildGraphFromWorkspace } from './services/graphBuilder';
import { findObjectNode, ObjectModelNode } from './services/modelIndex';
import './App.css';

const { Header, Sider, Content } = Layout;
const { TabPane } = Tabs;

const App: React.FC = () => {
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [openModalVisible, setOpenModalVisible] = useState(false);
  const [directory, setDirectory] = useState('');
  const [workspaceOptions, setWorkspaceOptions] = useState<any[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [activeTab, setActiveTab] = useState<string>('');
  const [openTabs, setOpenTabs] = useState<any[]>([]);
  const [isDirty, setIsDirty] = useState(false);
  const [isGeneratingGraph, setIsGeneratingGraph] = useState(false);

  const handleScanWorkspaces = async () => {
    setIsScanning(true);
    try {
      const result = await workspaceApi.scanWorkspaces();
      setWorkspaceOptions(result.success ? (result.data || []) : []);
    } catch (error) {
      setWorkspaceOptions([]);
    } finally {
      setIsScanning(false);
    }
  };

  useEffect(() => {
    if (openModalVisible) {
      handleScanWorkspaces();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [openModalVisible]);

  const handleOpenWorkspace = async () => {
    if (!directory) {
      message.error('请输入目录路径');
      return;
    }

    try {
      const result = await workspaceApi.openWorkspace(directory);
      if (result.success) {
        setWorkspace(result.data);
        message.success('工作区打开成功');
        setOpenModalVisible(false);
      } else {
        message.error(result.error?.message || '打开失败');
      }
    } catch (error: any) {
      message.error(error.response?.data?.error?.message || '打开工作区失败');
    }
  };

  const handleSaveWorkspace = async () => {
    if (!workspace) {
      message.warning('没有打开的工作区');
      return;
    }

    try {
      const result = await workspaceApi.saveWorkspace(workspace, { validateBeforeSave: true });
      if (result.success) {
        message.success('保存成功');
        setIsDirty(false);
      } else {
        message.error(result.error?.message || '保存失败');
      }
    } catch (error: any) {
      message.error(error.response?.data?.error?.message || '保存失败');
    }
  };

  const handleValidate = async () => {
    if (!workspace) {
      message.warning('没有打开的工作区');
      return;
    }

    try {
      const result = await validationApi.runValidation(workspace);
      if (result.success) {
        const validation = result.data;
        if (validation.errors.length === 0) {
          message.success('校验通过');
        } else {
          message.error(`发现 ${validation.errors.length} 个错误`);
        }
        setWorkspace({
          ...workspace,
          validation
        });
      }
    } catch (error: any) {
      message.error('校验失败');
    }
  };

  const handleGenerateKnowledgeGraph = async () => {
    if (!workspace) {
      message.warning('没有打开的工作区');
      return;
    }

    setIsGeneratingGraph(true);
    const hide = message.loading('正在生成知识图谱...', 0);

    try {
      // Simulate processing time for better UX
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const graphData = buildGraphFromWorkspace(workspace);
      
      const tabKey = 'knowledge-graph';
      const existingTab = openTabs.find(tab => tab.key === tabKey);
      
      if (existingTab) {
        // Update existing tab with new data
        setOpenTabs(openTabs.map(tab => 
          tab.key === tabKey ? { ...tab, data: graphData } : tab
        ));
        setActiveTab(tabKey);
      } else {
        // Create new tab
        setOpenTabs([...openTabs, {
          key: tabKey,
          title: '知识图谱',
          nodeType: 'knowledge-graph',
          data: graphData
        }]);
        setActiveTab(tabKey);
      }
      
      hide();
      message.success('知识图谱生成成功');
    } catch (error: any) {
      hide();
      message.error('生成知识图谱失败');
    } finally {
      setIsGeneratingGraph(false);
    }
  };

  const handleNodeSelect = (nodeType: string, nodeId: string, isReference: boolean) => {
    const tabKey = `${nodeType}-${nodeId}`;
    
    // 检查是否已打开
    const existingTab = openTabs.find(tab => tab.key === tabKey);
    if (existingTab) {
      setActiveTab(tabKey);
      return;
    }

    // 获取节点数据
    let nodeData = null;
    let title = '';
    let editorType = nodeType;

    if (nodeType === 'entity') {
      nodeData = findObjectNode(workspace, nodeId);
      title = nodeData?.name || nodeId;
    } else if (nodeType === 'behavior' && workspace?.models.behaviorModel?.behaviors) {
      nodeData = workspace.models.behaviorModel.behaviors.find((b: Behavior) => b.id === nodeId);
      title = nodeData?.name || nodeId;
    } else if (nodeType === 'event' && workspace?.models.eventModel?.events) {
      nodeData = workspace.models.eventModel.events.find((e: Event) => e.eventId === nodeId);
      title = nodeData?.eventName || nodeId;
    } else if (nodeType === 'rule' && workspace?.models.ruleModel?.rules) {
      nodeData = workspace.models.ruleModel.rules.find((r: Rule) => r.id === nodeId);
      title = nodeData?.name || nodeId;
    } else if (nodeType === 'usecase' && workspace?.models.scenarioModel?.use_cases) {
      nodeData = workspace.models.scenarioModel.use_cases.find((uc: UseCase) => uc.id === nodeId);
      title = nodeData?.name || nodeId;
    } else if (nodeType === 'actor' && workspace?.models.actorModel?.actors) {
      nodeData = workspace.models.actorModel.actors.find((actor: Actor) => actor.actorId === nodeId);
      title = nodeData?.name || nodeId;
    } else if (nodeType === 'role' && workspace?.models.actorModel?.roles) {
      nodeData = workspace.models.actorModel.roles.find((role: Role) => role.roleId === nodeId);
      title = nodeData?.name || nodeId;
    } else if (nodeType === 'permission' && workspace?.models.actorModel?.permissions) {
      nodeData = workspace.models.actorModel.permissions.find((permission: Permission) => permission.permissionId === nodeId);
      title = nodeData?.permissionId || nodeId;
    } else if (nodeType === 'flow' && workspace?.models.flowModel?.flows) {
      nodeData = workspace.models.flowModel.flows.find((f: any) => f.id === nodeId);
      title = nodeData?.name || nodeId;
    } else if (nodeType === 'report' && workspace?.models.reportModel?.query_reports) {
      nodeData = workspace.models.reportModel.query_reports.find((r: any) => r.id === nodeId);
      title = nodeData?.name || nodeId;
    } else if (nodeType === 'compensation' && workspace?.models.compensationModel?.compensations) {
      nodeData = workspace.models.compensationModel.compensations.find((c: any) => c.compensationId === nodeId);
      title = nodeData?.compensationId || nodeId;
    } else if (nodeType === 'quality' && workspace?.models.qualityModel?.quality_annotations) {
      nodeData = workspace.models.qualityModel.quality_annotations.find((q: any) => (q.annotationId || q.id) === nodeId);
      title = nodeData?.annotationId || nodeId;
    } else if (nodeType === 'metric' && workspace?.models.metricModel?.metrics) {
      nodeData = workspace.models.metricModel.metrics.find((m: any) => m.id === nodeId);
      title = nodeData?.name || nodeId;
    } else if (nodeType === 'ui' && workspace?.models.uiModel) {
      const uiModel = workspace.models.uiModel;
      const screens = Array.isArray(uiModel.screens)
        ? uiModel.screens
        : Array.isArray(uiModel.page_registry)
          ? uiModel.page_registry
          : (uiModel.pages || []);
      nodeData = screens.find((s: any) => (s.screenId || s.pageId || s.id) === nodeId)
        || (nodeId === 'ui-model' ? uiModel : undefined);
      title = nodeData?.name || nodeData?.title || nodeId;
    }

    if (nodeData) {
      setOpenTabs([...openTabs, {
        key: tabKey,
        title,
        nodeType: editorType,
        nodeId,
        data: nodeData,
        isReference
      }]);
      setActiveTab(tabKey);
    }
  };

  const updateObjectInWorkspace = (updatedNode: ObjectModelNode): Workspace | null => {
    if (!workspace || !updatedNode?.raw) return workspace;

    const objectModel = workspace.models.objectModel;
    const updatedRaw = updatedNode.raw;
    let nextObjectModel = objectModel;

    if (updatedNode.kind === 'entity') {
      nextObjectModel = {
        ...objectModel,
        entities: (objectModel.entities || []).map((entity: any) =>
          entity.id === updatedNode.id || entity.alias === updatedNode.alias ? updatedRaw : entity
        )
      };
    } else if (updatedNode.kind === 'aggregate') {
      nextObjectModel = {
        ...objectModel,
        aggregates: (objectModel.aggregates || []).map((aggregate: any) =>
          aggregate.id === updatedNode.id ? updatedRaw : aggregate
        )
      };
    } else if (updatedNode.kind === 'aggregateRoot') {
      nextObjectModel = {
        ...objectModel,
        aggregates: (objectModel.aggregates || []).map((aggregate: any) =>
          aggregate.id === updatedNode.aggregateId
            ? { ...aggregate, rootEntity: updatedRaw }
            : aggregate
        )
      };
    } else if (updatedNode.kind === 'internalEntity') {
      nextObjectModel = {
        ...objectModel,
        aggregates: (objectModel.aggregates || []).map((aggregate: any) => {
          if (aggregate.id !== updatedNode.aggregateId) return aggregate;

          const updateEntity = (entity: any) =>
            entity.alias === updatedNode.alias || entity.name === updatedNode.name || entity.id === updatedNode.id
              ? updatedRaw
              : entity;

          return {
            ...aggregate,
            internalEntities: Array.isArray(aggregate.internalEntities)
              ? aggregate.internalEntities.map(updateEntity)
              : aggregate.internalEntities,
            entities: Array.isArray(aggregate.entities)
              ? aggregate.entities.map(updateEntity)
              : aggregate.entities
          };
        })
      };
    } else if (updatedNode.kind === 'masterEntity') {
      nextObjectModel = {
        ...objectModel,
        masterEntities: (objectModel.masterEntities || []).map((entity: any) =>
          entity.alias === updatedNode.alias || entity.name === updatedNode.name || entity.id === updatedNode.id
            ? updatedRaw
            : entity
        )
      };
    }

    const nextWorkspace = {
      ...workspace,
      models: {
        ...workspace.models,
        objectModel: nextObjectModel
      }
    };

    setWorkspace(nextWorkspace);
    return nextWorkspace;
  };

  const updateActorModelItem = (itemType: 'actor' | 'role' | 'permission', updated: any) => {
    if (!workspace) return;

    const actorModel = workspace.models.actorModel || {};
    let nextActorModel = actorModel;

    if (itemType === 'actor') {
      nextActorModel = {
        ...actorModel,
        actors: (actorModel.actors || []).map((actor: any) =>
          actor.actorId === updated.actorId ? updated : actor
        )
      };
    } else if (itemType === 'role') {
      nextActorModel = {
        ...actorModel,
        roles: (actorModel.roles || []).map((role: any) =>
          role.roleId === updated.roleId ? updated : role
        )
      };
    } else if (itemType === 'permission') {
      nextActorModel = {
        ...actorModel,
        permissions: (actorModel.permissions || []).map((permission: any) =>
          permission.permissionId === updated.permissionId ? updated : permission
        )
      };
    }

    setWorkspace({
      ...workspace,
      models: {
        ...workspace.models,
        actorModel: nextActorModel
      }
    });
  };

  const handleTabClose = (targetKey: string) => {
    const newTabs = openTabs.filter(tab => tab.key !== targetKey);
    setOpenTabs(newTabs);
    if (activeTab === targetKey && newTabs.length > 0) {
      setActiveTab(newTabs[newTabs.length - 1].key);
    }
  };

  const renderEditor = (tab: any) => {
    if (!workspace) return null;

    const availableRules = workspace.models.ruleModel?.rules?.map((r: any) => r.id) || [];
    const availableBehaviors = workspace.models.behaviorModel?.behaviors?.map((b: any) => b.id) || [];
    const availableRoles = workspace.models.actorModel?.roles?.map((r: any) => r.roleId) || [];
    const availablePermissions = workspace.models.actorModel?.permissions?.map((p: any) => p.permissionId) || [];

    switch (tab.nodeType) {
      case 'entity':
        return (
          <EntityEditor
            entity={tab.data}
            onChange={(updated) => {
              setIsDirty(true);
              updateObjectInWorkspace(updated as ObjectModelNode);
              setOpenTabs(currentTabs => currentTabs.map(currentTab =>
                currentTab.key === tab.key
                  ? { ...currentTab, data: updated, title: updated.name || updated.raw?.name || currentTab.title }
                  : currentTab
              ));
            }}
          />
        );
      case 'behavior':
        return (
          <BehaviorEditor
            behavior={tab.data}
            onChange={(updated) => {
              setIsDirty(true);
            }}
            availableRules={availableRules}
          />
        );
      case 'event':
        return (
          <EventEditor
            event={tab.data}
            onChange={(updated) => {
              setIsDirty(true);
            }}
            availableBehaviors={availableBehaviors}
          />
        );
      case 'rule':
        return (
          <RuleEditor
            rule={tab.data}
            onChange={(updated) => {
              setIsDirty(true);
            }}
          />
        );
      case 'usecase':
        return (
          <UseCaseEditor
            useCase={tab.data}
            workspace={workspace}
          />
        );
      case 'actor':
      case 'role':
      case 'permission':
        return (
          <ActorEditor
            itemType={tab.nodeType}
            data={tab.data}
            availableRoles={availableRoles}
            availablePermissions={availablePermissions}
            availableBehaviors={availableBehaviors}
            onChange={(updated) => {
              setIsDirty(true);
              updateActorModelItem(tab.nodeType, updated);
              setOpenTabs(currentTabs => currentTabs.map(currentTab =>
                currentTab.key === tab.key
                  ? { ...currentTab, data: updated, title: updated.name || updated.permissionId || currentTab.title }
                  : currentTab
              ));
            }}
          />
        );
      case 'flow':
      case 'report':
      case 'compensation':
      case 'quality':
      case 'metric':
      case 'ui':
        // 扩展模型：先提供只读查看，详细编辑器后续补充
        return (
          <div style={{ padding: 24 }}>
            <h2>{tab.title}</h2>
            <pre style={{
              background: '#fafafa',
              border: '0.5px solid #d9d9d9',
              borderRadius: 8,
              padding: 16,
              overflow: 'auto',
              maxHeight: 'calc(100vh - 180px)',
              fontSize: 12
            }}>
              {JSON.stringify(tab.data, null, 2)}
            </pre>
          </div>
        );
      case 'knowledge-graph':
        return (
          <KnowledgeGraph graphData={tab.data} />
        );
      default:
        return <div>暂不支持该类型编辑器</div>;
    }
  };

  return (
    <Layout style={{ height: '100vh' }}>
      <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h1 style={{ margin: 0 }}>本体模型编辑器</h1>
        <div>
          <Button 
            icon={<FolderOpenOutlined />} 
            onClick={() => setOpenModalVisible(true)}
            style={{ marginRight: 8 }}
          >
            打开工作区
          </Button>
          <Button 
            icon={<SaveOutlined />} 
            onClick={handleSaveWorkspace}
            disabled={!workspace}
            type={isDirty ? 'primary' : 'default'}
            style={{ marginRight: 8 }}
          >
            保存
          </Button>
          <Button 
            icon={<CheckCircleOutlined />} 
            onClick={handleValidate}
            disabled={!workspace}
            style={{ marginRight: 8 }}
          >
            校验
          </Button>
          <Button 
            icon={<ApartmentOutlined />} 
            onClick={handleGenerateKnowledgeGraph}
            disabled={!workspace}
            loading={isGeneratingGraph}
          >
            知识图谱
          </Button>
          {workspace && (
            <Badge 
              count={workspace.validation?.errors?.length || 0} 
              style={{ marginLeft: 16 }}
            >
              <ExclamationCircleOutlined style={{ fontSize: 20 }} />
            </Badge>
          )}
        </div>
      </Header>
      <Layout>
        <Sider width={300} style={{ background: '#fff', overflow: 'auto' }}>
          <div style={{ padding: 16 }}>
            <h3>模型树</h3>
            <ModelTree workspace={workspace} onSelect={handleNodeSelect} />
          </div>
        </Sider>
        <Content style={{ background: '#fff', margin: 0 }}>
          {openTabs.length > 0 ? (
            <Tabs
              className="kg-tabs"
              style={{ height: '100%' }}
              type="editable-card"
              activeKey={activeTab}
              onChange={setActiveTab}
              onEdit={(targetKey, action) => {
                if (action === 'remove') {
                  handleTabClose(targetKey as string);
                }
              }}
              hideAdd
            >
              {openTabs.map(tab => (
                <TabPane tab={tab.title} key={tab.key} closable>
                  {renderEditor(tab)}
                </TabPane>
              ))}
            </Tabs>
          ) : (
            <div style={{ padding: 24, textAlign: 'center', color: '#999' }}>
              <p>请从左侧树中选择要编辑的节点</p>
            </div>
          )}
        </Content>
      </Layout>

      <Modal
        title="打开工作区"
        open={openModalVisible}
        onOk={handleOpenWorkspace}
        onCancel={() => setOpenModalVisible(false)}
      >
        <Select
          style={{ width: '100%', marginBottom: 8 }}
          placeholder={isScanning ? '正在扫描模型目录...' : '从已识别的工作区中选择'}
          loading={isScanning}
          showSearch
          optionFilterProp="label"
          allowClear
          value={workspaceOptions.some(opt => opt.directory === directory) ? directory : undefined}
          onChange={(val) => setDirectory(val || '')}
          options={workspaceOptions.map(opt => ({
            label: `${opt.name}${opt.domain ? ` · ${opt.domain}` : ''}（${opt.files.length} 个模型）`,
            value: opt.directory
          }))}
        />
        <Input
          placeholder="或手动输入目录路径，例如: D:/models/contract"
          value={directory}
          onChange={(e) => setDirectory(e.target.value)}
        />
        <p style={{ marginTop: 8, color: '#999', fontSize: 12 }}>
          提示：下拉框会自动识别包含模型YAML文件的目录，也可手动输入路径
        </p>
      </Modal>
    </Layout>
  );
};

export default App;
