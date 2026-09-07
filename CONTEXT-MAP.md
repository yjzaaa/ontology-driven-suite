# 限界上下文地图

本项目包含多个限界上下文。每个上下文拥有独立的统一语言、领域规则和持久化责任；跨上下文只能通过稳定 ID、发布模型、命令、查询或事件协议协作。

## 上下文

### Evidence Discovery

**职责**

- 使用 codebase-memory MCP 和定向 Roslyn extractor 分析 DPA。
- 生成带 revision、来源位置和证据等级的不可变 Evidence Snapshot。
- 记录覆盖率、缺口和源码变化影响。

**不负责**

- 不判断最终业务语义。
- 不发布本体。
- 不授予查询或行为执行权。

### Ontology Governance

**职责**

- 管理 M1/M2/M3/M5/M6/M7/MU/MI 候选模型。
- 校验 Schema、引用、证据、兼容性和生命周期。
- 完成人工审核并发布不可变模型包。

**核心领域**

本体治理是平台的核心领域。模型语义、发布条件和变更治理必须集中于本上下文。

### Semantic Query

**职责**

- 解析已发布 M7 Query。
- 执行身份范围、行级范围、字段策略和资源限制。
- 通过 MI 选择受治理 DPA 读取能力或只读 Database MCP。
- 返回稳定对象、集合、关系和指标投影。

**不负责**

- 不接受任意 SQL。
- 不执行业务写入。

### Action Governance

**职责**

- 创建和校验 Action Proposal。
- 计算风险与影响预览。
- 管理 Approval、Execution、幂等和不可变收据。
- 在 Draft Application、Gateway Execution 和 Legacy View 之间作出受治理选择。

**核心领域**

行为治理是平台的核心领域。Proposal、Approval 和 Execution 是不同聚合，不能合并为一个通用任务对象。

### DPA Integration

**职责**

- 作为平台与遗留 DPA 之间的防腐层。
- 解释 MI，完成请求/响应转换、固定参数、错误归一化和凭据转发。
- 隐藏 URL、HTTP Method、Header、Cookie、DTO 和数据库技术细节。

**关系**

本上下文对 DPA 采用 Anticorruption Layer。DPA 模型不得直接渗入平台核心领域。

### Agent Experience

**职责**

- 自主实现 Agent Runtime、Agent UI、Studio、Workbench 和 Explorer。
- 使用已发布语义 Tool、Runtime Projection 和事件协议。
- 将模型、查询、提案和执行状态呈现给用户。

**不负责**

- 不判断权限。
- 不解析 MI。
- 不直接调用 DPA。
- 不保存 Proposal、Approval 或 Execution 的权威状态。

### Identity and Audit

**职责**

- 建立不携带原始凭据的 Identity Context。
- 关联用户、会话、模型、查询、提案和执行。
- 保存脱敏审计事件和不可变收据。

**关系**

身份上下文服从 DPA 最终授权；平台预检不能替代 DPA 业务授权。

## 上下文关系

```text
Evidence Discovery
        │ Evidence Published Language
        ▼
Ontology Governance
        │ Published Model Bundle
        ├───────────────┬────────────────┐
        ▼               ▼                ▼
Semantic Query   Action Governance   Agent Experience
        │               │                │
        └───────┬───────┘                │
                ▼                        │
         DPA Integration ◄───────────────┘
                │
                ▼
               DPA

Identity and Audit 为 Query、Action、Integration 和 Agent Experience
提供身份上下文与审计协议，但不接管各上下文的领域规则。
```

## 共享规则

- `CONTEXT.md` 保存跨上下文统一使用的规范术语。
- 同一个词在不同上下文含义不同时，必须使用上下文前缀或不同名称。
- 跨上下文不共享 ORM Entity、数据库事务或内部异常类型。
- 发布模型包是 Ontology Governance 向运行时上下文提供的 Published Language。
- MI 是 DPA Integration 的内部模型，Agent Experience 只能看到语义引用。
- 每个上下文拥有自己的数据库表和迁移；允许共用 PostgreSQL 实例，不允许跨上下文直接写表。
