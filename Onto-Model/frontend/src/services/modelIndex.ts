import { Workspace } from '../types/models';

export type ObjectNodeKind =
  | 'entity'
  | 'aggregate'
  | 'aggregateRoot'
  | 'internalEntity'
  | 'masterEntity';

export interface ObjectModelNode {
  id: string;
  key: string;
  name: string;
  alias?: string;
  kind: ObjectNodeKind;
  raw: any;
  aggregate?: any;
  aggregateId?: string;
  aggregateName?: string;
  attributes: any[];
  constraints: any[];
  matches: string[];
}

const pushMatch = (matches: string[], value: any) => {
  if (value !== undefined && value !== null && `${value}`.trim()) {
    matches.push(`${value}`);
  }
};

const makeNode = (
  kind: ObjectNodeKind,
  raw: any,
  key: string,
  fallbackId: string,
  aggregate?: any
): ObjectModelNode => {
  const id = raw?.id || raw?.alias || fallbackId;
  const name = raw?.name || raw?.alias || id;
  const alias = raw?.alias;
  const matches: string[] = [];

  pushMatch(matches, id);
  pushMatch(matches, raw?.id);
  pushMatch(matches, raw?.alias);
  pushMatch(matches, raw?.name);
  pushMatch(matches, aggregate?.id);
  pushMatch(matches, aggregate?.name);

  return {
    id,
    key,
    name,
    alias,
    kind,
    raw,
    aggregate,
    aggregateId: aggregate?.id,
    aggregateName: aggregate?.name,
    attributes: Array.isArray(raw?.attributes) ? raw.attributes : [],
    constraints: [
      ...(Array.isArray(raw?.constraints) ? raw.constraints : []),
      ...(Array.isArray(raw?.aggregateConstraints) ? raw.aggregateConstraints : []),
      ...(Array.isArray(raw?.invariants) ? raw.invariants : [])
    ],
    matches: Array.from(new Set(matches))
  };
};

export const getObjectNodes = (objectModel: any): ObjectModelNode[] => {
  if (!objectModel) return [];

  const nodes: ObjectModelNode[] = [];

  if (Array.isArray(objectModel.entities)) {
    objectModel.entities.forEach((entity: any, index: number) => {
      nodes.push(makeNode('entity', entity, `entity:${entity?.id || index}`, `entity-${index}`));
    });
  }

  if (Array.isArray(objectModel.aggregates)) {
    objectModel.aggregates.forEach((aggregate: any, aggregateIndex: number) => {
      const aggregateId = aggregate?.id || `aggregate-${aggregateIndex}`;
      nodes.push(makeNode('aggregate', aggregate, `aggregate:${aggregateId}`, aggregateId));

      if (aggregate?.rootEntity) {
        nodes.push(
          makeNode(
            'aggregateRoot',
            aggregate.rootEntity,
            `aggregate:${aggregateId}:root`,
            `${aggregateId}:root`,
            aggregate
          )
        );
      }

      const internalEntities = [
        ...(Array.isArray(aggregate?.internalEntities) ? aggregate.internalEntities : []),
        ...(Array.isArray(aggregate?.entities) ? aggregate.entities : [])
      ];

      internalEntities.forEach((entity: any, entityIndex: number) => {
        nodes.push(
          makeNode(
            'internalEntity',
            entity,
            `aggregate:${aggregateId}:internal:${entity?.alias || entityIndex}`,
            `${aggregateId}:internal:${entityIndex}`,
            aggregate
          )
        );
      });
    });
  }

  if (Array.isArray(objectModel.masterEntities)) {
    objectModel.masterEntities.forEach((entity: any, index: number) => {
      nodes.push(makeNode('masterEntity', entity, `master:${entity?.alias || index}`, `master-${index}`));
    });
  }

  return nodes;
};

export const findObjectNode = (workspace: Workspace | null | undefined, ref: string | undefined): ObjectModelNode | undefined => {
  if (!workspace || !ref) return undefined;
  return getObjectNodes(workspace.models.objectModel).find(node => node.matches.includes(ref));
};

export const findBehavior = (workspace: Workspace | null | undefined, behaviorId: string | undefined): any => {
  if (!workspace || !behaviorId) return undefined;
  return workspace.models.behaviorModel?.behaviors?.find((behavior: any) => behavior.id === behaviorId);
};

export const findRule = (workspace: Workspace | null | undefined, ruleId: string | undefined): any => {
  if (!workspace || !ruleId) return undefined;
  return workspace.models.ruleModel?.rules?.find((rule: any) => rule.id === ruleId);
};

export const findEvent = (workspace: Workspace | null | undefined, eventId: string | undefined): any => {
  if (!workspace || !eventId) return undefined;
  return workspace.models.eventModel?.events?.find((event: any) => event.eventId === eventId);
};

export const findActor = (workspace: Workspace | null | undefined, actorId: string | undefined): any => {
  if (!workspace || !actorId) return undefined;
  return workspace.models.actorModel?.actors?.find((actor: any) => actor.actorId === actorId);
};

export const findRole = (workspace: Workspace | null | undefined, roleId: string | undefined): any => {
  if (!workspace || !roleId) return undefined;
  return workspace.models.actorModel?.roles?.find((role: any) => role.roleId === roleId);
};

export const findPermission = (workspace: Workspace | null | undefined, permissionId: string | undefined): any => {
  if (!workspace || !permissionId) return undefined;
  return workspace.models.actorModel?.permissions?.find((permission: any) => permission.permissionId === permissionId);
};

export const getBehaviorOwnerObject = (workspace: Workspace | null | undefined, behavior: any): ObjectModelNode | undefined => {
  return findObjectNode(workspace, behavior?.ownerEntity);
};

export const getObjectTitle = (node?: ObjectModelNode, fallback?: string) => {
  if (!node) return fallback || '';
  return node.name || node.alias || node.id;
};
