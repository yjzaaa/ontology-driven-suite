# Onto-AppGen 实施计划

> 核心共识（已与用户逐条对齐）：
> - **最终产物 = 数据**（本体 YAML M1~M5+ME + Schema JSON），不是代码；数据是唯一真相源。
> - **固定引擎解释执行**：引擎只写一份、住工作台内，读数据 → 建库 → 行为 API → 渲染；改业务改数据不改代码。
> - **换技术栈/老系统无 API，都不重写本体**：差异封在 connector 层，本体不变。

---

## 第一阶段 · 平台内跑（本轮实现）

**目标**：跑通「数据产物 → 固定引擎解释执行 → 固定渲染器」最小闭环，在 DSH 里通过薄插件层挂载可用。

> ✅ **已完成**（2026-09-05）：见下方「第一阶段完成情况」。

### 要做的改造（把"生成独立 app.cjs"收敛为"固定引擎 + 数据"）

1. **引擎固定化** —— 新增 `engine/engine.cjs`（node:sqlite + node:http）
   - 启动时 `--project <path>` 指向某项目目录，读该项目的 `yaml/*.yaml` + `app.schema.json`；
   - 建库 + 行为 API（前置条件/后置条件状态机）+ serve 渲染器；
   - **不再每项目生成一份 app.cjs**。

2. **渲染器固定化** —— `engine/renderer.html`（React + antd，本地 serve）
   - 从"每项目复制"改为"引擎内固定一份，运行时注入 schema"。

3. **产物 = 数据** —— 项目目录只留：
   ```
   <workspace>/.workbuddy/ontology/<项目>/
     ├─ yaml/*.yaml          # 本体模型（唯一真相源）
     └─ app.schema.json      # 应用描述（LLM 生成，被校验）
   ```

4. **SDK 收敛**（`src/`）：
   - `types.ts`（协议）/ `validator.ts`（校验）保留；
   - 生成器从"拼 app.cjs + renderer.html"改为**只产 `app.schema.json`**（schema 落盘，引擎运行时读）。

5. **DSH 插件层**（`dsh-plugin/`）：
   - 保留 `ontology_app` 工具（validate / generate / read），补 `run`（spawn 固定引擎 + 返回 URL）。

6. **端到端验证**：用 `workbench-v3` 或 device-repair 本体 → 生成 schema → 校验 → 固定引擎启动 → 行为 API + 渲染实测。

### 第一阶段验收标准
- 项目目录里**没有 app.cjs / renderer.html 副本**，只有 yaml + schema 数据；
- 引擎一份、按 `--project` 切数据，行为 API 前置条件拦截生效；
- DSH 插件层 `ontology_app` 的 validate/generate/run 可用；
- 浏览器能渲染出多页面应用、下拉从主数据取数。

### 第一阶段完成情况（2026-09-05，已验收）

| 验收标准 | 结果 |
|---|---|
| 产物=数据、无代码副本 | ✅ `app/` 只含 `tables.json` / `behaviors.json` / `app.schema.json`，无 app.cjs/renderer.html |
| 固定引擎 | ✅ `engine/engine.cjs` 零第三方依赖（node:sqlite + node:http），按 `--project` 读数据切应用 |
| 固定渲染器 | ✅ `engine/renderer.html` 固定一份，运行时注入 schema（React+antd） |
| 行为 API 受控写回 | ✅ 前置条件拦截（`RULE-*`）、主键自动编号、postconditions 生效（实测 `AppSchema-0001`） |
| 插件层 | ✅ `ontology_app` validate/generate/run 全链路实测通过 |
| 浏览器渲染 | ✅ Puppeteer 实测多页面 UI 渲染、零错误 |
| SDK 单测 | ✅ `tests/sdk.spec.ts` 5/5 通过 |

**产物目录约定（第一阶段）**：`<workspace>/.workbuddy/ontology/<项目>/app/` 只放数据（tables/behaviors/schema JSON），**不再含任何代码文件**；引擎与渲染器固定在 `engine/`，按项目切数据运行。

---

## 迭代 · Formily 渲染升级（本轮实现）

**目标**：渲染层从手写控件映射升级为 **Formily**（阿里 JSON Schema 驱动表单引擎，12567★，React+antd 深度集成）。LLM 生成的 App Schema（页面组织）不变，仅把**字段级表单渲染**换成 Formily，获得控件联动（reactions）/校验/布局/变体能力。

### 集成思路（两层协议，互补不冲突）

```
App Schema（我们的协议，不变）           Formily Schema（渲染层，新）
├─ 页面/Block/行为绑定（业务语义）  →    └─ 字段级：控件类型/联动/校验/布局
└─ 字段定义（name/label/control/ref）      （由 toFormilySchema 转换器生成）
```

### 技术路线

- **引入方式**：~~CDN UMD~~ → **本地构建**（关键验证：Formily UMD 有 peer 依赖问题，`Subscribable`/`ReactIs` 缺失、浏览器跑不起来；必须 npm 装 + Vite 打包，依赖全解析）。顺带完成第二阶段「渲染资源本地化」。
- **构建产物**：`frontend/`（Vite + React + antd + Formily）→ 构建为 `engine/renderer-dist/` 静态 bundle；`engine.cjs` serve 该 bundle + 注入 schema。
- **转换器**：`toFormilySchema(appSchemaField) → Formily Schema`：
  - control: select/input/textarea/date/datetime/radio/number → `x-component: Select/Input/Input.TextArea/DatePicker(+showTime)/Radio.Group/InputNumber`
  - required → `required: true`
  - options（枚举）→ `enum: [...]`
  - refTable（引用）→ 预拉数据注入 `enum` 或 `dataSource`
- **替换点**：FormBlock 表单部分用手写 Control 换成 Formily `<SchemaField>`；TableBlock 仍用 antd Table（或用 Formily ArrayTable，后续）。

### 实施步骤

1. 建 `frontend/`：Vite + React + antd + Formily（npm 装 @formily/core/react/antd）。
2. 写 SchemaRenderer 组件 + `toFormilySchema` 转换器（App Schema Field → Formily Schema）。
3. FormBlock 用 Formily `<SchemaField>` 渲染；引用字段预拉数据注入；TableBlock 仍 antd Table。
4. Vite 构建 → `engine/renderer-dist/`；`engine.cjs` serve bundle + 注入 schema。
5. 用 workbench-v3 / device-repair 实测：控件联动、校验、布局质量；对比手写版。

### 验收标准

- FormBlock 用 Formily 渲染（非手写控件），构建产物本地化（无 CDN 依赖）；
- 引用下拉/枚举下拉/日期/单选等控件正常；
- 必填校验生效（Formily validate）；
- 渲染质量（布局/交互）优于手写版。

### Formily 迭代完成情况（2026-09-05，已验收）

**关键技术验证**：Formily UMD 有 peer 依赖问题（`Subscribable`/`ReactIs` 缺失）跑不起来 → 改**本地构建**；`@formily/antd` 仅支持 antd v4 → 换 **`@formily/antd-v5@1.2.4`**（v5 适配包）；`SchemaField` 由 `createSchemaField()` 工厂创建。

| 验收标准 | 结果 |
|---|---|
| FormBlock 用 Formily 渲染 | ✅ `frontend/src/FormBlock.tsx` 用 `createSchemaField` + `<SchemaField>` |
| 构建产物本地化（无 CDN） | ✅ `frontend/`（Vite）→ `engine/renderer-dist/`（index.html + renderer.js，含 React+antd+Formily） |
| 必填校验（Formily validate） | ✅ Puppeteer 实测：空提交三字段内联报错「该字段是必填字段」 |
| **控件联动（x-reactions）** | ✅ Field 加 `visibleWhen` → `x-reactions`+`x-display`；实测：选"硬件故障"显示、选其他隐藏故障描述字段 |
| 渲染质量优于手写版 | ✅ Formily FormItem/FormLayout（必填星号、标签布局、内联校验、联动）替代手写 Control |
| SDK 单测不破坏 | ✅ 5/5 通过 |

**engine.cjs 变更**：serve `renderer-dist/` 静态 bundle（含 MIME 映射 + 路径穿越防护），index.html 运行时注入 schema；删除旧 `engine/renderer.html`（CDN 版）。

---

## 第二阶段 · 生产对接（未来 TODO，本轮不实现）

1. **connector 适配层**（老系统触达分级）：
   - ① API 编排 ② DB 直连（谨慎+审计） ③ RPA 界面自动化 ④ 人工作业降级（待办+回填）；
   - connector 可复用模板，本体/YAML 不变，换实现只在 connector 层。

2. **审批流（M6 流程模型）**：执行前审批、谁批、批什么。

3. **决策记忆**：每次 action + 谁批准 + 结果写回，成为下次判断上下文。

4. **沙盘推演**：候选方案比较连锁影响，再受控执行。

5. **失败补偿**：把 M2 `compensationRef` 从字段变成运行时真执行的回滚。

6. **文件 SQLite 持久化**：数据落盘，重启不丢（替代内存库）。

7. **渲染资源本地化**：去 CDN/Babel 依赖，React/antd 随引擎本地托管（离线可用）。

8. **原生融合**（终态）：SchemaRenderer 作为 DSH 前端组件，应用走 apiproxy，与建模/图谱同一套 RPC，不再有第二个 HTTP 端点/iframe。

---

## 技术栈约定

- 引擎：Node 22+ 内置 `node:sqlite` + `node:http`，零第三方运行时依赖。
- SDK：TypeScript，仅 `js-yaml` 读模型。
- 渲染器：React 18 + Ant Design 5（与 Onto-Model 前端同栈）。
- DSH 侧：薄插件层通过 `--patch` 挂载，核心不写入 DSH 源码。