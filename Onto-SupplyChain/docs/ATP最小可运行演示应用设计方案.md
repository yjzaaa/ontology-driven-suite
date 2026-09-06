# ATP最小可运行演示应用设计方案

## 1. 目标边界

本阶段只聚焦 **ATP 交期承诺演示**，不做完整 APS 自动重排。

演示应用目标：

- 基于现有供应链本体模型知识图谱，构建一个可交互的 ATP 智能承诺演示系统
- 左侧保留本体知识图谱展示、节点高亮、搜索、业务域过滤
- 取消右侧实体详情面板，改为 AI 对话与场景推演面板
- 后端使用 SQLite + Python Flask
- 前端使用 React + TypeScript
- 大模型按真实接入方式设计，首版直接预留 DeepSeek API 调用能力
- 所有演示数据由本地 SQLite 提供，配套单独造数脚本
- 能完整跑通从“场景输入”到“ATP承诺结果输出”的最小闭环

非目标：

- 不做多工厂全局优化
- 不做复杂 MILP/CP-SAT 求解器集成
- 不做真正生产级 SAP/MES 对接
- 不做向量数据库首版集成

---

## 2. 最小闭环

### 2.1 用户演示流程

1. 用户打开演示首页
2. 左侧展示供应链本体模型图谱
3. 右侧显示 AI 对话区和预设场景
4. 用户点击某个预设场景，例如“客户加急插单”
5. 前端向后端发送场景请求
6. 后端加载相关订单、库存、BOM、供应商、工作中心、工单、工艺路线数据
7. ATP 服务完成最小规则推理与时间计算
8. DeepSeek 基于结构化上下文输出自然语言说明和建议
9. 前端展示：
   - 承诺日期
   - 置信度
   - 风险等级
   - 原因链
   - 影响对象
   - 备选方案
10. 用户可继续追问，例如“如果允许加班呢”“如果启用替代料呢”

### 2.2 演示价值

演示应用要体现的不是“聊天”，而是以下闭环：

- 本体模型承载业务语义
- SQLite 承载结构化业务测试数据
- Python 服务完成最小 ATP 计算
- 大模型负责意图理解、解释生成、多方案表达
- React 页面同时展示图谱、场景、推理结果

---

## 3. 首版预设场景

首版固定 4 个场景，每个场景都要能从数据库中拿到完整测试数据。

### 场景 A：客户加急插单

问题示例：

- “VIP客户华东终端临时插单 300 台，最早什么时候能交？”

系统重点检查：

- 成品库存是否可直接承诺
- 是否需要新增生产工单
- 瓶颈工作中心是否有可插入窗口
- 是否影响既有订单承诺

### 场景 B：客户需求数量上调

问题示例：

- “订单 SO1002 数量从 200 提高到 350，交期还能维持不变吗？”

系统重点检查：

- 库存追加消耗
- BOM 子项缺口
- 原工单产能和工序时间是否可覆盖
- 承诺日期是否延后

### 场景 C：关键物料缺料/在途延迟

问题示例：

- “核心芯片来料延迟 3 天，这张订单还能按原承诺交付吗？”

系统重点检查：

- `available_qty` 是否不足
- 在途预计到货时间是否晚于需求窗口
- 是否存在替代料
- 供应风险是否需要增加缓冲天数

### 场景 D：瓶颈工作中心产能不足

问题示例：

- “SMT-01 本周产能爆满，这张单还能承诺 4 月 12 日吗？”

系统重点检查：

- 工作中心日历与负荷
- 当前在制工单占用
- 替代路线是否可用
- 是否需要给出加班/优先级调整方案

---

## 4. 总体技术架构

### 4.1 技术栈

- 数据库：SQLite
- 后端：Python 3 + Flask
- 前端：React + TypeScript + Vite
- 图谱：沿用 D3 力导向图思路，迁移为 React 页面组件
- 大模型：DeepSeek API
- 接口通信：REST，聊天回答支持流式扩展

### 4.2 模块划分

后端建议拆成 6 个模块：

1. `db`
   - SQLite 连接
   - Schema 初始化
   - 查询封装
2. `seed`
   - 造数脚本
   - 场景初始化脚本
3. `ontology`
   - 本体节点定义
   - 节点关系定义
   - 本体到数据库的映射说明
4. `services/atp`
   - ATP 核心计算
   - 库存、BOM、供应、产能、工艺路线分析
5. `services/llm`
   - DeepSeek 客户端
   - Prompt 构建
   - 输出结构化校验
6. `api`
   - 场景接口
   - 图谱接口
   - 聊天接口
   - ATP 分析接口

前端建议拆成 5 个模块：

1. `graph`
   - 本体图谱画布
2. `chat`
   - AI 对话面板
   - 消息气泡
   - 预设场景卡
3. `result`
   - ATP 结果卡片
   - 原因链卡片
   - 风险与方案卡片
4. `state`
   - 当前选中节点
   - 当前演示场景
   - 当前对话上下文
5. `api`
   - 后端接口封装

---

## 5. 本体模型到 SQLite 的映射

首版不追求把所有本体属性完全落表，但必须覆盖 ATP 推理最小闭环。

### 5.1 核心表清单

#### 需求域

`customers`

- `customer_id`
- `customer_name`
- `priority_level`
- `penalty_threshold_days`
- `penalty_rate`
- `delivery_reliability`
- `complaint_sensitivity`

`finished_items`

- `item_id`
- `item_name`
- `item_category`
- `safety_stock`
- `min_order_quantity`
- `lot_size_rule`
- `abc_classification`

`customer_orders`

- `order_id`
- `customer_id`
- `item_id`
- `quantity`
- `requested_date`
- `committed_date`
- `order_priority`
- `order_type`
- `status`
- `created_at`

#### 生产域

`work_centers`

- `wc_id`
- `wc_name`
- `wc_type`
- `plant_id`
- `standard_capacity_per_day`
- `efficiency_factor`
- `overtime_capacity_per_day`
- `bottleneck_flag`
- `utilization_target`

`work_center_calendar`

- `calendar_id`
- `wc_id`
- `work_date`
- `available_hours`
- `maintenance_hours`
- `overtime_hours`

`production_orders`

- `wo_id`
- `order_id`
- `item_id`
- `planned_quantity`
- `confirmed_quantity`
- `planned_start`
- `planned_end`
- `actual_start`
- `actual_end`
- `forecast_end`
- `priority`
- `status`
- `delay_risk_score`

`operations`

- `op_id`
- `wo_id`
- `op_sequence`
- `op_name`
- `wc_id`
- `setup_time_hours`
- `process_time_per_unit_hours`
- `queue_time_hours`
- `move_time_hours`
- `completion_percentage`
- `parallel_flag`
- `quality_hold_flag`

`operation_dependencies`

- `id`
- `op_id`
- `predecessor_op_id`
- `overlap_percentage`

#### 供应域

`inventory`

- `inventory_id`
- `item_id`
- `plant_id`
- `storage_location`
- `on_hand_qty`
- `in_transit_qty`
- `reserved_qty`
- `available_qty`
- `reorder_point`
- `last_updated`
- `data_source`

`inventory_inbound`

- `inbound_id`
- `item_id`
- `source_type`
- `source_id`
- `expected_arrival_date`
- `quantity`
- `status`

`bom_headers`

- `bom_id`
- `bom_version`
- `parent_item_id`
- `effective_from`
- `effective_to`

`bom_items`

- `bom_item_id`
- `bom_id`
- `child_item_id`
- `level`
- `quantity_per`
- `scrap_factor`
- `phantom_flag`
- `purchase_or_make`

`bom_alternatives`

- `alt_id`
- `bom_item_id`
- `alt_item_id`
- `usage_priority`
- `substitution_ratio`
- `approval_status`

`suppliers`

- `supplier_id`
- `supplier_name`
- `supplier_tier`
- `standard_lt_days`
- `rush_lt_days`
- `lt_variability`
- `moq`
- `capacity_limit`
- `on_time_rate`
- `quality_pass_rate`
- `average_delay_days`
- `geo_risk_level`
- `single_source_flag`

`item_suppliers`

- `id`
- `item_id`
- `supplier_id`
- `is_primary`

#### 计划域

`routings`

- `routing_id`
- `item_id`
- `routing_version`
- `routing_type`
- `total_lead_time_days`
- `bottleneck_wc_id`
- `min_batch_size`
- `max_batch_size`

`routing_operations`

- `routing_op_id`
- `routing_id`
- `op_sequence`
- `wc_id`
- `standard_setup_hours`
- `standard_process_hours`

`routing_alternatives`

- `id`
- `routing_id`
- `alternative_routing_id`
- `applicability_condition`

`atp_commitments`

- `commitment_id`
- `order_id`
- `commitment_version`
- `committed_date`
- `commitment_type`
- `confidence_score`
- `risk_level`
- `reason_chain_json`
- `cost_impact`
- `created_by`
- `created_at`
- `actual_delivery_date`
- `deviation_days`

#### 演示场景

`demo_scenarios`

- `scenario_id`
- `scenario_code`
- `scenario_name`
- `scenario_type`
- `user_prompt`
- `target_order_id`
- `payload_json`
- `is_default`

---

## 6. ATP 最小计算链路

首版 ATP 不引入复杂优化器，而采用“规则计算 + 时间推演 + 风险修正”。

### 6.1 计算步骤

#### Step 1：识别场景对象

从用户输入或预设场景中提取：

- 订单号
- 客户
- 成品物料
- 变更数量
- 目标交期
- 事件类型

#### Step 2：判断库存承诺可能性

优先用于 MTS 场景：

- 查询成品 `available_qty`
- 若可覆盖数量，则直接给出库存承诺日期
- 若不足，则进入生产补足计算

#### Step 3：展开 BOM 缺口

对于需要生产的部分：

- 计算净需求量
- 展开 BOM
- 按 `quantity_per * scrap_factor * 需求数量` 计算子项需求
- 对每个子项检查 `available_qty`
- 若不足，检查：
  - 在途到货日期
  - 替代料
  - 供应商提前期

#### Step 4：估算最早可开工时间

最早可开工时间取以下最大值：

- 物料齐套时间
- 当前工单释放时间
- 前序工单完工时间

#### Step 5：估算最早完工时间

基于 Routing 和 Work Center 日历计算：

- 每道工序时间 = `setup + process * qty + queue + move`
- 考虑工作中心当日剩余能力
- 识别瓶颈工作中心
- 估算最早完工日期

#### Step 6：生成候选承诺方案

首版固定输出最多 3 个方案：

1. 标准方案 `Standard`
2. 加班方案 `Overtime`
3. 替代料/替代路线方案 `Alternative`

#### Step 7：风险与置信度修正

置信度首版可以先用规则评分：

- 基础分 85
- 库存充足 +5
- 单一供应商 -10
- 供应商准时率低于 85% -8
- 瓶颈工作中心利用率高于目标值 -8
- 存在质量暂停工序 -15
- 使用替代路线 -5
- 使用加班方案 -3

风险等级建议：

- `>= 90`：Low
- `75-89`：Medium
- `< 75`：High

#### Step 8：调用大模型生成业务化说明

DeepSeek 不直接算时间，而是输入结构化 ATP 摘要，输出：

- 推荐方案说明
- 原因链
- 风险解释
- 业务建议

---

## 7. DeepSeek 接入设计

### 7.1 设计原则

- 必须按真实大模型调用链路设计
- 数值计算留在 Python 服务
- LLM 负责语义理解和解释输出
- 保留模型切换能力，不把厂商写死在业务代码里

### 7.2 服务抽象

建议定义统一接口：

`LLMClient`

- `parse_user_intent(message, scenarios, ontology_context)`
- `generate_atp_explanation(atp_summary, scenario_context, graph_context)`
- `chat_followup(messages, atp_summary, graph_context)`

再实现：

`DeepSeekClient(LLMClient)`

配置项：

- `base_url`
- `api_key`
- `model`
- `timeout`
- `temperature`

### 7.3 Prompt 输入上下文

建议给 DeepSeek 的结构化上下文包含：

- 当前场景名称
- 当前订单摘要
- 客户等级与合同风险
- 成品物料属性
- 库存摘要
- BOM 缺口摘要
- 供应商风险摘要
- 工作中心产能摘要
- 候选 ATP 方案
- 推荐方案

### 7.4 输出格式

要求模型输出 JSON，至少包括：

- `recommended_commitment_type`
- `recommended_date`
- `confidence_score`
- `risk_level`
- `reason_chain`
- `impact_objects`
- `alternatives`
- `user_facing_reply`

后端必须做 JSON 校验和兜底。

---

## 8. Flask API 设计

### 8.1 图谱接口

`GET /api/ontology/graph`

返回：

- 节点列表
- 关系列表
- 节点所属域

### 8.2 场景列表接口

`GET /api/scenarios`

返回：

- 场景名称
- 场景说明
- 默认问题文案
- 目标订单

### 8.3 场景触发接口

`POST /api/scenarios/<scenario_code>/run`

请求：

```json
{
  "message": "VIP客户华东终端临时插单300台，最早什么时候能交？"
}
```

返回：

- 场景摘要
- ATP 结果
- 聊天回复
- 可追问建议

### 8.4 通用聊天接口

`POST /api/chat`

请求：

```json
{
  "message": "如果允许加班呢？",
  "scenario_code": "urgent_insert_order",
  "selected_node_id": "WorkCenter",
  "conversation_id": "conv_001"
}
```

返回：

- 消息回复
- 是否触发新一轮 ATP 重算
- 新 ATP 结果

### 8.5 ATP 分析接口

`POST /api/atp/analyze`

适合后续非场景模式直接分析订单。

### 8.6 健康检查接口

`GET /api/health`

返回：

- SQLite 连接状态
- DeepSeek 配置状态

---

## 9. React 页面设计

### 9.1 页面布局

首版采用三段式：

- 顶部：标题、环境状态、模型连接状态
- 左侧：知识图谱区
- 右侧：AI 对话与 ATP 结果区

右侧内部再分两块：

- 上部：预设场景卡 + 对话消息区
- 下部：ATP 结果摘要区

### 9.2 页面组件建议

`AppShell`

- 顶层布局

`OntologyGraphPanel`

- 本体图谱
- 搜索
- 域过滤
- 节点点击高亮

`ScenarioQuickStart`

- 四个预设场景卡片

`ChatPanel`

- 用户输入框
- 消息流
- AI 回答
- 推荐追问

`ATPResultPanel`

- 承诺日期卡
- 置信度卡
- 风险卡
- 原因链
- 备选方案
- 影响对象

`NodeContextBadge`

- 显示当前点击节点，例如“当前关注：WorkCenter / 工作中心”

### 9.3 图谱交互要求

保留：

- 节点点击高亮
- 节点 hover 提示
- 搜索
- 按业务域过滤
- 缩放和平移

取消：

- 右侧实体详情面板
- 图谱边标签默认展示

替代方式：

- 节点点击后，将节点信息作为聊天上下文注入
- 在聊天区显示“你正在基于 WorkCenter 追问”

---

## 10. 造数策略

必须单独提供造数脚本，例如：

`scripts/seed_demo_data.py`

### 10.1 造数原则

- 不是大规模随机造数
- 必须围绕 4 个演示场景定向造数
- 每个场景都要有清晰的冲突与可解释结果
- 同一批数据能支撑多个场景复用

### 10.2 建议数据规模

- 客户：4-6 个
- 成品物料：4-6 个
- 原材料/组件：10-15 个
- 供应商：4-6 个
- 工作中心：4-6 个
- 工艺路线：4-6 条
- 订单：8-12 张
- 生产工单：8-15 张
- 工序：30-60 道
- ATP 承诺历史：10-20 条
- 演示场景：4 条

### 10.3 数据设计重点

要人工设计出这些状态：

- 某个成品库存刚好不足，必须补生产
- 某个关键芯片在途晚到 3 天
- 某个 BOM 项存在替代料
- 某个工作中心负荷高于目标值
- 某个 VIP 客户订单有罚款风险
- 某条替代路线能绕过瓶颈但成本更高

---

## 11. 建议目录结构

```text
codex-supplychain/
├─ docs/
├─ backend/
│  ├─ app.py
│  ├─ config.py
│  ├─ api/
│  ├─ db/
│  ├─ models/
│  ├─ services/
│  │  ├─ atp/
│  │  └─ llm/
│  ├─ prompts/
│  ├─ scripts/
│  │  └─ seed_demo_data.py
│  └─ data/
│     └─ atp_demo.sqlite3
├─ frontend/
│  ├─ src/
│  │  ├─ components/
│  │  ├─ pages/
│  │  ├─ services/
│  │  ├─ store/
│  │  └─ types/
│  └─ public/
└─ ATP最小可运行演示应用设计方案.md
```

---

## 12. 开发顺序建议

### 第一阶段：数据和后端基础

1. 建 SQLite Schema
2. 编写造数脚本
3. 实现图谱接口、场景接口、ATP 分析接口
4. 接入 DeepSeek 客户端和 Prompt 模板

### 第二阶段：前端演示页

1. 起 React + TypeScript 项目
2. 迁移现有图谱效果
3. 改造右侧为 AI 对话区
4. 对接 ATP 结果卡片和场景触发

### 第三阶段：联调和演示优化

1. 打通 4 个预设场景
2. 优化结果展示和追问逻辑
3. 增加错误提示、加载状态、模型状态展示
4. 调整造数，让场景更有戏剧性和解释性

---

## 13. 当前结论

当前最合理的落地方式是：

- 用现有“供应链本体模型知识图谱”作为左侧视觉核心
- 用 SQLite 做本体对象映射和场景测试数据
- 用 Flask 实现 ATP 协调与 DeepSeek 调用
- 用 React 重构整页，把右侧变成 AI 对话和 ATP 结果区
- 用 4 个预设场景构成完整最小演示闭环

这个范围足够小，可以很快做出可运行演示；同时语义、本体、数据库、AI、ATP 计算链路又是完整的，不会沦为纯静态效果稿。
