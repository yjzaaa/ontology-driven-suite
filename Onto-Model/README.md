# Onto-Model

本体模型可视化查看与维护工具。项目提供一个 Flask + React 的 Web 编辑器，用于打开一组 YAML 本体模型文件，浏览模型树和知识图谱，查看定义与引用关系，执行跨文件校验，并将修改保存回原有 YAML 文件。

## 项目定位

Onto-Model 面向采用本体驱动软件建模方法的研发和分析团队，重点解决以下问题：

- 多文件 YAML 本体模型的统一浏览
- 对象、行为、规则、事件、场景和主体之间的引用关系展示
- 定义节点与引用节点的区分
- 跨文件引用校验和删除影响分析
- 在不改变 YAML 扩展字段的情况下编辑和保存模型
- 使用 D3.js 动态生成本体知识图谱

这是一个本地开发工具，不包含登录系统、数据库或云端存储。模型文件本身是持久化载体。

## 功能

### 模型浏览

- M1 对象模型：实体、聚合、属性、关系和约束
- M2 行为模型：行为定义、归属对象、前后置条件和规则引用
- M3 规则模型：业务规则、校验规则和计算规则
- ME 事件模型：生产者、订阅者和事件链
- M4 场景模型：用例、流程和行为引用
- M5 主体模型：主体、角色和权限

### 编辑与校验

- 树状模型导航和多标签编辑
- 实体、行为、规则、事件、用例、主体等编辑器
- 定义与引用分离，避免重复修改同一模型元素
- 全局实体 ID、行为归属、规则引用、事件链和主体权限引用校验
- 查找引用关系并分析删除影响
- 保留 `description`、`remark`、`notes` 以及未知扩展字段
- 保存前自动校验，校验通过后写回对应 YAML 文件

### 知识图谱

前端使用 D3.js Canvas 绘制模型关系图，支持节点分类筛选、缩放、拖拽和关系连线。图谱关系来自对象模型显式关系、聚合组合关系、行为归属、规则应用、事件生产/订阅以及场景行为引用。

## 技术栈

- 后端：Python 3.8+、Flask、Flask-CORS、PyYAML
- 前端：React 18、TypeScript、Vite、Ant Design、D3.js、Axios
- 数据格式：YAML
- API：JSON over HTTP

## 目录结构

```text
Onto-Model/
├─ backend/
│  ├─ app.py                         # Flask 入口
│  ├─ routes/                        # 工作区、校验、引用分析接口
│  ├─ services/                      # 文件、YAML、工作区、校验和引用服务
│  └─ requirements.txt
├─ frontend/
│  ├─ public/                        # 静态入口
│  ├─ src/
│  │  ├─ components/                 # 模型树、知识图谱和模型编辑器
│  │  ├─ services/                   # API 客户端、模型索引和图谱构建
│  │  └─ types/                      # TypeScript 类型定义
│  ├─ package.json
│  └─ package-lock.json
├─ sample/                           # 从原 sample-new 整理的当前示例模型
├─ docs/
│  ├─ requirements/                  # 需求和组件/API 设计资料
│  ├─ ARCHITECTURE.md                # 系统架构说明
│  └─ KNOWLEDGE_GRAPH.md             # 知识图谱说明
├─ .gitignore
└─ README.md
```

## 关于 sample 和 sample-new

原项目同时存在两个示例目录：

- `sample/`：旧版合同管理模型，包含旧格式模型、静态 HTML 和历史说明，不再作为当前实现的基准。
- `sample-new/`：新版模型，使用当前前端和后端支持的聚合对象结构及 `me-event-model.yaml` 文件名。

整理后的仓库只保留 `sample-new` 的内容，并将其重命名为 `sample`，作为唯一官方示例。代码没有硬编码示例目录，用户可以打开任意包含支持的 YAML 文件的工作区。

## 环境要求

- Python 3.8 或更高版本
- Node.js 16 或更高版本
- npm

## 启动后端

在项目根目录打开终端：

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

后端默认监听 `http://localhost:5000`。

## 启动前端

另开一个终端：

```bash
cd frontend
npm install
npm run dev
```

前端使用 Vite 启动，默认监听 `http://localhost:3000`。如果 3000 端口已被占用，Vite 会自动选择下一个可用端口并在终端输出实际地址。也可以指定端口：macOS/Linux 使用 `npm run dev -- --port 3100`，Windows PowerShell 使用 `npm run dev -- --port 3100`，Windows CMD 使用 `npm run dev -- --port 3100`。前端 API 客户端默认请求 `http://localhost:5000/api`，因此启动前端前请确保后端已经运行。

生产构建使用 `npm run build`，本地预览使用 `npm run preview`，类型检查使用 `npm run typecheck`。

本项目不再提供安装或启动 BAT 文件，开发者按上述命令手工启动即可。

## 使用示例

1. 打开终端中提示的前端地址（通常是 <http://localhost:3000>）。
2. 点击“打开工作区”。
3. 输入示例模型目录的绝对路径，例如：

   ```text
   E:/BaiduDownload/github/Onto-Model/sample
   ```

4. 在左侧模型树中浏览对象、行为、规则、事件、场景和主体。
5. 点击节点查看详情或打开编辑器。
6. 使用顶部的校验功能检查跨文件引用。
7. 保存前确认校验结果，再将修改写回 YAML 文件。

### 工作区支持的文件

后端会按以下文件名读取模型；事件模型兼容 `me-event-model.yaml` 和旧版 `event-model.yaml`：

```text
m1-object-model.yaml
m2-behavior-model.yaml
m3-rule-model.yaml
m4-scenario-model.yaml
m5-actor-model.yaml
me-event-model.yaml
```

## API 接口

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/workspace/open` | 打开并解析一个模型目录 |
| `POST` | `/api/workspace/save` | 校验并保存工作区 |
| `GET` | `/api/workspace/current` | 获取当前工作区 |
| `POST` | `/api/validation/run` | 执行完整跨文件校验 |
| `POST` | `/api/references/find` | 查找指定节点的引用 |
| `POST` | `/api/references/delete-impact` | 分析节点删除影响 |

## 开发说明

- 后端使用内存中的工作区副本处理请求，保存时才写回 YAML。
- `WorkspaceService` 支持绝对路径、当前进程相对路径和项目根相对路径。
- 前端通过 `modelIndex.ts` 统一解析模型节点，通过 `graphBuilder.ts` 构建图谱节点和边。
- 校验逻辑集中在 `backend/services/validation_service.py`，引用索引集中在 `reference_service.py`。
- 生产部署时建议使用 WSGI 服务器和反向代理，并限制可打开的工作区路径。

## 资料

- [本体模型编辑器前端页面与组件设计](docs/requirements/本体模型编辑器前端页面与组件设计.txt)
- [Flask API 与文件服务设计](docs/requirements/本体模型编辑器Flask_API与文件服务设计.txt)
- [本体模型维护需求](docs/requirements/本体模型维护需求.txt)
- [本体模型维护需求 V2](docs/requirements/本体模型维护需求V2.txt)
- [原始需求和 AI 对话](docs/requirements/原始需求和AI的对话.txt)
- [本体建模规范](docs/requirements/ontology_modeling_framework.md)
- [系统架构](docs/ARCHITECTURE.md)
- [知识图谱](docs/KNOWLEDGE_GRAPH.md)

## License

本项目采用 [MIT License](LICENSE) 开源。您可以自由使用、复制、修改、合并、发布和再许可本项目，但须保留原版权声明和许可声明。

---

## English Summary

Onto-Model is a local web editor for ontology model files. It provides YAML workspace browsing, model-tree navigation, D3.js knowledge-graph visualization, cross-file reference validation, delete-impact analysis, and round-trip editing without losing extension fields.

The repository uses the current `sample-new` model set as its only `sample` directory. The legacy `sample` directory, dependency installations, build output, logs, archives, and batch scripts are intentionally excluded.

### Manual startup

```bash
cd backend
python -m venv .venv
# Activate the environment, then:
pip install -r requirements.txt
python app.py
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the frontend URL printed by the terminal (normally <http://localhost:3000>). If port 3000 is occupied, Vite automatically selects the next available port. To choose a port, run `npm run dev -- --port 3100`. Use `npm run build` for a production build, `npm run preview` to preview it locally, and `npm run typecheck` for TypeScript checking. The backend API runs on port `5000`. Use the “Open Workspace” action and select the bundled `sample` directory or any compatible model directory.
