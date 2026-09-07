# 运行时概念及其所有权（T01.5 产出）

> 本文件是 Wayfinder 工作包 [01-define-domain-language-and-model-boundaries](../wayfinder/tickets/01-define-domain-language-and-model-boundaries.md) 的 T01.5 产出。
> 任务：统一 Runtime Projection、Legacy View、Action Proposal、Draft Application、Execution 等运行时概念，明确它们与已发布 YAML 的关系、创建者、事实来源、可变性、生命周期和消费方。
> 依赖：T01.2 `model-boundary-matrix.md`、T01.4 `behavior-rule-execution-boundaries.md`。

## 1. 运行时概念清单

| 概念 | 创建者 | 事实来源 | 可变性 | 生命周期 | 消费方 |
|---|---|---|---|---|---|
| Runtime Projection | 平台（由已发布本体生成） | `models/<domain>/` 已发布 YAML | 只读（随模型版本重建） | 模型发布周期 | Agent UI、Workbench、Explorer、Query/Behavior 卡片 |
| Legacy View | DPA 原页面（平台提供受控入口） | DPA 页面/服务 | DPA 自有 | DPA 页面生命周期 | 复杂编辑、工作流、页面专有行为 |
| Action Proposal | 平台（Agent/用户发起） | 已发布 YAML + 已验证参数 + IdentityContext | 不可变 | 审批生命周期（待审→批准/驳回/过期） | Policy、Approval、Execution、审计 |
| Draft Application | 平台（将建议值应用到原表单） | Proposal 的建议值 | 会话内可变 | 会话/表单生命周期，不持久化 | 用户、原 DPA 表单 |
| Execution | 平台（HITL 批准后） | Proposal + MI + DPA 响应 | 不可变收据 | 执行生命周期（幂等、重试、收据） | 审计、用户、Workbench |
| 运行时语义 Tool | 平台（由已发布 YAML 投影） | 已发布 YAML | 只读 | 模型发布周期 | Agent Runtime |
| 事件（领域事件/运行时事件） | 平台/DPA（记录已发生事实） | 各上下文 | 不可变 | 事件流 | Agent UI、审计、联动 |

## 2. 事实来源与唯一所有权

- **已发布 YAML 是运行时语义唯一事实源**（`models/<domain>/`）。所有 Runtime Projection、语义 Tool、对象视图、查询结果、行为卡片、流程状态和关系图都必须是该事实源的**只读投影**，不成为第二事实源（TERM-006）。
- **Execution 是唯一被批准改变 DPA 业务状态的路径**，由 HITL 状态机保证（`CONTEXT-MAP.md` Action Governance）。
- **每个运行时概念有唯一所有者和事实来源**：
  - 语义类（Projection、语义 Tool）→ 唯一来源 = 已发布 YAML；
  - 用户会话类（Draft Application、会话内批量编辑 ID）→ 来源 = 用户会话，不持久化；
  - 决策类（Proposal、Execution）→ 来源 = 平台状态机 + 审计收据；
  - 遗留入口（Legacy View）→ 来源 = DPA 原页面。

## 3. 约束

- **Runtime Projection 不得成为第二事实源**：Agent UI、Workbench、Explorer 显示的内容若与已发布 YAML 冲突，以 YAML 为准；投影仅用于呈现（`CONTEXT.md` Runtime Projection）。
- **Legacy View 不得成为平台业务事实源**：复杂编辑回到原 DPA 页面，平台只提供受控同源导航入口，不复制复杂表单（边界 9）。
- **Draft Application 不持久化**：只把已验证建议值应用到原表单，用户仍需执行原 DPA 保存动作；其数据事实仍归 DPA。
- **凭据/技术细节不属于运行时概念**：Cookie、Token、URL、HTTP Method、Header 只在 MI 技术侧存在，不进入模型上下文（边界 10）。

## 4. 概念链路（M2/MU/MI → 提案 → 草稿 → DPA 保存）

```text
已发布 YAML (M1/M2/M3/M5/M6/M7/MU/MI)
      │ 投影
      ▼
Runtime Projection / 语义 Tool（只读）
      │ 用户选择行为 + 参数
      ▼
Action Proposal（不可变，绑定风险/版本/MI）
      │ HITL 审批
      ├─ 批准 → Execution（经 MI → DPA HTTP，写 + 审计收据）
      └─ 或 → Draft Application（建议值应用到原 DPA 表单，不持久化）
                     │ 用户使用原 DPA 保存动作
                     ▼
              DPA 实际持久化（最终执行系统）
```

- Legacy View 是链路的**分叉入口**：当编辑超出平台能力（复杂表单/工作流），直接跳原 DPA 页面，不再走提案/草稿。

## 5. MasterData 落地示例

- `UpdateSubtableData`（写 + 缓存副作用，MIXED/HIGH）：
  - M2 表达“更新子表数据”；M3 判断允许条件；M5 约束权限；MU 呈现表单。
  - 用户发起 → 生成 Action Proposal → 审批通过 → Execution 经 MI 调用 DPA `UpdateSubtableData` → DPA 持久化 + 缓存清理 → 审计收据。
  - 或：审批/编辑路径中先生成 Draft Application，建议值回填原表单，由用户在 DPA 页面确认保存。
- `GetSubtableDatalist`（纯查询候选）：M7 Query 定义语义 → 平台生成查询投影 → MU 显示结果；不产生提案/执行。

## 6. 验证记录

- 每个运行时概念均有唯一所有者和事实来源（见第 1、2 节）。
- 文档明确 `models/<domain>/` 已发布 YAML 是运行时语义唯一事实源。
- 任一运行时对象可追溯到模型版本、用户会话或 DPA 原入口之一；不存在来源不明的持久语义。
- 命令：`git diff --check` 应通过。
