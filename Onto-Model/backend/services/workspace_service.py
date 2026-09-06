import os
from typing import Dict, Any, List
from services.file_service import FileService
from services.yaml_service import YamlService, MODEL_TYPE_TO_KEY
from services.validation_service import ValidationService
from services.reference_service import ReferenceService

class WorkspaceService:
    def __init__(self):
        self.file_service = FileService()
        self.yaml_service = YamlService()
        self.validation_service = ValidationService()
        self.reference_service = ReferenceService()
        self.current_workspace = None
    
    def open_workspace(self, directory: str) -> Dict[str, Any]:
        """打开工作区目录：扫描所有 YAML，按文件内 model_type 识别并加载。"""
        directory = self._resolve_directory(directory)

        workspace = {
            'workspaceMeta': {
                'directory': directory,
                'domain': None
            },
            'models': {},
            'validation': {'errors': [], 'warnings': []},
            'fileStats': {},
            'extensions': {
                'modelFiles': {},
                'unrecognizedFiles': []
            }
        }

        # 扫描目录内所有 yaml，按 model_type 归类（不再依赖文件名白名单）
        for filename in self.file_service.list_yaml_files(directory):
            file_path = os.path.join(directory, filename)
            content = self.file_service.read_file(file_path)
            if not content:
                continue
            parsed = self.yaml_service.parse_yaml(content)
            if not parsed or not isinstance(parsed, dict):
                workspace['extensions']['unrecognizedFiles'].append({
                    'file': filename, 'reason': '不是有效的 YAML 字典'
                })
                continue

            model_type = parsed.get('model_type')
            model_key = MODEL_TYPE_TO_KEY.get(model_type) if model_type else None
            if not model_key:
                workspace['extensions']['unrecognizedFiles'].append({
                    'file': filename,
                    'model_type': model_type,
                    'reason': '未知或缺失 model_type'
                })
                continue

            # M1 对象模型先做结构归一化（扁平/实体式 → 聚合根式）
            if model_key == 'objectModel':
                parsed = self._normalize_object_model(parsed)

            workspace['models'][model_key] = parsed
            workspace['extensions']['modelFiles'][model_key] = filename
            if not workspace['workspaceMeta']['domain'] and parsed.get('domain'):
                workspace['workspaceMeta']['domain'] = parsed['domain']

        # 执行校验
        validation_result = self.validation_service.validate_workspace(workspace)
        workspace['validation'] = validation_result

        # 构建引用索引
        self.reference_service.build_index(workspace)

        self.current_workspace = workspace
        return workspace

    def _normalize_object_model(self, m: Dict[str, Any]) -> Dict[str, Any]:
        """M1 对象模型归一化：把多种结构形态统一成『聚合根式』，供前端 modelIndex/graphBuilder 复用。

        支持形态：
        1) 聚合根式  aggregates[].rootEntity + internalEntities + masterEntities（V1）
        2) 扁平式    aggregates[].alias + attributes（属性直接挂聚合上）+ aggregate_associations（V2）
        3) 实体式    顶层 entities + relations（DataAnalyse）

        归一化后统一提供：
        - aggregates[]：每个聚合均含 rootEntity（扁平式自动提升）
        - associations[]：统一关联表（source/target 用对象可解析的 id/别名）
        """
        if not isinstance(m, dict):
            return m
        m = dict(m)

        # ---- 3) 实体式：顶层 entities + relations → 拆成聚合（每实体一个聚合根）----
        if not m.get('aggregates') and isinstance(m.get('entities'), list):
            aggs = []
            for entity in m['entities']:
                if not isinstance(entity, dict):
                    continue
                root = {
                    'alias': entity.get('alias') or entity.get('id'),
                    'name': entity.get('name') or entity.get('alias') or entity.get('id'),
                    'description': entity.get('description'),
                    'lifecycle': entity.get('lifecycle'),
                    'tags': entity.get('tags'),
                }
                attrs = entity.get('attributes')
                if attrs is not None:
                    root['attributes'] = attrs
                aggs.append({
                    'id': entity.get('id'),
                    'name': root['name'],
                    'rootEntity': root,
                })
            m['aggregates'] = aggs

        # ---- 2) 扁平式：aggregate 无 rootEntity 但有 attributes → 提升为 rootEntity ----
        aggs = []
        for agg in (m.get('aggregates') or []):
            if not isinstance(agg, dict):
                aggs.append(agg)
                continue
            if 'rootEntity' not in agg and agg.get('attributes') is not None:
                root = {}
                for k in ('alias', 'name', 'description', 'lifecycle', 'tags', 'attributes',
                          'constraints', 'compositions', 'aggregateConstraints'):
                    if k in agg:
                        root[k] = agg[k]
                new_agg = {k: v for k, v in agg.items() if k not in root}
                new_agg['rootEntity'] = root
                aggs.append(new_agg)
            else:
                aggs.append(agg)
        m['aggregates'] = aggs

        # ---- 统一关联表 associations ----
        associations = []
        # relations（DataAnalyse 实体式 / sample 顶层 relations）
        for rel in (m.get('relations') or []):
            if not isinstance(rel, dict):
                continue
            associations.append({
                'source': rel.get('sourceEntity') or rel.get('source'),
                'target': rel.get('targetEntity') or rel.get('target'),
                'type': (rel.get('type') or 'association').lower(),
                'sourceRole': rel.get('sourceRole'),
                'targetRole': rel.get('targetRole'),
                'cardinality': rel.get('sourceCardinality') or rel.get('cardinality'),
                'cascadeDelete': rel.get('cascadeDelete', False),
            })
        # aggregate_associations（V2 扁平式）
        for assoc in (m.get('aggregate_associations') or []):
            if not isinstance(assoc, dict):
                continue
            associations.append({
                'source': assoc.get('sourceAggregate'),
                'target': assoc.get('targetAggregate'),
                'type': (assoc.get('associationType') or 'reference').lower(),
                'sourceRole': assoc.get('sourceRole'),
                'targetRole': assoc.get('targetRole'),
                'cardinality': assoc.get('cardinality'),
                'cascadeDelete': assoc.get('cascadeDelete', False),
                'referenceField': assoc.get('referenceField'),
            })
        if associations:
            m['associations'] = associations

        return m
    
    def save_workspace(self, workspace: Dict[str, Any], validate_before_save: bool = True) -> Dict[str, Any]:
        """保存工作区"""
        if validate_before_save:
            validation = self.validation_service.validate_workspace(workspace)
            if validation['errors']:
                return {
                    'success': False,
                    'error': {
                        'code': 'MODEL_VALIDATION_ERROR',
                        'message': '模型校验失败',
                        'details': validation
                    }
                }
        
        directory = workspace['workspaceMeta']['directory']
        model_files = workspace.get('extensions', {}).get('modelFiles', {})

        # 动态模型表：只保存本工作区实际加载且登记过原文件的模型
        for model_key, filename in model_files.items():
            model_data = workspace['models'].get(model_key)
            if model_data:
                file_path = os.path.join(directory, filename)
                yaml_content = self.yaml_service.serialize_yaml(model_data)
                self.file_service.write_file(file_path, yaml_content)

        return {'success': True, 'message': '保存成功'}

    def _resolve_directory(self, directory: str) -> str:
        """支持绝对路径、当前进程相对路径和项目根相对路径。"""
        if self.file_service.check_directory(directory):
            return directory

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        project_relative = os.path.join(project_root, directory)
        if self.file_service.check_directory(project_relative):
            return project_relative

        return directory
    
    def scan_workspaces(self, root: str = None, max_depth: int = 4) -> List[Dict[str, Any]]:
        """扫描目录，返回候选工作区列表（含模型文件清单与领域）。
        root 为空时默认扫描项目根目录（Sharptoolbox 工作区）。
        """
        if not root:
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

        candidates = self.file_service.scan_workspace_directories(root, max_depth)

        # 补充每个候选目录的领域信息（优先读对象模型 m1 的 domain 字段）
        for candidate in candidates:
            m1_path = os.path.join(candidate['directory'], 'm1-object-model.yaml')
            content = self.file_service.read_file(m1_path)
            if content:
                parsed = self.yaml_service.parse_yaml(content)
                if parsed and parsed.get('domain'):
                    candidate['domain'] = parsed['domain']

        return candidates
