# 场景触发 AI 推理过程说明

## 1. 文档目的

本文档说明当前演示应用中，用户点击预设场景按钮后，系统如何自动执行 ATP 交期承诺分析。

说明范围包括：

- 每个场景的触发入口
- 参与推理的本体对象
- 应用到的本体规则
- 需要调用的前后端 API
- 后端从数据库装载的核心数据
- 当前实现中的主要推理步骤

本文档对应当前代码实现，核心逻辑见：

- [backend/app.py](../backend/app.py)
- [backend/services/atp/engine.py](../backend/services/atp/engine.py)
- [backend/scripts/seed_demo_data.py](../backend/scripts/seed_demo_data.py)
- [frontend/src/App.tsx](../frontend/src/App.tsx)

---

## 2. 总体触发链路

### 2.1 前端触发方式

用户在右侧 AI 面板点击任一预设场景卡片后，前端执行：

- `handleRunScenario(scenarioCode)`

对应代码：

- [App.tsx](../frontend/src/App.tsx)

前端调用接口：

- `POST /api/scenarios/<scenario_code>/run`

例如：

- `POST /api/scenarios/urgent_insert_order/run`
- `POST /api/scenarios/demand_increase/run`
- `POST /api/scenarios/material_delay/run`
- `POST /api/scenarios/capacity_bottleneck/run`

### 2.2 后端总体流程

后端统一入口：

- [app.py](../backend/app.py)

处理顺序：

1. Flask 路由接收场景请求
2. `ATPService.run_scenario()` 根据 `scenario_code` 读取 `demo_scenarios`
3. `ATPService.analyze_order()` 进入统一 ATP 分析流程
4. 加载订单、客户、成品、库存、BOM、供应商、工艺路线、工作中心日历等数据
5. 执行库存判断、BOM 展开、物料缺口分析、产能推演、候选方案比较
6. 生成 `reasoning_trace`
7. 调用 `DeepSeekClient.generate_atp_explanation()` 输出业务化解释
8. 返回前端：
   - `atp_summary`
   - `reasoning_trace`
   - `assistant`

### 2.3 当前使用的主要 API

#### 前端调用后端

- `GET /api/health`
- `GET /api/ontology/graph`
- `GET /api/scenarios`
- `POST /api/scenarios/<scenario_code>/run`
- `POST /api/chat`
- `POST /api/atp/analyze`

#### 后端调用大模型

- `POST {DEEPSEEK_BASE_URL}/chat/completions`

默认地址：

- `https://api.deepseek.com/chat/completions`

### 2.4 后端从数据库装载数据的主要方式

当前不是通过 ORM，而是通过 SQLite SQL 直接读取。

主要装载点在：

- [engine.py](../backend/services/atp/engine.py)

核心装载函数：

- `_load_inventory()`
- `_load_suppliers()`
- `_load_bom()`
- `_load_routing()`
- `_existing_load()`
- `_next_calendar_day()`

统一数据库连接：

- [database.py](../backend/db/database.py)

---

## 3. 统一 ATP 推理步骤

当前四个场景虽然业务触发点不同，但底层共享一套 ATP 推理骨架。

### Step S1：识别场景对象

涉及本体对象：

- `CustomerOrder`
- `Customer`
- `FinishedItem`

数据库装载：

- `customer_orders`
- `customers`
- `finished_items`

说明：

- 先定位场景关联订单
- 读取客户等级、订单要求交期、成品类型
- 确认本次分析的目标数量和事件类型

对应规则：

- `Ontology:CustomerOrder`
- `Ontology:Customer`
- `Ontology:FinishedItem`

### Step S2：加载基础对象数据

涉及本体对象：

- `Inventory`
- `BOMLevel`
- `Supplier`
- `Routing`
- `WorkCenter`

数据库装载：

- `inventory`
- `inventory_inbound`
- `bom_headers`
- `bom_items`
- `bom_alternatives`
- `suppliers`
- `item_suppliers`
- `routings`
- `routing_operations`

说明：

- 装载成品和组件库存
- 装载 BOM 层级和替代料关系
- 装载供应商提前期和风险
- 装载标准路线和替代路线

对应规则：

- `CR-01`
- `CR-02`
- `CR-03`
- `ALT-01`

### Step S3：成品库存可承诺判断

涉及本体对象：

- `Inventory`
- `CustomerOrder`
- `FinishedItem`

数据库装载：

- `inventory`

说明：

- 计算成品 `available_qty`
- 判断可直接覆盖多少需求
- 计算剩余必须走生产补足的数量

对应规则：

- `CR-01`
- `Inventory.available_qty`

### Step S4：展开 BOM 并识别物料缺口

涉及本体对象：

- `BOMLevel`
- `Inventory`
- `Supplier`

数据库装载：

- `bom_headers`
- `bom_items`
- `bom_alternatives`
- `inventory`
- `inventory_inbound`
- `suppliers`
- `item_suppliers`

说明：

- 根据 `quantity_per * scrap_factor * 生产需求量` 计算组件需求
- 判断每个组件库存是否足够
- 不足时检查：
  - 在途到货
  - 替代料
  - 标准采购提前期

对应规则：

- `BOMLevel.quantity_per`
- `BOMLevel.scrap_factor`
- `CR-03`
- `RISK-01`

### Step S5：产能排程推演

涉及本体对象：

- `Routing`
- `WorkCenter`
- `ProductionOrder`
- `Operation`

数据库装载：

- `routings`
- `routing_operations`
- `work_centers`
- `work_center_calendar`
- `production_orders`
- `operations`

说明：

- 按工艺路线工序顺序推演
- 根据工作中心日历确定可用能力
- 读取既有工单负荷
- 计算每道工序的可插入时间
- 最终得到最早完工日期和瓶颈压力

对应规则：

- `C-01`
- `C-02`
- `C-03`
- `ALT-01`

### Step S6：场景事件修正

说明：

- 每个场景会对通用推理骨架做额外修正
- 比如物料延迟、工作中心爆满、数量变化等

### Step S7：候选方案生成和比较

涉及本体对象：

- `ATPCommitment`
- `Routing`
- `WorkCenter`
- `Supplier`

说明：

- 固定输出三类候选方案：
  - `Standard`
  - `Overtime`
  - `AlternativeRouting` 或 `AlternativeMaterial`
- 比较维度：
  - 承诺日期
  - 置信度
  - 风险等级
  - 成本影响

对应规则：

- `AUTO-01`
- `ALT-01`

### Step S8：生成承诺结果和业务解释

涉及本体对象：

- `ATPCommitment`

说明：

- 生成推荐方案
- 输出原因链、影响对象、候选方案
- 调用 DeepSeek 输出用户可读解释

对应规则：

- `ATPCommitment`
- `LEARN-01`

---

## 4. 场景一：客户加急插单

### 4.1 触发方式

前端场景按钮：

- `客户加急插单`

数据库场景记录：

- `demo_scenarios.scenario_code = urgent_insert_order`

默认问题：

- `VIP客户华东终端临时插单300台，最早什么时候能交？`

目标订单：

- `SO1001`

### 4.2 涉及本体对象

- `Customer`
- `CustomerOrder`
- `FinishedItem`
- `Inventory`
- `BOMLevel`
- `Supplier`
- `Routing`
- `WorkCenter`
- `ProductionOrder`
- `Operation`
- `ATPCommitment`

### 4.3 重点规则

- `CR-01`：不可重复承诺，必须用 `available_qty`
- `CR-03`：替代料使用条件
- `C-01`：工作中心可用产能
- `C-02`：工序耗时计算
- `C-03`：最早完工时间
- `AUTO-01`：候选承诺自动化分层

### 4.4 实际推理重点

- 由于是 VIP 客户临时插单，首先要判断库存能直接覆盖多少
- 覆盖不足时，立即转入生产补足分析
- 展开 `FG_A100` 的 BOM，判断芯片、板卡、结构件、测试件缺口
- 检查 SMT、组装、测试、包装等工作中心是否有可插入窗口
- 比较：
  - 标准方案
  - 加班方案
  - 替代路线方案

### 4.5 需要装载的数据

- 订单、客户、成品主数据
- 成品和组件库存
- 组件在途到货
- 供应商提前期和准时率
- A100 的标准/替代工艺路线
- 工作中心日历和既有工单负荷

### 4.6 结果说明

当前代码实现中，这个场景的推荐结果通常会优先考虑：

- 若加班可以更早满足交期，则推荐 `Overtime`
- 同时保留标准路线和替代路线作为备选

---

## 5. 场景二：客户需求数量上调

### 5.1 触发方式

前端场景按钮：

- `客户需求数量上调`

数据库场景记录：

- `demo_scenarios.scenario_code = demand_increase`

默认问题：

- `订单SO1002数量从200提高到350，交期还能维持不变吗？`

目标订单：

- `SO1002`

### 5.2 涉及本体对象

- `CustomerOrder`
- `FinishedItem`
- `Inventory`
- `BOMLevel`
- `Supplier`
- `Routing`
- `WorkCenter`
- `Operation`
- `ATPCommitment`

### 5.3 重点规则

- `CR-01`
- `CR-03`
- `C-01`
- `C-02`
- `C-03`
- `AUTO-01`

### 5.4 实际推理重点

- 把订单需求数量替换成 `350`
- 重新计算成品库存可覆盖量
- 重新展开 BOM 需求
- 判断数量上调后是否产生新的组件缺口
- 重新按工作中心排程
- 判断原承诺交期是否还能保持

### 5.5 需要装载的数据

- `SO1002` 订单
- `FG_A100` 成品库存
- `FG_A100` BOM 数据
- 相关供应商风险
- A100 工艺路线与工作中心日历

### 5.6 结果说明

这个场景的核心不是“新插一张单”，而是“原订单继续保留、数量上调后是否还能承诺原交期”。  
因此推理过程里，数量变化会直接影响：

- 生产补足量
- 物料缺口
- 工序加工时长
- 工作中心占用

---

## 6. 场景三：关键物料缺料 / 在途延迟

### 6.1 触发方式

前端场景按钮：

- `关键物料缺料/在途延迟`

数据库场景记录：

- `demo_scenarios.scenario_code = material_delay`

默认问题：

- `核心芯片来料延迟3天，这张订单还能按原承诺交付吗？`

目标订单：

- `SO1002`

场景修正参数：

- `delay_item_id = COMP_CHIP_X1`
- `delay_days = 3`

### 6.2 涉及本体对象

- `CustomerOrder`
- `FinishedItem`
- `BOMLevel`
- `Inventory`
- `Supplier`
- `Routing`
- `WorkCenter`
- `ATPCommitment`

### 6.3 重点规则

- `CR-01`
- `CR-02`
- `CR-03`
- `RISK-01`
- `C-01`
- `C-02`
- `C-03`

### 6.4 实际推理重点

- 核心关注对象是关键芯片 `COMP_CHIP_X1`
- 先判断该芯片库存和在途是否能覆盖需求
- 在途延迟场景会强制将物料齐套时间顺延
- 再检查是否存在已批准替代料 `COMP_CHIP_X1_ALT`
- 最后重新推导路线完工时间和 ATP 日期

### 6.5 需要装载的数据

- `FG_A100` 的 BOM
- `COMP_CHIP_X1` 库存
- `COMP_CHIP_X1` 在途到货记录
- `COMP_CHIP_X1_ALT` 替代料记录
- 芯片供应商准时率与单一来源标识
- A100 工艺路线与相关工作中心

### 6.6 结果说明

这个场景重点体现三件事：

1. 本体中的 `Inventory.in_transit_qty` 和到货日期语义
2. 本体中的 `BOMLevel.alternative_items` 语义
3. 本体中的 `Supplier.single_source_flag` 与 `on_time_rate` 风险语义

也就是说，它是最能体现“本体 + ATP + 风险推理”价值的场景。

---

## 7. 场景四：瓶颈工作中心产能不足

### 7.1 触发方式

前端场景按钮：

- `瓶颈工作中心产能不足`

数据库场景记录：

- `demo_scenarios.scenario_code = capacity_bottleneck`

默认问题：

- `SMT-01本周产能爆满，这张单还能承诺4月12日吗？`

目标订单：

- `SO1002`

场景修正参数：

- `bottleneck_wc_id = WC_SMT_01`

### 7.2 涉及本体对象

- `WorkCenter`
- `Routing`
- `Operation`
- `ProductionOrder`
- `CustomerOrder`
- `ATPCommitment`

### 7.3 重点规则

- `C-01`
- `C-02`
- `C-03`
- `ALT-01`
- `AUTO-01`

### 7.4 实际推理重点

- 把 `WC_SMT_01` 作为爆满瓶颈场景对象
- 标准路线完工时间强制额外顺延
- 比较：
  - 标准路线
  - 加班路线
  - 替代路线

### 7.5 需要装载的数据

- `WC_SMT_01` 工作中心主数据
- 工作中心日历
- 既有工单负荷
- 标准路线与替代路线
- 订单需求数量

### 7.6 结果说明

这个场景重点体现：

- 本体中的 `WorkCenter.capacity_model`
- 本体中的 `Routing.alternative_routings`
- ATP 不是只算物料，还要算产能瓶颈与路线切换

---

## 8. 当前系统如何体现“本体对象 + 规则 + 数据装载”

为了便于你演示，这里做一个汇总。

### 8.1 本体对象层

当前推理中真实参与的本体对象主要有：

- `Customer`
- `CustomerOrder`
- `FinishedItem`
- `Inventory`
- `BOMLevel`
- `Supplier`
- `Routing`
- `WorkCenter`
- `ProductionOrder`
- `Operation`
- `ATPCommitment`

### 8.2 规则层

当前代码里实际显式体现的规则主要有：

- `CR-01` 不可重复承诺
- `CR-02` 在途库存时效
- `CR-03` 替代料判断
- `RISK-01` 供应风险缓冲
- `C-01` 工作中心可用产能计算
- `C-02` 工序时长推导
- `C-03` 最早完工时间推导
- `ALT-01` 替代路线评估
- `AUTO-01` 候选方案分层输出
- `LEARN-01` 承诺实体化与反馈学习语义

### 8.3 数据装载层

当前后端需要从数据库装载的关键表有：

- `customers`
- `finished_items`
- `customer_orders`
- `inventory`
- `inventory_inbound`
- `bom_headers`
- `bom_items`
- `bom_alternatives`
- `suppliers`
- `item_suppliers`
- `routings`
- `routing_operations`
- `routing_alternatives`
- `work_centers`
- `work_center_calendar`
- `production_orders`
- `operations`
- `demo_scenarios`

---

## 9. 建议用途

这份文档可以直接用于：

- 演示时对客户解释“点击按钮后系统到底做了什么”
- 对齐后续正式实现中的服务拆分
- 对齐未来把 ATP 推理过程导出为审计日志或流程图
- 对齐未来把 `reasoning_trace` 升级成真正的“AI 推理可追溯记录”
