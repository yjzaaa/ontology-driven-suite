# Onto-Contract

本体驱动的 AI 原生合同管理系统示例。项目将合同领域的对象、行为、规则、事件、场景和 UI 元数据以 YAML 本体模型描述，由 Flask 后端加载并为固定业务页面、只读语义查询和 AI 对话提供统一的领域上下文。

## 功能概览

- 合同录入、查询与详情查看
- 合同开票录入、收款登记
- 基于本体注册表的领域元数据与知识查询
- DeepSeek Function Calling 与 SSE 流式 AI 对话
- 严格只读的动态 SQL 查询（白名单表、字段、行数和连接数限制）
- SQLite 示例数据库和默认演示数据

## 技术栈

- 后端：Python 3.11+、Flask、SQLite、PyYAML、Requests
- 前端：React 18、TypeScript、Vite、ECharts、Framer Motion、Lucide
- 本体模型：`models/contract/*.yaml`

## 目录结构

```text
Onto-Contract/
├─ backend/
│  ├─ app/                 # Flask 应用、AI 编排、本体加载和业务服务
│  ├─ scripts/             # 语义查询与 LLM 编排冒烟测试
│  ├─ requirements.txt
│  └─ run.py
├─ frontend/
│  ├─ src/                 # React 前端源码
│  ├─ package.json
│  └─ vite.config.ts
├─ data/contract.db        # SQLite 示例数据库
├─ models/contract/         # 随项目发布的合同领域本体 YAML
├─ AI原生应用技术架构设计文档.md
├─ deepseek.config.example.yaml
└─ .gitignore
```

## 快速开始

### 1. 配置 DeepSeek（可选）

```powershell
Copy-Item deepseek.config.example.yaml deepseek.config.yaml
```

编辑 `deepseek.config.yaml`，填入自己的 `ai.api_key` 和随机的 `app.secret_key`。该文件已被 `.gitignore` 忽略，不应提交真实密钥。

未配置 API Key 时，固定业务页面仍可运行，AI 对话会使用本地规则兜底能力。

### 2. 启动后端

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py
```

后端默认监听 `http://127.0.0.1:5000`。

### 3. 启动前端

另开一个终端：

```powershell
cd frontend
npm install
npm run dev
```

前端默认地址为 `http://127.0.0.1:5173`，Vite 会将 `/api` 请求代理到后端。

默认演示账号：`admin` / `ChangeMe123!`。首次运行后请在实际部署中修改默认凭据和密钥。

## 测试

在后端虚拟环境中执行：

```powershell
cd backend
python scripts/run_semantic_query_smoketests.py
python scripts/run_llm_orchestration_smoketests.py
```

前端构建检查：

```powershell
cd frontend
npm run build
```

## 本体模型

`models/contract` 中的 YAML 文件分别描述对象、行为、规则、场景、角色、补偿、质量、事件和 UI 模型。后端启动时会自动加载该目录并构建 `OntologyRegistry`。路径由 `backend/app/config.py` 基于仓库根目录解析，因此项目可以独立复制或克隆，不依赖上级目录。

## 数据与安全说明

- `data/contract.db` 是用于本地演示的 SQLite 数据库，不应直接用于生产环境。
- `deepseek.config.yaml` 可能包含 API 密钥，已加入忽略规则。
- 生产部署前请更换默认管理员密码、Flask secret key，并根据实际场景配置数据库和访问控制。

## License

本项目采用 [MIT License](LICENSE) 开源许可。你可以自由使用、复制、修改、合并、发布和再许可本项目，但须保留版权声明和许可声明。

---

## English

Onto-Contract is an ontology-driven, AI-native contract management system. Contract objects, behaviors, rules, events, scenarios, and UI metadata are modeled as YAML files. The Flask backend loads these models into a shared `OntologyRegistry` used by business pages, read-only semantic queries, and the AI assistant.

### Features

- Contract creation, search, and detail views
- Invoice entry and payment receipt recording
- Ontology registry metadata and domain knowledge queries
- DeepSeek Function Calling with SSE streaming responses
- Strict read-only dynamic SQL with table/column allowlists and row/join limits
- SQLite demo database with sample reference and contract data

### Technology

- Backend: Python 3.11+, Flask, SQLite, PyYAML, Requests
- Frontend: React 18, TypeScript, Vite, ECharts, Framer Motion, Lucide
- Ontology models: `models/contract/*.yaml`

### Quick Start

1. Optional DeepSeek configuration:

   ```powershell
   Copy-Item deepseek.config.example.yaml deepseek.config.yaml
   ```

   Set `ai.api_key` and a random `app.secret_key` in the copied file. The local configuration is ignored by Git and must never be committed.

2. Start the backend:

   ```powershell
   cd backend
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   python run.py
   ```

   The backend listens on `http://127.0.0.1:5000` by default.

3. Start the frontend in another terminal:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

   Open `http://127.0.0.1:5173`. Vite proxies `/api` requests to the backend.

The demo account is `admin` / `ChangeMe123!`. Change the default credentials and secret key before any real deployment. Without a DeepSeek key, fixed business pages continue to work and the AI page uses local fallback rules.

### Tests

Run backend smoke tests inside the virtual environment:

```powershell
cd backend
python scripts/run_semantic_query_smoketests.py
python scripts/run_llm_orchestration_smoketests.py
```

Build the frontend with:

```powershell
cd frontend
npm run build
```

### Repository Independence

All runtime ontology YAML files are bundled under `models/contract`. The backend resolves the database, model directory, and bundled architecture document from the repository itself, so a clone does not depend on files from a parent directory. The included `data/contract.db` is for local demonstration only.

### License

This project is released under the [MIT License](LICENSE). You may use, copy, modify, merge, publish, and sublicense the project, provided that the copyright and license notices are preserved.
