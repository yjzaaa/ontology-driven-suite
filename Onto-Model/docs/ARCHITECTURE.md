# 架构设计文档

## 系统架构

本体模型编辑器采用前后端分离架构：

```
┌─────────────────────────────────────────────────────────┐
│                    浏览器 (Browser)                      │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │         React Frontend (Port 3000)              │    │
│  │  ┌──────────────┐  ┌──────────────────────┐   │    │
│  │  │  UI Components│  │  State Management    │   │    │
│  │  │  - ModelTree  │  │  - Workspace State   │   │    │
│  │  │  - Editors    │  │  - Validation State  │   │    │
│  │  │  - Toolbar    │  │  - UI State          │   │    │
│  │  └──────────────┘  └──────────────────────┘   │    │
│  │           │                    │                │    │
│  │           └────────┬───────────┘                │    │
│  │                    │                            │    │
│  │         ┌──────────▼──────────┐                │    │
│  │         │   API Service Layer  │                │    │
│  │         │   - workspaceApi     │                │    │
│  │         │   - validationApi    │                │    │
│  │         │   - referenceApi     │                │    │
│  │         └──────────┬──────────┘                │    │
│  └────────────────────┼───────────────────────────┘    │
└────────────────────────┼────────────────────────────────┘
                         │ HTTP/JSON
                         │
┌────────────────────────▼────────────────────────────────┐
│              Flask Backend (Port 5000)                   │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │              API Routes Layer                   │    │
│  │  - /api/workspace/*                             │    │
│  │  - /api/validation/*                            │    │
│  │  - /api/references/*                            │    │
│  └────────────────┬───────────────────────────────┘    │
│                   │                                      │
│  ┌────────────────▼───────────────────────────────┐    │
│  │            Service Layer                        │    │
│  │  ┌──────────────────┐  ┌──────────────────┐   │    │
│  │  │ WorkspaceService │  │ ValidationService│   │    │
│  │  └──────────────────┘  └──────────────────┘   │    │
│  │  ┌──────────────────┐  ┌──────────────────┐   │    │
│  │  │ ReferenceService │  │   YamlService    │   │    │
│  │  └──────────────────┘  └──────────────────┘   │    │
│  │  ┌──────────────────┐                          │    │
│  │  │   FileService    │                          │    │
│  │  └──────────────────┘                          │    │
│  └────────────────┬───────────────────────────────┘    │
└────────────────────┼────────────────────────────────────┘
                     │
                     │ File I/O
                     │
┌────────────────────▼────────────────────────────────────┐
│                  File System                             │
│                                                          │
│  models/                                                 │
│  └── {domain}/                                          │
│      ├── m1-object-model.yaml                           │
│      ├── m2-behavior-model.yaml                         │
│      ├── m3-rule-model.yaml                             │
│      ├── m4-scenario-model.yaml                         │
│      └── event-model.yaml                               │
└──────────────────────────────────────────────────────────┘
```

## 核心设计原则

### 1. 定义与引用分离

**问题**：如何避免模型定义的重复和不一致？

**解决方案**：
- 每个模型元素只在一个地方定义（单一事实来源）
- 其他地方通过引用（Reference）关联
- 树状视图中区分"定义节点"和"引用节点"

**实现**：
```typescript
// 定义节点（可编辑）
{
  nodeType: 'behavior',
  nodeId: 'Contract_Create',
  isReference: false  // 定义
}

// 引用节点（只读或有限编辑）
{
  nodeType: 'behavior',
  nodeId: 'Contract_Create',
  isReference: true   // 引用
}
```

### 2. 多文件存储

**问题**：如何组织复杂的本体模型？

**解决方案**：
- 按模型类型拆分为独立YAML文件
- 运行时在内存中构建统一工作区
- 保存时分别写回各个文件

**文件映射**：
```
M1 对象模型    → m1-object-model.yaml
M2 行为模型    → m2-behavior-model.yaml
M3 规则模型    → m3-rule-model.yaml
M4 场景模型    → m4-scenario-model.yaml
独立事件模型   → event-model.yaml
```

### 3. 工作区模式

**工作区结构**：
```typescript
interface Workspace {
  workspaceMeta: {
    directory: string;      // 文件目录
    domain: string | null;  // 业务域
  };
  models: {
    objectModel: any;       // M1
    behaviorModel: any;     // M2
    ruleModel: any;         // M3
    eventModel: any;        // 独立事件
    scenarioModel: any;     // M4
  };
  validation: {
    errors: ValidationError[];
    warnings: ValidationError[];
  };
  fileStats: any;
  extensions: any;          // 扩展字段保留
}
```

### 4. 保真导入导出

**目标**：导入后再导出应得到等价的YAML结构

**策略**：
1. 保留所有结构化说明字段（description、remark、notes）
2. 保留未识别的扩展字段到 `extensions`
3. 序列化时保持字段顺序稳定
4. 使用 `allow_unicode=True` 支持中文

## 数据流

### 打开工作区流程

```
用户输入目录路径
    ↓
前端调用 workspaceApi.openWorkspace()
    ↓
后端 WorkspaceService.open_workspace()
    ↓
FileService 读取5个YAML文件
    ↓
YamlService 解析为Python字典
    ↓
ValidationService 执行跨文件校验
    ↓
ReferenceService 构建引用索引
    ↓
返回完整Workspace对象
    ↓
前端更新状态并渲染树
```

### 保存工作区流程

```
用户点击保存
    ↓
前端调用 workspaceApi.saveWorkspace()
    ↓
后端 WorkspaceService.save_workspace()
    ↓
（可选）ValidationService 保存前校验
    ↓
YamlService 序列化为YAML字符串
    ↓
FileService 原子写入文件
    ↓
返回保存结果
    ↓
前端更新脏状态标记
```

### 校验流程

```
用户点击校验
    ↓
前端调用 validationApi.runValidation()
    ↓
后端 ValidationService.validate_workspace()
    ↓
构建实体/行为/规则ID索引
    ↓
执行15项校验规则
    ↓
返回 errors 和 warnings 列表
    ↓
前端显示错误徽章和详情
```

## 校验规则实现

### 1. 实体唯一性校验
```python
entity_ids = set()
for entity in entities:
    if entity.id in entity_ids:
        errors.append({
            'code': 'ENTITY_ID_DUPLICATE',
            'message': f'实体ID重复: {entity.id}'
        })
    entity_ids.add(entity.id)
```

### 2. 行为归属校验
```python
for behavior in behaviors:
    if behavior.ownerEntity not in entity_ids:
        errors.append({
            'code': 'BEHAVIOR_OWNER_NOT_FOUND',
            'message': f'行为的ownerEntity不存在'
        })
```

### 3. 事件生产者校验
```python
for event in events:
    if event.producerBehaviorRef not in behavior_ids:
        errors.append({
            'code': 'EVENT_PRODUCER_NOT_FOUND',
            'message': f'事件的生产者行为不存在'
        })
```

## 引用索引设计

### 索引结构
```python
{
  'behavior_to_entity': {
    'Contract_Create': 'ENT-CON-001'
  },
  'behavior_to_rules': {
    'Contract_Create': ['RULE-CON-001', 'RULE-CON-002']
  },
  'event_to_producer': {
    'Contract.Created': 'Contract_Create'
  },
  'event_to_subscribers': {
    'Contract.Created': ['PaymentTerm_BatchCreate']
  }
}
```

### 删除影响分析
```python
def analyze_delete_impact(node_type, node_id):
    references = find_references(node_type, node_id)
    can_delete = len(references) == 0
    return {
        'canDelete': can_delete,
        'references': references,
        'message': '...'
    }
```

## 前端状态管理

### 状态层次
```
全局状态
├── workspace (Workspace | null)
├── openTabs (Tab[])
├── activeTab (string)
└── isDirty (boolean)

Tab状态
├── key (string)
├── title (string)
├── nodeType (string)
├── nodeId (string)
├── data (any)
└── isReference (boolean)
```

### 编辑器路由
```typescript
switch (tab.nodeType) {
  case 'entity':
    return <EntityEditor />;
  case 'behavior':
    return <BehaviorEditor />;
  case 'event':
    return <EventEditor />;
  case 'rule':
    return <RuleEditor />;
  case 'usecase':
    return <UseCaseEditor />;
}
```

## 扩展性设计

### 1. 新增模型类型

后端：
```python
# services/workspace_service.py
files = {
    'm1': 'm1-object-model.yaml',
    'm2': 'm2-behavior-model.yaml',
    'm5': 'm5-actor-model.yaml',  # 新增
}
```

前端：
```typescript
// types/models.ts
export interface Workspace {
  models: {
    objectModel: any;
    behaviorModel: any;
    actorModel: any;  // 新增
  };
}
```

### 2. 新增编辑器

```typescript
// components/editors/ActorEditor.tsx
const ActorEditor: React.FC<ActorEditorProps> = ({ actor, onChange }) => {
  // 实现编辑器
};

// App.tsx
case 'actor':
  return <ActorEditor />;
```

### 3. 新增校验规则

```python
# services/validation_service.py
def validate_workspace(workspace):
    # 现有校验...
    
    # 新增校验
    self._validate_actor_roles(workspace)
```

## 性能优化

### 1. 大文件处理
- 使用流式解析（未来）
- 分页加载树节点
- 虚拟滚动列表

### 2. 校验优化
- 增量校验（只校验修改部分）
- 异步校验
- 缓存校验结果

### 3. 前端优化
- React.memo 避免不必要渲染
- useMemo 缓存计算结果
- 懒加载编辑器组件

## 安全考虑

### 1. 文件路径安全
```python
# 防止路径遍历攻击
def validate_path(path):
    if '..' in path or path.startswith('/'):
        raise SecurityError('Invalid path')
```

### 2. YAML注入防护
- 使用 `yaml.safe_load()` 而非 `yaml.load()`
- 限制YAML文件大小
- 验证YAML结构

### 3. CORS配置
```python
# 生产环境应限制来源
CORS(app, origins=['https://your-domain.com'])
```

## 测试策略

### 后端测试
```python
# tests/test_validation_service.py
def test_entity_uniqueness():
    workspace = create_test_workspace()
    result = validation_service.validate_workspace(workspace)
    assert len(result['errors']) == 0
```

### 前端测试
```typescript
// components/__tests__/ModelTree.test.tsx
test('renders tree nodes correctly', () => {
  render(<ModelTree workspace={mockWorkspace} />);
  expect(screen.getByText('对象模型')).toBeInTheDocument();
});
```

## 未来增强

1. **实时协作**：WebSocket + OT算法
2. **版本控制**：Git集成
3. **代码生成**：基于模型生成实体类、API接口
4. **可视化**：图形化展示实体关系、事件链
5. **导入导出**：支持JSON、XML格式
6. **权限管理**：基于M5主体模型的访问控制
