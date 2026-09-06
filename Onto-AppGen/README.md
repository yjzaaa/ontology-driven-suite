# Onto-AppGen

Schema 驱动的应用生成器 —— 本体工作台 V3 的落地项目（独立项目，不写入 DSH 源码）。

## 定位

LLM 读取本体模型（M1~M5+ME）后，自行决定前端页面如何组织，输出一份
**App Schema（页面组织决议）**；本项目提供确定性执行层：

- **协议 meta-schema**：定义 App Schema 长什么样（页面/Block/字段/列/操作）
- **校验器**：引用 entity/behavior/refTable 指回模型、控件合法、id 唯一、跳转存在
- **渲染器**：React + antd，按 schema 渲染多页面应用（与 Onto-Model 前端同栈）
- **运行时**：node:sqlite CRUD + 行为 API（M2 前置/后置条件驱动状态流转）
- **生成器**：模型 + schema → 可运行自包含应用（app/ 目录）

## Dogfood

本项目自身按「本体建模 → 生成应用」流程开发：
- 本体模型：`model/`（对应本体工作台 workbench-v3 项目，见 `.workbuddy/ontology/workbench-v3/`）
- 执行层代码由模型驱动实现（M2 行为 = 校验/API 生成/渲染/生成/运行）

## 目录

```
model/            本体模型 YAML（M1~M5+ME，工作台 V3 自身）
src/              执行层（校验器/渲染器模板/运行时模板/生成器）
app/              生成的应用产物（app.cjs + renderer.html + app.schema.json）
scripts/          Dogfood 端到端验证脚本
docs/             设计文档
```
