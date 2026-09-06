import yaml
from typing import Dict, Any, Optional

# 模型类型 → Workspace.models 中的 key（按内容 model_type 识别，而非文件名）
# v6 十一模型 + 已知并行变体；未知类型由调用方兜底登记
MODEL_TYPE_TO_KEY = {
    'AGGREGATE_OBJECT': 'objectModel',   # V1 聚合根式对象模型
    'OBJECT': 'objectModel',             # V2 扁平式 / DataAnalyse 实体式对象模型
    'BEHAVIOR': 'behaviorModel',
    'RULE': 'ruleModel',
    'EVENT': 'eventModel',
    'SCENARIO': 'scenarioModel',
    'ACTOR': 'actorModel',
    'FLOW': 'flowModel',
    'REPORT': 'reportModel',
    'UI': 'uiModel',
    'UI-Model': 'uiModel',
    'UI_MODEL': 'uiModel',
    'MAPPING': 'mappingModel',
    'MM': 'mappingModel',
    'INTERFACE': 'interfaceModel',
    'MI': 'interfaceModel',
    # 已知但当前未启用详细编辑的并行变体（仍会加载并兑底渲染）
    'COMPENSATION': 'compensationModel',
    'QUALITY': 'qualityModel',
    'METRIC': 'metricModel',
}

# 模型类型 → 中文名称（供树/告警显示）
MODEL_TYPE_LABEL = {
    'AGGREGATE_OBJECT': '对象模型', 'OBJECT': '对象模型', 'BEHAVIOR': '行为模型',
    'RULE': '规则模型', 'EVENT': '事件模型', 'SCENARIO': '场景模型', 'ACTOR': '主体模型',
    'FLOW': '流程模型', 'REPORT': '报表模型', 'UI': 'UI模型', 'UI-Model': 'UI模型',
    'UI_MODEL': 'UI模型', 'MAPPING': '映射模型', 'MM': '映射模型',
    'INTERFACE': '接口模型', 'MI': '接口模型',
    'COMPENSATION': '补偿模型', 'QUALITY': '质量模型', 'METRIC': '度量模型',
}


class YamlService:
    def parse_yaml(self, content: str) -> Optional[Dict[str, Any]]:
        """解析YAML内容"""
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            print(f"YAML解析失败: {str(e)}")
            return None
    
    def serialize_yaml(self, data: Dict[str, Any]) -> str:
        """序列化为YAML"""
        try:
            return yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
        except Exception as e:
            print(f"YAML序列化失败: {str(e)}")
            return ""
