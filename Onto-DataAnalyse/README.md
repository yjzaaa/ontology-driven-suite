# Onto-DataAnalyse

本体驱动的电商数据智能分析系统示例。项目使用 AI 将业务需求细化为指标、数据对象、关系和规则，再生成可视化本体模型，将本体实体映射到现有数据库，执行预设分析场景，并输出带推理过程、图表和数据溯源的分析报告。

## 项目定位

这是一个可本地运行的演示系统，展示“本体作为业务语义中间层”的完整闭环：

```text
需求文档 + 数据库 Schema
          ↓
阶段一：需求探索
          ↓
阶段二：本体建模与数据库字段映射
          ↓
阶段三：预设场景执行（SQL、统计、AI 推理）
          ↓
阶段四：自然语言对话与可视化报告
```

系统不会修改业务数据库，只通过本体模型和字段映射连接数据与 AI 分析能力。当前实现使用 DeepSeek 的 OpenAI 兼容接口，API 不可用时会明确报错，不伪造 AI 结果。

## 功能

- 阶段一：上传或加载数据库 Schema 与分析需求，流式解析分析目标、对象、指标和追问
- 阶段二：生成 M1 对象、M2 行为、M3 规则、M4 场景和 M_Metric 指标模型
- 动态知识图谱：随着本体生成过程逐步显示实体与关系
- 字段级数据库映射：展示本体属性到数据库表字段的连接和置信度
- 阶段三：经营异常、GMV、客户流失三个预设分析场景
- SQL 安全控制：仅允许只读查询，限制关键字、返回行数和执行重试
- 统计分析：趋势、同比/环比、3σ 异常检测、RFM 等
- AI 推理：流式输出思考、结论、建议、置信度和图表配置
- 阶段四：自然语言调用预设场景并生成咨询报告
- 报告导出为独立 HTML 文件

## 技术栈

- 后端：Python 3.10+、Flask、Flask-CORS、python-dotenv、PyYAML、OpenAI SDK、Pydantic
- 前端：React 18、TypeScript、Vite、Axios、D3.js、ECharts、React Markdown
- 数据库：SQLite
- AI：DeepSeek Chat / Reasoner（通过环境变量配置）

## 目录结构

```text
Onto-DataAnalyse/
├─ backend/
│  ├─ app.py                  # Flask 入口
│  ├─ ai/                     # DeepSeek 客户端、Prompt 编排、场景执行、对话处理
│  ├─ api/                    # 阶段一至四和系统接口
│  ├─ config/                 # .env 与 YAML 配置加载
│  ├─ core/                   # 本体引擎、图谱、映射、SQL、统计核心算法
│  ├─ db/                     # 系统库 schema 和演示库生成脚本
│  ├─ models/default/         # 随仓库发布的默认本体模型
│  ├─ prompts/                # AI Prompt 与本体规范
│  ├─ scenarios/              # 异常、GMV、流失场景及 fallback SQL
│  ├─ data/demo_ecommerce.db  # 演示电商数据库（已包含）
│  └─ requirements.txt
├─ frontend/src/              # React 页面、组件、API 客户端和类型
├─ config/                    # 应用配置与阶段 AI 配置
├─ demo_files/                # 可在阶段一直接加载的 Schema 和需求文档
├─ docs/                      # 需求、详细设计、数据库和本体建模资料
├─ .env.example
├─ start_backend.bat
└─ start_frontend.bat
```

## 环境要求

- Python 3.10 或更高版本
- Node.js 18 或更高版本
- 可选：DeepSeek API Key，用于真实 AI 解析、建模、推理和报告生成

## 快速启动

### Windows 一键启动

在项目根目录分别打开两个终端：

```bat
start_backend.bat
```

```bat
start_frontend.bat
```

首次启动后端会创建 `.venv`、安装 Python 依赖，并在缺少演示数据库时生成数据。前端脚本会自动执行 `npm install`。浏览器访问：<http://localhost:5173>。

### 手动启动

后端：

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
python -m backend.app
```

前端（另开终端）：

```bash
cd frontend
npm install
npm run dev
```

后端默认端口为 `5000`，前端默认端口为 `5173`，Vite 会把 `/api` 请求代理到后端。

## 配置

复制 `.env.example` 为 `.env`，至少配置：

```dotenv
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_REASONING_MODEL=deepseek-reasoner
```

`.env` 已被 Git 忽略，真实密钥不得提交。还可以通过环境变量调整端口、数据库路径、SQL 最大返回行数、AI 温度和重试次数。应用和阶段模型配置分别位于 `config/app_config.yaml` 与 `config/ai_config.yaml`。

## 演示数据

`backend/data/demo_ecommerce.db` 已随项目提供，覆盖交易、商品、用户、店铺、营销、物流和退款等业务域，能够直接用于三个预设场景。数据库结构说明位于 `demo_files/ecommerce_db_schema.md`，DDL 和可重复生成脚本位于 `backend/db/demo_data/`。

系统状态库 `backend/data/system.db` 不随项目发布，首次启动时自动创建。若需要重置状态，可删除该文件；若要重新生成演示库，可删除 `demo_ecommerce.db` 后重新启动后端。

## 本体模型与文档

运行时默认模型位于 `backend/models/default/`：

- `m1_object_model.yaml`：核心业务实体与关系
- `m2_behavior_model.yaml`：分析行为
- `m3_rule_model.yaml`：业务和数据质量规则
- `m4_scenario_model.yaml`：分析场景
- `m_metric_model.yaml`：指标定义、口径和 SQL 模板
- `data_mapping.yaml`：本体到数据库字段的映射

配套资料位于 `docs/`：

- [原始需求说明](docs/原始需求说明.txt)
- [完整需求文档](docs/最终需求：电商数据智能分析系统-完整需求文档.md)
- [详细设计与实现文档](docs/详细设计与实现文档.md)
- [本体建模规范](docs/ontology_modeling_framework.md)
- [补充澄清说明](docs/第二次补充澄清的内容说明.txt)

## 测试与构建

后端语法检查：

```bash
python -m compileall backend
```

前端类型检查和生产构建：

```bash
cd frontend
npm run build
```

## 安全边界

- 只读 SQL 执行器拒绝数据写入、DDL、多语句和危险关键字
- AI 生成 SQL 会经过校验、试运行和有限次数重试
- 场景 YAML 提供 fallback SQL，但不会绕过只读校验
- `.env`、虚拟环境、Node 依赖、构建产物和系统状态库不会提交
- 发布前请确认 `.env.example` 仍为占位符，并更换生产环境的密钥和访问策略

## License

本项目采用 [MIT License](LICENSE) 开源许可。你可以自由使用、复制、修改、合并、发布和再许可本项目，但须保留版权声明和许可声明。

---

## English

Onto-DataAnalyse is an ontology-driven e-commerce analytics demo. AI first turns business questions into metrics, entities, relationships, and rules; the system then generates ontology models, maps ontology fields to an existing database, executes analysis scenarios, and produces traceable reports with charts and reasoning details.

### Highlights

- Four-stage workflow: requirement exploration, ontology modeling, scenario execution, and conversational reporting
- M1/M2/M3/M4/M_Metric ontology models with YAML persistence
- Dynamic ontology graph and field-level database mapping visualization
- Preset GMV, churn, and anomaly analysis scenarios
- Read-only SQL validation with allowlists, row limits, and retry controls
- Streaming DeepSeek responses, structured reasoning, confidence, charts, and HTML export
- Bundled SQLite demo database and reproducible data-generation scripts

### Quick Start

Requirements: Python 3.10+, Node.js 18+, and an optional DeepSeek API key.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
python -m backend.app
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. The backend runs on port `5000` by default. Windows users can also run `start_backend.bat` and `start_frontend.bat`.

Set `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL`, and `DEEPSEEK_REASONING_MODEL` in `.env`. The file is ignored by Git and must never contain committed credentials.

### Project Resources

The demo database is `backend/data/demo_ecommerce.db`. Database design, requirements, implementation details, and ontology modeling guidance are available under `demo_files/`, `backend/db/`, `backend/prompts/`, and `docs/`. The default ontology models and fallback scenario definitions are included in the repository so the project can run independently after cloning.

### License

This project is released under the [MIT License](LICENSE). You may use, copy, modify, merge, publish, and sublicense the project, provided that the copyright and license notices are preserved.
