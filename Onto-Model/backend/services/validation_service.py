from typing import Dict, Any, List

class ValidationService:
    def validate_workspace(self, workspace: Dict[str, Any]) -> Dict[str, Any]:
        """校验整个工作区"""
        errors = []
        warnings = []
        
        models = workspace.get('models', {})
        object_model = models.get('objectModel', {})
        behavior_model = models.get('behaviorModel', {})
        rule_model = models.get('ruleModel', {})
        event_model = models.get('eventModel', {})
        scenario_model = models.get('scenarioModel', {})
        actor_model = models.get('actorModel', {})
        
        # 构建对象引用索引。旧规范用 entities[].id，新规范用聚合根/内部实体 alias。
        object_refs = self._collect_object_refs(object_model)
        entity_ids = set()
        if object_model and 'entities' in object_model:
            for entity in object_model['entities']:
                entity_id = entity.get('id')
                if entity_id:
                    if entity_id in entity_ids:
                        errors.append({
                            'code': 'ENTITY_ID_DUPLICATE',
                            'message': f'实体ID重复: {entity_id}',
                            'nodeType': 'entity',
                            'nodeId': entity_id,
                            'file': 'm1-object-model.yaml',
                            'severity': 'error'
                        })
                    entity_ids.add(entity_id)
        
        # 校验行为的ownerEntity
        if behavior_model and 'behaviors' in behavior_model:
            for behavior in behavior_model['behaviors']:
                owner_entity = behavior.get('ownerEntity')
                if owner_entity and owner_entity not in object_refs:
                    errors.append({
                        'code': 'BEHAVIOR_OWNER_NOT_FOUND',
                        'message': f'行为的ownerEntity不存在: {owner_entity}',
                        'nodeType': 'behavior',
                        'nodeId': behavior.get('id'),
                        'file': 'm2-behavior-model.yaml',
                        'path': f"behaviors[{behavior.get('id')}].ownerEntity",
                        'severity': 'error'
                    })
        
        # 构建行为ID索引
        behavior_ids = set()
        if behavior_model and 'behaviors' in behavior_model:
            for behavior in behavior_model['behaviors']:
                behavior_id = behavior.get('id')
                if behavior_id:
                    behavior_ids.add(behavior_id)
        
        # 构建规则ID索引
        rule_ids = set()
        if rule_model and 'rules' in rule_model:
            for rule in rule_model['rules']:
                rule_id = rule.get('id')
                if rule_id:
                    rule_ids.add(rule_id)
        
        # 校验行为引用的规则
        if behavior_model and 'behaviors' in behavior_model:
            for behavior in behavior_model['behaviors']:
                applied_rules = behavior.get('appliedRules', [])
                for rule_ref in applied_rules:
                    if rule_ref not in rule_ids:
                        errors.append({
                            'code': 'RULE_NOT_FOUND',
                            'message': f'行为引用的规则不存在: {rule_ref}',
                            'nodeType': 'behavior',
                            'nodeId': behavior.get('id'),
                            'file': 'm2-behavior-model.yaml',
                            'severity': 'error'
                        })
        
        # 校验事件的生产者行为
        event_ids = set()
        if event_model and 'events' in event_model:
            for event in event_model['events']:
                event_id = event.get('eventId')
                if event_id:
                    event_ids.add(event_id)

        # 校验行为产出的事件引用
        if behavior_model and 'behaviors' in behavior_model and event_ids:
            for behavior in behavior_model['behaviors']:
                for event_ref in behavior.get('producedEvents', []):
                    if isinstance(event_ref, dict):
                        event_id = event_ref.get('eventId')
                    else:
                        event_id = event_ref
                    if event_id and event_id not in event_ids:
                        errors.append({
                            'code': 'PRODUCED_EVENT_NOT_FOUND',
                            'message': f'行为产生的事件不存在: {event_id}',
                            'nodeType': 'behavior',
                            'nodeId': behavior.get('id'),
                            'file': 'm2-behavior-model.yaml',
                            'severity': 'error'
                        })

        # 校验主体模型引用链：主体 -> 角色 -> 权限 -> 行为
        role_ids = set()
        permission_ids = set()
        if actor_model and 'roles' in actor_model:
            for role in actor_model['roles']:
                role_id = role.get('roleId')
                if role_id:
                    role_ids.add(role_id)

        if actor_model and 'permissions' in actor_model:
            for permission in actor_model['permissions']:
                permission_id = permission.get('permissionId')
                if permission_id:
                    permission_ids.add(permission_id)

                target_type = permission.get('targetType')
                target_ref = permission.get('targetRef')
                target_refs = target_ref if isinstance(target_ref, list) else [target_ref]
                for ref in target_refs:
                    if target_type == 'BEHAVIOR' and ref and ref not in behavior_ids:
                        warnings.append({
                            'code': 'PERMISSION_TARGET_BEHAVIOR_NOT_FOUND',
                            'message': f'权限绑定的行为不存在: {ref}',
                            'nodeType': 'permission',
                            'nodeId': permission_id,
                            'file': 'm5-actor-model.yaml',
                            'severity': 'warning'
                        })

        if actor_model and 'actors' in actor_model:
            for actor in actor_model['actors']:
                for role_ref in actor.get('roles', []):
                    if role_ref not in role_ids:
                        errors.append({
                            'code': 'ACTOR_ROLE_NOT_FOUND',
                            'message': f'主体引用的角色不存在: {role_ref}',
                            'nodeType': 'actor',
                            'nodeId': actor.get('actorId'),
                            'file': 'm5-actor-model.yaml',
                            'severity': 'error'
                        })

        if actor_model and 'roles' in actor_model:
            for role in actor_model['roles']:
                for permission_ref in role.get('permissions', []):
                    if permission_ref not in permission_ids:
                        errors.append({
                            'code': 'ROLE_PERMISSION_NOT_FOUND',
                            'message': f'角色引用的权限不存在: {permission_ref}',
                            'nodeType': 'role',
                            'nodeId': role.get('roleId'),
                            'file': 'm5-actor-model.yaml',
                            'severity': 'error'
                        })

        if event_model and 'events' in event_model:
            for event in event_model['events']:
                producer_ref = event.get('producerBehaviorRef')
                if producer_ref and producer_ref not in behavior_ids:
                    errors.append({
                        'code': 'EVENT_PRODUCER_NOT_FOUND',
                        'message': f'事件的生产者行为不存在: {producer_ref}',
                        'nodeType': 'event',
                        'nodeId': event.get('eventId'),
                        'file': 'event-model.yaml',
                        'severity': 'error'
                    })
                
                # 校验订阅者行为
                subscribers = event.get('subscriberBehaviorRefs', [])
                for subscriber_ref in subscribers:
                    if subscriber_ref not in behavior_ids:
                        errors.append({
                            'code': 'EVENT_SUBSCRIBER_NOT_FOUND',
                            'message': f'事件的订阅者行为不存在: {subscriber_ref}',
                            'nodeType': 'event',
                            'nodeId': event.get('eventId'),
                            'file': 'event-model.yaml',
                            'severity': 'error'
                        })
        
        return {
            'errors': errors,
            'warnings': warnings
        }

    def _collect_object_refs(self, object_model: Dict[str, Any]) -> set:
        refs = set()
        if not object_model:
            return refs

        for entity in object_model.get('entities', []):
            self._add_object_ref(refs, entity.get('id'))
            self._add_object_ref(refs, entity.get('alias'))
            self._add_object_ref(refs, entity.get('name'))

        for aggregate in object_model.get('aggregates', []):
            self._add_object_ref(refs, aggregate.get('id'))
            self._add_object_ref(refs, aggregate.get('name'))

            root = aggregate.get('rootEntity') or {}
            self._add_object_ref(refs, root.get('id'))
            self._add_object_ref(refs, root.get('alias'))
            self._add_object_ref(refs, root.get('name'))

            for entity in aggregate.get('internalEntities', []):
                self._add_object_ref(refs, entity.get('id'))
                self._add_object_ref(refs, entity.get('alias'))
                self._add_object_ref(refs, entity.get('name'))

            for entity in aggregate.get('entities', []):
                self._add_object_ref(refs, entity.get('id'))
                self._add_object_ref(refs, entity.get('alias'))
                self._add_object_ref(refs, entity.get('name'))

        for entity in object_model.get('masterEntities', []):
            self._add_object_ref(refs, entity.get('id'))
            self._add_object_ref(refs, entity.get('alias'))
            self._add_object_ref(refs, entity.get('name'))

        return refs

    def _add_object_ref(self, refs: set, value: Any):
        if value:
            refs.add(str(value))
