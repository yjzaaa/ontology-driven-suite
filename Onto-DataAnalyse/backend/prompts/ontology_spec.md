# 本体建模规范（本项目使用版本）

> 本规范基于 *Ontology-Driven Software Modeling Framework v1.0*（人月聊IT）
> **裁剪后**仅保留 M1 / M2 / M3 / M4 / M_Metric 五个模型，用于电商经营数据智能分析
> **不生成**：ME 事件模型、M5 主体模型、M6 异常补偿模型、M7 质量约束模型

---

## 总体设计哲学

把业务世界中的 **存在（What）**、**行为（How）**、**规则（Why）**、**场景（When/Flow）** 与
**度量（Measurement）** 分离建模：

| 编号 | 模型 | 核心职责 |
|------|------|---------|
| M1 | 对象模型 | 数据实体、属性、实体间双向关联、参照完整性约束 |
| M2 | 行为模型（**分析行为**） | 数据分析行为定义，含分析意图、依赖数据、推理类型 |
| M3 | 规则模型 | 业务规则与口径规则、数据质量规则 |
| M4 | 场景模型（**分析场景**） | 端到端分析用例编排，包含步骤序列 |
| M_Metric | 指标模型（扩展） | 数据分析指标的语义定义与计算配置 |

---

## M1 对象模型 (m1_object_model.yaml)

### 实体（Entity）

```yaml
entities:
  - id: ENT-ORD-001                          # 实体唯一 ID
    name: 订单                                # 业务中文名
    alias: Order                              # 英文标识，用于代码映射
    domain: 交易域                            # 业务域
    description: 用户在平台的一次购买记录...   # 业务含义
    lifecycle: [待付款, 已付款, 已发货, 已签收, 已取消, 退款完成]
    attributes:
      - name: orderId                        # 英文 camelCase
        label: 订单号                         # 中文展示
        type: String                          # String/Integer/Decimal/Date/DateTime/Boolean/Enum/Reference
        required: true
        unique: true
      - name: status
        label: 订单状态
        type: Enum
        enumValues: [1, 2, 3, 4, 5, 6]
      - name: payAmount
        label: 实付金额
        type: Decimal
        required: true
      - name: buyerId                        # Reference 类型字段会被图谱算法识别为关联边
        label: 买家ID
        type: Reference
        refEntity: ENT-USR-001               # 指向用户实体
        refCardinality: MANY_TO_ONE
    constraints:
      - constraintType: CHECK
        scope: ENTITY
        expression: "payAmount >= 0"
        violationMessage: 实付金额不能为负
    tags: [核心域]
```

### 关联关系（Relation）

**重要**：所有实体间的语义关系都必须在 relations 列表中显式定义。
不要只依赖 Reference 类型属性 — 双向都要可以读出。

```yaml
relations:
  - id: REL-001
    type: COMPOSITION                        # COMPOSITION/AGGREGATION/ASSOCIATION/DEPENDENCY
    sourceEntity: ENT-ORD-001                # 订单
    targetEntity: ENT-ORD-002                # 订单明细
    sourceRole: 所属订单
    targetRole: 订单明细
    sourceCardinality: ONE
    targetCardinality: ONE_OR_MORE           # ONE/ZERO_OR_ONE/MANY/ONE_OR_MORE
    cascadeDelete: true
    description: 订单包含一个或多个订单明细
```

**关系类型选择指南**：
- COMPOSITION（组合）：子对象生命周期完全依赖父对象（订单-订单明细 / 会话-页面访问）
- AGGREGATION（聚合）：弱拥有关系，子对象可独立存在（用户-用户行为）
- ASSOCIATION（关联）：业务上相关联（用户-订单、商品-类目）
- DEPENDENCY（依赖）：弱依赖、单向引用

---

## M2 行为模型 — 分析行为版 (m2_behavior_model.yaml)

> ⚠️ 本项目 M2 建模的是**数据分析行为**（如"生成经营概览"、"异常检测"），
> 不是电商业务行为（不要建模"下单"、"支付"这类操作）。

```yaml
behaviors:
  - id: BHV-ANA-001
    name: 生成经营概览
    description: 输出指定时间窗口内的核心指标摘要，含同环比
    ownerEntity: ENT-ORD-001                 # 主要操作的实体
    behaviorType: ANALYSIS                   # ANALYSIS/QUERY（本项目只用这两种）
    triggerType: USER_ACTION                 # USER_ACTION/SYSTEM
    computationType: SQL_COMPUTE             # SQL_COMPUTE/STAT_ALGO/LLM_REASONING
    inputParams:
      - name: timeRange
        type: DateRange
        required: true
      - name: comparisonPeriod
        type: Enum
        enumValues: [MoM, YoY, None]
    outputType: MetricsSummary
    relatedMetrics:                          # 涉及的指标 ID 列表
      - MTR-TXN-001
      - MTR-TXN-002
      - MTR-USR-004
    appliedRules:                            # 引用的规则
      - RULE-MTR-001
    description_detail: 用户触发时执行...
```

> 注意：M2 不再保留 `producedEvents` 字段（本项目不使用事件模型）。

---

## M3 规则模型 (m3_rule_model.yaml)

```yaml
rules:
  - id: RULE-MTR-001
    name: GMV口径定义
    ruleType: VALIDATION                     # VALIDATION/CALCULATION/DERIVATION/TRANSFORMATION
    description: 有效订单 = status NOT IN (5 已取消, 6 退款完成)；退款金额从 GMV 扣减
    expression: |
      effective_orders = orders WHERE status NOT IN (5, 6)
      gmv = SUM(effective_orders.payment_amount) - SUM(refunds.refund_amount)
    inputParams:
      - name: orders
        type: List<Order>
        sourceField: t_order
      - name: refunds
        type: List<Refund>
        sourceField: t_refund
    outputType: Decimal
    version: "1.0"
    reusedBy:
      - BHV-ANA-001
      - BHV-ANA-002

  - id: RULE-DQ-001
    name: 测试订单排除
    ruleType: VALIDATION
    description: 排除测试账号订单和金额 ≤ 0.01 元的订单
    expression: "buyer_id NOT IN test_accounts AND payment_amount > 0.01"
    version: "1.0"
```

**规则分类**：
- VALIDATION：判断对错（如"是否有效订单"）
- CALCULATION：计算值（如"GMV 计算公式"）
- DERIVATION：从已知推导（如"用户等级 = 年度 GMV 区间映射"）
- TRANSFORMATION：数据转换（如"枚举值映射"）

---

## M4 场景模型 — 分析场景版 (m4_scenario_model.yaml)

> ⚠️ 本项目 M4 建模的是**数据分析场景**（如"经营异常分析"），
> 不是电商业务流程。

```yaml
scenarios:
  - id: SCN-ANOMALY-001
    name: 经营异常分析
    description: 识别近期经营指标的异常波动并归因
    intent: 用户希望快速发现"哪里有问题"
    actors: [运营人员, 数据分析师]
    relatedBehaviors:
      - BHV-ANA-001                          # 生成经营概览
      - BHV-ANA-007                          # 异常检测
      - BHV-ANA-008                          # 归因分析
    keyMetrics:
      - MTR-TXN-001                          # GMV
      - MTR-TXN-005                          # 订单取消率
      - MTR-TXN-006                          # 退款率
      - MTR-USR-004                          # 复购率
    primaryFlow:
      - stepId: S01
        type: DATA_COLLECT                   # DATA_COLLECT/STAT_COMPUTE/AI_REASONING/REPORT_ASSEMBLE
        description: 采集核心指标月度数据
      - stepId: S02
        type: STAT_COMPUTE
        description: 计算同环比与异常检测（3σ）
      - stepId: S03
        type: AI_REASONING
        description: AI 推理异常根因
      - stepId: S04
        type: REPORT_ASSEMBLE
        description: 组装可视化报告
    preconditions:
      - 时间范围已指定
      - 本体模型与数据库映射已就绪
    outputs:
      - 异常指标列表（带严重程度）
      - 趋势可视化图表
      - AI 推理结论与置信度
      - 行动建议（带优先级）
```

---

## M_Metric 指标模型 (m_metric_model.yaml)

```yaml
model_type: METRIC
version: "1.0"
domain: "电商经营分析"

metrics:
  - id: MTR-TXN-001                          # MTR-{Domain}-{Seq}
                                              # Domain: TXN交易 / TFC流量 / USR用户 / PRD商品 / MKT营销 / SCM供链
    name: GMV
    alias: gmv                                # camelCase
    description: 成交总额（含退款扣减后的实际收入）
    formula_description: "SUM(t_order.payment_amount) WHERE status NOT IN (5,6) MINUS SUM(t_refund.refund_amount)"
    computation_type: SQL_COMPUTE             # SQL_COMPUTE / STAT_ALGO / LLM_REASONING
    depends_on_entities:                      # 依赖的 M1 实体
      - ENT-ORD-001
      - ENT-ORD-004                           # 退款
    rule_refs:                                # 依赖的 M3 规则
      - RULE-MTR-001
    sql_template: |                           # SQL 模板（仅 computation_type=SQL_COMPUTE 时必填）
      SELECT strftime('{date_format}', gmt_create) AS period,
             SUM(payment_amount) - COALESCE(SUM(refund_amount), 0) AS gmv
      FROM t_order
      WHERE status NOT IN (5, 6)
        AND gmt_create BETWEEN '{date_start}' AND '{date_end}'
      GROUP BY period ORDER BY period
    stat_algorithm: null                      # 仅 computation_type=STAT_ALGO 时填
                                              # 可选：mom_yoy/anomaly_3sigma/rfm_score/abc_classification
    supported_grains: [DAY, WEEK, MONTH, QUARTER, YEAR]
    supported_dimensions: [shop, category, channel, region]
    default_visualization: line               # line/bar/pie/scatter/heatmap/funnel/gauge
    unit: "元"
    tags: [core, growth]
```

**Domain 代码**：
- TXN 交易规模（GMV、订单数、客单价、取消率、退款率...）
- TFC 流量转化（UV、PV、访问转化、加购转化...）
- USR 用户质量（新用户、活跃、复购、留存、流失、RFM...）
- PRD 商品运营（销售额、销量、好评率、库存周转...）
- MKT 营销效果（活动 GMV 贡献、券使用率、ROI...）
- SCM 供应链履约（发货及时率、配送时长、售后率...）

---

## 模型间依赖关系

```
M4 场景 ──→ M2 行为 + M_Metric 指标
M2 行为 ──→ M1 实体 + M3 规则 + M_Metric 指标
M3 规则 ──→ M1 实体（只读）
M_Metric ──→ M1 实体 + M3 规则
M1 关系 ──→ M1 实体（双向）
```

**生成顺序**（无循环依赖）：
1. M1 对象模型（含 entities 和 relations，关系必须完整）
2. M3 规则模型
3. M_Metric 指标模型
4. M2 行为模型
5. M4 场景模型

---

## YAML 输出质量要求

1. **每个文件以 `model_type` 字段开头**，明确模型类型
2. **ID 命名规范**：
   - 实体：`ENT-{域}-{序号}`（如 `ENT-ORD-001`）
   - 行为：`BHV-ANA-{序号}`
   - 规则：`RULE-{类别}-{序号}`
   - 场景：`SCN-{主题}-{序号}`
   - 指标：`MTR-{域}-{序号}`
   - 关系：`REL-{序号}`
3. **不要使用 Markdown 代码块包裹**（不要 ` ```yaml ` ）
4. **中文文本无需引号**，但含冒号 `:` 的描述需要加单引号
5. **必填字段不能缺失**，可选字段可以省略
6. **不要编造**：所有内容必须有需求文档或数据库 Schema 文档的依据
