# 渐进式 DDD 采用规则

## 目的

本项目不要求所有代码从第一天采用完整 DDD。DDD 的使用深度由本体模型揭示的业务语义、生命周期和一致性复杂度决定。

本体模型提供业务知识和候选边界，代码模型通过场景、测试和实现反馈逐步深化。不得根据 YAML 类型一对一生成 Entity、Aggregate、Repository 或 Domain Service。

## 基本原则

- 先建立统一语言和明确 Module，再考虑战术模式。
- 先用最简单的实现证明业务闭环，再根据真实变化压力深化模型。
- DDD 深度可以升级，但不得为了短期方便绕过已经建立的不变量。
- 领域复杂度低的 Module 保持简单；技术 Adapter 不需要伪装成领域模型。
- 每次升级必须解决一个可描述的问题，例如规则分散、状态非法、并发冲突或遗留模型泄漏。

## 五级采用模型

### L0：技术实现

**适用条件**

- 纯协议转换、文件处理、MCP 查询、UI Renderer 或基础设施 Adapter。
- 没有业务身份、生命周期、不变量或业务决策。

**代码风格**

- 使用普通函数、dataclass、Pydantic 边界模型或小型 Module。
- 不创建 Aggregate、Repository、Domain Event。

**典型模块**

- codebase-memory Evidence Adapter。
- JSON Schema 校验器。
- Cytoscape 图投影转换。

### L1：统一语言与类型

**适用条件**

- 已出现稳定业务术语和 ID。
- 错误主要来自字符串混用、单位混用、非法枚举或边界值。

**代码风格**

- 使用明确命名、Enum、不可变 Value Object 和 typed ID。
- 在构造时验证局部不变量。
- 仍可由 Application Module 直接协调持久化。

**本体信号**

- M1 中出现稳定标识、状态、金额、时间范围或分类。
- M3 中只有局部字段约束，没有跨对象一致性。

### L2：显式领域规则

**适用条件**

- 规则在 Controller、Handler、UI 或 SQL 中重复。
- 行为是否允许取决于对象状态、用户范围或多个条件。
- 规则需要由业务人员命名和单独测试。

**代码风格**

- 将规则放入 Entity、Value Object、Specification、Policy 或纯领域函数。
- Command 使用业务语言表达意图。
- Query 继续使用独立投影，不强制经过 Aggregate。

**本体信号**

- M2 Behavior 与 M3 Rule 形成稳定关联。
- M5 Actor/Permission 会改变行为可用性。

### L3：Aggregate 与生命周期

**适用条件**

- 多个字段或子对象必须在同一事务中保持不变量。
- 存在明确状态机、并发修改、幂等、版本冲突或一次性消费。
- 外部调用者不应直接修改内部成员。

**代码风格**

- 建立 Aggregate Root，并通过业务方法执行状态转换。
- Repository 只持久化 Aggregate Root。
- 使用 Factory 保证复杂有效构造。
- Domain Event 表达 Aggregate 内已经发生的业务事实。

**本体信号**

- M1 具有稳定生命周期。
- M2 改变状态或成员集合。
- M3 定义跨字段或跨成员不变量。
- M6 描述同一一致性范围内的状态转换。

**本项目优先候选**

- Action Proposal。
- Approval。
- Execution。
- Published Ontology Version。

这些概念是否分别成为 Aggregate，必须通过事务和并发场景验证，不能仅凭名称决定。

### L4：限界上下文与跨上下文协作

**适用条件**

- 同一术语在不同模块具有不同含义。
- 不同生命周期、团队责任、数据所有权或安全区需要独立演进。
- 跨模块强一致成本过高，需要明确最终一致性。

**代码风格**

- 使用 `CONTEXT-MAP.md` 中的限界上下文。
- 通过 Published Language、命令、查询或事件协作。
- 遗留 DPA 使用 Anticorruption Layer。
- 跨上下文不共享 ORM Entity、内部异常和数据库事务。

**本体信号**

- 同一 M1 对象在治理态、运行态和 DPA 执行态具有不同生命周期。
- M6 Flow 跨越多个所有者。
- MI 显示平台语义与 DPA 技术模型存在明显翻译。

## 本体到代码的映射指导

| 本体模型 | 可能的代码表达 | 不应自动生成 |
|---|---|---|
| M1 Object | Entity、Value Object、读模型或普通 DTO | 默认 Aggregate、默认数据库表 |
| M2 Behavior | Aggregate 方法、Command、Application 用例 | 一接口一方法、一行为一微服务 |
| M3 Rule | Specification、Policy、Value Object 校验、领域函数 | 可执行 HTTP 调用 |
| M5 Actor/Permission | Policy 输入、Identity Context、授权规则 | 前端角色判断作为最终授权 |
| M6 Flow | Application 编排、Process Manager、状态机 | 默认分布式 Saga |
| M7 Query | Query Handler、只读投影、Specification | 强制通过 Aggregate 加载 |
| MU Presentation | Renderer 元数据、视图模型 | 领域对象或业务规则 |
| MI Integration | Anticorruption Layer Adapter | Agent 可见领域类型 |

## 复杂度判定

每个新 Module 或行为从 L0/L1 开始。出现以下信号时考虑升级：

| 信号 | 建议升级 |
|---|---|
| 稳定 ID、单位、枚举反复混用 | L0 → L1 |
| 同一规则在两个以上调用点重复 | L1 → L2 |
| 行为存在多个允许/禁止条件 | L1 → L2 |
| 非法状态可以被直接构造 | L2 → L3 |
| 多字段必须原子变化 | L2 → L3 |
| 并发修改或一次性消费 | L2 → L3 |
| 同一词在模块间含义不同 | L3 → L4 |
| 遗留 DTO 或表结构污染核心语言 | 任意级别 → ACL |

以下情况不升级：

- 只是文件数量增加。
- 只是希望目录看起来“标准”。
- 只有一个 Adapter，且不存在替换需求。
- 只有简单 CRUD，没有业务不变量。
- 只是为了复用一个通用 Base 类。

## 演进流程

1. 从本体和真实场景识别业务语言。
2. 使用当前最低足够级别实现。
3. 添加使用统一语言描述的测试。
4. 观察规则重复、非法状态、并发和跨上下文翻译压力。
5. 记录升级原因和要保护的不变量。
6. 在保持行为不变的前提下提升一级。
7. 只有模型改变时才同步调整本体或创建 ADR。

## 评审门禁

引入 Aggregate、Repository、Domain Service、Process Manager 或 Domain Event 时，代码评审必须回答：

- 它保护了什么具体业务不变量。
- 为什么更低一级的实现不够。
- Aggregate 的一致性范围是什么。
- 哪些操作允许并发，哪些必须串行。
- Repository 为什么需要存在，它持久化哪个 Root。
- 该模式是否来自本体和业务场景，而不是框架模板。
- 对应测试如何证明合法和非法行为。
