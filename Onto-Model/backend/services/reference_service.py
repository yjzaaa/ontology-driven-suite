from typing import Dict, Any, List

class ReferenceService:
    def __init__(self):
        self.index = {}
    
    def build_index(self, workspace: Dict[str, Any]):
        """构建引用索引"""
        self.index = {
            'behavior_to_entity': {},
            'behavior_to_rules': {},
            'event_to_producer': {},
            'event_to_subscribers': {},
            'scenario_to_behaviors': {}
        }
        
        models = workspace.get('models', {})
        behavior_model = models.get('behaviorModel', {})
        event_model = models.get('eventModel', {})
        scenario_model = models.get('scenarioModel', {})
        
        # 索引行为到实体
        if behavior_model and 'behaviors' in behavior_model:
            for behavior in behavior_model['behaviors']:
                behavior_id = behavior.get('id')
                owner_entity = behavior.get('ownerEntity')
                if behavior_id and owner_entity:
                    self.index['behavior_to_entity'][behavior_id] = owner_entity
                
                # 索引行为到规则
                applied_rules = behavior.get('appliedRules', [])
                if applied_rules:
                    self.index['behavior_to_rules'][behavior_id] = applied_rules
        
        # 索引事件
        if event_model and 'events' in event_model:
            for event in event_model['events']:
                event_id = event.get('eventId')
                producer = event.get('producerBehaviorRef')
                subscribers = event.get('subscriberBehaviorRefs', [])
                
                if event_id and producer:
                    self.index['event_to_producer'][event_id] = producer
                if event_id and subscribers:
                    self.index['event_to_subscribers'][event_id] = subscribers
    
    def find_references(self, node_type: str, node_id: str) -> List[Dict[str, Any]]:
        """查找节点的引用关系"""
        references = []
        
        if node_type == 'behavior':
            # 查找哪些事件引用了这个行为
            for event_id, producer in self.index.get('event_to_producer', {}).items():
                if producer == node_id:
                    references.append({
                        'type': 'event_producer',
                        'nodeType': 'event',
                        'nodeId': event_id,
                        'description': f'事件 {event_id} 的生产者'
                    })
            
            for event_id, subscribers in self.index.get('event_to_subscribers', {}).items():
                if node_id in subscribers:
                    references.append({
                        'type': 'event_subscriber',
                        'nodeType': 'event',
                        'nodeId': event_id,
                        'description': f'事件 {event_id} 的订阅者'
                    })
        
        return references
    
    def analyze_delete_impact(self, node_type: str, node_id: str) -> Dict[str, Any]:
        """分析删除影响"""
        references = self.find_references(node_type, node_id)
        
        can_delete = len(references) == 0
        
        return {
            'canDelete': can_delete,
            'references': references,
            'message': '该节点被其他节点引用，删除前请先解除引用' if not can_delete else '可以安全删除'
        }
