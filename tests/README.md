# tests/

模型契约、集成和端到端验收测试。

## 当前内容

| 文件 | 类型 | 覆盖 |
|---|---|---|
| `e2e_mvp_vertical_slice.py` | 端到端验收 | MVP 竖切九场景（LLM 意图解析 → 治理读 → HITL 提案/批准 → 读写自洽 → 语义护栏 → V2 类型化查询） |
| `test_engine_generalization.py` | 引擎回归 | **V2 验收判据**："新增类型化对象 = 纯 YAML 提交，gateway 零代码改动"；M3 规则刚性执行（派生/校验/手填拒绝）；非法引用与规则登记 fail-fast |

## 运行端到端验收

```bash
# 1. 启动网关（另一终端）
gateway/.venv/Scripts/python.exe -m uvicorn mvp_server:app --app-dir gateway --port 8000

# 2. 运行验收（九个测试问题自动执行）
gateway/.venv/Scripts/python.exe -X utf8 tests/e2e_mvp_vertical_slice.py
```

### 九个测试问题（脚本自动执行）

| # | 输入 | 断言 |
|---|---|---|
| 1 | 帮我查一下 9305733 这个主数据文档 | LangGraph 编排生效；返回非空结果表且字段完整 |
| 2 | 请把 9305733 停用 | HIGH 提案卡；批准 → SUCCEEDED；local_json 模式下执行码=LOCAL_SANDBOX_APPLIED（诚实码，不伪装真实写） |
| 3 | 9305733 这条文档现在什么状态？ | 状态=Inactive（**读写自洽**：批准结果对查询可见） |
| 4 | 帮我把 9305733 重新启用了 | 口语化解析为启用；批准后基线恢复 Active |
| 5 | 把 9305733 删掉 | **语义护栏**：删除不在可用动作内 → 不产生提案、返回未识别意图 |
| 6 | 今天天气怎么样 | 越界输入 → 不产生提案、返回未识别意图 |
| 7 | 查厂商 9305733 | V2 类型化视图（厂商类型）；VendorCode/VendorName/VendorType 投影完整 |
| 8 | 查商品 芝士 | 标准商品视图；内容字段检索命中；类型化列（目录编码/单价/资产分类）；vendorCode→vendorName 富化引用生效 |
| 9 | 查预算 FY23_Ext testing | 预算参考号视图；预算三件套（Budget/Used/Remaining）投影完整 |

## 运行引擎回归（无需网关，进程内执行）

```bash
gateway/.venv/Scripts/python.exe -X utf8 tests/test_engine_generalization.py
```

验证四件事：
1. **纯 YAML 新增对象**：进程内给模型追加第 4 个类型化对象 GL_Account（不修改任何
   .py），注册表校验通过、类型过滤+JSON 投影查询直接可用；
2. **ref 富化零代码生效**：新声明的引用字段自动进入富化索引（运行时富化由 e2e 场景 8 覆盖）；
3. **M3 规则刚性执行**：派生规则由引擎计算（手填派生字段拒绝、非数值输入 fail-closed）；
   校验规则 fail-closed（科目段 6 开头、条件必填）——防 LLM 幻觉写入的结构防线；
4. **fail-fast**：引用未建模对象、规则未知 kind/op、联动挂未知对象，启动即拒。

### 纪律

- **安全护栏**：`GATEWAY_WRITE_MODE` 必须为 `local_json` 才能运行 e2e（脚本产生真实写提案）；
  要在 `dpa_http` 模式下验收需显式 `E2E_ALLOW_DPA=1`——绝不允许无意写真实 DPA。
- **LLM 可选**：`.env` 未配置 `LLM_*` 时场景 1/3/4 的输入措辞同时兼容目录路由；
  场景 5/6 断言对两种路由均成立；场景 7-9 的触发词（厂商/商品/预算）来自本体 YAML 声明，
  两种路由均可命中。
- **幂等**：场景 4 结束时恢复文档基线状态（Active），可重复运行。
- 场景 5 由 gpt-5 语义护栏保障（意图解析提示词：动作目录之外的动词一律 none，
  禁止猜测近似动作）；若换用其他模型，请重跑场景 5 验证护栏仍然生效。
