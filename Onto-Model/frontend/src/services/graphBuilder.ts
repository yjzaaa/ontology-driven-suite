import { Workspace } from '../types/models';
import { findObjectNode, getObjectNodes } from './modelIndex';

export interface GraphNode {
  id: string;
  label: string;
  cat: string;
  sub: string;
  r: number;
  desc: string;
}

export interface GraphEdge {
  s: string;
  t: string;
  type: string;
  label: string;
  dash: boolean;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export const buildGraphFromWorkspace = (workspace: Workspace): GraphData => {
  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];
  const addedNodes = new Set<string>();

  const addNode = (node: GraphNode) => {
    if (addedNodes.has(node.id)) return;
    addedNodes.add(node.id);
    nodes.push(node);
  };

  // 1. Extract entities from Object Model
  const objectNodes = getObjectNodes(workspace.models.objectModel);
  if (objectNodes.length > 0) {
    objectNodes.forEach((objectNode: any) => {
      const raw = objectNode.raw || {};
      const isCoreEntity = raw.tags?.includes('核心域') || objectNode.kind === 'aggregateRoot';
      const isSupportEntity = raw.tags?.includes('支撑域') || objectNode.kind === 'masterEntity';
      
      addNode({
        id: objectNode.id,
        label: objectNode.name,
        cat: 'entity',
        sub: isCoreEntity ? 'entity_core' : (isSupportEntity ? 'entity_support' : 'entity_core'),
        r: objectNode.kind === 'aggregate' ? 30 : (isCoreEntity ? 28 : 18),
        desc: raw.description || objectNode.kind
      });
    });
  }

  // 2. Extract relations from Object Model
  if (workspace.models.objectModel?.relations) {
    workspace.models.objectModel.relations.forEach((rel: any) => {
      const relType = rel.type?.toLowerCase() || 'association';
      edges.push({
        s: rel.sourceEntity,
        t: rel.targetEntity,
        type: relType,
        label: rel.targetRole || '关联',
        dash: relType === 'association'
      });
    });
  }

  // 2b. Extract Reference-attribute associations (e.g. Contract.productId → Product)
  // 模型常用 attributes[].type: Reference + refEntity 表达对象间关联，这里补成关联边，
  // 避免被引用的主数据/对象变成孤立节点。同一 source→target 只保留一条边。
  objectNodes.forEach((objectNode: any) => {
    const raw = objectNode.raw || {};
    const attrs = Array.isArray(raw.attributes) ? raw.attributes : [];
    const refSeen = new Set<string>();
    attrs.forEach((attr: any) => {
      if (typeof attr !== 'object' || attr === null) return;
      if (`${attr.type || ''}`.toLowerCase() !== 'reference') return;
      if (!attr.refEntity) return;
      const target = findObjectNode(workspace, attr.refEntity);
      const targetId = target?.id || attr.refEntity;
      if (targetId === objectNode.id) return; // 自引用忽略
      const dedupKey = `${objectNode.id}->${targetId}`;
      if (refSeen.has(dedupKey)) return;
      refSeen.add(dedupKey);
      edges.push({
        s: objectNode.id,
        t: targetId,
        type: 'association',
        label: attr.label || attr.name || '引用',
        dash: true
      });
    });
  });

  // 2c. Extract normalized associations (backend 已将 aggregate_associations / relations 统一为 associations)
  const assocSeen = new Set<string>();
  (workspace.models.objectModel?.associations || []).forEach((rel: any) => {
    if (!rel || !rel.source || !rel.target) return;
    const src = findObjectNode(workspace, rel.source);
    const tgt = findObjectNode(workspace, rel.target);
    const s = src?.id || rel.source;
    const t = tgt?.id || rel.target;
    if (s === t) return; // 自引用忽略
    const dedupKey = `${s}->${t}`;
    if (assocSeen.has(dedupKey)) return;
    assocSeen.add(dedupKey);
    const relType = rel.type || 'association';
    edges.push({
      s,
      t,
      type: relType,
      label: rel.sourceRole || rel.targetRole || '关联',
      dash: relType === 'association' || relType === 'reference'
    });
  });

  if (workspace.models.objectModel?.aggregates) {
    workspace.models.objectModel.aggregates.forEach((aggregate: any) => {
      const aggregateNode = objectNodes.find(node => node.kind === 'aggregate' && node.raw === aggregate);
      const rootNode = objectNodes.find(node => node.kind === 'aggregateRoot' && node.aggregate === aggregate);
      const internalNodes = objectNodes.filter(node => node.kind === 'internalEntity' && node.aggregate === aggregate);

      if (aggregateNode && rootNode) {
        edges.push({
          s: aggregateNode.id,
          t: rootNode.id,
          type: 'composition',
          label: '聚合根',
          dash: false
        });
      }

      internalNodes.forEach(node => {
        if (aggregateNode) {
          edges.push({
            s: aggregateNode.id,
            t: node.id,
            type: 'composition',
            label: '包含',
            dash: false
          });
        }
      });

      (aggregate.rootEntity?.compositions || []).forEach((composition: any) => {
        const target = findObjectNode(workspace, composition.targetEntity);
        if (rootNode && target) {
          edges.push({
            s: rootNode.id,
            t: target.id,
            type: 'composition',
            label: composition.name || composition.alias || '组合',
            dash: false
          });
        }
      });
    });
  }

  // 3. Extract behaviors from Behavior Model
  if (workspace.models.behaviorModel?.behaviors) {
    workspace.models.behaviorModel.behaviors.forEach((behavior: any) => {
      addNode({
        id: behavior.id,
        label: behavior.name,
        cat: 'behavior',
        sub: 'behavior',
        r: 18,
        desc: `${behavior.behaviorType || ''} | ${behavior.triggerType || ''}\n${behavior.description || ''}`
      });

      // Behavior → Entity (owns)
      if (behavior.ownerEntity) {
        const owner = findObjectNode(workspace, behavior.ownerEntity);
        edges.push({
          s: behavior.id,
          t: owner?.id || behavior.ownerEntity,
          type: 'event',
          label: '操作',
          dash: false
        });
      }

      // Behavior → Rules (applies)
      if (behavior.appliedRules && Array.isArray(behavior.appliedRules)) {
        behavior.appliedRules.forEach((ruleId: string) => {
          edges.push({
            s: behavior.id,
            t: ruleId,
            type: 'applies_rule',
            label: '应用',
            dash: true
          });
        });
      }

      // Event chains (behavior → behavior)
      if (behavior.producedEvents && Array.isArray(behavior.producedEvents)) {
        behavior.producedEvents.forEach((eventRef: any) => {
          const eventId = typeof eventRef === 'string' ? eventRef : eventRef?.eventId;
          if (eventId) {
            edges.push({
              s: behavior.id,
              t: eventId,
              type: 'event',
              label: '产生',
              dash: true
            });
          }
        });
      }
    });
  }

  // 4. Extract rules from Rule Model
  if (workspace.models.ruleModel?.rules) {
    workspace.models.ruleModel.rules.forEach((rule: any) => {
      addNode({
        id: rule.id,
        label: rule.name,
        cat: 'rule',
        sub: 'rule',
        r: 16,
        desc: `${rule.ruleType || ''}\n${rule.description || ''}`
      });
    });
  }

  // 5. Extract events from Event Model
  if (workspace.models.eventModel?.events) {
    workspace.models.eventModel.events.forEach((event: any) => {
      addNode({
        id: event.eventId,
        label: event.eventName,
        cat: 'event',
        sub: 'event',
        r: 16,
        desc: event.description || ''
      });

      // Producer Behavior → Event
      if (event.producerBehaviorRef) {
        edges.push({
          s: event.producerBehaviorRef,
          t: event.eventId,
          type: 'event',
          label: '产生',
          dash: true
        });
      }

      // Event → Subscriber Behaviors
      if (event.subscriberBehaviorRefs && Array.isArray(event.subscriberBehaviorRefs)) {
        event.subscriberBehaviorRefs.forEach((behaviorId: string) => {
          edges.push({
            s: event.eventId,
            t: behaviorId,
            type: 'event',
            label: '订阅',
            dash: true
          });
        });
      }
    });
  }

  // 6. Extract scenarios from Scenario Model
  if (workspace.models.scenarioModel?.use_cases) {
    workspace.models.scenarioModel.use_cases.forEach((useCase: any) => {
      addNode({
        id: useCase.id,
        label: useCase.name,
        cat: 'scenario',
        sub: 'scenario',
        r: 20,
        desc: useCase.description || ''
      });

      // Scenario → Behaviors (from primaryFlow)
      if (useCase.primaryFlow && Array.isArray(useCase.primaryFlow)) {
        useCase.primaryFlow.forEach((step: any) => {
          if (step.behaviorRef) {
            edges.push({
              s: useCase.id,
              t: step.behaviorRef,
              type: 'triggers',
              label: '调用',
              dash: false
            });
          }
        });
      }
    });
  }

  // 7. Extract actors, roles and permissions
  if (workspace.models.actorModel) {
    (workspace.models.actorModel.actors || []).forEach((actor: any) => {
      addNode({
        id: actor.actorId,
        label: actor.name || actor.actorId,
        cat: 'actor',
        sub: 'actor',
        r: 18,
        desc: actor.actorType || ''
      });

      (actor.roles || []).forEach((roleId: string) => {
        edges.push({
          s: actor.actorId,
          t: roleId,
          type: 'authorization',
          label: '角色',
          dash: false
        });
      });
    });

    (workspace.models.actorModel.roles || []).forEach((role: any) => {
      addNode({
        id: role.roleId,
        label: role.name || role.roleId,
        cat: 'actor',
        sub: 'role',
        r: 16,
        desc: ''
      });

      (role.permissions || []).forEach((permissionId: string) => {
        edges.push({
          s: role.roleId,
          t: permissionId,
          type: 'authorization',
          label: '权限',
          dash: false
        });
      });
    });

    (workspace.models.actorModel.permissions || []).forEach((permission: any) => {
      addNode({
        id: permission.permissionId,
        label: permission.permissionId,
        cat: 'actor',
        sub: 'permission',
        r: 14,
        desc: `${permission.targetType || ''} ${permission.dataScope || ''}`
      });

      const targetRefs = Array.isArray(permission.targetRef) ? permission.targetRef : [permission.targetRef];
      targetRefs.filter(Boolean).forEach((targetRef: string) => {
        edges.push({
          s: permission.permissionId,
          t: targetRef,
          type: 'authorization',
          label: '授权',
          dash: true
        });
      });
    });
  }

  // 8. Extract business processes
  if (workspace.models.scenarioModel?.business_processes) {
    workspace.models.scenarioModel.business_processes.forEach((bp: any) => {
      addNode({
        id: bp.id,
        label: bp.name,
        cat: 'scenario',
        sub: 'scenario',
        r: 22,
        desc: bp.description || ''
      });

      // BP → Use Cases
      if (bp.useCases && Array.isArray(bp.useCases)) {
        bp.useCases.forEach((ucId: string) => {
          edges.push({
            s: bp.id,
            t: ucId,
            type: 'triggers',
            label: '包含',
            dash: false
          });
        });
      }
    });
  }

  // 9. 类型注册式兜底：flow / report / compensation / quality / metric 模型
  // 每种类型只需注册「取列表 + 取 id + 取名称」配置，即可在图中渲染（编辑/详情后续补）
  const genericModels: Array<{
    key: string;
    cat: string;
    listKey: string;
    idOf: (item: any) => string;
    labelOf: (item: any) => string;
    descOf?: (item: any) => string;
    r: number;
  }> = [
    { key: 'flowModel', cat: 'flow', listKey: 'flows', idOf: (i) => i.id, labelOf: (i) => i.name || i.id, descOf: (i) => i.description || i.flowType || '', r: 18 },
    { key: 'reportModel', cat: 'report', listKey: 'query_reports', idOf: (i) => i.id, labelOf: (i) => i.name || i.id, descOf: (i) => i.description || '', r: 16 },
    { key: 'compensationModel', cat: 'compensation', listKey: 'compensations', idOf: (i) => i.compensationId, labelOf: (i) => i.compensationId || i.name, descOf: (i) => i.fallback || '', r: 15 },
    { key: 'qualityModel', cat: 'quality', listKey: 'quality_annotations', idOf: (i) => i.annotationId || i.id, labelOf: (i) => i.annotationId || i.id || i.name, descOf: (i) => i.description || '', r: 14 },
    { key: 'metricModel', cat: 'metric', listKey: 'metrics', idOf: (i) => i.id, labelOf: (i) => i.name || i.id, descOf: (i) => i.description || i.computation_type || '', r: 16 },
  ];
  genericModels.forEach((cfg) => {
    const model: any = workspace.models[cfg.key];
    const items = Array.isArray(model?.[cfg.listKey]) ? model[cfg.listKey] : [];
    items.forEach((item: any) => {
      if (!item || typeof item !== 'object') return;
      const id = cfg.idOf(item);
      if (!id) return;
      addNode({
        id: `${cfg.cat}:${id}`, // 前缀避免与行为/对象等其它模型 id 冲突
        label: cfg.labelOf(item),
        cat: cfg.cat,
        sub: cfg.cat,
        r: cfg.r,
        desc: cfg.descOf ? cfg.descOf(item) : ''
      });
    });
  });

  // 10. UI 模型（结构多样，按 screens / page_registry / pages 取列表，无结构则单节点兜底）
  const uiModel: any = workspace.models.uiModel;
  if (uiModel) {
    const screens = Array.isArray(uiModel.screens)
      ? uiModel.screens
      : Array.isArray(uiModel.page_registry)
        ? uiModel.page_registry
        : (uiModel.pages || []);
    if (screens.length > 0) {
      screens.forEach((s: any) => {
        if (!s || typeof s !== 'object') return;
        const id = s.screenId || s.pageId || s.id;
        if (!id) return;
        addNode({
          id: `ui:${id}`,
          label: s.name || s.title || id,
          cat: 'ui',
          sub: 'ui',
          r: 15,
          desc: s.description || ''
        });
      });
    } else {
      addNode({
        id: 'ui-model',
        label: 'UI 模型',
        cat: 'ui',
        sub: 'ui',
        r: 16,
        desc: ''
      });
    }
  }

  return { nodes, edges };
};
