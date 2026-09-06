import React from 'react';
import { Tree } from 'antd';
import {
  ApartmentOutlined,
  ClusterOutlined,
  DatabaseOutlined,
  FileOutlined,
  FolderOutlined,
  FunctionOutlined,
  LinkOutlined,
  SettingOutlined,
  SafetyCertificateOutlined,
  TeamOutlined,
  ThunderboltOutlined,
  UserOutlined
} from '@ant-design/icons';
import { TreeNode, Workspace } from '../types/models';
import {
  findBehavior,
  findEvent,
  findObjectNode,
  findPermission,
  findRule,
  findRole,
  getBehaviorOwnerObject,
  getObjectNodes,
  ObjectModelNode
} from '../services/modelIndex';

interface ModelTreeProps {
  workspace: Workspace | null;
  onSelect: (nodeType: string, nodeId: string, isReference: boolean) => void;
}

const ModelTree: React.FC<ModelTreeProps> = ({ workspace, onSelect }) => {
  const modelIcon = <FolderOutlined />;

  const makeReferenceNode = (
    key: string,
    title: string,
    nodeType: string,
    nodeId: string,
    icon: React.ReactNode
  ): TreeNode => ({
    key,
    title,
    nodeType,
    nodeId,
    icon,
    isReference: true
  });

  const makeFolder = (key: string, title: string, children: TreeNode[]): TreeNode | undefined => {
    if (children.length === 0) return undefined;
    return {
      key,
      title,
      nodeType: 'folder',
      icon: <FolderOutlined />,
      children
    };
  };

  const getEventId = (eventRef: any) => {
    if (typeof eventRef === 'string') return eventRef;
    return eventRef?.eventId;
  };

  const buildAttributeFolder = (objectNode: ObjectModelNode): TreeNode | undefined => {
    const attributes = objectNode.attributes || [];
    return makeFolder(
      `${objectNode.key}:attributes`,
      '属性',
      attributes.map((attr: any, index: number) => {
        const attrName = typeof attr === 'string' ? attr : attr?.name;
        const attrLabel = typeof attr === 'string' ? attr : (attr?.label || attr?.name);
        return {
          key: `${objectNode.key}:attr:${attrName || index}`,
          title: attrLabel || `属性${index + 1}`,
          nodeType: 'attribute',
          icon: <FileOutlined />
        };
      })
    );
  };

  const buildConstraintFolder = (objectNode: ObjectModelNode): TreeNode | undefined => {
    const constraints = objectNode.constraints || [];
    return makeFolder(
      `${objectNode.key}:constraints`,
      '约束',
      constraints.map((constraint: any, index: number) => ({
        key: `${objectNode.key}:constraint:${constraint?.name || constraint?.constraintType || index}`,
        title: constraint?.name || constraint?.constraintType || constraint?.expression || `约束${index + 1}`,
        nodeType: 'constraint',
        icon: <SettingOutlined />
      }))
    );
  };

  const buildCompositionFolder = (objectNode: ObjectModelNode): TreeNode | undefined => {
    const compositions = objectNode.raw?.compositions || [];
    return makeFolder(
      `${objectNode.key}:compositions`,
      '组合子对象',
      compositions.map((composition: any, index: number) => {
        const target = findObjectNode(workspace, composition?.targetEntity);
        const title = composition?.name || target?.name || composition?.targetEntity || `子对象${index + 1}`;
        const targetChildren = target ? [
          buildAttributeFolder(target),
          buildConstraintFolder(target),
          buildObjectBehaviorFolder(target)
        ].filter(Boolean) as TreeNode[] : undefined;

        return {
          key: `${objectNode.key}:composition:${composition?.alias || composition?.targetEntity || index}`,
          title,
          nodeType: target ? 'entity' : 'composition',
          nodeId: target?.id,
          icon: <ClusterOutlined />,
          isReference: Boolean(target),
          children: targetChildren && targetChildren.length > 0 ? targetChildren : undefined
        };
      })
    );
  };

  // prefix 为所属行为节点在整棵树中的唯一 key，用于保证其内部所有节点 key 全树唯一。
  // 同一行为会同时出现在「对象模型」与「行为模型」下，若只按 behavior.id 生成 key 会发生冲突。
  const buildBehaviorReferenceFolders = (behavior: any, prefix: string): TreeNode[] => {
    const children: TreeNode[] = [];

    const owner = getBehaviorOwnerObject(workspace, behavior);
    const ownerFolder = owner ? makeFolder(`${prefix}:owner`, '所属对象', [
      makeReferenceNode(`${prefix}:owner:${owner.id}`, owner.name, 'entity', owner.id, <DatabaseOutlined />)
    ]) : undefined;
    if (ownerFolder) children.push(ownerFolder);

    const rules = (behavior.appliedRules || [])
      .map((ruleId: string) => findRule(workspace, ruleId) || { id: ruleId, name: ruleId });
    const ruleFolder = makeFolder(`${prefix}:rules`, '应用规则', rules.map((rule: any) =>
      makeReferenceNode(`${prefix}:rule:${rule.id}`, rule.name || rule.id, 'rule', rule.id, <SettingOutlined />)
    ));
    if (ruleFolder) children.push(ruleFolder);

    const producedEvents = (behavior.producedEvents || [])
      .map(getEventId)
      .filter(Boolean)
      .map((eventId: string) => findEvent(workspace, eventId) || { eventId, eventName: eventId });
    const producedFolder = makeFolder(`${prefix}:produced-events`, '产生事件', producedEvents.map((event: any) =>
      makeReferenceNode(`${prefix}:event:${event.eventId}`, event.eventName || event.eventId, 'event', event.eventId, <ThunderboltOutlined />)
    ));
    if (producedFolder) children.push(producedFolder);

    const subscribedEvents = workspace?.models.eventModel?.events?.filter((event: any) =>
      Array.isArray(event.subscriberBehaviorRefs) && event.subscriberBehaviorRefs.includes(behavior.id)
    ) || [];
    const subscribedFolder = makeFolder(`${prefix}:subscribed-events`, '订阅事件', subscribedEvents.map((event: any) =>
      makeReferenceNode(`${prefix}:subscribed:${event.eventId}`, event.eventName || event.eventId, 'event', event.eventId, <ThunderboltOutlined />)
    ));
    if (subscribedFolder) children.push(subscribedFolder);

    return children;
  };

  const buildObjectBehaviorFolder = (objectNode: ObjectModelNode): TreeNode | undefined => {
    const behaviors = workspace?.models.behaviorModel?.behaviors?.filter((behavior: any) =>
      objectNode.matches.includes(behavior.ownerEntity)
    ) || [];

    return makeFolder(`${objectNode.key}:behaviors`, '行为', behaviors.map((behavior: any) => ({
      key: `${objectNode.key}:behavior:${behavior.id}`,
      title: behavior.name || behavior.id,
      nodeType: 'behavior',
      nodeId: behavior.id,
      icon: <FunctionOutlined />,
      isReference: true,
      children: buildBehaviorReferenceFolders(behavior, `${objectNode.key}:behavior:${behavior.id}`)
    })));
  };

  const buildObjectNode = (objectNode: ObjectModelNode, extraChildren: TreeNode[] = []): TreeNode => {
    const children = [
      buildAttributeFolder(objectNode),
      buildCompositionFolder(objectNode),
      buildConstraintFolder(objectNode),
      buildObjectBehaviorFolder(objectNode),
      ...extraChildren
    ].filter(Boolean) as TreeNode[];

    const icon = objectNode.kind === 'aggregate'
      ? <ClusterOutlined />
      : objectNode.kind === 'masterEntity'
        ? <DatabaseOutlined />
        : <FileOutlined />;

    return {
      key: objectNode.key,
      title: objectNode.name,
      nodeType: 'entity',
      nodeId: objectNode.id,
      icon,
      children: children.length > 0 ? children : undefined
    };
  };

  const buildObjectModelTree = (): TreeNode | undefined => {
    const objectModel = workspace?.models.objectModel;
    if (!objectModel) return undefined;

    if (Array.isArray(objectModel.aggregates)) {
      const allObjects = getObjectNodes(objectModel);
      const aggregateNodes = objectModel.aggregates.map((aggregate: any, index: number) => {
        const aggregateNode = allObjects.find(node => node.kind === 'aggregate' && node.raw === aggregate);
        const rootNode = allObjects.find(node => node.kind === 'aggregateRoot' && node.aggregate === aggregate);

        const aggregateChildren = [
          rootNode ? buildObjectNode(rootNode) : undefined,
          aggregateNode ? buildConstraintFolder(aggregateNode) : undefined
        ].filter(Boolean) as TreeNode[];

        return {
          key: `aggregate:${aggregate?.id || index}`,
          title: aggregate?.name || aggregate?.id || `聚合${index + 1}`,
          nodeType: 'entity',
          nodeId: aggregateNode?.id || aggregate?.id,
          icon: <ClusterOutlined />,
          children: aggregateChildren.length > 0 ? aggregateChildren : undefined
        };
      });

      const masterNodes = allObjects
        .filter(node => node.kind === 'masterEntity')
        .map(node => buildObjectNode(node));
      const masterFolder = makeFolder('master-entities', '主数据对象', masterNodes);

      return {
        key: 'object-model',
        title: '对象模型',
        nodeType: 'root',
        icon: modelIcon,
        children: [...aggregateNodes, masterFolder].filter(Boolean) as TreeNode[]
      };
    }

    const objectNodes = getObjectNodes(objectModel).map(node => buildObjectNode(node));
    return {
      key: 'object-model',
      title: '对象模型',
      nodeType: 'root',
      icon: modelIcon,
      children: objectNodes
    };
  };

  const inferRuleObjectRefs = (rule: any): ObjectModelNode[] => {
    const objectNodes = getObjectNodes(workspace?.models.objectModel);
    const text = [
      rule.expression,
      rule.description,
      ...(rule.inputParams || []).map((param: any) => param?.sourceField || param?.name || '')
    ].join(' ');

    return objectNodes.filter(node => node.matches.some(match => text.includes(match)));
  };

  const buildExtensionModelTrees = (): TreeNode[] => {
    const trees: TreeNode[] = [];

    const configs: Array<{
      key: string;
      title: string;
      nodeType: string;
      listKey: string;
      idOf: (item: any) => string;
      nameOf: (item: any) => string;
      icon: React.ReactNode;
    }> = [
      { key: 'flowModel', title: '流程模型', nodeType: 'flow', listKey: 'flows', idOf: (i) => i.id, nameOf: (i) => i.name || i.id, icon: <FunctionOutlined /> },
      { key: 'reportModel', title: '报表模型', nodeType: 'report', listKey: 'query_reports', idOf: (i) => i.id, nameOf: (i) => i.name || i.id, icon: <FileOutlined /> },
      { key: 'compensationModel', title: '补偿模型', nodeType: 'compensation', listKey: 'compensations', idOf: (i) => i.compensationId, nameOf: (i) => i.compensationId || i.name, icon: <ThunderboltOutlined /> },
      { key: 'qualityModel', title: '质量模型', nodeType: 'quality', listKey: 'quality_annotations', idOf: (i) => i.annotationId || i.id, nameOf: (i) => i.annotationId || i.id || i.name, icon: <SafetyCertificateOutlined /> },
      { key: 'metricModel', title: '度量模型', nodeType: 'metric', listKey: 'metrics', idOf: (i) => i.id, nameOf: (i) => i.name || i.id, icon: <SettingOutlined /> },
    ];

    configs.forEach((cfg) => {
      const model: any = workspace?.models[cfg.key];
      const items = Array.isArray(model?.[cfg.listKey]) ? model[cfg.listKey] : [];
      if (items.length === 0) return;
      trees.push({
        key: cfg.key,
        title: cfg.title,
        nodeType: 'root',
        icon: modelIcon,
        children: items.map((item: any) => ({
          key: `${cfg.key}:${cfg.idOf(item)}`,
          title: cfg.nameOf(item),
          nodeType: cfg.nodeType,
          nodeId: cfg.idOf(item),
          icon: cfg.icon
        }))
      });
    });

    // UI 模型结构多样，单独处理
    const uiModel: any = workspace?.models.uiModel;
    if (uiModel) {
      const screens = Array.isArray(uiModel.screens)
        ? uiModel.screens
        : Array.isArray(uiModel.page_registry)
          ? uiModel.page_registry
          : (uiModel.pages || []);
      if (screens.length > 0) {
        trees.push({
          key: 'uiModel',
          title: '界面模型',
          nodeType: 'root',
          icon: modelIcon,
          children: screens.map((s: any) => ({
            key: `uiModel:${s.screenId || s.pageId || s.id}`,
            title: s.name || s.title || s.screenId || s.pageId,
            nodeType: 'ui',
            nodeId: s.screenId || s.pageId || s.id,
            icon: <SettingOutlined />
          }))
        });
      } else {
        trees.push({
          key: 'uiModel',
          title: '界面模型',
          nodeType: 'root',
          icon: modelIcon,
          children: [{
            key: 'uiModel:root',
            title: 'UI 模型',
            nodeType: 'ui',
            nodeId: 'ui-model',
            icon: <SettingOutlined />
          }]
        });
      }
    }

    return trees;
  };

  const buildTreeData = (): TreeNode[] => {
    if (!workspace) return [];

    const treeData: TreeNode[] = [];
    const models = workspace.models;

    const objectModelTree = buildObjectModelTree();
    if (objectModelTree) treeData.push(objectModelTree);

    if (models.behaviorModel?.behaviors) {
      treeData.push({
        key: 'behavior-model',
        title: '行为模型',
        nodeType: 'root',
        icon: modelIcon,
        children: models.behaviorModel.behaviors.map((behavior: any) => ({
          key: `behavior-list-${behavior.id}`,
          title: behavior.name || behavior.id,
          nodeType: 'behavior',
          nodeId: behavior.id,
          icon: <FunctionOutlined />,
          children: buildBehaviorReferenceFolders(behavior, `behavior-list-${behavior.id}`)
        }))
      });
    }

    if (models.ruleModel?.rules) {
      treeData.push({
        key: 'rule-model',
        title: '规则模型',
        nodeType: 'root',
        icon: modelIcon,
        children: models.ruleModel.rules.map((rule: any) => {
          const objectRefs = inferRuleObjectRefs(rule);
          const reusedBy = models.behaviorModel?.behaviors?.filter((behavior: any) =>
            behavior.appliedRules?.includes(rule.id) || rule.reusedBy?.includes(behavior.id)
          ) || [];
          const children = [
            makeFolder(`${rule.id}:objects`, '引用对象', objectRefs.map(node =>
              makeReferenceNode(`rule:${rule.id}:object:${node.id}`, node.name, 'entity', node.id, <DatabaseOutlined />)
            )),
            makeFolder(`${rule.id}:behaviors`, '被行为引用', reusedBy.map((behavior: any) =>
              makeReferenceNode(`rule:${rule.id}:behavior:${behavior.id}`, behavior.name || behavior.id, 'behavior', behavior.id, <FunctionOutlined />)
            ))
          ].filter(Boolean) as TreeNode[];

          return {
            key: `rule-${rule.id}`,
            title: rule.name || rule.id,
            nodeType: 'rule',
            nodeId: rule.id,
            icon: <SettingOutlined />,
            children: children.length > 0 ? children : undefined
          };
        })
      });
    }

    if (models.eventModel?.events) {
      treeData.push({
        key: 'event-model',
        title: '事件模型',
        nodeType: 'root',
        icon: modelIcon,
        children: models.eventModel.events.map((event: any) => {
          const producer = findBehavior(workspace, event.producerBehaviorRef);
          const subscriberBehaviors = (event.subscriberBehaviorRefs || [])
            .map((behaviorId: string) => findBehavior(workspace, behaviorId) || { id: behaviorId, name: behaviorId });
          const relatedObjects = [
            producer ? getBehaviorOwnerObject(workspace, producer) : undefined,
            ...subscriberBehaviors.map((behavior: any) => getBehaviorOwnerObject(workspace, behavior))
          ].filter(Boolean) as ObjectModelNode[];
          const uniqueObjects = relatedObjects.filter((node, index, list) =>
            list.findIndex(item => item.id === node.id) === index
          );

          const children = [
            producer ? makeFolder(`${event.eventId}:producer`, '生产者行为', [
              makeReferenceNode(`event:${event.eventId}:producer:${producer.id}`, producer.name || producer.id, 'behavior', producer.id, <FunctionOutlined />)
            ]) : undefined,
            makeFolder(`${event.eventId}:subscribers`, '订阅者行为', subscriberBehaviors.map((behavior: any) =>
              makeReferenceNode(`event:${event.eventId}:subscriber:${behavior.id}`, behavior.name || behavior.id, 'behavior', behavior.id, <FunctionOutlined />)
            )),
            makeFolder(`${event.eventId}:objects`, '相关对象', uniqueObjects.map(node =>
              makeReferenceNode(`event:${event.eventId}:object:${node.id}`, node.name, 'entity', node.id, <DatabaseOutlined />)
            ))
          ].filter(Boolean) as TreeNode[];

          return {
            key: `event-${event.eventId}`,
            title: event.eventName || event.eventId,
            nodeType: 'event',
            nodeId: event.eventId,
            icon: <ThunderboltOutlined />,
            children: children.length > 0 ? children : undefined
          };
        })
      });
    }

    if (models.actorModel) {
      const actorModel = models.actorModel;
      treeData.push({
        key: 'actor-model',
        title: '主体模型',
        nodeType: 'root',
        icon: modelIcon,
        children: [
          makeFolder('actor-model:actors', '主体', (actorModel.actors || []).map((actor: any) => {
            const roles = (actor.roles || []).map((roleId: string) => findRole(workspace, roleId) || { roleId, name: roleId });
            return {
              key: `actor-${actor.actorId}`,
              title: actor.name || actor.actorId,
              nodeType: 'actor',
              nodeId: actor.actorId,
              icon: <UserOutlined />,
              children: [
                makeFolder(`${actor.actorId}:roles`, '关联角色', roles.map((role: any) =>
                  makeReferenceNode(`actor:${actor.actorId}:role:${role.roleId}`, role.name || role.roleId, 'role', role.roleId, <TeamOutlined />)
                ))
              ].filter(Boolean) as TreeNode[]
            };
          })),
          makeFolder('actor-model:roles', '角色', (actorModel.roles || []).map((role: any) => {
            const permissions = (role.permissions || []).map((permissionId: string) =>
              findPermission(workspace, permissionId) || { permissionId }
            );
            return {
              key: `role-${role.roleId}`,
              title: role.name || role.roleId,
              nodeType: 'role',
              nodeId: role.roleId,
              icon: <TeamOutlined />,
              children: [
                makeFolder(`${role.roleId}:permissions`, '权限', permissions.map((permission: any) =>
                  makeReferenceNode(
                    `role:${role.roleId}:permission:${permission.permissionId}`,
                    permission.permissionId,
                    'permission',
                    permission.permissionId,
                    <SafetyCertificateOutlined />
                  )
                ))
              ].filter(Boolean) as TreeNode[]
            };
          })),
          makeFolder('actor-model:permissions', '权限', (actorModel.permissions || []).map((permission: any) => {
            const targetRefs = Array.isArray(permission.targetRef) ? permission.targetRef : [permission.targetRef];
            const behaviors = permission.targetType === 'BEHAVIOR'
              ? targetRefs.map((targetRef: string) => findBehavior(workspace, targetRef)).filter(Boolean)
              : [];
            return {
              key: `permission-${permission.permissionId}`,
              title: permission.permissionId,
              nodeType: 'permission',
              nodeId: permission.permissionId,
              icon: <SafetyCertificateOutlined />,
              children: [
                makeFolder(`${permission.permissionId}:target`, '目标行为', behaviors.map((behavior: any) =>
                  makeReferenceNode(
                    `permission:${permission.permissionId}:behavior:${behavior.id}`,
                    behavior.name || behavior.id,
                    'behavior',
                    behavior.id,
                    <FunctionOutlined />
                  )
                ))
              ].filter(Boolean) as TreeNode[]
            };
          }))
        ].filter(Boolean) as TreeNode[]
      });
    }

    // 扩展模型（流程/报表/界面/补偿/质量/度量）——类型注册式浏览
    treeData.push(...buildExtensionModelTrees());

    if (models.scenarioModel?.use_cases) {
      treeData.push({
        key: 'scenario-model',
        title: '场景模型',
        nodeType: 'root',
        icon: modelIcon,
        children: models.scenarioModel.use_cases.map((useCase: any) => {
          const primaryFlow = makeFolder(
            `${useCase.id}:primaryFlow`,
            '主流程',
            (useCase.primaryFlow || []).map((step: any, index: number) => {
              if (step.stepType === 'BEHAVIOR_CALL' && step.behaviorRef) {
                const behavior = findBehavior(workspace, step.behaviorRef);
                return makeReferenceNode(
                  `${useCase.id}:step:${step.stepId}`,
                  `${index + 1}. ${behavior?.name || step.behaviorRef}`,
                  'behavior',
                  step.behaviorRef,
                  <FunctionOutlined />
                );
              }

              if (step.stepType === 'EVENT_WAIT' && step.waitForEvent) {
                const event = findEvent(workspace, step.waitForEvent);
                return makeReferenceNode(
                  `${useCase.id}:step:${step.stepId}`,
                  `${index + 1}. 等待事件: ${event?.eventName || step.waitForEvent}`,
                  'event',
                  step.waitForEvent,
                  <ThunderboltOutlined />
                );
              }

              if (step.stepType === 'EVENT_EMIT' && step.eventRef) {
                const event = findEvent(workspace, step.eventRef);
                return makeReferenceNode(
                  `${useCase.id}:step:${step.stepId}`,
                  `${index + 1}. 发出事件: ${event?.eventName || step.eventRef}`,
                  'event',
                  step.eventRef,
                  <ThunderboltOutlined />
                );
              }

              return {
                key: `${useCase.id}:step:${step.stepId || index}`,
                title: `${index + 1}. ${step.description || step.gatewayType || step.stepType}`,
                nodeType: 'step',
                nodeId: step.stepId,
                icon: step.stepType === 'GATEWAY' ? <ApartmentOutlined /> : <LinkOutlined />
              };
            })
          );

          return {
            key: `usecase-${useCase.id}`,
            title: useCase.name || useCase.id,
            nodeType: 'usecase',
            nodeId: useCase.id,
            icon: <ApartmentOutlined />,
            children: primaryFlow ? [primaryFlow] : undefined
          };
        })
      });
    }

    return treeData;
  };

  const handleSelect = (selectedKeys: React.Key[], info: any) => {
    if (selectedKeys.length > 0) {
      const node = info.node;
      if (node.nodeType && node.nodeId) {
        onSelect(node.nodeType, node.nodeId, node.isReference || false);
      }
    }
  };

  return (
    <Tree
      showIcon
      treeData={buildTreeData()}
      onSelect={handleSelect}
      defaultExpandAll
    />
  );
};

export default ModelTree;
