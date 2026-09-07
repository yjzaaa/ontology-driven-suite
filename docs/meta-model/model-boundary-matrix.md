# 八类本体模型职责边界矩阵（T01.2 产出）

> 本文件是 Wayfinder 工作包 [01-define-domain-language-and-model-boundaries](../wayfinder/tickets/01-define-domain-language-and-model-boundaries.md) 的 T01.2 产出。
> 任务：为 M1 Object、M2 Behavior、M3 Rule、M5 Actor/Permission、M6 Flow、M7 Query、MU Presentation、MI Integration 建立互斥且可判定的职责矩阵。
> MasterData 示例仅使用 [MasterData 试点范围](../wayfinder/masterdata-scope.md) 已观察事实，不扩展到无 `SubtableType` 可达证据的逻辑。
> 本文件解决 TERM-001/005/009/012 的模型编号与职责分歧，并给出 T01.3/T01.4 可继续引用的判定规则。

## 0. 模型编号约定（裁决 TERM-001/009/012）

| 编号 | 本项目名称 | 表达什么 | 参考源差异 |
|---|---|---|---|
| M1 | Object（对象） | 业务对象 | `ontology-driven-dev` 相同；`Onto-Contract` m1-object 相同 |
| M2 | Behavior（行为） | 业务行为 | 三源一致 |
| M3 | Rule（规则） | 业务规则 | 三源一致 |
| M5 | Actor/Permission（参与者/权限） | 角色与权限 | `Onto-Contract` m5-actor 仅 Actor，本项目扩展 Permission |
| M6 | Flow（流程） | 业务/编排流程 | `Onto-Contract` m6 为 compensation，含义不同；本项目采用 Flow |
| M7 | Query（查询） | 受治理查询 | `Onto-Contract` m7 为 quality，含义不同；本项目采用 Query |
| MU | Presentation（展示） | 展示/渲染契约 | `ontology-driven-dev` MU=UI 模型（相近）；`Onto-Contract` 用 m9 表示 UI |
| MI | Integration（集成映射） | 防腐层集成契约 | 三源均无；本项目专有 |

**裁决**：本项目采用 `M1/M2/M3/M5/M6/M7/MU/MI` 八类模型（`AGENTS.md` 与 `docs/wayfinder/map.md` 一致）。不引入 `M4`（scenario）与 `ME`（event）：场景折叠进 Flow 与行为判定，事件作为运行时协议而非持久本体模型（见 T01.2.5 边界说明）。MI 全称采用 **Integration**（避免 TERM-002 的 “Integration Mapping 集成” 冗余，全称在 T01.6 词汇表定稿）。

## 1. 职责矩阵总表

| 模型 | 表达什么 | 不得表达什么 | 主要引用对象 | 运行时用途 |
|---|---|---|---|---|
| M1 Object | 业务身份、属性、生命周期、关系 | URL、HTTP Method、SQL、DTO 字段、页面布局、执行细节 | M2/M3/M5/M6/M7/MU 引用其稳定 ID | 对象视图、表单字段候选、关系导航、身份引用 |
| M2 Behavior | 业务结果能力（与 endpoint 解耦） | endpoint 技术细节、参数序列化、权限实现、持久化语句 | M1、M3、M5、M7、MU | Agent 语义 Tool 行为面、行为提案语义 |
| M3 Rule | 可复用判断/派生约束 | 状态修改、直接写操作、授权实现、校验器内部逻辑 | M1、M2、M5 | 提案风险、行为可用性、字段约束 |
| M5 Actor/Permission | 角色、权限、数据范围 | 用户身份值、Cookie/Token、DPA 过滤器实现 | M1、M2、M7、MI | 权限预检、行为授权、范围过滤 |
| M6 Flow | 跨行为的编排/流程与状态转换 | 单 endpoint 的 Controller 逻辑、页面导航、审批 UI | M1、M2、M3、M5、MU | 流程状态投影、行为建议序列 |
| M7 Query | 受治理查询及结果形状 | 任意 SQL、表结构、DPA 查询接口、技术分页 | M1、M5、MU、MI | 语义查询、对象/集合/指标投影 |
| MU Presentation | 展示契约、渲染选择、Legacy View 入口 | 业务规则、权限判断、执行逻辑、复杂表单复制 | M1、M2、M7、M6 | Renderer 选择、对象卡/表格/图表/Legacy View |
| MI Integration | 防腐层集成契约（技术目标） | 业务语义、Agent 可见参数、凭据、任意 SQL | M1、M2、M7（语义侧）；DPA endpoint/Database MCP（技术侧） | 执行期 DPA HTTP / Database MCP 适配 |

## 2. 模型选择判定树

对任一事实（源码证据、接口行为、页面绑定），按以下顺序判定主模型；协作模型以引用表示：

```text
1. 是“凭据/URL/HTTP Method/Header/任意 SQL/内部 DTO”？
   └─ 是 → 不构成任何本体模型的选择对象（归 MI 技术侧或明确排除），停止。
2. 是否有稳定业务身份 + 生命周期？
   └─ 是 → 主模型 M1 Object。
3. 是否产生稳定业务结果（读或写）？
   ├─ 业务结果 = 查询/统计/指标 → 主模型 M7 Query。
   ├─ 业务结果 = 状态转换/副作用 → 主模型 M2 Behavior。
   └─ 是否跨多个行为编排？ → 叠加 M6 Flow（引用各 M2）。
4. 是否是可复用判断/派生（不执行写）？
   └─ 是 → 主模型 M3 Rule。
5. 是否约束“谁在什么范围可做什么”？
   └─ 是 → 主模型 M5 Actor/Permission。
6. 是否决定“如何呈现/渲染/回到原页”？
   └─ 是 → 主模型 MU Presentation。
7. 是否决定“技术如何连接 DPA/Database MCP”？
   └─ 是 → 归 MI Integration（技术侧），不由 Agent 模型选择。
```

**协作规则**：一个事实可被多个模型引用（如“删除行为”由 M2 表达，M3 判断允许条件，M5 约束权限，M6 编排），但**主模型唯一**；协作关系一律通过稳定 ID 引用，不复制定义。

## 3. 八类模型 MasterData 正例与反例

### M1 Object

- 正例：`SubtableType` 枚举值解析出的数据源/对象候选，若证据证明其具有业务身份与生命周期，则为 M1 Object（`masterdata-scope.md`：每个枚举值对应的数据源、对象候选）。
- 反例：`MasterDataPROnlineApprovalController` 本身、`SubTableViewInfo` 的页面 ViewModel、数据库表行——它们可能是 M1 的候选输入或投影，不自动等于 M1（见 T01.3）。

### M2 Behavior

- 正例：`MasterDataPROnlineApprovalController` 中“根据 `SubtableType` 生成通用页面 / 重定向专用 Controller”所表达的业务结果（如“加载某子表类型的数据”），行为与具体 Action 解耦。
- 反例：单个 ASP.NET Action 的 HTTP 调用细节、参数绑定、返回 JSON——这些是 endpoint 技术事实，不是 M2。

### M3 Rule

- 正例：`SubtableType` 禁止更新列表（`ESN`、`Tax_Rate`、`Tax_Code`、`Tax_code_prefix`、`Exchange_Rate`）——“该类型不允许更新”是可复用判断。
- 反例：校验器中对某个输入框的非空检查，若只是页面级输入校验而非业务约束，不自动判定为 M3（TERM-007）。

### M5 Actor/Permission

- 正例：`MasterDataPROnlineApprovalController` 中“仅审批角色可对 `SubtableType` 执行在线审批”这类权限语义（需证据确认权限归属）。
- 反例：DPA 过滤器/权限实现的 C# 类与角色枚举值——技术实现细节不是 M5 本体内容（M5 表达语义权限）。

### M6 Flow

- 正例：`MasterDataPROnlineApprovalController` 的“审批 → 通过/驳回”状态转换链（若证据证明其存在）编排的流程。
- 反例：单次页面刷新的 Controller 分支、按钮点击导航——不构成跨行为流程（TERM-005：与用户流/DPA Workflow 区分）。

### M7 Query

- 正例：`Depth_Structure` 的 Jedox 数据读取分支——对特定数据源的受治理查询，表达“读取某结构数据”的查询语义。
- 反例：DPA 内嵌 SQL 语句本身、存储过程调用——技术查询实现，M7 只表达查询语义与结果形状（技术目标归 MI）。

### MU Presentation

- 正例：`SubtableViewInfo` 定义的表单字段、列表列、上传模板在页面的呈现方式——展示契约与 Legacy View 入口。
- 反例：页面 HTML 布局、样式、JS 事件绑定细节——不复制 DPA 复杂表单（边界 9）。

### MI Integration

- 正例：`MasterDataPROnlineApprovalController` 中把已发布 M7 Query 或 M2 Behavior 连接到具体 DPA endpoint 的防腐契约（固定参数、错误映射、凭据转发方式）。
- 反例：M7 Query 的语义参数、M2 Behavior 的业务参数——这些是语义模型内容，不属于 MI 技术侧；MI 只承载技术映射。

## 4. 跨模型信息传递规则

- 跨模型只通过稳定 ID 引用：M2 引用 M1 的 `objectId`，M7 引用 M1/M5 范围，MU 引用 M1/M2/M7 的展示对象，MI 引用 M2/M7 的语义 ID 与 DPA 技术目标。
- **禁止在目标模型内复制**对象、行为、规则或权限定义（`AGENTS.md`：跨模型只通过稳定 ID 引用）。
- MI 是 DPA Integration 的内部模型，Agent Experience 只能看到语义引用（`CONTEXT-MAP.md:128`），因此 MI 的引用方向单向：语义模型 → MI → DPA 技术目标。
- 运行时投影由已发布模型生成，不成为第二事实源（TERM-006）。

## 5. 边界说明（裁决 TERM-005/012）

- **M6 Flow 与用户流（user flows）**：M6 是持久本体模型，表达跨行为的业务/编排流程；`tickets/10` 的“四条关键用户路径”是产品体验路径，不是本体模型。两者使用不同术语：M6=流程，用户路径=场景（scenario），避免 TERM-005。
- **不引入 M4/ME**：场景（scenario）作为分析与验收工具，不进入持久本体模型集；事件（event）作为运行时协议（`CONTEXT-MAP.md` 领域事件）存在于 CONTEXT-MAP 的事件语言，不作为第八类本体 YAML。若后续证据证明需要事件本体，将单独提出工作包，不在本工作包内预置（TERM-012）。

## 6. 验证记录

- 八类模型均含独立条目（表达什么、不得表达什么、主要引用对象、运行时用途、正例、反例）。
- 每个 MasterData 示例按判定树可得到唯一主模型类型，协作模型以引用表示。
- 矩阵未把 URL、HTTP Method、任意 SQL、凭据或内部 DTO 映射暴露为模型可选择的业务语义（全部归 MI 技术侧或排除）。
- 命令：`git diff --check` 应通过。
