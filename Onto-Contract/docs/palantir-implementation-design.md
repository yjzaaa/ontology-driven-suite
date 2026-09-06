# Onto-Contract 项目 Palantir 思想落地实施设计文档

## 文档信息

- **版本**: v1.0
- **日期**: 2026-01-15
- **作者**: AI Assistant
- **状态**: 设计阶段

---

## 目录

1. [项目概述](#1-项目概述)
2. [现状分析](#2-现状分析)
3. [Palantir 核心思想借鉴](#3-palantir-核心思想借鉴)
4. [工程化能力设计](#4-工程化能力设计)
5. [实施路线图](#5-实施路线图)
6. [技术架构设计](#6-技术架构设计)
7. [数据模型增强](#7-数据模型增强)
8. [API 设计](#8-api-设计)
9. [安全与权限](#9-安全与权限)
10. [监控与运维](#10-监控与运维)

---

## 1. 项目概述

### 1.1 项目背景

Onto-Contract 是一个基于本体驱动架构（Ontology-Driven Architecture）的合同管理系统。项目采用"需求探索 → 本体建模 → 应用构建"的三步法，通过七模型本体 YAML（M1~M7+ME）定义业务语义，并构建可运行的业务系统。

### 1.2 设计目标

本文档旨在将 Palantir Foundry/Ontology 的核心思想落地到 Onto-Contract 项目中，提升系统的工程化水平，使其从"可运行的原型"进化为"生产级的企业应用"。

### 1.3 核心借鉴来源

| 来源 | 核心思想 | 借鉴内容 |
|-----|---------|---------|
| **Palantir Foundry** | 数字孪生、OAG、Action Types | 本体作为企业 AI 操作系统 |
| **微服务社区** | Saga 模式、熔断器 | 分布式事务与容错 |
| **DDD 社区** | 聚合根、限界上下文 | 领域模型设计 |
| **LLM 工程** | Function Calling、轨迹记录 | AI 可观测性 |

---

## 2. 现状分析

### 2.1 当前架构

```
Onto-Contract 当前架构:
┌─────────────────────────────────────────┐
│  前端 (React + TypeScript)              │
│  ├── 固定页面（合同录入/开票/收款/查询）  │
│  └── AI Chat 面板（DeepSeek 对话）       │
├─────────────────────────────────────────┤
│  后端 (Python + Flask + SQLite)         │
│  ├── API 路由层 (routes.py)              │
│  ├── 业务服务层 (contract_service.py)    │
│  ├── AI 编排层 (orchestrator.py)         │
│  └── 本体加载器 (loader.py)              │
├─────────────────────────────────────────┤
│  数据层                                 │
│  ├── SQLite (contract.db)               │
│  └── YAML 本体模型 (models/contract/*.yaml)│
└─────────────────────────────────────────┘
```

### 2.2 当前能力矩阵

| 能力 | 状态 | 说明 |
|-----|------|------|
| 本体建模 | ✅ 完整 | M1~M7+ME 十一模型 |
| 运行时加载 | ✅ 完整 | OntologyRegistry 内存加载 |
| 标准 CRUD | ✅ 完整 | 合同/发票/收款的增删改查 |
| 主从结构 | ✅ 一层 | 合同 + 付款条款 |
| AI 对话 | ✅ 基础 | DeepSeek 对话辅助 |
| 语义查询 | ✅ 基础 | 自然语言 → SQL |
| **执行轨迹** | ❌ 缺失 | 无执行过程记录 |
| **审计日志** | ⚠️ 基础 | 仅记录行为执行，不完整 |
| **Saga 补偿** | ❌ 缺失 | 无事务补偿机制 |
| **熔断降级** | ❌ 缺失 | 无容错机制 |
| **权限控制** | ❌ 缺失 | 仅基础登录 |
| **分布式追踪** | ❌ 缺失 | 无 Trace ID |

### 2.3 核心问题

1. **AI 只能查询，不能可靠执行**：当前 AI 对话仅支持只读查询，写操作需要人工在固定页面完成
2. **无执行过程可追溯**：用户无法查看 AI 的决策过程，无法回放执行轨迹
3. **无事务保障**：复杂业务操作（如收款确认后更新合同状态）缺乏事务一致性保障
4. **无容错机制**：外部服务（如 DeepSeek API）故障时无降级策略
5. **权限控制薄弱**：无 RBAC/ABAC，所有登录用户拥有全部权限

---

## 3. Palantir 核心思想借鉴

### 3.1 数字孪生（Digital Twin）

**Palantir 定义**："A digital twin of the organization — a semantic layer that sits on top of datasets and models."

**落地实施**：
- 将 OntologyRegistry 从"配置加载器"升级为"数字孪生引擎"
- 实时同步业务数据状态到本体模型
- 为 AI 提供完整的业务语义上下文

```python
# 升级后的 OntologyRegistry
class DigitalTwinEngine:
    def __init__(self):
        self.ontology = OntologyRegistry()  # 本体定义
        self.state = RealTimeState()        # 实时状态
        self.history = StateHistory()       # 状态历史
    
    def get_object(self, object_type, object_id):
        """获取对象的完整视图（定义 + 实时状态 + 历史）"""
        definition = self.ontology.get(object_type)
        state = self.state.get(object_type, object_id)
        history = self.history.get(object_type, object_id)
        return ObjectView(definition, state, history)
```

### 3.2 OAG（Ontology Augmented Generation）

**Palantir 创新**：用结构化业务对象查询替代文本检索，实现确定性匹配。

**落地实施**：
- 将当前的自然语言 → SQL 升级为自然语言 → Ontology Query → 结构化执行
- AI 不再"猜测"表结构，而是"理解"业务对象关系

```json
// 当前：自然语言 → SQL（易出错）
{
  "query": "查询销售一部的合同",
  "sql": "SELECT * FROM contracts c JOIN departments d ON c.dept_id = d.id WHERE d.dept_name = '销售一部'"
}

// 目标：自然语言 → Ontology Query（确定性）
{
  "query": "查询销售一部的合同",
  "ontology_query": {
    "object_type": "Contract",
    "filters": {
      "department": {"eq": "销售一部"}
    },
    "links": ["department", "customer", "owner"],
    "response_format": "table"
  }
}
```

### 3.3 Action Types（动作类型）

**Palantir 定义**："Action type is the schema definition of a set of changes or edits to objects, property values, and links that a user can take at once."

**落地实施**：
- 将 M2 行为模型增强为可执行的 Action Type
- 定义前置条件、执行效果、副作用、补偿操作

```yaml
# m2-behavior-model.yaml 增强
action_types:
  - id: Payment_Receive
    name: 确认收款
    description: 确认发票收款，更新合同收款状态
    
    input:
      - name: invoiceId
        type: Reference
        refEntity: Invoice
        required: true
      - name: receivedDate
        type: DateTime
        required: false
    
    preconditions:
      - expression: "invoice.status == '已开票'"
        violationMessage: "只有已开票的发票才能确认收款"
      - expression: "invoice.isReceived == false"
        violationMessage: "该发票已确认收款"
    
    effects:
      - target: Invoice
        operation: UPDATE
        fields:
          isReceived: true
          status: "已收款"
          receivedDate: "{{input.receivedDate || now()}}"
      
      - target: Contract
        operation: UPDATE
        fields:
          receivedAmountTotal: "{{contract.receivedAmountTotal + invoice.amount}}"
        
      - target: Contract
        operation: EVALUATE
        field: receiptStatus
        rules:
          - condition: "receivedAmountTotal >= totalAmount"
            value: "已收款"
          - condition: "receivedAmountTotal > 0"
            value: "部分收款"
    
    side_effects:
      - type: EMIT_EVENT
        event: Payment.Received
        payload: ["invoiceId", "contractId", "amount"]
      
      - type: AUDIT_LOG
        action: "Payment_Receive"
        actor: "{{context.actor}}"
      
      - type: NOTIFICATION
        channel: "finance_dept"
        template: "contract_payment_received"
    
    compensation:
      - condition: "on_failure"
        operations:
          - target: Invoice
            operation: UPDATE
            fields:
              isReceived: false
              status: "已开票"
              receivedDate: null
```

### 3.4 Human-in-the-Loop

**Palantir 原则**："We don't sell autonomous driving. We sell a copilot."

**落地实施**：
- AI 推荐 Action → 人工确认 → 执行
- 高风险操作必须人工审批
- 执行过程透明可审查

```
用户: "帮我确认合同 HT001 的收款"
        │
        ▼
AI: 查询 Ontology → 发现 Invoice FP001 已开票未收款
        │
        ▼
AI: 推荐 Action: Payment_Receive(invoiceId=FP001)
     影响分析:
     - 发票 FP001 状态变更为"已收款"
     - 合同 HT001 累计收款增加 18万
     - 合同收款状态可能变更为"部分收款"
     - 将通知财务部门
        │
        ▼
用户: [确认执行] / [修改参数] / [取消]
        │
        ▼
AI: 执行 Action → 记录完整轨迹 → 返回结果
```

---

## 4. 工程化能力设计

### 4.1 执行轨迹记录（Trajectory / Replay）

#### 4.1.1 设计目标

- 记录 AI 决策的完整过程（为什么这样决策）
- 记录业务执行的每一步（做了什么、结果如何）
- 支持执行过程的回放与审查
- 支持从任意步骤重试

#### 4.1.2 数据模型

```python
# trajectory_models.py

@dataclass
class ExecutionStep:
    """执行步骤"""
    step_id: str                    # 步骤唯一ID (step-{n})
    action_type: str                # 动作类型 (QUERY / ACTION / VALIDATION / NOTIFICATION)
    action_name: str                # 动作名称
    
    # 输入输出
    input_data: Dict[str, Any]      # 输入数据
    output_data: Dict[str, Any]     # 输出结果
    
    # 状态
    status: str                     # PENDING / RUNNING / SUCCESS / FAILED / COMPENSATED / SKIPPED
    
    # 时间
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: int                # 执行耗时
    
    # 元数据
    metadata: Dict[str, Any]        # 扩展信息
    
    # 补偿信息
    compensation_step_id: Optional[str]  # 对应的补偿步骤ID

@dataclass
class ExecutionTrajectory:
    """执行轨迹"""
    trajectory_id: str              # 轨迹ID (traj-{timestamp}-{random})
    trace_id: str                   # 分布式追踪ID (trace-{uuid})
    
    # 参与者
    user_id: str                    # 执行用户
    agent_id: str                   # 执行Agent
    session_id: str                 # 会话ID
    
    # 执行计划
    plan: Dict[str, Any]            # 执行计划（DAG）
    steps: List[ExecutionStep]      # 执行步骤列表
    
    # 状态
    final_status: str               # SUCCESS / FAILED / PARTIAL / CANCELLED
    
    # 时间
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    total_duration_ms: int
    
    # 上下文
    context: Dict[str, Any]         # 执行上下文（用户角色、权限等）

@dataclass
class TrajectorySummary:
    """轨迹摘要（用于列表展示）"""
    trajectory_id: str
    user_id: str
    action_summary: str             # 动作摘要
    final_status: str
    created_at: datetime
    total_duration_ms: int
    step_count: int
```

#### 4.1.3 存储设计

```sql
-- trajectories 表
CREATE TABLE trajectories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trajectory_id TEXT UNIQUE NOT NULL,
    trace_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    agent_id TEXT,
    session_id TEXT,
    plan_json TEXT,                 -- 执行计划JSON
    steps_json TEXT,                -- 步骤列表JSON
    final_status TEXT NOT NULL,     -- SUCCESS / FAILED / PARTIAL / CANCELLED
    context_json TEXT,              -- 上下文JSON
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    total_duration_ms INTEGER,
    
    INDEX idx_trace_id (trace_id),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_final_status (final_status)
);

-- trajectory_steps 表（步骤详情，用于查询单步）
CREATE TABLE trajectory_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trajectory_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    step_order INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    action_name TEXT NOT NULL,
    input_json TEXT,
    output_json TEXT,
    status TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    duration_ms INTEGER,
    metadata_json TEXT,
    compensation_step_id TEXT,
    
    FOREIGN KEY (trajectory_id) REFERENCES trajectories(trajectory_id),
    INDEX idx_trajectory_id (trajectory_id),
    INDEX idx_step_id (step_id)
);
```

#### 4.1.4 核心实现

```python
# trajectory_service.py

class TrajectoryRecorder:
    """执行轨迹记录器"""
    
    def __init__(self, db: sqlite3.Connection):
        self.db = db
    
    def start_trajectory(self, user_id: str, agent_id: str, 
                        plan: Dict[str, Any], context: Dict[str, Any]) -> str:
        """开始记录一条执行轨迹"""
        trajectory_id = f"traj-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        trace_id = f"trace-{uuid.uuid4().hex}"
        
        self.db.execute("""
            INSERT INTO trajectories 
            (trajectory_id, trace_id, user_id, agent_id, plan_json, context_json, final_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            trajectory_id, trace_id, user_id, agent_id,
            json.dumps(plan), json.dumps(context), "RUNNING"
        ))
        self.db.commit()
        
        return trajectory_id
    
    def record_step(self, trajectory_id: str, step: ExecutionStep):
        """记录一个执行步骤"""
        # 更新步骤表
        self.db.execute("""
            INSERT INTO trajectory_steps
            (trajectory_id, step_id, step_order, action_type, action_name,
             input_json, output_json, status, started_at, completed_at, 
             duration_ms, metadata_json, compensation_step_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trajectory_id, step.step_id, len(self._get_steps(trajectory_id)),
            step.action_type, step.action_name,
            json.dumps(step.input_data), json.dumps(step.output_data),
            step.status, step.started_at.isoformat(),
            step.completed_at.isoformat() if step.completed_at else None,
            step.duration_ms, json.dumps(step.metadata),
            step.compensation_step_id
        ))
        
        # 更新轨迹表
        self.db.execute("""
            UPDATE trajectories 
            SET steps_json = ?, updated_at = ?
            WHERE trajectory_id = ?
        """, (json.dumps([s.__dict__ for s in self._get_steps(trajectory_id)]),
              datetime.now().isoformat(), trajectory_id))
        
        self.db.commit()
    
    def complete_trajectory(self, trajectory_id: str, status: str, 
                           total_duration_ms: int):
        """完成轨迹记录"""
        self.db.execute("""
            UPDATE trajectories 
            SET final_status = ?, completed_at = ?, total_duration_ms = ?
            WHERE trajectory_id = ?
        """, (status, datetime.now().isoformat(), total_duration_ms, trajectory_id))
        self.db.commit()
    
    def get_trajectory(self, trajectory_id: str) -> Optional[ExecutionTrajectory]:
        """获取完整轨迹"""
        row = self.db.execute(
            "SELECT * FROM trajectories WHERE trajectory_id = ?", 
            (trajectory_id,)
        ).fetchone()
        
        if not row:
            return None
        
        steps = self._get_steps(trajectory_id)
        
        return ExecutionTrajectory(
            trajectory_id=row["trajectory_id"],
            trace_id=row["trace_id"],
            user_id=row["user_id"],
            agent_id=row["agent_id"],
            session_id=row["session_id"],
            plan=json.loads(row["plan_json"]),
            steps=steps,
            final_status=row["final_status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            total_duration_ms=row["total_duration_ms"],
            context=json.loads(row["context_json"]) if row["context_json"] else {}
        )
    
    def replay(self, trajectory_id: str, from_step: int = 0) -> Generator[ExecutionStep, None, None]:
        """回放执行轨迹"""
        trajectory = self.get_trajectory(trajectory_id)
        if not trajectory:
            raise ValueError(f"Trajectory {trajectory_id} not found")
        
        for step in trajectory.steps[from_step:]:
            yield step
    
    def _get_steps(self, trajectory_id: str) -> List[ExecutionStep]:
        """获取轨迹的所有步骤"""
        rows = self.db.execute(
            "SELECT * FROM trajectory_steps WHERE trajectory_id = ? ORDER BY step_order",
            (trajectory_id,)
        ).fetchall()
        
        return [ExecutionStep(
            step_id=row["step_id"],
            action_type=row["action_type"],
            action_name=row["action_name"],
            input_data=json.loads(row["input_json"]) if row["input_json"] else {},
            output_data=json.loads(row["output_json"]) if row["output_json"] else {},
            status=row["status"],
            started_at=datetime.fromisoformat(row["started_at"]),
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            duration_ms=row["duration_ms"],
            metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else {},
            compensation_step_id=row["compensation_step_id"]
        ) for row in rows]
```

#### 4.1.5 使用示例

```python
# 在业务服务中使用轨迹记录

class ContractServiceWithTrajectory:
    def __init__(self, db, trajectory_recorder):
        self.db = db
        self.trajectory = trajectory_recorder
    
    def create_contract(self, payload: dict, actor: str = None):
        # 开始轨迹
        traj_id = self.trajectory.start_trajectory(
            user_id=actor,
            agent_id="contract-service",
            plan={"action": "Contract_Create", "steps": ["validate", "insert", "notify"]},
            context={"actor": actor, "ip": get_client_ip()}
        )
        
        try:
            # Step 1: 校验
            step1 = ExecutionStep(
                step_id="step-1",
                action_type="VALIDATION",
                action_name="validate_contract_payload",
                input_data=payload,
                status="RUNNING",
                started_at=datetime.now()
            )
            
            self._validate_payload(payload)
            
            step1.status = "SUCCESS"
            step1.output_data = {"valid": True}
            step1.completed_at = datetime.now()
            step1.duration_ms = 45
            self.trajectory.record_step(traj_id, step1)
            
            # Step 2: 插入数据库
            step2 = ExecutionStep(
                step_id="step-2",
                action_type="ACTION",
                action_name="insert_contract",
                input_data=payload,
                status="RUNNING",
                started_at=datetime.now()
            )
            
            contract_id = self._insert_contract(payload)
            
            step2.status = "SUCCESS"
            step2.output_data = {"contract_id": contract_id}
            step2.completed_at = datetime.now()
            step2.duration_ms = 120
            self.trajectory.record_step(traj_id, step2)
            
            # 完成轨迹
            self.trajectory.complete_trajectory(traj_id, "SUCCESS", 165)
            
            return {"ok": True, "id": contract_id, "trajectory_id": traj_id}
            
        except Exception as e:
            # 记录失败
            self.trajectory.complete_trajectory(traj_id, "FAILED", 0)
            raise
```

### 4.2 审计与追责（Audit & Accountability）

#### 4.2.1 设计目标

- 不可篡改的审计日志
- 支持事后追责
- 满足合规要求（SOX、GDPR 等）
- 与执行轨迹关联

#### 4.2.2 数据模型

```python
# audit_models.py

@dataclass
class AuditRecord:
    """审计记录"""
    id: str                         # 记录ID
    timestamp: datetime             # 时间戳
    
    # 事件分类
    event_type: str                 # 事件类型
    event_category: str             # 事件分类 (SECURITY / BUSINESS / SYSTEM / DATA)
    
    # 参与者
    actor: str                      # 执行者 (用户ID / AgentID / system)
    actor_type: str                 # actor类型 (USER / AGENT / SYSTEM)
    
    # 操作对象
    resource_type: str              # 资源类型 (Contract / Invoice / User)
    resource_id: str                # 资源ID
    
    # 操作详情
    action: str                     # 动作名称
    action_type: str                # 动作类型 (READ / WRITE / DELETE / EXECUTE)
    
    # 输入输出
    input_data: Dict[str, Any]      # 输入数据（脱敏后）
    output_data: Dict[str, Any]     # 输出结果（脱敏后）
    
    # 结果
    status: str                     # SUCCESS / FAILED / DENIED
    error_message: Optional[str]    # 错误信息
    
    # 上下文
    trace_id: str                   # 追踪ID
    trajectory_id: str              # 轨迹ID
    session_id: str                 # 会话ID
    ip_address: str                 # IP地址
    user_agent: str                 # 用户代理
    
    # 完整性校验
    record_hash: str                # 记录哈希（防篡改）
    prev_hash: str                  # 上一条记录哈希

# 事件类型枚举
class AuditEventType:
    # 安全事件
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    
    # 业务事件
    BEHAVIOR_EXECUTE = "BEHAVIOR_EXECUTE"
    DATA_CREATE = "DATA_CREATE"
    DATA_UPDATE = "DATA_UPDATE"
    DATA_DELETE = "DATA_DELETE"
    DATA_QUERY = "DATA_QUERY"
    
    # AI 事件
    AGENT_DECISION = "AGENT_DECISION"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    AI_RECOMMENDATION = "AI_RECOMMENDATION"
    
    # 系统事件
    SYSTEM_ERROR = "SYSTEM_ERROR"
    CIRCUIT_BREAK = "CIRCUIT_BREAK"
    COMPENSATION_START = "COMPENSATION_START"
    
    # 数据事件
    DATA_EXPORT = "DATA_EXPORT"
    DATA_IMPORT = "DATA_IMPORT"
    BACKUP_CREATE = "BACKUP_CREATE"
```

#### 4.2.3 存储设计

```sql
-- audit_logs 表（不可篡改审计日志）
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT UNIQUE NOT NULL,     -- 记录唯一ID
    timestamp TEXT NOT NULL,             -- 时间戳
    
    event_type TEXT NOT NULL,            -- 事件类型
    event_category TEXT NOT NULL,        -- 事件分类
    
    actor TEXT NOT NULL,                 -- 执行者
    actor_type TEXT NOT NULL,            -- 执行者类型
    
    resource_type TEXT,                  -- 资源类型
    resource_id TEXT,                    -- 资源ID
    
    action TEXT NOT NULL,                -- 动作
    action_type TEXT NOT NULL,           -- 动作类型
    
    input_json TEXT,                     -- 输入数据（脱敏）
    output_json TEXT,                    -- 输出数据（脱敏）
    
    status TEXT NOT NULL,                -- 状态
    error_message TEXT,                  -- 错误信息
    
    trace_id TEXT,                       -- 追踪ID
    trajectory_id TEXT,                  -- 轨迹ID
    session_id TEXT,                     -- 会话ID
    ip_address TEXT,                     -- IP地址
    user_agent TEXT,                     -- 用户代理
    
    record_hash TEXT NOT NULL,           -- 本记录哈希
    prev_hash TEXT,                      -- 上一条记录哈希
    
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_timestamp (timestamp),
    INDEX idx_actor (actor),
    INDEX idx_resource (resource_type, resource_id),
    INDEX idx_trace_id (trace_id),
    INDEX idx_event_type (event_type)
);
```

#### 4.2.4 核心实现

```python
# audit_service.py
import hashlib
import json
from typing import Optional

class AuditLogger:
    """审计日志记录器 - 不可篡改"""
    
    def __init__(self, db: sqlite3.Connection):
        self.db = db
    
    def log(self, 
            event_type: str,
            actor: str,
            action: str,
            resource_type: Optional[str] = None,
            resource_id: Optional[str] = None,
            input_data: Optional[dict] = None,
            output_data: Optional[dict] = None,
            status: str = "SUCCESS",
            error_message: Optional[str] = None,
            trajectory_id: Optional[str] = None,
            context: Optional[dict] = None) -> str:
        """记录审计日志"""
        
        record_id = f"audit-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
        
        # 获取上一条记录的哈希
        prev_hash = self._get_last_hash()
        
        # 构建记录数据
        record_data = {
            "record_id": record_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "actor": actor,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "input_data": self._sanitize(input_data),
            "output_data": self._sanitize(output_data),
            "status": status,
            "error_message": error_message,
            "trajectory_id": trajectory_id,
            "prev_hash": prev_hash
        }
        
        # 计算哈希
        record_hash = self._calculate_hash(record_data)
        
        # 保存记录
        self.db.execute("""
            INSERT INTO audit_logs
            (record_id, timestamp, event_type, event_category, actor, actor_type,
             resource_type, resource_id, action, action_type, input_json, output_json,
             status, error_message, trace_id, trajectory_id, session_id, ip_address,
             user_agent, record_hash, prev_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record_id,
            record_data["timestamp"],
            event_type,
            self._categorize_event(event_type),
            actor,
            context.get("actor_type", "USER") if context else "USER",
            resource_type,
            resource_id,
            action,
            self._classify_action(action),
            json.dumps(record_data["input_data"]),
            json.dumps(record_data["output_data"]),
            status,
            error_message,
            context.get("trace_id") if context else None,
            trajectory_id,
            context.get("session_id") if context else None,
            context.get("ip_address") if context else None,
            context.get("user_agent") if context else None,
            record_hash,
            prev_hash
        ))
        self.db.commit()
        
        return record_id
    
    def verify_integrity(self) -> bool:
        """验证审计日志完整性"""
        rows = self.db.execute(
            "SELECT * FROM audit_logs ORDER BY id"
        ).fetchall()
        
        prev_hash = None
        for row in rows:
            record_data = {
                "record_id": row["record_id"],
                "timestamp": row["timestamp"],
                "event_type": row["event_type"],
                "actor": row["actor"],
                "action": row["action"],
                "resource_type": row["resource_type"],
                "resource_id": row["resource_id"],
                "input_data": json.loads(row["input_json"]) if row["input_json"] else None,
                "output_data": json.loads(row["output_json"]) if row["output_json"] else None,
                "status": row["status"],
                "error_message": row["error_message"],
                "trajectory_id": row["trajectory_id"],
                "prev_hash": prev_hash
            }
            
            expected_hash = self._calculate_hash(record_data)
            if expected_hash != row["record_hash"]:
                return False
            
            prev_hash = row["record_hash"]
        
        return True
    
    def _calculate_hash(self, record_data: dict) -> str:
        """计算记录哈希"""
        data = json.dumps(record_data, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _get_last_hash(self) -> Optional[str]:
        """获取最后一条记录的哈希"""
        row = self.db.execute(
            "SELECT record_hash FROM audit_logs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row["record_hash"] if row else None
    
    def _sanitize(self, data: Optional[dict]) -> Optional[dict]:
        """数据脱敏"""
        if not data:
            return None
        
        sensitive_fields = ["password", "token", "secret", "credit_card", "ssn"]
        sanitized = {}
        for key, value in data.items():
            if any(sf in key.lower() for sf in sensitive_fields):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized
    
    def _categorize_event(self, event_type: str) -> str:
        """事件分类"""
        security_events = ["LOGIN", "LOGOUT", "PERMISSION_DENIED", "PASSWORD_CHANGE"]
        business_events = ["BEHAVIOR_EXECUTE", "DATA_CREATE", "DATA_UPDATE", "DATA_DELETE"]
        ai_events = ["AGENT_DECISION", "HUMAN_APPROVAL", "AI_RECOMMENDATION"]
        system_events = ["SYSTEM_ERROR", "CIRCUIT_BREAK", "COMPENSATION_START"]
        
        if event_type in security_events:
            return "SECURITY"
        elif event_type in business_events:
            return "BUSINESS"
        elif event_type in ai_events:
            return "AI"
        elif event_type in system_events:
            return "SYSTEM"
        else:
            return "OTHER"
    
    def _classify_action(self, action: str) -> str:
        """动作分类"""
        if any(x in action for x in ["CREATE", "INSERT", "ADD"]):
            return "WRITE"
        elif any(x in action for x in ["UPDATE", "MODIFY", "EDIT"]):
            return "WRITE"
        elif any(x in action for x in ["DELETE", "REMOVE", "CANCEL"]):
            return "DELETE"
        elif any(x in action for x in ["QUERY", "GET", "LIST", "SEARCH"]):
            return "READ"
        elif any(x in action for x in ["EXECUTE", "RUN", "PERFORM"]):
            return "EXECUTE"
        else:
            return "OTHER"
```

### 4.3 Saga 事务补偿

#### 4.3.1 设计目标

- 支持跨多个步骤的长事务
- 任一步骤失败时，自动补偿已完成的步骤
- 补偿失败时，升级到人工处理
- 与轨迹记录集成

#### 4.3.2 核心实现

```python
# saga.py

from enum import Enum
from typing import Callable, List, Optional, Dict, Any
from dataclasses import dataclass

class SagaStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    COMPENSATING = "COMPENSATING"
    COMPENSATED = "COMPENSATED"
    FAILED = "FAILED"

@dataclass
class SagaStep:
    """Saga 步骤"""
    name: str
    execute: Callable[[], Any]           # 执行函数
    compensate: Optional[Callable[[], Any]] = None  # 补偿函数
    
    # 执行结果
    result: Any = None
    error: Optional[Exception] = None
    status: SagaStatus = SagaStatus.PENDING

class SagaOrchestrator:
    """Saga 协调器"""
    
    def __init__(self, trajectory_recorder=None):
        self.steps: List[SagaStep] = []
        self.completed_steps: List[SagaStep] = []
        self.trajectory = trajectory_recorder
        self.saga_id = None
    
    def add_step(self, name: str, execute: Callable, compensate: Optional[Callable] = None):
        """添加步骤"""
        self.steps.append(SagaStep(name=name, execute=execute, compensate=compensate))
        return self
    
    def execute(self, saga_id: Optional[str] = None) -> Dict[str, Any]:
        """执行 Saga"""
        self.saga_id = saga_id or f"saga-{uuid.uuid4().hex[:8]}"
        
        try:
            for i, step in enumerate(self.steps):
                # 记录步骤开始
                step.status = SagaStatus.RUNNING
                
                if self.trajectory:
                    self.trajectory.record_step(self.saga_id, ExecutionStep(
                        step_id=f"step-{i}",
                        action_type="SAGA_STEP",
                        action_name=step.name,
                        status="RUNNING",
                        started_at=datetime.now()
                    ))
                
                try:
                    # 执行步骤
                    step.result = step.execute()
                    step.status = SagaStatus.SUCCEEDED
                    self.completed_steps.append(step)
                    
                    # 记录成功
                    if self.trajectory:
                        self.trajectory.record_step(self.saga_id, ExecutionStep(
                            step_id=f"step-{i}",
                            action_type="SAGA_STEP",
                            action_name=step.name,
                            status="SUCCESS",
                            output_data={"result": step.result},
                            completed_at=datetime.now()
                        ))
                    
                except Exception as e:
                    step.error = e
                    step.status = SagaStatus.FAILED
                    
                    # 记录失败
                    if self.trajectory:
                        self.trajectory.record_step(self.saga_id, ExecutionStep(
                            step_id=f"step-{i}",
                            action_type="SAGA_STEP",
                            action_name=step.name,
                            status="FAILED",
                            output_data={"error": str(e)},
                            completed_at=datetime.now()
                        ))
                    
                    # 触发补偿
                    self._compensate()
                    raise SagaFailedException(self.saga_id, step.name, e)
            
            return {
                "saga_id": self.saga_id,
                "status": "SUCCEEDED",
                "results": [step.result for step in self.completed_steps]
            }
            
        except SagaFailedException:
            raise
        except Exception as e:
            self._compensate()
            raise SagaFailedException(self.saga_id, "unknown", e)
    
    def _compensate(self):
        """执行补偿"""
        for step in reversed(self.completed_steps):
            if step.compensate:
                try:
                    step.compensate()
                    step.status = SagaStatus.COMPENSATED
                    
                    if self.trajectory:
                        self.trajectory.record_step(self.saga_id, ExecutionStep(
                            step_id=f"compensate-{step.name}",
                            action_type="COMPENSATION",
                            action_name=f"compensate_{step.name}",
                            status="SUCCESS",
                            completed_at=datetime.now()
                        ))
                        
                except Exception as e:
                    # 补偿失败，需要人工介入
                    if self.trajectory:
                        self.trajectory.record_step(self.saga_id, ExecutionStep(
                            step_id=f"compensate-{step.name}",
                            action_type="COMPENSATION",
                            action_name=f"compensate_{step.name}",
                            status="FAILED",
                            output_data={"error": str(e)},
                            completed_at=datetime.now()
                        ))
                    
                    self._escalate_to_human(step, e)

class SagaFailedException(Exception):
    """Saga 失败异常"""
    def __init__(self, saga_id: str, step_name: str, original_error: Exception):
        self.saga_id = saga_id
        self.step_name = step_name
        self.original_error = original_error
        super().__init__(f"Saga {saga_id} failed at step {step_name}: {original_error}")

# 使用示例
def payment_receive_saga(invoice_id: int, received_date: str, actor: str):
    """收款确认的 Saga"""
    
    saga = SagaOrchestrator()
    
    # 步骤1: 校验发票
    saga.add_step(
        name="validate_invoice",
        execute=lambda: validate_invoice(invoice_id)
    )
    
    # 步骤2: 更新发票状态（可补偿）
    original_invoice_status = None
    def update_invoice():
        nonlocal original_invoice_status
        original_invoice_status = get_invoice_status(invoice_id)
        return update_invoice_status(invoice_id, "已收款", received_date)
    
    def restore_invoice():
        if original_invoice_status:
            restore_invoice_status(invoice_id, original_invoice_status)
    
    saga.add_step(
        name="update_invoice_status",
        execute=update_invoice,
        compensate=restore_invoice
    )
    
    # 步骤3: 更新合同汇总（可补偿）
    original_contract_summary = None
    def update_contract():
        nonlocal original_contract_summary
        invoice = get_invoice(invoice_id)
        contract_id = invoice["contract_id"]
        original_contract_summary = get_contract_summary(contract_id)
        return update_contract_receipt_summary(contract_id, invoice["amount"])
    
    def restore_contract():
        if original_contract_summary:
            restore_contract_summary(contract_id, original_contract_summary)
    
    saga.add_step(
        name="update_contract_summary",
        execute=update_contract,
        compensate=restore_contract
    )
    
    # 步骤4: 发送通知（无需补偿，幂等）
    saga.add_step(
        name="send_notification",
        execute=lambda: send_payment_notification(invoice_id, actor)
    )
    
    return saga.execute()
```

### 4.4 熔断降级（Circuit Breaker）

#### 4.4.1 设计目标

- 防止外部服务故障导致级联失败
- 快速失败，避免资源耗尽
- 自动恢复检测
- 多级降级策略

#### 4.4.2 核心实现

```python
# circuit_breaker.py

import time
import threading
from enum import Enum
from typing import Callable, Optional, Any
from dataclasses import dataclass

class CircuitState(Enum):
    CLOSED = "CLOSED"           # 正常状态
    OPEN = "OPEN"               # 熔断状态
    HALF_OPEN = "HALF_OPEN"     # 半开状态（试探）

@dataclass
class CircuitBreakerConfig:
    """熔断器配置"""
    failure_threshold: int = 5          # 失败阈值
    recovery_timeout: int = 60          # 恢复超时（秒）
    half_open_max_calls: int = 3        # 半开状态最大试探次数
    success_threshold: int = 2          # 半开状态成功阈值

class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.half_open_calls = 0
        
        self._lock = threading.Lock()
    
    def call(self, func: Callable, fallback: Optional[Callable] = None, *args, **kwargs) -> Any:
        """执行函数，带熔断保护"""
        
        with self._lock:
            # 检查状态
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    self.success_count = 0
                else:
                    # 快速失败
                    return self._fallback(fallback, *args, **kwargs)
            
            elif self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    return self._fallback(fallback, *args, **kwargs)
                self.half_open_calls += 1
        
        try:
            # 执行函数
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            if fallback:
                return fallback(*args, **kwargs)
            raise
    
    def _on_success(self):
        """成功处理"""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    # 恢复关闭状态
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.half_open_calls = 0
            else:
                self.failure_count = 0
    
    def _on_failure(self):
        """失败处理"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                # 半开状态失败，重新熔断
                self.state = CircuitState.OPEN
            elif self.failure_count >= self.config.failure_threshold:
                # 达到失败阈值，熔断
                self.state = CircuitState.OPEN
                
                # 记录熔断事件
                audit.log(
                    event_type="CIRCUIT_BREAK",
                    actor="system",
                    action="CIRCUIT_OPEN",
                    resource_type="CircuitBreaker",
                    resource_id=self.name,
                    status="SUCCESS",
                    output_data={
                        "failure_count": self.failure_count,
                        "recovery_timeout": self.config.recovery_timeout
                    }
                )
    
    def _should_attempt_reset(self) -> bool:
        """是否应该尝试恢复"""
        if not self.last_failure_time:
            return True
        return (time.time() - self.last_failure_time) >= self.config.recovery_timeout
    
    def _fallback(self, fallback: Optional[Callable], *args, **kwargs) -> Any:
        """执行降级逻辑"""
        if fallback:
            return fallback(*args, **kwargs)
        
        raise CircuitBreakerOpenException(
            f"Circuit breaker '{self.name}' is OPEN. "
            f"Service temporarily unavailable. "
            f"Please try again after {self.config.recovery_timeout} seconds."
        )
    
    def get_state(self) -> dict:
        """获取当前状态"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "half_open_calls": self.half_open_calls
        }

class CircuitBreakerOpenException(Exception):
    """熔断器打开异常"""
    pass

# 多级降级策略
class DegradationStrategy:
    """降级策略"""
    
    @staticmethod
    def level_0_normal(func, *args, **kwargs):
        """Level 0: 正常服务"""
        return func(*args, **kwargs)
    
    @staticmethod
    def level_1_local_model(query: str) -> dict:
        """Level 1: 降级到本地轻量模型"""
        # 使用本地模型（如 Qwen-7B）处理简单查询
        return {
            "ok": True,
            "degraded": True,
            "level": 1,
            "message": "使用本地模型处理",
            "result": local_model_process(query)
        }
    
    @staticmethod
    def level_2_rule_engine(query: str) -> dict:
        """Level 2: 降级到规则引擎"""
        # 基于关键字的本地回退
        return {
            "ok": True,
            "degraded": True,
            "level": 2,
            "message": "使用规则引擎处理",
            "result": rule_based_fallback(query)
        }
    
    @staticmethod
    def level_3_static_response() -> dict:
        """Level 3: 完全降级"""
        return {
            "ok": False,
            "degraded": True,
            "level": 3,
            "message": "AI 服务暂时不可用，请使用固定业务页面操作或稍后重试",
            "suggestion": "请访问 /entry/Contract 进行手动操作"
        }

# 使用示例
class AIChatService:
    def __init__(self):
        self.breaker = CircuitBreaker(
            name="deepseek_api",
            config=CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=300
            )
        )
    
    def chat(self, message: str) -> dict:
        def call_deepseek():
            return deepseek_client.chat_completion(message)
        
        def fallback(msg):
            # 多级降级
            try:
                return DegradationStrategy.level_1_local_model(msg)
            except:
                try:
                    return DegradationStrategy.level_2_rule_engine(msg)
                except:
                    return DegradationStrategy.level_3_static_response()
        
        return self.breaker.call(call_deepseek, fallback, message)
```

### 4.5 权限与安全（RBAC + ABAC）

#### 4.5.1 设计目标

- 基于角色的访问控制（RBAC）
- 基于属性的访问控制（ABAC）
- 数据范围控制
- 审计追踪

#### 4.5.2 数据模型

```python
# security_models.py

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class Permission(Enum):
    """权限枚举"""
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    EXECUTE = "EXECUTE"
    ADMIN = "ADMIN"

@dataclass
class Role:
    """角色"""
    id: str
    name: str
    description: str
    permissions: List[str]  # ["Contract:CREATE", "Contract:READ", ...]
    data_scope: Optional[str] = None  # "ALL" / "DEPARTMENT" / "SELF"

@dataclass
class User:
    """用户"""
    id: str
    username: str
    display_name: str
    roles: List[str]
    department_id: Optional[str] = None
    
    def has_permission(self, resource: str, action: str, roles_dict: Dict[str, Role]) -> bool:
        """检查是否有权限"""
        required = f"{resource}:{action}"
        for role_id in self.roles:
            role = roles_dict.get(role_id)
            if role and (required in role.permissions or "*:*" in role.permissions):
                return True
        return False

class SecurityGuard:
    """安全守卫"""
    
    def __init__(self, db: sqlite3.Connection):
        self.db = db
        self.roles_cache: Dict[str, Role] = {}
        self._load_roles()
    
    def _load_roles(self):
        """加载角色配置"""
        # 从数据库或配置文件加载
        self.roles_cache = {
            "admin": Role(
                id="admin",
                name="系统管理员",
                description="拥有所有权限",
                permissions=["*:*"],
                data_scope="ALL"
            ),
            "contract_manager": Role(
                id="contract_manager",
                name="合同管理员",
                description="管理合同相关操作",
                permissions=[
                    "Contract:CREATE", "Contract:READ", "Contract:UPDATE", "Contract:DELETE",
                    "Invoice:CREATE", "Invoice:READ", "Invoice:UPDATE",
                    "Payment:EXECUTE"
                ],
                data_scope="DEPARTMENT"
            ),
            "contract_viewer": Role(
                id="contract_viewer",
                name="合同查看员",
                description="只能查看合同",
                permissions=["Contract:READ", "Invoice:READ"],
                data_scope="DEPARTMENT"
            ),
            "finance": Role(
                id="finance",
                name="财务人员",
                description="负责收款确认",
                permissions=["Payment:EXECUTE", "Invoice:READ", "Contract:READ"],
                data_scope="ALL"
            )
        }
    
    def check_permission(self, user: User, resource: str, action: str) -> bool:
        """检查权限"""
        return user.has_permission(resource, action, self.roles_cache)
    
    def check_data_scope(self, user: User, resource: str, resource_data: Dict[str, Any]) -> bool:
        """检查数据范围"""
        # 获取用户的角色
        user_roles = [self.roles_cache.get(r) for r in user.roles]
        
        # 检查是否有全局权限
        for role in user_roles:
            if role and role.data_scope == "ALL":
                return True
        
        # 检查部门权限
        for role in user_roles:
            if role and role.data_scope == "DEPARTMENT":
                if resource_data.get("dept_id") == user.department_id:
                    return True
        
        # 检查个人权限
        for role in user_roles:
            if role and role.data_scope == "SELF":
                if resource_data.get("owner_id") == user.id:
                    return True
        
        return False
    
    def authorize(self, user: User, resource: str, action: str, 
                  resource_data: Optional[Dict[str, Any]] = None) -> bool:
        """完整授权检查"""
        
        # 1. RBAC 检查
        if not self.check_permission(user, resource, action):
            audit.log(
                event_type="PERMISSION_DENIED",
                actor=user.id,
                action=action,
                resource_type=resource,
                status="DENIED",
                error_message="RBAC check failed"
            )
            return False
        
        # 2. ABAC 检查（数据范围）
        if resource_data and not self.check_data_scope(user, resource, resource_data):
            audit.log(
                event_type="PERMISSION_DENIED",
                actor=user.id,
                action=action,
                resource_type=resource,
                resource_id=resource_data.get("id"),
                status="DENIED",
                error_message="ABAC check failed"
            )
            return False
        
        return True
```

---

## 5. 实施路线图

### 5.1 阶段规划

```
Phase 1: 基础工程化（2-3 周）
├── 1.1 轨迹记录系统
│   ├── 数据模型设计
│   ├── 存储实现
│   └── 与业务服务集成
├── 1.2 审计日志增强
│   ├── 不可篡改设计
│   ├── 完整性校验
│   └── 与轨迹系统关联
└── 1.3 基础权限控制
    ├── RBAC 模型
    └── 与 API 集成

Phase 2: 事务与容错（2-3 周）
├── 2.1 Saga 事务补偿
│   ├── 协调器实现
│   ├── 补偿定义
│   └── 与业务操作集成
├── 2.2 熔断降级
│   ├── 熔断器实现
│   ├── 多级降级策略
│   └── 与 AI 服务集成
└── 2.3 分布式追踪
    ├── Trace ID 传递
    └── 与轨迹系统整合

Phase 3: AI 能力升级（3-4 周）
├── 3.1 OAG 实现
│   ├── Ontology Query Language
│   ├── 查询解析器
│   └── 与 LLM 集成
├── 3.2 Action Types
│   ├── 声明式动作定义
│   ├── 执行引擎
│   └── 副作用处理
└── 3.3 Human-in-the-Loop
    ├── 审批流程
    ├── 影响分析
    └── 确认机制

Phase 4: 生产化（2-3 周）
├── 4.1 性能优化
├── 4.2 监控告警
├── 4.3 备份恢复
└── 4.4 文档完善
```

### 5.2 优先级矩阵

| 能力 | 业务价值 | 技术复杂度 | 优先级 |
|-----|---------|----------|--------|
| 轨迹记录 | 高 | 中 | P0 |
| 审计日志 | 高 | 低 | P0 |
| Saga 补偿 | 高 | 高 | P1 |
| 熔断降级 | 中 | 中 | P1 |
| RBAC 权限 | 高 | 中 | P1 |
| OAG | 高 | 高 | P2 |
| Action Types | 高 | 高 | P2 |
| 分布式追踪 | 中 | 中 | P2 |

---

## 6. 技术架构设计

### 6.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         生产级 Onto-Contract 架构                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   用户界面   │    │   AI 对话    │    │   固定页面   │    │   管理后台   │  │
│  │  (React/TS) │    │  (Copilot)   │    │  (Workshop)  │    │  (Admin)    │  │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘  │
│         │                   │                   │                   │        │
│         └───────────────────┴───────────────────┴───────────────────┘        │
│                                 │                                           │
│                         ┌───────▼───────┐                                   │
│                         │   API Gateway  │  ← 限流、认证、路由                │
│                         │  + Rate Limit  │                                   │
│                         └───────┬───────┘                                   │
│                                 │                                           │
│  ┌──────────────────────────────┼──────────────────────────────────────┐   │
│  │                              ▼                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │                    Agent Runtime                             │   │   │
│  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │   │   │
│  │  │  │ Intent  │→ │ Planner │→ │Executor │→ │Reviewer │        │   │   │
│  │  │  │ Parser  │  │ (DAG)   │  │(Saga)   │  │(Human)  │        │   │   │
│  │  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │   │   │
│  │  │       │            │            │            │               │   │   │
│  │  │       ▼            ▼            ▼            ▼               │   │   │
│  │  │  ┌─────────────────────────────────────────────────────────┐│   │   │
│  │  │  │              Trajectory Recorder                        ││   │   │
│  │  │  │         （每一步都记录，可回放、可审计）                   ││   │   │
│  │  │  └─────────────────────────────────────────────────────────┘│   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  │                              │                                      │   │
│  │  ┌───────────────────────────┼──────────────────────────────────┐  │   │
│  │  │                           ▼                                   │  │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │  │   │
│  │  │  │   Circuit   │  │   Audit     │  │   Compensation      │  │  │   │
│  │  │  │   Breaker   │  │   Logger    │  │   Engine            │  │  │   │
│  │  │  │   (熔断)     │  │   (审计)     │  │   (补偿)             │  │  │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────────────┘  │  │   │
│  │  └─────────────────────────────────────────────────────────────┘  │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │              Ontology Registry (数字孪生)                     │   │   │
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │   │   │
│  │  │  │ Objects │ │ Actions │ │  Rules  │ │ Events  │           │   │   │
│  │  │  │ (M1)    │ │ (M2)    │ │ (M3)    │ │ (ME)    │           │   │   │
│  │  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Data Layer                                   │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │   │
│  │  │ SQLite  │ │  Audit  │ │Trajectory│ │  Cache  │ │ Message │      │   │
│  │  │ (业务)   │ │  Log    │ │  Store   │ │ (Redis) │ │ Queue   │      │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 核心模块设计

#### 6.2.1 轨迹记录模块

```python
# trajectory_module.py

class TrajectoryModule:
    """轨迹记录模块"""
    
    def __init__(self, db: sqlite3.Connection):
        self.recorder = TrajectoryRecorder(db)
    
    def record_action(self, action_func):
        """装饰器：自动记录函数执行"""
        def wrapper(*args, **kwargs):
            # 开始轨迹
            traj_id = self.recorder.start_trajectory(
                user_id=get_current_user(),
                agent_id="system",
                plan={"action": action_func.__name__},
                context=get_request_context()
            )
            
            try:
                result = action_func(*args, **kwargs)
                self.recorder.complete_trajectory(traj_id, "SUCCESS", 0)
                return result
            except Exception as e:
                self.recorder.complete_trajectory(traj_id, "FAILED", 0)
                raise
        
        return wrapper
```

#### 6.2.2 审计模块

```python
# audit_module.py

class AuditModule:
    """审计模块"""
    
    def __init__(self, db: sqlite3.Connection):
        self.logger = AuditLogger(db)
    
    def audit_action(self, event_type: str):
        """装饰器：自动记录审计日志"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                
                self.logger.log(
                    event_type=event_type,
                    actor=get_current_user(),
                    action=func.__name__,
                    input_data=kwargs,
                    output_data=result if isinstance(result, dict) else None,
                    status="SUCCESS"
                )
                
                return result
            return wrapper
        return decorator
```

#### 6.2.3 Saga 模块

```python
# saga_module.py

class SagaModule:
    """Saga 事务模块"""
    
    def __init__(self, trajectory_recorder=None):
        self.trajectory = trajectory_recorder
    
    def create_saga(self, saga_id: Optional[str] = None) -> SagaOrchestrator:
        """创建 Saga 协调器"""
        return SagaOrchestrator(trajectory_recorder=self.trajectory)
```

#### 6.2.4 熔断模块

```python
# circuit_breaker_module.py

class CircuitBreakerModule:
    """熔断器模块"""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
    
    def get_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """获取或创建熔断器"""
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(name, config)
        return self.breakers[name]
    
    def get_all_status(self) -> Dict[str, dict]:
        """获取所有熔断器状态"""
        return {name: breaker.get_state() for name, breaker in self.breakers.items()}
```

#### 6.2.5 安全模块

```python
# security_module.py

class SecurityModule:
    """安全模块"""
    
    def __init__(self, db: sqlite3.Connection):
        self.guard = SecurityGuard(db)
    
    def require_permission(self, resource: str, action: str):
        """装饰器：要求权限"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                user = get_current_user()
                
                if not self.guard.authorize(user, resource, action):
                    raise PermissionDeniedException(
                        f"User {user.id} does not have {action} permission on {resource}"
                    )
                
                return func(*args, **kwargs)
            return wrapper
        return decorator
```

---

## 7. 数据模型增强

### 7.1 新增表结构

```sql
-- 1. 执行轨迹表
CREATE TABLE trajectories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trajectory_id TEXT UNIQUE NOT NULL,
    trace_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    agent_id TEXT,
    session_id TEXT,
    plan_json TEXT,
    steps_json TEXT,
    final_status TEXT NOT NULL,
    context_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TEXT,
    total_duration_ms INTEGER
);

CREATE INDEX idx_trajectories_trace_id ON trajectories(trace_id);
CREATE INDEX idx_trajectories_user_id ON trajectories(user_id);
CREATE INDEX idx_trajectories_created_at ON trajectories(created_at);
CREATE INDEX idx_trajectories_final_status ON trajectories(final_status);

-- 2. 轨迹步骤表
CREATE TABLE trajectory_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trajectory_id TEXT NOT NULL,
    step_id TEXT NOT NULL,
    step_order INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    action_name TEXT NOT NULL,
    input_json TEXT,
    output_json TEXT,
    status TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    duration_ms INTEGER,
    metadata_json TEXT,
    compensation_step_id TEXT,
    FOREIGN KEY (trajectory_id) REFERENCES trajectories(trajectory_id)
);

CREATE INDEX idx_trajectory_steps_trajectory_id ON trajectory_steps(trajectory_id);
CREATE INDEX idx_trajectory_steps_step_id ON trajectory_steps(step_id);

-- 3. 审计日志表
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT UNIQUE NOT NULL,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_category TEXT NOT NULL,
    actor TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    action TEXT NOT NULL,
    action_type TEXT NOT NULL,
    input_json TEXT,
    output_json TEXT,
    status TEXT NOT NULL,
    error_message TEXT,
    trace_id TEXT,
    trajectory_id TEXT,
    session_id TEXT,
    ip_address TEXT,
    user_agent TEXT,
    record_hash TEXT NOT NULL,
    prev_hash TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_logs_actor ON audit_logs(actor);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_trace_id ON audit_logs(trace_id);
CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);

-- 4. 角色表
CREATE TABLE roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    permissions_json TEXT NOT NULL,
    data_scope TEXT DEFAULT 'SELF',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 5. 用户角色关联表
CREATE TABLE user_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    granted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    granted_by TEXT,
    UNIQUE(user_id, role_id)
);

-- 6. 熔断器状态表（用于持久化）
CREATE TABLE circuit_breaker_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    breaker_name TEXT UNIQUE NOT NULL,
    state TEXT NOT NULL,
    failure_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    last_failure_time TEXT,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

## 8. API 设计

### 8.1 轨迹管理 API

```yaml
# 轨迹管理 API

GET /api/trajectories
  查询参数:
    - user_id: 用户ID（可选）
    - status: 状态过滤（可选）
    - start_date: 开始日期（可选）
    - end_date: 结束日期（可选）
    - page: 页码
    - page_size: 每页数量
  响应:
    - total: 总数
    - items: 轨迹列表

GET /api/trajectories/{trajectory_id}
  响应:
    - 完整轨迹详情（含所有步骤）

POST /api/trajectories/{trajectory_id}/replay
  请求体:
    - from_step: 从第几步开始回放（可选，默认0）
  响应:
    - 回放结果流

GET /api/trajectories/{trajectory_id}/steps/{step_id}
  响应:
    - 单步详情
```

### 8.2 审计查询 API

```yaml
# 审计查询 API

GET /api/audit/logs
  查询参数:
    - actor: 执行者（可选）
    - event_type: 事件类型（可选）
    - resource_type: 资源类型（可选）
    - start_date: 开始日期（可选）
    - end_date: 结束日期（可选）
    - page: 页码
    - page_size: 每页数量
  响应:
    - total: 总数
    - items: 审计记录列表

GET /api/audit/logs/{record_id}
  响应:
    - 单条审计记录详情

POST /api/audit/verify
  请求体:
    - start_date: 开始日期（可选）
    - end_date: 结束日期（可选）
  响应:
    - valid: 是否通过完整性校验
    - checked_count: 检查记录数
    - invalid_records: 异常记录列表
```

### 8.3 熔断器管理 API

```yaml
# 熔断器管理 API

GET /api/system/circuit-breakers
  响应:
    - breakers: 熔断器状态列表

GET /api/system/circuit-breakers/{name}
  响应:
    - 单个熔断器详情

POST /api/system/circuit-breakers/{name}/reset
  请求体:
    - force: 是否强制重置（可选）
  响应:
    - 重置结果
```

---

## 9. 安全与权限

### 9.1 权限矩阵

| 角色 | 合同管理 | 开票管理 | 收款确认 | 查询统计 | 系统管理 |
|-----|---------|---------|---------|---------|---------|
| 系统管理员 | CRUD | CRUD | 执行 | 全部 | 全部 |
| 合同管理员 | CRUD | CRUD | - | 部门范围 | - |
| 财务人员 | 查看 | 查看 | 执行 | 全部 | - |
| 销售人员 | 创建/查看 | 创建/查看 | - | 个人范围 | - |
| 审计人员 | 查看 | 查看 | 查看 | 全部 | 审计日志 |

### 9.2 数据范围规则

```python
# 数据范围规则
DATA_SCOPE_RULES = {
    "ALL": "可以访问所有数据",
    "DEPARTMENT": "只能访问同部门数据",
    "SELF": "只能访问自己创建的数据",
    "TEAM": "只能访问同团队数据"
}
```

---

## 10. 监控与运维

### 10.1 关键指标

| 指标 | 说明 | 告警阈值 |
|-----|------|---------|
| trajectory_success_rate | 轨迹执行成功率 | < 95% |
| audit_log_integrity | 审计日志完整性 | < 100% |
| circuit_breaker_open_count | 熔断器触发次数 | > 5/小时 |
| saga_compensation_rate | Saga 补偿率 | > 10% |
| api_response_time_p99 | API 响应时间 P99 | > 2s |
| ai_fallback_rate | AI 降级率 | > 20% |

### 10.2 健康检查端点

```yaml
GET /api/health
  响应:
    status: UP / DEGRADED / DOWN
    components:
      database: { status: UP, responseTime: 45ms }
      ai_service: { status: UP, fallbackRate: 0.05 }
      circuit_breakers: { status: UP, openCount: 0 }
      audit_log: { status: UP, integrity: true }
```

---

## 附录

### A. 术语表

| 术语 | 英文 | 说明 |
|-----|------|------|
| 本体 | Ontology | 业务语义模型 |
| 数字孪生 | Digital Twin | 业务的数字化映射 |
| OAG | Ontology Augmented Generation | 本体增强生成 |
| Saga | Saga | 长事务协调模式 |
| 熔断器 | Circuit Breaker | 容错保护机制 |
| RBAC | Role-Based Access Control | 基于角色的访问控制 |
| ABAC | Attribute-Based Access Control | 基于属性的访问控制 |

### B. 参考资料

1. Palantir Foundry Documentation: https://www.palantir.com/docs/foundry/
2. Microservices Patterns (Chris Richardson): Saga Pattern
3. Release It! (Michael Nygard): Circuit Breaker Pattern
4. Domain-Driven Design (Eric Evans): Aggregate Root, Bounded Context

---

**文档结束**
