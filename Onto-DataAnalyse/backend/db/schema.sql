-- ===== 系统库 schema =====
-- 项目表（本系统固定单一默认项目 'default'）
CREATE TABLE IF NOT EXISTS projects (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT,
    current_stage   INTEGER DEFAULT 1,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    db_schema_doc   TEXT,                  -- 阶段一上传的 DB Schema 原文
    requirement_doc TEXT,                  -- 阶段一上传的需求 原文
    requirement_doc_parsed TEXT,           -- 阶段一 AI 解析后的结构化 JSON
    ontology_data   TEXT,                  -- 阶段二 M1/M2/M3/M4/M_Metric 内容摘要
    mapping_data    TEXT,                  -- 阶段二本体→DB 映射配置 JSON
    stage_status    TEXT DEFAULT '{"1":false,"2":false,"3":false,"4":false}'
);

-- 对话会话表（阶段四使用）
CREATE TABLE IF NOT EXISTS chat_sessions (
    id          TEXT PRIMARY KEY,
    project_id  TEXT NOT NULL,
    title       TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

-- 对话消息表
CREATE TABLE IF NOT EXISTS chat_messages (
    id              TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL,
    role            TEXT NOT NULL,        -- user / assistant
    content         TEXT NOT NULL,
    message_type    TEXT DEFAULT 'text',  -- text / report
    report_data     TEXT,                 -- JSON：完整报告
    reasoning_data  TEXT,                 -- JSON：推理过程
    created_at      TEXT NOT NULL
);

-- 场景执行记录表（阶段三）
CREATE TABLE IF NOT EXISTS execution_records (
    id              TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL,
    scenario_id     TEXT NOT NULL,
    status          TEXT DEFAULT 'running',   -- running / completed / failed
    steps_data      TEXT,                     -- JSON：各步骤数据
    report_data     TEXT,                     -- JSON：最终报告
    started_at      TEXT NOT NULL,
    completed_at    TEXT
);
