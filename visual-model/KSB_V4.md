# 知识体系构建可视化建模提示语规范
## Knowledge-System-Building（KSB建模法）v3.6

---

> **本文件是一份可直接使用的「知识体系构建提示词」**。当你（或任一 AI）需要为**任意知识领域**构建一套完整、可可视化、可阅读的知识体系时，调用本规范即可。
> 本规范基于 `KSB_V2.md` / `KSB_v1.md` / `SBR_V2.md` 演进而来：建模对象为「知识领域」，采用「三层递进 + 四图联动」结构。**v3.0 重点升级顶层可视化：思维导图改用 D3.js 实现「中心双侧平衡布局」**；**v3.1 重点强化最底层知识图谱：要求抽取 ≥50 个核心知识点，并按重要度/枢纽度同比放大节点形状**；**v3.2 重点升级中间层多维矩阵：三维知识结构支持任选两个维度动态生成矩阵**；**v3.3 要求顶层思维导图默认展开到三级，并优化 50+ 节点底层图谱的呈现方式**；**v3.4 在依赖关系较多时，保留 DAG 依赖路径图，并额外输出地铁线路图式核心学习路线**；**v3.5 强化中间层矩阵的难度层级配色，要求入门/进阶/高级使用醒目的绿色/浅黄色/深黄色区分**；**v3.6 新增强制学习路线图：底层知识图谱之后必须输出 D3.js + dagre-d3 的 LR 分层学习路线图，明确前导知识、后续知识与知识组装路径**。

**交付物（每次调用本提示词必须产出以下文件）：**
1. `知识体系_<领域>.md` —— 完整 Markdown 知识文档（**建议 3000–5000 字，视领域复杂度而定**，三层标题结构）
2. `knowledge_top.html` —— 顶层：**D3.js 中心双侧思维导图**（根节点居中，主干左右对称展开）
3. `knowledge_middle.html` —— 中间层：多维知识矩阵图
4. `knowledge_bottom.html` —— 最底层：力导向知识网络图谱
5. `knowledge_learning_path.html` —— **强制必选**：学习路线图，使用 **D3.js + dagre-d3**，布局方向 `LR`，从左到右逐层递进，明确前导知识、后续知识与知识组装关系
6. `knowledge_bottom_dependency.html` ——（条件必选）当 `depends` 边占比超过 35% 时输出 DAG/层级依赖路径图
7. `knowledge_dependency_metro.html` ——（条件必选）当 `depends` 边占比超过 35% 时输出地铁线路图式核心学习路线
8. `knowledge_graph.json` / `knowledge_graph.csv` ——（可选）底层图谱结构化数据，便于导入 Neo4j 等工具

---

## 〇、适用领域声明

- **最适用**：结构化较强的领域，如自然科学、工程技术、计算机科学、管理学科、医学、会计/金融等。
- **酌情调整**：人文社科（如哲学史、文学批评）、艺术类（如音乐流派、绘画风格）。这类领域边界模糊、关系以「影响/继承/类比」为主，建议：
  - 顶层分支适当减少（5–8 个），用「学派/时期/流派」替代「模块」；
  - 中间层维度改用「时间 × 地域 × 人物」或「主题 × 风格 × 代表作」；
  - 底层边类型以「影响、继承、对比」为主，弱化「依赖、因果」。
- **不适用**：纯主观感受、无共识定义的主题（如「什么是好音乐」）。遇到时应在 §2.3 提示并改用结构化子主题。

---

## 一、核心建模理念

### 1.1 三层知识体系模型
任何知识领域都可被组织为一个**由树到网、由粗到细**的三层递进体系：

| 层级 | 形态 | 可视化 | 核心问题 |
|---|---|---|---|
| **顶层 · 领域主干** | 中心双侧树状发散 | **D3.js 思维导图（中心双侧）** | 有哪些大块知识？（广度覆盖） |
| **中间层 · 多维矩阵** | 维度交叉 | 知识矩阵（grid/heatmap） | 如何分类与交叉？（维度定位） |
| **最底层 · 知识网络** | 节点+关系 | 分组聚类知识图谱（force graph 为主，依赖强时补 DAG 视图） | 如何关联成网？（关联密度） |
| **学习路线 · 前后依赖** | 分层 DAG | D3.js + dagre-d3 左到右路线图 | 先学什么？某知识的前导是什么？能组装出什么？ |

> **一句话核心原则**：顶层回答「有哪些」，中间层回答「怎么分类交叉」，最底层回答「如何关联成网」——三层由树到网，缺一不可。本规范下文各层均据此原则展开，不再重复阐述。

### 1.2 关键术语表
| 术语 | 定义 |
|---|---|
| **主干（Branch）** | 顶层的一级知识分支，对应领域的一个大模块/子领域。 |
| **维度（Dimension）** | 中间层矩阵的一个分类轴（如「学习范式」「任务类型」），每个维度有若干取值。 |
| **交叉条目（Cell Entry）** | 矩阵某行列交叉处的知识条目（概念/方法/案例）。 |
| **最小知识单元（Atom）** | 底层的一个节点；**必须能独立解释一个现象或完成一个操作**，不可再拆。 |
| **关系边（Edge）** | 底层两节点间的关联，含类型与权重。 |
| **学习路线图（Learning Path DAG）** | 将底层知识节点按前导依赖、演进与组装关系重排为左到右分层 DAG，用于表达学习先后顺序。 |
| **知识密度（Density）** | 矩阵单元格内条目数 / 该领域典型值，映射为背景色深浅。 |
| **盲区（Gap）** | 矩阵中无条目或底层缺少应有边的交叉点，标记为待补全。 |
| **双侧布局（Bilateral）** | 顶层思维导图中，主干以根节点为中心分列左右两侧的平衡布局。 |

---

## 二、建模前置处理规则（强制执行）

在绘制任何图形 / 撰写任何文字前，必须先完成以下分析并显式输出。

### 2.1 输入类型判断
- **类型 A：指定领域**（如「机器学习」）→ 直接界定范围后展开。
- **类型 B：一段文章/主题描述** → 先抽象出核心领域，再界定范围后展开。
- **类型 C：模糊主题**（如「帮我理清区块链」）→ 由模型主动界定边界（给出 1 句定义 + 范围），再展开。

### 2.2 输入材料约束（防凭空捏造）
调用本规范时，**应要求用户至少提供下列之一**作为知识抽取起点：
- ≥ 3 篇参考文献 / 权威资料链接；**或**
- ≥ 5 个该领域关键术语；**或**
- 一段不少于 300 字的主题说明。

> 若用户仅给一个主题名而无上述材料，模型必须在文档开头标注：「⚠️ 本知识体系基于通用常识构建，未经权威资料校验，可能不具权威性，建议补充参考文献后复审。」

### 2.3 领域边界界定（含模板，必须按此填写）
```
【领域】：______
【核心定义】：用 1 句话定义该领域是什么。
【范围边界】：
  - 包含：列出至少 5 个核心子领域 / 主题
  - 不包含：列出 3 个相邻但不属于本领域的内容（划清边界）
  - 前置依赖：进入本领域前需先了解哪些基础知识
【目标受众与用途】：学习入门 / 教学讲解 / 研究综述 / 工程应用
【典型应用场景】：给出 2~3 个具体用例
【三层粒度规划】：见 §2.5
```

### 2.4 知识抽取与三级映射（含引导问题）
从输入中抽取三类要素，并回答对应引导问题：

| 要素 | 引导问题 |
|---|---|
| **概念（名词）** | 这个领域最核心的 10 个术语是什么？分别一句话定义。 |
| **方法（动词）** | 有哪些标准流程、算法、操作步骤？输入→处理→输出是什么？ |
| **关系（连接）** | A 依赖于 B 吗？A 与 B 是类比还是对比？A 是否导致 B？ |

**最小知识单元判定**：一个候选知识点若能独立解释一个现象或完成一个操作，即为合法 Atom；否则需上移为子主题或下拆为更细 Atom。

随后自顶向下映射：
```
顶层分支  ← 一级主干概念（领域大模块）
中间矩阵  ← 主干概念 × 维度取值（交叉知识条目）
底层节点  ← 最小知识单元 Atom（术语/公式/案例/工具）
```

> **禁止跳过前置分析直接绘图或写作。** 体系质量完全取决于领域界定与知识抽取的深度。

### 2.5 粒度规划（建议范围 + 例外处理）
| 层级 | 建议范围 | 例外处理 |
|---|---|---|
| 顶层主干 | 6–12 个 | 领域很窄可减至 5 个；领域宏大可增至 15 个。**双侧布局时尽量配平左右数量**（差 ≤1）。 |
| 中间层维度 | 2–3 个，每维 3–6 取值 | 二维领域直接生成固定矩阵；三维领域必须在 HTML 中提供维度选择器，允许用户任选两个维度动态生成矩阵，剩余维度作为筛选器或单元格标签/密度编码。 |
| 底层节点 | **≥50 个核心知识点**，建议 50–80 个 | 领域很窄时也应尽量抽取 ≥50 个 Atom；若确实不足，必须说明原因并补充相邻依赖知识。若超过 100 个，主图谱保留 ≥50 个核心节点，并按主干分组生成二级子图谱（如 `knowledge_bottom_<主干>.html`）。 |

> 三层篇幅不必均等。若某层偏薄（如纯理论领域缺少实践维度），可在「粒度规划」中说明理由后调整，但三层结构不得缺失。

---

## 三、三层可视化建模规范

> 各层均遵循 §1.1 核心原则：顶层求广度、中间层求交叉、底层求关联。以下仅给出实现与容错细则。

### 3.1 顶层可视化：思维导图（knowledge_top.html）—— D3.js 中心双侧三级布局
- **形态**：根节点（领域名）居于画布**正中心**，一级主干分支**左右双侧对称展开**（XMind 经典平衡布局）。每主干下挂 3–6 个二级子主题，每个二级子主题再下挂 2–5 个三级知识点，整体向远离中心方向延伸。
- **展开深度（强制）**：顶层思维导图默认必须**展开到三级**：根节点 → 一级主干 → 二级子主题 → 三级知识点。若某主干无法展开到三级，必须在 Markdown 中说明该分支粒度不足或资料不足。
- **渲染库**：**D3.js v7**（`d3.hierarchy` + `d3.tree`）。**不再使用 ECharts radial tree**（其节点为圆形、连线机械，观感偏「树图」而非「思维导图」）。
- **双侧分配规则**：将主干按 `i%2`（下标奇偶）或按主题相关性配对分为左/右两组；每组独立用 `d3.tree().nodeSize([vgap, hstep])` 布局后，**纵向居中到 0**；根节点固定于 `(0,0)`，映射到画布中心。
- **紧凑与防覆盖要求（强制）**：
  - 布局应尽量紧凑，避免主干、二级、三级之间出现过长连接线或大面积空白；但不强制横向或纵向比例，画布比例由领域内容和节点数量自适应决定。
  - 默认展开到三级时，必须检测节点包围盒，保证同侧相邻节点不覆盖；若发生覆盖，应增大 `vgap`、调整 `hstep` 或局部展开间距。
  - 三级节点数量较多时，优先保证节点不覆盖和文字可读，而不是强行压缩到固定画布比例。
- **连线**：cubic-bezier 横向曲线，方向由 `target.side` 决定（右侧→向右伸展、左侧→向左伸展）。主干色继承到其叶子与连线。
- **镜像对称细节（强制）**：
  - 右侧叶子的彩色色条贴**左**（靠根一侧），左侧叶子色条贴**右**（靠根一侧）。
  - 折叠标记：右侧用 `▸`、左侧用 `◂`。
- **节点样式**：
  - 根节点 = 深色药丸（白字加粗）；
  - 主干 = 彩色药丸（白字），颜色取自全局 `KSB_PALETTE.branches`；
  - 叶子 = 白底圆角 + 侧边色条 + 深色字；
  - 节点宽度按文字长度动态计算：`width = max(72, name.length*13+24)`。
- **交互**：点击主干或子主题节点折叠/展开；顶部「展开全部 / 展开到三级 / 折叠到主干 / 重置视图」按钮；`d3.zoom` 滚轮缩放 + 拖拽平移。
- **默认状态**：展开到三级，初始视图显示根节点、一级主干、二级子主题和三级知识点；若存在四级及更深内容，默认折叠在三级节点之后。
- **实现防坑（强制，踩过的坑必须规避）**：
  1. **缩放层与布局层分离**：外层 `gZoom` 承载 `d3.zoom` 变换，内层 `g` 只承载布局偏移（`translate(-minX,-minY)`）。**二者不可写在同一 `<g>` 上**，否则缩放 transform 与布局 transform 互相覆盖，导致图形错位或不显示。
  2. **禁止对 null 调用节点辅助函数**：计算画布尺寸时不得把 `null` 传给 `nodeWidth/nodeHeight`（会触发 `null.depth` 抛 TypeError 中断渲染），高度余量直接用常量（如 40）。
  3. **画布宽度** `W = maxX − minX`（含两侧 PAD），root（xx=0）映射到 `W/2`；纵向按 `(maxY−minY)` 居中。
  4. **数据连接 key** 用 `name+depth`，避免重名节点冲突。

### 3.2 中间层可视化：知识矩阵（knowledge_middle.html）
- **形态**：支持二维或三维多维知识结构。
  - **二维场景**：行 = 维度①取值，列 = 维度②取值，直接生成固定知识矩阵。
  - **三维场景**：必须提供「行维度」「列维度」两个选择器，用户可从 3 个维度中任选两个作为矩阵坐标轴，系统基于当前选择动态重渲染矩阵。
- **单元格内容**：该交叉点下的知识条目（列表呈现），背景色深浅 = 知识密度；若矩阵包含「难度/层级/学习阶段」维度，还必须叠加难度层级配色。
- **难度层级配色（强制）**：
  - 当第三维筛选器为「全部」时，单元格内不同难度分组必须使用醒目的背景色块区分，不能只用普通标题文字区分。
  - 入门 = 绿色背景（建议 `#dff6e5`），进阶 = 浅黄色背景（建议 `#fff1b8`），高级 = 深黄色背景（建议 `#f2c94c`）。
  - 当「难度层级」被选为行维度或列维度时，对应整格也必须按上述颜色显示。
  - 当「难度层级」作为筛选维度且选择单一取值时，当前矩阵单元格应按该取值使用对应背景色。
  - 知识密度色阶仍保留，但优先级低于难度层级配色；同一单元格同时存在难度色与密度色时，以难度色为主。
- **渲染（二选一）**：
  - 方案 A（推荐）：HTML/CSS Grid 网格矩阵，可读性强。
  - 方案 B：ECharts `heatmap`，颜色映射密度，tooltip 显示明细。
- **三维矩阵实现方案（强制）**：
  - 若识别出 3 个有效维度，`knowledge_middle.html` 必须包含 3 个控件：`行维度`、`列维度`、`筛选维度取值`。
  - `行维度` 与 `列维度` 不得相同；切换任一选择器后，矩阵行列标题、单元格条目、知识密度背景色必须同步重算。
  - 未被选为行/列的第三维，默认作为筛选器；筛选器支持「全部」以及该维度的所有取值。
  - 当筛选器为「全部」时，单元格内条目应按第三维取值分组展示，避免不同维度语义混在一起。
  - 若第三维为「难度层级」，分组块必须使用入门/进阶/高级三色背景，并在图例中解释颜色含义。
  - 知识密度始终按当前行列维度与筛选条件动态计算，而不是写死在静态 HTML 中。
- **必含**：每个维度标注含义与取值；矩阵外附「矩阵解读」（重点交叉 + 盲区标注）。

### 3.3 最底层可视化：分组聚类知识图谱（knowledge_bottom.html）
- **形态选择原则**：50+ 节点的知识图谱若只使用普通力导向图，容易出现节点拥挤、关系线缠绕、阅读成本高的问题。因此底层默认采用**分组聚类力导向图谱**：force-directed graph 仍作为基础布局，但必须叠加主干分组、关系筛选、枢纽突出和局部聚焦能力。若该领域以严格前置依赖为主（如数学、编程、医学流程），应额外提供依赖路径视图或 DAG 视图，帮助用户看清学习先后。
- **形态**：节点 = Atom，边 = 关系。底层图谱必须体现「知识点—知识点」之间的依赖、包含、因果、演进、类比、对比等关联，而不是只做概念散点展示。
- **节点规模（强制）**：
  - 必须从该知识域中抽取 **50 个以上核心知识点** 构建图谱；建议 50–80 个，保证覆盖所有顶层主干。
  - 每个顶层主干至少对应 5 个底层节点；若某主干不足 5 个，需在 Markdown 中说明该主干粒度较粗或资料不足。
  - 节点必须是可独立解释或可独立操作的 Atom，禁止把「某某体系」「某某模块」这类过粗主题直接塞入底层。
- **节点**：
  - `importance`：0~1，综合「领域基础性、学习优先级、实践频率、被依赖程度」评估。
  - `degreeScore`：按入边、出边和高权重边综合计算，用于衡量该节点在知识网络中的枢纽程度。
  - `symbolSize`：按 `importance` + `degreeScore` 同比缩放（建议 12–60），权重大的知识点必须显示为更大的节点形状；枢纽节点不得与普通叶子节点同尺寸。
  - `category`：所属主干（颜色与顶层一致）。
  - `value`：悬停/点击显示的定义与要点。
- **边（增强：权重 + 方向 + 依赖）**：
  - 每个节点平均至少连接 2 条边；孤岛节点原则上不允许超过节点总数的 5%，且必须说明补全方向。
  - `linkWeight`（0~1）：影响 `lineStyle.width = linkWeight * 4 + 1`，体现关系强弱；强依赖 / 强因果边建议 ≥0.75。
  - 关系类型 → 颜色/线型（见附录 B）。
  - `depends` / `causes` / `evolved-to` 等方向性关系必须使用箭头；`evolved-to`（演进）关系使用**箭头 + 文字标签**显示方向。
  - 依赖关系应优先补全：若 A 的理解或操作必须以 B 为前提，则必须添加 `A depends B`；若 A 会触发/导致 B，则添加 `A causes B`。
- **节点大小计算建议（强制写入生成脚本）**：
  ```js
  // importance: 0~1；degreeScore 可由连接数量与边权重归一化得到
  node.symbolSize = 12 + Math.round((node.importance * 0.6 + node.degreeScore * 0.4) * 48);
  ```
- **标签截断（技术方案）**：`label.formatter` 截断超长名，tooltip 显示全名。
- **50+ 节点呈现优化（强制）**：
  - **分组聚类**：节点按顶层主干 `category` 着色并形成视觉分区；同一主干节点应尽量聚集，跨主干关系用更淡的边或曲线表示。
  - **关系筛选**：HTML 必须提供关系类型筛选控件（全部 / depends / causes / contains / analogy / contrast / evolved），降低复杂图谱的线条噪声。
  - **枢纽优先**：默认突出 Top 10 枢纽节点，普通节点标签可在缩放或悬停时显示，避免全量标签互相遮挡。
  - **局部聚焦**：点击节点后高亮一阶邻居和二阶邻居，并弱化无关节点/边。
  - **DAG 依赖路径视图**：若 `depends` 边占比超过 35%，必须保留并额外输出 `knowledge_bottom_dependency.html`，以 DAG/层级图方式呈现前置依赖链，帮助用户看清“先学什么、后学什么”。
  - **地铁线路图式学习路径（新增，强制）**：若 `depends` 边占比超过 35%，除 DAG 依赖路径视图外，还必须额外输出 `knowledge_dependency_metro.html`。该图应将核心学习路线组织成多条“地铁线路”（如基础路线、工程路线、应用路线、安全路线），共享枢纽节点作为换乘站，并用细虚线贝塞尔曲线箭头连接路线间核心依赖关系。
  - **地铁图设计要求**：主线路使用粗彩色折线或直线，核心节点用站点圆点表示；跨线路依赖使用较细的 cubic-bezier 曲线，带箭头，颜色与主线路区分；悬停或点击依赖线时显示“源节点 → 目标节点”和依赖说明。
- **交互（增强）**：
  - 可拖拽、缩放、悬停高亮相邻（`emphasis.focus: 'adjacency'`）。
  - **点击节点弹窗**显示详细定义；或 `window.open` 跳转到 Markdown 对应锚点（`知识体系_<领域>.md#<节点名>`）。
- **完整性度量**：图中标注「节点总数、边总数、平均度、孤岛节点数量、Top 10 枢纽节点」，提示补全方向。

### 3.4 学习路线图（knowledge_learning_path.html）—— D3.js + dagre-d3 左到右分层 DAG
- **强制交付**：每次生成 `knowledge_bottom.html` 之后，必须额外输出独立文件 `knowledge_learning_path.html`。该文件不受 `depends` 边占比限制，始终必选。
- **核心目的**：底层知识图谱回答「知识如何关联成网」，学习路线图回答「学习顺序如何展开」。它必须明确体现：
  - 学习某个知识点前需要掌握哪些前导知识；
  - 学习某个知识点后可以通向哪些后续知识；
  - 多个基础知识如何组装成高阶概念、方法或专题；
  - 从左到右逐层递进的学习路径。
- **渲染库**：使用 **D3.js + dagre-d3**，推荐 CDN：
  - `https://cdn.jsdelivr.net/npm/d3@5/dist/d3.min.js`
  - `https://cdn.jsdelivr.net/npm/dagre-d3@0.6.4/dist/dagre-d3.min.js`
- **布局方向（强制）**：`rankdir:'LR'`，即 Left → Right。画面左侧为基础/前导知识，右侧为进阶/后续/综合知识。
- **分层规则**：
  - 每个节点必须分配 `layer`，表示学习阶段或依赖层级，如 `L0 基础概念 → L1 核心框架 → L2 方法/模型 → L3 应用/专题 → L4 综合/前沿`。
  - 层级可由依赖拓扑排序、课程学习顺序、时代顺序或专家判断确定；若某领域依赖不严格，应在 Markdown 中说明“学习层级是推荐路径而非唯一逻辑必然”。
  - `depends` 边必须优先用于确定层级；`contains` 表示组装/包含；`evolved` 表示思想/技术演进；`contrast` 表示对比阅读；`analogy` 表示旁路参照。
- **边方向语义（强制）**：
  - 学习路线图中的箭头必须统一解释为：`前导知识 → 后续知识`。
  - 若底层图谱中采用 `{source: 高阶节点, target: 前导节点, type:'depends'}` 的反向建模方式，生成学习路线图时必须反转为 `target → source`。
  - `contains` 边在学习路线图中也应表达为「组成部分 / 子知识 → 组合后的上位知识」；若原始边为「整体 contains 部分」，生成路线图时必须反转。
  - `evolved` 边应表达为「早期思想/方法 → 后续思想/方法」；若原始数据方向相反，必须按学习语义纠正。
- **节点与颜色**：
  - 节点仍使用底层图谱的 Atom，不得把过粗的主干分支直接当作路线图节点。
  - 节点颜色必须继承 `KSB_PALETTE.branches`，与顶层主干和底层图谱一致。
  - 节点标签显示短名称；悬停/点击面板显示完整名称、定义、所属主干、所在层级、直接前导和直接后续。
- **关系线样式**：
  - `depends`：蓝色实线，表示强前导依赖；
  - `contains`：灰蓝色较粗实线，表示知识组装/构成；
  - `evolved`：紫色实线，表示历史/方法演进；
  - `contrast`：橙色虚线，表示对比学习；
  - `analogy`：绿色点线，表示类比参照；
  - 方向性关系必须带箭头，箭头方向始终从左到右指向后续知识。
- **路线筛选（强制）**：
  - 页面必须提供路线选择器，至少包含「全景路线」和 3 条以上差异化路线，如「通识入门」「理论基础」「方法实践」「高级专题」「工程应用」「研究前沿」等，具体名称按领域调整。
  - 选择某条路线时，必须自动补齐该路线节点的必要前导知识，避免出现“中间节点缺失导致路线断裂”。
  - 页面必须提供关系类型筛选器：学习主线 / 全部关系 / depends / contains / evolved / contrast / analogy。
- **交互（强制）**：
  - 支持缩放与拖拽平移；
  - 点击节点后，高亮该节点、所有前导路径、所有后续路径；
  - 用不同视觉状态区分：当前节点、前导节点、后续节点、无关节点；
  - 右侧或浮层详情面板显示：
    - 节点定义；
    - 所属主干与学习层级；
    - 直接前导知识；
    - 可组装/通向的后续知识；
    - 关系说明（为何依赖、为何演进或为何对比）。
- **防坑要求**：
  - dagre-d3 只负责布局，缩放必须放在外层 `<g id="zoom">`，图形渲染放在内层 `<g id="graph">`，避免缩放 transform 覆盖布局 transform。
  - 路线图必须保证无明显节点重叠；若节点过多，应通过路线筛选、层级分组、横向间距 `ranksep` 和纵向间距 `nodesep` 控制可读性。
  - 对可能形成环的关系，生成学习路线图时必须过滤弱关系或拆分为对比/旁路关系，主学习路径必须保持 DAG 可读。
  - 若某节点存在多个前导，应保留多入边，以体现知识组装；不得为了线性美观删除关键前导关系。

---

## 四、HTML 生成与交付规范

### 4.1 通用 HTML 模板规则
- 每个图为**自包含单文件**，UTF-8，无外部依赖除 CDN。
- **CDN 按层选用**：
  - 顶层思维导图：**D3.js v7** — `https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js`
  - 中间层矩阵：纯 HTML/CSS（无依赖）或 ECharts
  - 底层图谱：ECharts — `https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js`
  - 学习路线图：**D3.js + dagre-d3** — `https://cdn.jsdelivr.net/npm/d3@5/dist/d3.min.js` + `https://cdn.jsdelivr.net/npm/dagre-d3@0.6.4/dist/dagre-d3.min.js`
- 浅色主题优先（背景 `#f7f8fa`、卡片 `#fff`、文字 `#1a1a2e`）；深色用 `#0f1420`。
- 必含：标题栏、图例、交互提示（「可拖拽 / 悬停查看 / 点击详情」）。
- 容器响应式：`width:100%; height:100vh;`。

### 4.2 三文件命名与职责
| 文件 | 图层 | 可视化形式 | 核心问题 |
|---|---|---|---|
| `knowledge_top.html` | 顶层 | **D3.js 中心双侧思维导图** | 有哪些大块知识？ |
| `knowledge_middle.html` | 中间层 | 知识矩阵（网格/热力） | 如何分类与交叉？ |
| `knowledge_bottom.html` | 最底层 | 分组聚类知识图谱 | 如何关联成网？ |
| `knowledge_learning_path.html` | 学习路线 | D3.js + dagre-d3 左到右分层 DAG | 先学什么？如何组装？ |
| `knowledge_bottom_dependency.html` | 条件底层 | DAG/层级依赖路径图 | 前置依赖链是什么？ |
| `knowledge_dependency_metro.html` | 条件底层 | 地铁线路图式学习路径 | 核心学习路线如何串联？ |

### 4.3 四图联动（配色一致性，强制）
四图必须使用**同一全局配色对象**，确保视觉一致。顶层 D3、底层 ECharts 与学习路线图 dagre-d3 共用同一 `KSB_PALETTE`：

```js
const KSB_PALETTE = {
  branches: ['#3f51b5','#009688','#ff9800','#e91e63','#4caf50',
             '#00bcd4','#9c27b0','#ff5722','#795548','#607d8b','#cddc39','#f44336'],
  relation: {
    contains:'#8896c7', depends:'#4f9bff', causes:'#ff5252',
    analogy:'#43a047', contrast:'#ffa726', evolved:'#ab47bc'
  },
  bg: { light:'#f7f8fa', dark:'#0f1420' }
};
```
- 顶层主干色 = 底层节点 `category` 色（同一主干用同一色）。
- 顶层一个主干分支，应在中间层至少对应一个维度取值、在底层对应一个节点群。

### 4.4 额外导出格式（增强）
除 HTML 外，底层图谱应同时输出结构化数据，便于导入 Neo4j 等工具：
- `knowledge_graph.json`：`{ nodes:[{id,name,category,value,importance,degreeScore,symbolSize}], edges:[{source,target,type,weight}] }`
- `knowledge_graph.csv`（边表）：`source,target,type,weight`

---

## 五、建模流程指引（含反馈迭代）

**第一步 · 领域界定**（§2.3）：输出定义、边界、受众、粒度规划。
**第二步 · 知识抽取与映射**（§2.4）：列顶层分支、中间维度、底层节点清单。
**第三步 · 顶层思维导图**：构建三级树数据，按双侧规则分配左右，生成默认展开到三级的 `knowledge_top.html`（D3.js）。
**第四步 · 中间知识矩阵**：定 2–3 维度，填单元格；若为三维结构，生成可动态选择任意两个维度的 `knowledge_middle.html`。
**第五步 · 底层知识图谱**：抽取 ≥50 个核心 Atom，构建 nodes/links，计算 `importance`、`degreeScore` 与 `symbolSize`，生成带分组聚类、关系筛选和局部聚焦的 `knowledge_bottom.html` + JSON/CSV；若 `depends` 边占比超过 35%，必须同时补充 `knowledge_bottom_dependency.html`（DAG/层级依赖路径）和 `knowledge_dependency_metro.html`（地铁线路图式核心学习路线）。
**第六步 · 学习路线图**：基于底层 nodes/links 抽取前导依赖、组装包含、演进与对比关系，统一转换为「前导知识 → 后续知识」方向，分配 `layer`，生成 `rankdir:'LR'` 的 `knowledge_learning_path.html`（D3.js + dagre-d3），并提供路线筛选、关系筛选、点击高亮前导/后续路径和详情面板。
**第七步 · 汇总 Markdown 文档**：按 §六 撰写，每节嵌入对应 HTML 链接。
**第八步 · 反馈迭代（新增，必须执行）**：
1. 检查矩阵**盲区**：空白交叉是否应有知识？若有，反向补充底层节点。
2. 检查底层**缺失边**：明显应有因果/依赖却未连的节点，补连；若平均度过低或孤岛节点超过 5%，必须继续补边。
3. 检查顶层**覆盖**：是否有重要主干遗漏？若有，回补顶层分支并联动调整中下两层（同步调整左右双侧配平）。
4. 迭代直至三层自洽、无逻辑断裂。

> 每步都需先有「结构化清单」再生成图形/文字，禁止凭空绘图。

---

## 六、Markdown 知识文档结构规范（知识体系_<领域>.md）

**字数**：建议 3000–5000 字（视领域复杂度而定），强调「言之有物」，禁止机械凑字。
**结构（严格三级标题）**：

```markdown
# <领域名称> 知识体系

> 一句话定义 + 范围说明 + 本文结构指引（约 100 字）
> （若输入材料不足，在此标注 ⚠️ 通用常识构建提示）

## 一、顶层知识：领域主干（思维导图式展开）
> 📊 查看对应图表：[knowledge_top.html](knowledge_top.html)
> 先给「读图指引」，再逐分支说明。

### 1.1 <主干分支一>
- 定义：……
- 核心要点：① ② ③
- 可验证实例：……（至少 1 个可测量/可验证的实例）
- 关键子主题：……

### 1.2 <主干分支二>
……（覆盖全部主干分支）

## 二、中间层知识：多维矩阵（知识矩阵式展开）
> 📊 查看对应图表：[knowledge_middle.html](knowledge_middle.html)

### 2.1 维度定义
- 维度①：……（取值：A/B/C）
- 维度②：……（取值：X/Y/Z）

### 2.2 矩阵解读
- 重点交叉（如 A×X）：包含……（说明为何重要）
- 盲区标注：……（指出待补全方向）

## 三、最底层知识：知识网络（图谱式展开）
> 📊 查看对应图表：[knowledge_bottom.html](knowledge_bottom.html)

### 3.1 核心节点群（按主干分类）
- <节点名>：定义 + 关联（指向……）
……（覆盖主要节点）

### 3.2 关联类型与网络特征
- 高频关系：依赖/包含占主导 → 说明领域知识组织方式
- 关键枢纽节点：……（被大量关联，优先掌握）

### 3.3 推荐学习路径（至少 2 条差异化）
> 📊 查看对应图表：[knowledge_learning_path.html](knowledge_learning_path.html)

- **速成路线**（约 X 小时）：根 → 主干A → 节点a → 节点b；前置依赖：……
- **系统学习路线**（约 Y 小时）：根 → 主干A → … → 主干C；前置依赖：……

## 附录 A：图表索引
- 顶层思维导图：knowledge_top.html
- 中间层知识矩阵：knowledge_middle.html
- 最底层知识图谱：knowledge_bottom.html
- 左到右学习路线图：knowledge_learning_path.html
- 依赖路径视图：knowledge_bottom_dependency.html（若 `depends` 边占比超过 35%）
- 地铁线路图式学习路径：knowledge_dependency_metro.html（若 `depends` 边占比超过 35%）
- 结构化数据：knowledge_graph.json / knowledge_graph.csv

## 附录 B：版本与更新记录
- 创建日期：YYYY-MM-DD
- 知识来源：参考文献/资料清单（≥3 篇，或注明「通用常识」）
- 下次复审日期：YYYY-MM-DD（建议 6–12 个月复审）
- 变更记录：v1.0 初版 / v1.1 ……
```

**写作要求**：
- 顶层重「覆盖面与脉络」，中间层重「结构关系与交叉」，底层重「关联密度与学习优先级」。
- 每个知识点需有「定义 + 要点 + 可验证实例 + 关联」，避免空泛罗列。
- 三层篇幅可按领域调整（需在 §2.5 粒度规划说明理由），但三层结构不得缺失。

---

## 七、质量检查清单

**前置分析**
- [ ] 已显式输出领域定义、边界、受众、粒度规划
- [ ] 已获取输入材料（≥3 参考文献 或 ≥5 关键术语），或已标注通用常识提示
- [ ] 已完成知识抽取与三级映射

**内容准确性（新增）**
- [ ] 每个主干分支下至少有 1 个可测量/可验证的实例
- [ ] 底层节点间无明显缺失的边（尤其因果/依赖边）
- [ ] 矩阵交叉条目无重复或归类错误
- [ ] 盲区已标注并给出补全方向

**顶层思维导图（D3 双侧）**
- [ ] 使用 D3.js v7，根节点居中，主干左右双侧对称
- [ ] 默认展开到三级：根节点 → 一级主干 → 二级子主题 → 三级知识点
- [ ] 布局尽量紧凑，无明显过长连线或大面积空白
- [ ] 默认展开到三级时，同侧节点包围盒无重叠，文字无覆盖
- [ ] 左右主干数量配平（差 ≤1），每侧纵向居中
- [ ] 连线为 cubic-bezier，方向随 side 左右镜像；叶子色条贴根侧
- [ ] `gZoom`（缩放）与 `g`（布局偏移）分离，未共用同一 transform
- [ ] 节点宽度按文字长度动态计算，无文字溢出
- [ ] 含展开全部 / 展开到三级 / 折叠到主干 / 重置按钮，点击主干或子主题可折叠
- [ ] 配色取自全局 `KSB_PALETTE`

**中间层知识矩阵**
- [ ] 明确 2–3 个维度及取值
- [ ] 单元格有实际条目，盲区已标注
- [ ] 若为三维结构，HTML 支持任选两个维度作为行/列动态生成矩阵
- [ ] 三维结构下，剩余维度支持「全部/单取值」筛选，且单元格内容与密度色阶会随选择重算
- [ ] 若包含难度层级维度，入门/进阶/高级分别使用绿色/浅黄色/深黄色背景；筛选为「全部」时，单元格内难度分组色块清晰醒目
- [ ] 附矩阵解读

**最底层知识图谱**
- [ ] 已抽取 ≥50 个核心知识点，且覆盖全部顶层主干
- [ ] 每个主干至少对应 5 个底层节点；不足时已说明原因
- [ ] 边含权重 `linkWeight`，依赖/因果/演进关系有方向箭头
- [ ] 节点大小按 `importance + degreeScore` 同比缩放，权重大的节点明显更大
- [ ] 平均每节点至少 2 条边；孤岛节点不超过 5%，且已标注补全方向
- [ ] 节点按主干分类着色（与顶层一致）
- [ ] 50+ 节点场景已提供关系筛选、枢纽突出、局部聚焦，避免全量边线遮挡
- [ ] 若 `depends` 边占比超过 35%，已输出 `knowledge_bottom_dependency.html`，以 DAG/层级图呈现前置依赖链
- [ ] 若 `depends` 边占比超过 35%，已输出 `knowledge_dependency_metro.html`，以地铁线路图呈现核心学习路线
- [ ] 地铁线路图包含多条核心路线、共享换乘节点，并用贝塞尔曲线箭头表达路线间核心依赖关系
- [ ] 可交互（拖拽/缩放/悬停/点击弹窗），孤岛节点已标注
- [ ] 已同步输出 JSON/CSV

**学习路线图（D3.js + dagre-d3）**
- [ ] 已强制输出 `knowledge_learning_path.html`，不因 `depends` 边占比低而省略
- [ ] 使用 D3.js + dagre-d3，布局方向为 `rankdir:'LR'`，从左到右逐层递进
- [ ] 每个路线图节点来自底层 Atom，并分配了明确 `layer`
- [ ] 箭头统一表示「前导知识 → 后续知识」，已对底层图谱中方向相反的 `depends` / `contains` / `evolved` 边做学习语义转换
- [ ] 明确体现某知识点的直接前导、后续知识，以及多个前导如何组装成高阶知识
- [ ] 至少提供「全景路线」和 3 条以上差异化学习路线，且切换路线时自动补齐必要前导节点
- [ ] 提供关系类型筛选：学习主线 / 全部关系 / depends / contains / evolved / contrast / analogy
- [ ] 点击节点后能高亮当前节点、前导路径、后续路径，并弱化无关节点/边
- [ ] 详情面板显示定义、所属主干、学习层级、直接前导、可组装/通向的后续知识
- [ ] `depends`、`contains`、`evolved`、`contrast`、`analogy` 使用不同颜色/线型，且图例解释清楚
- [ ] 主学习路径保持 DAG 可读，无明显环路、节点重叠或文字覆盖

**文档与交付**
- [ ] 产出至少 5 个核心文件（1 md + 4 html + json/csv；依赖强时额外输出 DAG 与地铁图）
- [ ] Markdown 正文 3000–5000 字，严格三层标题
- [ ] 每节含 📊 图表超链接（相对路径）
- [ ] 学习路径 ≥ 2 条差异化且含前置依赖
- [ ] 文档末尾含版本与更新记录（来源/复审日期）
- [ ] 四图配色一致，可对应回溯
- [ ] 非专业人员能看懂 70% 以上内容

---

## 八、领域适配指南（差异化维度建议）

| 领域类型 | 常用中间层维度 | 底层主导关系 | 备注 |
|---|---|---|---|
| **理论型**（数学/哲学） | 概念 × 方法 × 难度 | 依赖、类比、演进 | 中间层可能偏薄，允许调整篇幅 |
| **工程型**（软件/机械） | 理论 × 实践 × 工具 | 依赖、因果、对比 | 底层节点通常应 ≥50；超 100 时主图保留核心节点并补充子图谱 |
| **历史型**（断代史/流派） | 时间 × 地域 × 人物 | 影响、继承、对比 | 弱化因果，强化时序演进边 |
| **技能型**（烹饪/演奏） | 环节 × 难度 × 工具 | 依赖、因果 | 底层节点为「操作步骤」型 Atom |

---

## 九、示例（简版，演示交付形态）

**输入**：「帮我构建『机器学习』知识体系」（用户提供 3 篇综述 + 8 个关键术语）

**§2.3 领域界定**：
- 定义：让计算机从数据中自动学习规律的科学。
- 包含：监督/无监督/强化学习、模型评估、特征工程、深度学习……
- 不包含：底层 GPU 硬件设计、分布式系统调度。
- 前置依赖：线性代数、概率统计、Python 基础。
- 受众：入门学习者。

**交付产物**：
- `知识体系_机器学习.md`（约 4200 字，含三层 + 版本记录）
- `knowledge_top.html`（**D3 中心双侧三级思维导图**：根「机器学习」居中，9 主干分列左右，默认展开到三级，可折叠）
- `knowledge_middle.html`（范式 / 任务 / 难度 三维可选矩阵，可任选两个维度动态生成矩阵）
- `knowledge_bottom.html`（≥50 节点分组聚类知识图谱，边含权重，节点大小按重要度/枢纽度缩放，支持关系筛选与局部聚焦）
- `knowledge_learning_path.html`（D3.js + dagre-d3 左到右分层学习路线图，明确前导知识、知识组装与后续路径）
- `knowledge_graph.json` / `.csv`（≥50 节点 + 边表）

---

## 附录 A：三层四图 HTML 模板代码（v3.6 更新版）

### A.1 顶层 · D3.js 中心双侧思维导图（v3 核心更新）
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>顶层知识体系思维导图（中心双侧）</title>
<script src="https://cdn.jsdelivr.net/npm/d3@7/dist/d3.min.js"></script>
<style>
  html,body{margin:0;height:100%;background:#f7f8fa;font-family:"Microsoft YaHei",sans-serif;color:#1a1a2e;}
  #bar{position:sticky;top:0;z-index:10;display:flex;align-items:center;gap:10px;
       padding:10px 16px;background:#fff;border-bottom:1px solid #e6e8f0;box-shadow:0 1px 4px #0001;flex-wrap:wrap;}
  #bar button{padding:5px 14px;font-size:13px;border:1px solid #3f51b5;background:#3f51b5;color:#fff;border-radius:5px;cursor:pointer;}
  #bar .tip{color:#888;font-size:12px;margin-left:auto;}
  #wrap{width:100%;overflow:auto;} svg{display:block;}
  .link{fill:none;stroke-linecap:round;}
  .node text{dominant-baseline:central;text-anchor:middle;pointer-events:none;}
  .leaf rect{stroke:#e3e6f0;stroke-width:1;} .node{cursor:pointer;} .node:hover rect{filter:brightness(0.96);}
</style>
</head>
<body>
<div id="bar">
  <b>顶层思维导图（中心双侧三级）</b>
  <button onclick="expandAll()">展开全部</button>
  <button onclick="expandToThird()">展开到三级</button>
  <button onclick="collapseAll()">折叠到主干</button>
  <button onclick="resetZoom()">重置视图</button>
  <span class="tip">点击主干/子主题折叠展开 ｜ 滚轮缩放 ｜ 拖拽平移</span>
</div>
<div id="wrap"><svg id="chart"></svg></div>
<script>
const PALETTE=['#3f51b5','#009688','#ff9800','#e91e63','#4caf50','#00bcd4','#9c27b0','#ff5722','#795548','#607d8b'];
// 数据：root -> 主干 -> 子主题 -> 三级知识点；更深层级默认折叠在三级节点之后。
const raw={name:'领域名称',children:[
  {name:'主干1',ci:0,children:[
    {name:'子主题A',children:[{name:'知识点A1'},{name:'知识点A2'}]},
    {name:'子主题B',children:[{name:'知识点B1'},{name:'知识点B2'}]}
  ]},
  {name:'主干2',ci:1,children:[
    {name:'子主题C',children:[{name:'知识点C1'},{name:'知识点C2'}]},
    {name:'子主题D',children:[{name:'知识点D1'},{name:'知识点D2'}]}
  ]}
  /* ...更多主干 */
]};

function walk(n,fn,depth=0){ fn(n,depth); (n.children||n._children||[]).forEach(c=>walk(c,fn,depth+1)); }
function foldAfterDepth(n,maxDepth,depth=0){
  if(depth>=maxDepth && n.children){ n._children=n.children; n.children=null; n._folded=true; return; }
  if(n.children)n.children.forEach(c=>foldAfterDepth(c,maxDepth,depth+1));
}
foldAfterDepth(raw,3); // 默认展开到三级；四级及更深内容折叠。

const VGAP=28,HSTEP=190,PAD=70;
const svg=d3.select('#chart');
const gZoom=svg.append('g').attr('class','zoom');   // 缩放层（外）
const g=gZoom.append('g');                           // 布局偏移层（内）
const linkG=g.append('g'), nodeG=g.append('g');

function colorOf(d){
  if(d.depth===0)return '#1a237e';
  if(d.depth===1)return PALETTE[d.data.ci??0];
  let p=d.parent; while(p&&p.depth>1)p=p.parent; return p?PALETTE[p.data.ci??0]:'#888';
}
function nodeWidth(d){ return d.depth===0?66:Math.max(72,d.data.name.length*13+24); }
function nodeHeight(d){ return d.depth===0?40:(d.depth===1?30:26); }

// 单侧布局：side=+1 右, -1 左
function buildSide(branches,side){
  if(!branches.length)return [];
  const h=d3.hierarchy({name:'_',children:branches});
  d3.tree().nodeSize([VGAP,HSTEP]).separation((a,b)=>a.parent===b.parent?1:1.3)(h);
  const nodes=h.descendants().filter(d=>d.depth>0);
  nodes.forEach(n=>{n.xx=side*n.y;n.yy=n.x;n.side=side;});
  const ys=nodes.map(n=>n.yy); const mid=(Math.min(...ys)+Math.max(...ys))/2;
  nodes.forEach(n=>n.yy-=mid);
  return nodes;
}
function linkPath(s,t){
  const sw=nodeWidth(s),tw=nodeWidth(t),dir=t.side>=0?1:-1;
  const x1=s.xx+dir*sw/2,x2=t.xx-dir*tw/2;
  const dx=Math.abs(x2-x1),c=Math.max(26,dx*0.42);
  return `M${x1},${s.yy} C${x1+dir*c},${s.yy} ${x2-dir*c},${t.yy} ${x2},${t.yy}`;
}

function render(){
  const right=buildSide(raw.children.filter((_,i)=>i%2===0),+1);
  const left =buildSide(raw.children.filter((_,i)=>i%2===1),-1);
  const sideNodes=right.concat(left);
  const rootNode={depth:0,data:raw,xx:0,yy:0,side:0,parent:null};
  const allNodes=sideNodes.concat([rootNode]);
  const links=[];
  sideNodes.forEach(n=>{ if(n.depth===1)links.push({source:rootNode,target:n}); else links.push({source:n.parent,target:n}); });
  const xs=allNodes.map(n=>n.xx),ys=allNodes.map(n=>n.yy);
  const minX=Math.min(...xs)-PAD,maxX=Math.max(...xs)+PAD,minY=Math.min(...ys)-20,maxY=Math.max(...ys)+20;
  const W=maxX-minX,H=maxY-minY;
  svg.attr('width',W).attr('height',H).attr('viewBox',`0 0 ${W} ${H}`);
  g.attr('transform',`translate(${-minX},${-minY})`);

  const link=linkG.selectAll('path').data(links,d=>d.target.data.name+d.target.depth);
  link.exit().remove();
  link.enter().append('path').attr('class','link')
    .attr('d',d=>linkPath(d.source,d.target))
    .attr('stroke',d=>colorOf(d.target))
    .attr('stroke-width',d=>d.target.depth===1?2.2:1.4)
    .attr('opacity',d=>d.target.depth===1?0.9:0.55);
  linkG.selectAll('path').attr('d',d=>linkPath(d.source,d.target)).attr('stroke',d=>colorOf(d.target));

  const node=nodeG.selectAll('g.node').data(allNodes,d=>(d.depth===0?'__root__':d.data.name)+d.depth);
  node.exit().remove();
  const ne=node.enter().append('g').attr('class','node')
    .on('click',(ev,d)=>{
      if(d.depth<1)return;
      if(d.data._children&&!d.data.children){d.data.children=d.data._children;d.data._children=null;d.data._folded=false;}
      else if(d.data.children){d.data._children=d.data.children;d.data.children=null;d.data._folded=true;}
      render();
    });
  ne.append('rect'); ne.append('text');

  const all=nodeG.selectAll('g.node');
  all.attr('transform',d=>`translate(${d.xx-nodeWidth(d)/2},${d.yy})`);
  all.each(function(d){
    const sel=d3.select(this),w=nodeWidth(d),h=nodeHeight(d),c=colorOf(d);
    if(d.depth===0){
      sel.select('rect').attr('width',w).attr('height',h).attr('rx',9).attr('fill',c).attr('filter','drop-shadow(0 3px 8px #1a237e66)');
      sel.select('text').text(d.data.name).attr('x',w/2).attr('y',h/2).attr('fill','#fff').attr('font-size',18).attr('font-weight',700);
    }else if(d.depth===1){
      sel.select('rect').attr('width',w).attr('height',h).attr('rx',7).attr('fill',c).attr('filter','drop-shadow(0 2px 4px #0002)');
      const arrow=d.data._folded?(d.side<0?'  ◂':'  ▸'):'';
      sel.select('text').text(d.data.name+arrow).attr('x',w/2).attr('y',h/2).attr('fill','#fff').attr('font-size',13).attr('font-weight',600);
    }else{
      sel.attr('class','node leaf');
      sel.select('rect').attr('width',w).attr('height',h).attr('rx',6).attr('fill','#ffffff').attr('filter','drop-shadow(0 1px 2px #0001)');
      const bar=sel.select('.bar'); if(bar.empty())sel.insert('rect','text').attr('class','bar');
      const barX=d.side<0?w-4:0;
      sel.select('.bar').attr('width',4).attr('height',h).attr('rx',2).attr('x',barX).attr('y',0).attr('fill',c);
      const arrow=d.data._folded?(d.side<0?'  ◂':'  ▸'):'';
      sel.select('text').text(d.data.name+arrow).attr('x',w/2+(d.side<0?0:2)).attr('y',h/2).attr('fill','#263238').attr('font-size',12.5).attr('font-weight',500);
    }
  });
}
function expandAll(){const w=n=>{if(n._children){n.children=n._children;n._children=null;n._folded=false;}if(n.children)n.children.forEach(w);};w(raw);render();}
function expandToThird(){expandAll();foldAfterDepth(raw,3);render();}
function collapseAll(){raw.children.forEach(b=>{if(b.children){b._children=b.children;b.children=null;b._folded=true;}});render();}

const zoom=d3.zoom().scaleExtent([0.4,2.5]).on('zoom',ev=>gZoom.attr('transform',ev.transform));
svg.call(zoom);
function resetZoom(){svg.transition().duration(400).call(zoom.transform,d3.zoomIdentity);}
render();
</script>
</body>
</html>
```

### A.2 中间层 · 动态多维知识矩阵（二维/三维自适应）
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>中间层知识矩阵</title>
<style>
body{font-family:sans-serif;background:#f7f8fa;margin:0;padding:20px;color:#1a1a2e;}
h2{text-align:center;}
.ctrl{display:flex;justify-content:center;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:12px;}
.ctrl select{padding:4px 8px;}
table{border-collapse:collapse;margin:0 auto;background:#fff;box-shadow:0 2px 8px #0001;}
th,td{border:1px solid #d7dbe8;padding:10px 14px;vertical-align:top;min-width:170px;max-width:260px;}
th{background:#3f51b5;color:#fff;}
.row-h{background:#5c6bc0;color:#fff;font-weight:bold;}
.cell{font-size:13px;line-height:1.6;}
.d0{background:#fff;} .d1{background:#f6f8ff;} .d2{background:#eef2ff;} .d3{background:#e3e9ff;}
.level-beginner{background:#dff6e5;} .level-intermediate{background:#fff1b8;} .level-advanced{background:#f2c94c;}
.level-block{border-radius:6px;margin:5px 0;padding:7px 9px;border:1px solid #00000012;}
.group{margin:0 0 3px;font-weight:700;color:#1f2a3d;}
.legend{text-align:center;margin-top:14px;color:#555;font-size:13px;}
.legend span{display:inline-block;width:14px;height:14px;margin:0 4px;vertical-align:middle;border:1px solid #00000018;}
</style>
</head>
<body>
<h2>中间层 · 动态多维知识矩阵</h2>
<div class="ctrl">
  <label>行维度：<select id="rowDim" onchange="syncDims()"></select></label>
  <label>列维度：<select id="colDim" onchange="syncDims()"></select></label>
  <label id="filterBox">筛选：<select id="filterVal" onchange="render()"></select></label>
</div>
<table id="mt"></table>
<div class="legend">
  难度层级：<span class="level-beginner"></span>入门 <span class="level-intermediate"></span>进阶 <span class="level-advanced"></span>高级 ｜
  知识密度：<span class="d1"></span>低 <span class="d2"></span>中 <span class="d3"></span>高 ｜ 「—」表示盲区（待补全）
</div>
<script>
// 三维示例；二维领域可只保留两个维度，控件会自动隐藏筛选器。
const dims = {
  paradigm:['监督学习','无监督学习','强化学习'],
  task:['分类','回归','聚类'],
  difficulty:['入门','进阶','高级']
};
const dimLabel = {paradigm:'学习范式', task:'任务类型', difficulty:'难度'};
const entries = [
  {name:'逻辑回归', paradigm:'监督学习', task:'分类', difficulty:'入门'},
  {name:'线性回归', paradigm:'监督学习', task:'回归', difficulty:'入门'},
  {name:'K-Means', paradigm:'无监督学习', task:'聚类', difficulty:'入门'},
  {name:'SVM', paradigm:'监督学习', task:'分类', difficulty:'进阶'},
  {name:'Q-Learning', paradigm:'强化学习', task:'分类', difficulty:'进阶'}
];
const keys = Object.keys(dims);
const rowSel = document.getElementById('rowDim');
const colSel = document.getElementById('colDim');
const filterSel = document.getElementById('filterVal');
function fillSelect(sel, selected){
  sel.innerHTML = keys.map(k=>`<option value="${k}" ${k===selected?'selected':''}>${dimLabel[k]}</option>`).join('');
}
function otherDim(){
  const r=rowSel.value,c=colSel.value;
  return keys.find(k=>k!==r&&k!==c);
}
function syncDims(){
  if(rowSel.value===colSel.value){
    colSel.value = keys.find(k=>k!==rowSel.value) || rowSel.value;
  }
  const f = otherDim();
  document.getElementById('filterBox').style.display = f ? 'inline-block' : 'none';
  filterSel.innerHTML = f ? '<option value="__all__">全部</option>' + dims[f].map(v=>`<option value="${v}">${v}</option>`).join('') : '';
  render();
}
function cls(n){ return n===0?'d0':(n<=1?'d1':(n<=3?'d2':'d3')); }
function levelCls(v){
  return v==='入门'?'level-beginner':(v==='进阶'?'level-intermediate':(v==='高级'?'level-advanced':''));
}
function isDifficultyDim(dim){
  return ['difficulty','level','stage'].includes(dim) || /难度|层级|阶段/.test(dimLabel[dim] || dim);
}
function itemsFor(rDim,rVal,cDim,cVal,fDim,fVal){
  return entries.filter(e=>e[rDim]===rVal && e[cDim]===cVal && (!fDim || fVal==='__all__' || e[fDim]===fVal));
}
function render(){
  const rDim=rowSel.value,cDim=colSel.value,fDim=otherDim(),fVal=filterSel.value || '__all__';
  const rows=dims[rDim], cols=dims[cDim];
  let html = `<tr><th>${dimLabel[rDim]} \\ ${dimLabel[cDim]}</th>` + cols.map(c=>`<th>${c}</th>`).join('') + '</tr>';
  for(const r of rows){
    html += `<tr><td class="row-h">${r}</td>`;
    for(const c of cols){
      const items = itemsFor(rDim,r,cDim,c,fDim,fVal);
      const cnt = items.length;
      let body = '—';
      let cellLevelClass = isDifficultyDim(rDim) ? levelCls(r) : (isDifficultyDim(cDim) ? levelCls(c) : '');
      if(items.length && fDim && fVal==='__all__'){
        body = dims[fDim].map(v=>{
          const group = items.filter(x=>x[fDim]===v);
          const blockClass = isDifficultyDim(fDim) ? ` level-block ${levelCls(v)}` : '';
          return group.length ? `<div class="${blockClass.trim()}"><div class="group">${v}</div>` + group.map(x=>'• '+x.name).join('<br>') + '</div>' : '';
        }).filter(Boolean).join('');
      }else if(items.length){
        body = items.map(x=>'• '+x.name).join('<br>');
        if(fDim && isDifficultyDim(fDim) && fVal!=='__all__') cellLevelClass = levelCls(fVal);
      }
      html += `<td class="cell ${cellLevelClass || cls(cnt)}">${body}</td>`;
    }
    html += '</tr>';
  }
  document.getElementById('mt').innerHTML = html;
}
fillSelect(rowSel, keys[0]); fillSelect(colSel, keys[1] || keys[0]); syncDims();
</script>
</body>
</html>
```

### A.3 最底层 · 分组聚类知识图谱（权重 + 方向 + 点击弹窗 + 截断）
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>最底层知识网络图谱</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>html,body{margin:0;height:100%;background:#0f1420;font-family:sans-serif;}
#c{width:100%;height:100vh;}
#popup{position:fixed;right:20px;top:60px;width:280px;background:#1b2233;color:#e8eaf6;
  padding:14px;border-radius:8px;box-shadow:0 4px 20px #0008;display:none;font-size:13px;line-height:1.6;}
#popup h4{margin:0 0 6px;color:#80d8ff;}</style>
</head>
<body><div id="c"></div>
<div id="popup"><h4 id="pt"></h4><div id="pd"></div></div>
<script>
const KSB_PALETTE = {
  branches:['#3f51b5','#009688','#ff9800','#e91e63','#4caf50','#00bcd4'],
  relation:{ contains:'#8896c7', depends:'#4f9bff', causes:'#ff5252',
             analogy:'#43a047', contrast:'#ffa726', evolved:'#ab47bc' }
};
const categories=[{name:'主干1'},{name:'主干2'},{name:'主干3'}];
const nodes=[
  {name:'节点AAAAAAAA', symbolSize:30, category:0, value:'定义/要点说明 A'},
  {name:'节点B', symbolSize:22, category:1, value:'定义/要点说明 B'},
  {name:'节点C', symbolSize:18, category:2, value:'定义/要点说明 C'}
];
const links=[
  {source:'节点AAAAAAAA', target:'节点B', type:'depends', weight:0.8},
  {source:'节点B', target:'节点C', type:'causes', weight:0.6},
  {source:'节点AAAAAAAA', target:'节点C', type:'evolved', weight:0.5}
];
links.forEach(l=>{
  l.lineStyle={ color:KSB_PALETTE.relation[l.type],
    width:l.weight*4+1,
    type:l.type==='causes'?'dashed':(l.type==='analogy'?'dotted':'solid') };
  if(l.type==='evolved'){ l.label={show:true, formatter:'演进', color:'#ab47bc', fontSize:10}; l.symbol=['none','arrow']; }
});
const chart=echarts.init(document.getElementById('c'));
chart.setOption({
  title:{text:'最底层 · 知识网络图谱（可拖拽/悬停/点击查看）', left:'center', textStyle:{color:'#e8eaf6'}},
  tooltip:{formatter:p=>p.dataType==='node'?`${p.data.name}：${p.data.value||''}`:p.data.type},
  legend:[{data:categories.map(c=>c.name), textStyle:{color:'#e8eaf6'}, top:36}],
  series:[{
    type:'graph', layout:'force', roam:true,
    data:nodes, links:links, categories:categories,
    label:{show:true, color:'#e8eaf6', fontSize:12,
      formatter:p=>p.data.name.length>6?p.data.name.slice(0,6)+'…':p.data.name},
    edgeSymbol:['none','none'],
    force:{repulsion:240, edgeLength:130},
    emphasis:{focus:'adjacency'},
    lineStyle:{curveness:0.1}
  }]
});
chart.on('click', p=>{
  if(p.dataType==='node'){
    document.getElementById('pt').textContent=p.data.name;
    document.getElementById('pd').textContent=p.data.value||'（无详情）';
    document.getElementById('popup').style.display='block';
  }
});
window.addEventListener('resize',()=>chart.resize());
</script>
</body>
</html>
```

### A.4 结构化导出（JSON / CSV 生成示例）
```js
// 在生成 knowledge_bottom.html 的脚本末尾追加，触发浏览器下载
function download(name, content, mime){
  const b=new Blob([content],{type:mime});
  const a=document.createElement('a'); a.href=URL.createObjectURL(b); a.download=name; a.click();
}
// JSON
download('knowledge_graph.json',
  JSON.stringify({nodes:nodes.map(n=>({id:n.name,name:n.name,category:categories[n.category].name,value:n.value,importance:n.importance,degreeScore:n.degreeScore,symbolSize:n.symbolSize})),
                  edges:links.map(l=>({source:l.source,target:l.target,type:l.type,weight:l.weight}))},null,2),
  'application/json');
// CSV（边表）
download('knowledge_graph.csv',
  'source,target,type,weight\n'+links.map(l=>`${l.source},${l.target},${l.type},${l.weight}`).join('\n'),
  'text/csv');
```

### A.5 学习路线图 · D3.js + dagre-d3 左到右分层 DAG
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>学习路线图</title>
<script src="https://cdn.jsdelivr.net/npm/d3@5/dist/d3.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/dagre-d3@0.6.4/dist/dagre-d3.min.js"></script>
<style>
html,body{margin:0;height:100%;font-family:sans-serif;background:#f7f8fa;color:#1a1a2e;}
header{position:fixed;left:0;right:0;top:0;z-index:5;background:#fff;border-bottom:1px solid #e4e7ef;padding:12px 18px;box-shadow:0 2px 10px #0001;}
.bar{display:flex;gap:12px;align-items:center;flex-wrap:wrap;}
h2{font-size:18px;margin:0 12px 0 0;} select,button{padding:5px 8px;border:1px solid #cfd5e5;border-radius:6px;background:#fff;}
.hint{font-size:12px;color:#5b6475;margin-top:8px;}
#wrap{height:100%;padding-top:96px;box-sizing:border-box;overflow:hidden;}
svg{width:100%;height:100%;cursor:grab;}
.node rect{rx:7px;ry:7px;stroke:#39445e;stroke-width:1.2px;filter:drop-shadow(0 2px 3px #0002);}
.node text{fill:#fff;font-size:13px;font-weight:650;}
.edgePath path{fill:none;stroke:#78849c;stroke-width:1.8px;}
.edgeLabel text{font-size:11px;fill:#4f5c73;}
.node.dim rect,.edgePath.dim path,.edgeLabel.dim{opacity:.12;}
.node.active rect{stroke:#e91e63;stroke-width:3px;}
.node.pre rect{stroke:#1565c0;stroke-width:3px;}
.node.next rect{stroke:#2e7d32;stroke-width:3px;}
.edgePath.active path{stroke:#e91e63!important;stroke-width:3.5px!important;opacity:1;}
#panel{position:fixed;right:18px;top:126px;width:320px;background:#fff;border:1px solid #dfe4f1;border-radius:8px;box-shadow:0 8px 28px #0002;padding:14px;display:none;z-index:6;font-size:13px;line-height:1.6;}
#panel h3{margin:0 0 8px;color:#1a237e;font-size:16px;}
</style>
</head>
<body>
<header>
  <div class="bar">
    <h2>学习路线图（左到右逐层递进）</h2>
    <label>路线 <select id="route" onchange="render()"><option value="all">全景路线</option><option value="intro">通识入门</option><option value="advanced">高级专题</option></select></label>
    <label>关系 <select id="relation" onchange="render()"><option value="learning">学习主线</option><option value="all">全部关系</option><option value="depends">depends</option><option value="contains">contains</option><option value="evolved">evolved</option><option value="contrast">contrast</option><option value="analogy">analogy</option></select></label>
    <button onclick="resetView()">重置视图</button>
    <button onclick="clearFocus()">清除高亮</button>
  </div>
  <div class="hint">箭头方向统一表示：前导知识 → 后续知识。点击节点高亮蓝色前导、绿色后续、粉色直接路径。</div>
</header>
<div id="wrap"><svg id="svg"><g id="zoom"><g id="graph"></g></g></svg></div>
<aside id="panel"><h3 id="pt"></h3><div id="pd"></div></aside>
<script>
const KSB_PALETTE={
  branches:['#3f51b5','#009688','#ff9800','#e91e63','#4caf50','#00bcd4','#9c27b0','#ff5722'],
  relation:{contains:'#8896c7',depends:'#4f9bff',causes:'#ff5252',analogy:'#43a047',contrast:'#ffa726',evolved:'#ab47bc'}
};
// nodes 必须来自底层 Atom；layer 表示学习层级。
const nodes=[
  {id:'基础概念A', category:0, layer:0, value:'定义与要点'},
  {id:'核心概念B', category:0, layer:1, value:'定义与要点'},
  {id:'组合知识C', category:1, layer:2, value:'定义与要点'}
];
// 注意：学习路线图边方向必须是「前导 → 后续」。
// 若底层图谱是「高阶 depends 前导」或「整体 contains 部分」，生成此数组时必须反转。
const edges=[
  {from:'基础概念A', to:'核心概念B', type:'depends', weight:.8},
  {from:'核心概念B', to:'组合知识C', type:'contains', weight:.7}
];
const routeSets={intro:['基础概念A','核心概念B'], advanced:['组合知识C']};
const layerNames=['L0 基础','L1 核心','L2 组装','L3 应用','L4 前沿'];
const nodeMap=new Map(nodes.map(n=>[n.id,n]));
const svg=d3.select('#svg'), zoomLayer=d3.select('#zoom'), inner=d3.select('#graph');
let currentEdges=[], currentNodes=[];
const zoom=d3.zoom().scaleExtent([.25,2.2]).on('zoom',()=>zoomLayer.attr('transform',d3.event.transform));
svg.call(zoom);
function edgeAllowed(e,rel){return rel==='all'||(rel==='learning'&&['depends','contains','evolved','contrast'].includes(e.type))||e.type===rel;}
function visibleSet(route){
  if(route==='all')return new Set(nodes.map(n=>n.id));
  const s=new Set(routeSets[route]||[]);
  let changed=true;
  while(changed){changed=false;edges.forEach(e=>{if(s.has(e.to)&&!s.has(e.from)){s.add(e.from);changed=true;}});}
  return s;
}
function render(){
  clearFocus(false);
  const route=document.getElementById('route').value, rel=document.getElementById('relation').value, visible=visibleSet(route);
  currentNodes=nodes.filter(n=>visible.has(n.id));
  currentEdges=edges.filter(e=>visible.has(e.from)&&visible.has(e.to)&&edgeAllowed(e,rel));
  const g=new dagreD3.graphlib.Graph({compound:true}).setGraph({rankdir:'LR',nodesep:34,ranksep:82,marginx:30,marginy:26}).setDefaultEdgeLabel(()=>({}));
  layerNames.forEach((name,i)=>g.setNode('cluster_'+i,{label:name,clusterLabelPos:'top',style:'fill:#fff;stroke:#d9deec'}));
  currentNodes.forEach(n=>{
    g.setNode(n.id,{label:n.id,rx:7,ry:7,paddingLeft:12,paddingRight:12,paddingTop:8,paddingBottom:8,
      style:`fill:${KSB_PALETTE.branches[n.category]};stroke:#39445e`,labelStyle:'fill:#fff;font-weight:650'});
    g.setParent(n.id,'cluster_'+n.layer);
  });
  currentEdges.forEach(e=>{
    const c=KSB_PALETTE.relation[e.type]||'#667085', dash=e.type==='contrast'?'stroke-dasharray:6 4;':'';
    g.setEdge(e.from,e.to,{label:e.type,curve:d3.curveBasis,arrowhead:'vee',
      style:`stroke:${c};stroke-width:${e.type==='contains'?3:2}px;${dash}fill:none`,arrowheadStyle:`fill:${c};stroke:${c}`,labelStyle:`fill:${c};font-weight:650`});
  });
  inner.selectAll('*').remove(); new dagreD3.render()(inner,g);
  inner.selectAll('g.node').on('click',id=>focusNode(id)).on('mouseover',id=>showPanel(id));
  inner.selectAll('g.edgePath,g.edgeLabel').each(function(v){d3.select(this).attr('data-from',v.v).attr('data-to',v.w);});
  resetView();
}
function related(id,dir){
  const seen=new Set(), stack=[id];
  while(stack.length){const cur=stack.pop();currentEdges.forEach(e=>{const next=dir==='pre'&&e.to===cur?e.from:(dir==='next'&&e.from===cur?e.to:null);if(next&&!seen.has(next)){seen.add(next);stack.push(next);}});}
  return seen;
}
function focusNode(id){
  const pre=related(id,'pre'), next=related(id,'next');
  inner.selectAll('g.node').classed('dim',true).classed('active',false).classed('pre',false).classed('next',false);
  inner.selectAll('g.node').filter(d=>d===id).classed('dim',false).classed('active',true);
  inner.selectAll('g.node').filter(d=>pre.has(d)).classed('dim',false).classed('pre',true);
  inner.selectAll('g.node').filter(d=>next.has(d)).classed('dim',false).classed('next',true);
  inner.selectAll('g.edgePath,g.edgeLabel').classed('dim',true).classed('active',false)
    .filter(function(){const f=this.getAttribute('data-from'),t=this.getAttribute('data-to');return f===id||t===id||pre.has(f)||next.has(t);}).classed('dim',false).classed('active',true);
  showPanel(id);
}
function showPanel(id){
  const n=nodeMap.get(id), pre=currentEdges.filter(e=>e.to===id).map(e=>e.from), next=currentEdges.filter(e=>e.from===id).map(e=>e.to);
  document.getElementById('pt').textContent=id;
  document.getElementById('pd').innerHTML=`${n.value}<br><br><b>学习层级：</b>${layerNames[n.layer]||n.layer}<br><b>直接前导：</b>${pre.join('、')||'无'}<br><b>可组装/通向：</b>${next.join('、')||'无'}`;
  document.getElementById('panel').style.display='block';
}
function clearFocus(hide=true){inner.selectAll('g.node,g.edgePath,g.edgeLabel').classed('dim',false).classed('active',false).classed('pre',false).classed('next',false);if(hide)document.getElementById('panel').style.display='none';}
function resetView(){
  const b=inner.node().getBBox(), w=svg.node().clientWidth, h=svg.node().clientHeight;
  const s=Math.min(1.05,Math.max(.28,Math.min((w-80)/b.width,(h-80)/b.height)));
  svg.transition().duration(300).call(zoom.transform,d3.zoomIdentity.translate((w-b.width*s)/2-b.x*s,36-b.y*s).scale(s));
}
window.addEventListener('resize',resetView);
render();
</script>
</body>
</html>
```

---

## 附录 B：配色映射表模板（全局对象）

```js
const KSB_PALETTE = {
  branches: ['#3f51b5','#009688','#ff9800','#e91e63','#4caf50',
             '#00bcd4','#9c27b0','#ff5722','#795548','#607d8b','#cddc39','#f44336'],
  relation: {
    contains:'#8896c7',   // 灰蓝，实线
    depends:  '#4f9bff',   // 蓝，实线
    causes:   '#ff5252',   // 红，虚线粗
    analogy:  '#43a047',   // 绿，点线
    contrast: '#ffa726',   // 橙，双线
    evolved:  '#ab47bc'    // 紫，箭头线
  },
  difficulty: {
    beginner:     '#dff6e5', // 入门：绿色
    intermediate: '#fff1b8', // 进阶：浅黄色
    advanced:     '#f2c94c'  // 高级：深黄色
  },
  bg: { light:'#f7f8fa', dark:'#0f1420' },
  card:{ light:'#ffffff', dark:'#1b2233' },
  text:{ light:'#1a1a2e', dark:'#e8eaf6' }
};
// 矩阵密度色阶
const DENSITY = ['#f6f8ff','#eef2ff','#e3e9ff','#d4dcff']; // 低→高；优先级低于 difficulty
```

---

**版本**：v3.6
**创建日期**：2026-07-13
**主要变更（相对 v3.5）**：
1. **新增强制学习路线图**：每次输出底层知识图谱后，必须额外输出 `knowledge_learning_path.html`，不再受 `depends` 边占比限制。
2. **学习路线图采用 D3.js + dagre-d3**：强制使用 `rankdir:'LR'` 左到右分层 DAG，表达「前导知识 → 后续知识」。
3. **强化知识组装表达**：路线图必须展示直接前导、后续知识、多前导如何组装成高阶知识，并提供节点点击高亮与详情面板。
4. **交付规范、流程、Markdown 模板、质量清单与附录模板同步更新**：从“三图联动”升级为“三层四图联动”。

**v3.5 主要变更（相对 v3.4）**：
1. **中间层难度配色增强**：当矩阵包含「难度/层级/学习阶段」维度时，入门/进阶/高级必须分别使用绿色/浅黄色/深黄色背景。
2. **三维矩阵全部筛选态增强**：筛选器为「全部」时，若第三维为难度层级，单元格内不同难度分组必须用醒目的色块展示。
3. **模板与质量清单同步更新**：附录 A.2 增加 `levelCls`、`isDifficultyDim` 和难度色块渲染逻辑，质量清单增加难度配色检查项。

**v3.4 主要变更（相对 v3.3）**：
1. **底层依赖视图增强**：当 `depends` 边占比超过 35% 时，保留原有 `knowledge_bottom_dependency.html` DAG/层级依赖路径图。
2. **新增地铁线路图式学习路径**：当 `depends` 边占比超过 35% 时，额外输出 `knowledge_dependency_metro.html`，用多条路线表达核心学习路径。
3. **新增跨路线依赖表达**：地铁线路图中，路线间核心依赖必须用带箭头的 cubic-bezier 曲线表示，并支持悬停/点击查看依赖说明。
4. **流程与质量清单同步更新**：第五步和质量检查清单新增 DAG 依赖图与地铁线路图的条件交付要求。

**v3.3 主要变更（相对 v3.2）**：
1. **顶层思维导图升级为默认展开到三级**：`knowledge_top.html` 必须展示根节点、一级主干、二级子主题、三级知识点；四级及更深内容默认折叠。
2. **顶层交互控件增强**：新增「展开到三级」按钮，保留「展开全部 / 折叠到主干 / 重置视图」，并允许主干与子主题节点折叠展开。
3. **底层图谱呈现方式优化**：50+ 节点场景不再只依赖普通力导向图，升级为分组聚类知识图谱，强制加入关系筛选、枢纽突出、局部聚焦。
4. **依赖型领域补充 DAG/依赖路径视图**：当 `depends` 边占比超过 35% 时，应提供依赖路径模式或额外输出 `knowledge_bottom_dependency.html`。
5. **顶层布局补充约束**：在不强制横纵比例的前提下，思维导图应尽量紧凑，并确保默认展开到三级时节点和文字不覆盖。

**v3.2 主要变更（相对 v3.1）**：
1. **中间层多维矩阵升级为二维/三维自适应**：二维领域直接生成固定矩阵；三维领域必须支持用户任选两个维度作为行/列动态生成矩阵。
2. **新增三维矩阵交互控件要求**：`knowledge_middle.html` 必须提供「行维度」「列维度」「筛选维度取值」控件，行列维度不得相同。
3. **动态重算矩阵内容与密度**：切换维度或筛选条件后，矩阵标题、单元格条目、盲区、知识密度背景色必须同步重算；第三维为「全部」时按取值分组展示。
4. **附录 A.2 模板升级**：由旧的第三维下拉筛选模板，替换为可任选两个维度的动态多维知识矩阵模板。

**v3.1 主要变更（相对 v3.0）**：
1. **最底层知识图谱升级为 ≥50 核心知识点标准**：§2.5、§3.3、§五、§七、§九统一要求底层图谱抽取 50 个以上 Atom，并覆盖全部顶层主干。
2. **新增节点重要度与枢纽度字段**：节点增加 `importance`、`degreeScore`，并要求 `symbolSize` 按二者同比缩放，权重大的知识点必须显示为更大的节点形状。
3. **强化知识点依赖关系建模**：依赖、因果、演进等方向性边必须补全箭头与权重；平均每节点至少 2 条边，孤岛节点不超过 5%。
4. **结构化导出同步增强**：`knowledge_graph.json` 导出新增 `importance`、`degreeScore` 字段，便于后续导入图数据库或做中心性分析。

**v3.0 主要变更（相对 v2.0）**：
1. **顶层可视化全面升级为 D3.js 中心双侧思维导图**（§3.1 重写）：根节点居中、主干按 `i%2` 左右双侧对称展开、每侧独立 `d3.tree` 布局并纵向居中、cubic-bezier 镜像连线、叶子色条贴根侧、折叠标记 ◂/▸ 左右区分。
2. **新增实现防坑条款**（§3.1 强制）：缩放层 `gZoom` 与布局层 `g` 必须分离；禁止对 `null` 调用节点辅助函数（会导致渲染中断）；画布宽度按 `maxX−minX`、root 映射到 `W/2`。
3. **附录 A.1 替换为 D3.js 双侧模板**（完整可运行代码，含折叠/展开/缩放）。
4. §4.1 CDN 按层区分：顶层用 D3.js v7，底层用 ECharts。
5. §2.5 粒度规划补充「双侧布局时左右主干数量配平（差 ≤1）」。
6. §五第三步、§九示例同步更新为 D3 双侧思维导图描述。
7. §七质量清单新增「D3 双侧」检查项（左右配平、gZoom/g 分离、动态宽度等）。
**适用对象**：需要为任意领域快速构建完整、可可视化、可校验知识体系的学习者、教育者、研究者、知识工程师。
