# visual-model

> 一套面向「复杂系统 / 知识体系」的**可视化建模提示词（Prompt）规范**集合。
> A collection of visualization-modeling prompt specifications for complex systems and knowledge systems.

本仓库收录了三套相互独立、可单独使用的中文建模提示词规范，均面向「让 AI 生成高质量、可复用的 SVG / D3.js 可视化图」这一共同目标。

This repository collects three independent, ready-to-use Chinese prompt specifications, all aimed at a common goal: **getting AI to produce high-quality, reusable SVG / D3.js visualizations**.

---

## 📚 文件说明 / Contents

| 文件 File | 名称 Name | 方法 Method | 简介 Summary |
|---|---|---|---|
| [`KSB_V4.md`](./KSB_V4.md) | 知识体系构建提示词 | **KSB** · Knowledge-System-Building v3.6 | 为**任意知识领域**构建完整、可可视化、可阅读的知识体系，采用「三层递进 + 四图联动」结构，交付 Markdown 文档与多张 D3.js 交互图（中心双侧思维导图 / 多维矩阵 / 力导向知识图谱 / 学习路线图）。 |
| [`MBSE.md`](./MBSE.md) | MBSE 可视化建模提示词模板 | **MBSE** · Model-Based Systems Engineering (SysML) | 基于 SysML 标准的系统工程可视化建模指南，规范需求 / 功能 / 逻辑 / 物理 / 行为五层元素与关系，提供需求图、块定义图、内部块图、活动图、状态机图等 SVG 绘制模板。 |
| [`SBR_v2.md`](./SBR_v2.md) | 可视化建模提示词规范 | **SBR** · Structure-Behavior-Relation v2.0 | 用「结构-行为-关系」三维框架理解并建模复杂系统，规定 SVG 形状语义、1600×900 画布布局、贝塞尔曲线防交叉连接线等，使 AI 产出清晰、均衡、专业的结构图。 |

---

## 🧪 案例 / Samples

`sample/` 目录收录了基于上述规范生成的实际案例，共包含 131 个文件，覆盖交互式 HTML、SVG 图、知识图谱数据及配套 Markdown 文档：

| 目录 | 内容 |
|---|---|
| [`sample/ksb`](./sample/ksb) | 多个主题的知识体系案例，包括人工智能、金融、心理学、数学、哲学等领域的知识图谱、学习路径和可视化页面。 |
| [`sample/mbse`](./sample/mbse) | 企业架构、云原生、数字化转型、知识管理等系统的 MBSE / SysML 风格架构图。 |
| [`sample/sbr`](./sample/sbr) | 软件、业务和复杂系统的 SBR 结构-行为-关系可视化案例，包含 D3.js 交互页面与 SVG 图。 |

大多数 HTML 文件可直接下载后用浏览器打开；部分页面依赖 CDN 加载 D3.js 等前端库，预览时请保持网络连接。

The [`sample/`](./sample) directory contains practical outputs generated with these specifications: interactive HTML/D3.js pages, SVG diagrams, knowledge-graph datasets (JSON/CSV), and supporting Markdown documents. Browse the [`ksb`](./sample/ksb), [`mbse`](./sample/mbse), and [`sbr`](./sample/sbr) subdirectories for examples. HTML files can usually be opened directly in a browser; pages that load D3.js from a CDN require an internet connection.

---

## 🧭 三者关系 / How They Relate

三者覆盖不同建模对象，可单独使用，也可组合：

- **SBR**：通用「复杂系统 / 架构」可视化底座——把任何系统拆成结构、行为、关系三维度并用 SVG 表达。
- **MBSE**：面向「工程系统」的严格方法论——以 SysML 五层视图保证需求可追溯、模型一致。
- **KSB**：面向「知识领域」的体系化方法——把知识组织成由树到网的三层体系并生成可交互图谱。

> 简言之：**SBR 画系统、MBSE 画工程、KSB 画知识。**
> In short: **SBR models systems, MBSE models engineering, KSB models knowledge.**

---

## 🚀 使用方式 / How to Use

1. 选定一套规范（如 `KSB_V4.md`），直接将其全文作为 prompt 交给任意支持长上下文的 AI（Claude / ChatGPT / 通义 / 文心等）。
2. 按规范中的「前置分析」步骤先完成领域界定 / 组件抽象，再进入绘图或写作。
3. 生成结果通常为：一份 Markdown 文档 + 若干 SVG / D3.js HTML 文件。

These prompts are model-agnostic. Provide the full spec text to your AI of choice, follow its "pre-analysis" steps, then let it generate the SVG / D3.js deliverables.

---

## 📄 License

内容以 **CC BY 4.0** 发布，可自由引用、改编与再分发，请注明出处。
Released under **CC BY 4.0** — free to reuse, adapt, and redistribute with attribution.

---

## 🇨🇳 中文整体说明

`visual-model` 是我个人维护的一套**可视化建模提示词规范**合集，目标是沉淀「如何指挥 AI 画出专业、清晰、可复用图形」的方法论。

仓库内目前包含三套规范：

1. **KSB（知识体系构建）v3.6**：用于把任意知识领域整理成「顶层思维导图 → 中间层多维矩阵 → 底层知识图谱 + 学习路线图」的完整体系，并输出可交互的 D3.js 网页。适合做学习地图、领域知识沉淀、教学讲解。
2. **MBSE（基于模型的系统工程）**：基于 SysML 标准，提供需求、功能、逻辑、物理、行为五层建模元素与关系符号规范，以及需求图、块定义图、活动图、状态机图等 SVG 模板。适合工程系统、产品架构的设计与评审。
3. **SBR（结构-行为-关系）v2.0**：通用系统可视化底座，用结构 / 行为 / 关系三维框架 + 固定画布与防交叉布局规则，让 AI 稳定产出均衡、专业的结构图。适合软件架构、业务流程、AI 系统等任意复杂系统的表达。

三套规范彼此独立，可按需取用，也常配合使用：先用 SBR/KSB 做概念与结构梳理，再用 MBSE 落地到工程级严谨模型。

---

## 🇬🇧 English Overview

`visual-model` is a personal collection of **visualization-modeling prompt specifications**, aimed at documenting the methodology of "how to instruct AI to draw professional, clear, and reusable diagrams."

It currently contains three specs:

1. **KSB (Knowledge-System-Building) v3.6** — organizes any knowledge domain into a complete system: a top-level mind map → a middle multi-dimensional matrix → a bottom knowledge graph + learning path, all delivered as interactive D3.js web pages. Ideal for learning maps, domain knowledge curation, and teaching.
2. **MBSE (Model-Based Systems Engineering)** — based on the SysML standard, it specifies modeling elements and relationship symbols across five layers (requirements, functional, logical, physical, behavioral), plus SVG templates for requirement diagrams, block definition diagrams, activity diagrams, state machine diagrams, etc. Ideal for engineering-system and product-architecture design and review.
3. **SBR (Structure-Behavior-Relation) v2.0** — a general-purpose system-modeling base. Using a Structure / Behavior / Relation framework plus fixed-canvas and anti-overlap layout rules, it makes AI reliably produce balanced, professional structural diagrams. Suitable for software architecture, business processes, AI systems, and any complex system.

The three specs are independent and can be used separately or together: use SBR/KSB for conceptual and structural exploration, then MBSE to formalize into rigorous engineering-grade models.
