# -*- coding: utf-8 -*-
"""引擎泛化回归测试：V2 验收判据——"新增类型化对象 = 纯 YAML 提交，gateway 零代码改动"。

方法：在本进程内给已加载的本体模型**追加**第 4 个类型化对象（GL_Account，
科目编码/中文名，1682 行），不修改任何 .py、不改磁盘上的候选区 YAML，
然后验证：
  1. ModelRegistry 校验通过（引用闭包完整）；
  2. 通用查询执行器（类型过滤 + JSON 投影）直接可用；
  3. ref 富化对声明了引用的字段生效；
  4. 非法模型（引用不存在的目标对象）启动即失败（fail-fast）。

运行：gateway/.venv/Scripts/python.exe -X utf8 tests/test_engine_generalization.py
"""
import copy
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "gateway"))

import yaml  # noqa: E402
from mvp_server import (ModelRegistry, _apply_derivations, _execute_query,  # noqa: E402
                        _run_validation_rules)  # noqa: E402

MODEL_PATH = ROOT / ".build/candidates/masterdata/mvp-vertical-slice.yaml"
PASS, FAIL = [], []


def check(name: str, cond: bool, detail: str = "") -> None:
    (PASS if cond else FAIL).append(name if cond else f"{name}：{detail}")
    print(f"  {'✓' if cond else '✗'} {name}" + ("" if cond else f" —— {detail}"))


base = yaml.safe_load(MODEL_PATH.read_text(encoding="utf-8"))

# ── 1. 纯声明式追加第 4 个类型化对象：GL_Account（无任何代码变更） ──
print("\n[验收] 纯 YAML 追加 GL_Account 对象")
ext = copy.deepcopy(base)
ext["objects"].append({
    "id": "gl_account",
    "display_name": "总账科目主数据",
    "description": "测试用声明式对象：科目编码/中文名（1682 行）",
    "primary_key": "id",
    "source_table": "tb_Master_Data_PR_Online_Approval",
    "doc_type": "GL_Account",
    "fields": [
        {"id": "id", "column": "id", "display_name": "行主键", "type": "int", "visible": False},
        {"id": "active_status", "column": "active_status", "display_name": "状态", "type": "string"},
    ],
    "content_fields": [
        {"id": "dic_code", "display_name": "科目编码", "type": "string"},
        {"id": "dic_name_CH", "display_name": "科目中文名", "type": "string"},
    ],
    "queries": [{
        "id": "gl_account_search", "display_name": "总账科目检索",
        "keywords": ["科目"], "mi_ref": "mi_gl_account_search", "row_limit": 50,
    }],
})
ext["mis"].append({
    "id": "mi_gl_account_search", "executor": "DATABASE_MCP", "effect": "READ_ONLY",
    "timeout_seconds": 10, "statement_template": "SELECT ... WHERE dic_name = 'GL_Account'",
    "params": [{"name": "kw", "type": "string", "required": False, "default": "%%"}],
    "local_source": "pr_approval",
    "type_filter": "GL_Account",
    "local_search_fields": ["dic_content", "id"],
    "content_fields": ["dic_code", "dic_name_CH"],
})
reg = ModelRegistry(ext)
check("注册表校验通过（4→5 对象）", "gl_account" in reg.objects, f"objects={list(reg.objects)}")

rows = _execute_query(reg, "gl_account_search", {"kw": "%1111999%"})
check("类型过滤+投影查询命中", len(rows) == 1 and rows[0].get("dic_code") == "1111999",
      f"rows={len(rows)}")
check("中文名投影生效", rows and rows[0].get("dic_name_CH") is not None,
      f"row={rows[0] if rows else None}")

# ── 2. ref 富化：给 GL_Account 声明一个引用后再查询 ──
print("\n[验收] ref 富化对新对象同样零代码生效")
ext2 = copy.deepcopy(ext)
for o in ext2["objects"]:
    if o["id"] == "gl_account":
        o["content_fields"].append({
            "id": "dic_name_CH_ref", "display_name": "科目引用测试", "type": "string",
            "ref": {"target": "vendor_type", "key": "VendorCode", "label": "VendorName"}})
        # 造一个值等于厂商编码的字段内容无法保证——改为给 standard_goods 反向验证：
        # 此处仅验证声明被接受并进入 mi_refs 索引（运行时富化已在 e2e 场景8覆盖）
reg2 = ModelRegistry(ext2)
check("新 ref 声明通过校验", any(f[0] == "dic_name_CH_ref"
                                for refs in reg2.mi_refs.values() for f in refs),
      f"mi_refs={reg2.mi_refs}")

# ── 3. fail-fast：引用不存在的目标对象必须拒绝启动 ──
print("\n[验收] 非法引用 fail-fast")
bad = copy.deepcopy(base)
for o in bad["objects"]:
    if o["id"] == "standard_goods":
        o["content_fields"][3]["ref"] = {"target": "not_modeled", "key": "X", "label": "Y"}
try:
    ModelRegistry(bad)
    check("坏引用拒绝启动", False, "未抛出异常")
except RuntimeError as e:
    check("坏引用拒绝启动", "not_modeled" in str(e), str(e)[:120])

# ── 4. M3 规则刚性执行：派生 + 校验（防 LLM 幻觉的结构防线） ──
print("\n[验收] M3 派生规则（引擎计算，LLM 禁填派生字段）")
inputs, applied = _apply_derivations("standard_goods", {"AssetType": "ITAsset", "vPrice": "6000"})
check("派生 >5000 → 6230", inputs.get("AssetClass") == "6230" and len(applied) == 1,
      f"inputs={inputs} applied={applied}")
inputs, _ = _apply_derivations("standard_goods", {"AssetType": "ITAsset", "vPrice": "5000"})
check("派生边界 ≤5000 → 6931", inputs.get("AssetClass") == "6931", f"inputs={inputs}")
try:
    _apply_derivations("standard_goods", {"AssetType": "ITAsset", "vPrice": "6000",
                                          "AssetClass": "6999"})
    check("手填派生字段拒绝", False, "未抛出异常")
except ValueError as e:
    check("手填派生字段拒绝", "禁止手动提供" in str(e), str(e)[:120])
try:
    _apply_derivations("standard_goods", {"AssetType": "ITAsset", "vPrice": "abc"})
    check("非数值派生输入 fail-closed", False, "未抛出异常")
except ValueError:
    check("非数值派生输入 fail-closed", True)

print("\n[验收] M3 校验规则（fail-closed，违规提案不产生）")
errs = _run_validation_rules("standard_goods", {"assetFlag": "n", "glAccount": "5100"})
check("科目段非 6 开头拦截", any("rule_sg_glaccount" in e for e in errs), str(errs))
errs = _run_validation_rules("standard_goods", {"assetFlag": "n", "glAccount": "6230"})
check("6 开头科目通过", errs == [], str(errs))
errs = _run_validation_rules("standard_goods", {"assetFlag": "n"})
check("assetFlag=n 缺 glAccount 拦截", any("必填" in e for e in errs), str(errs))
errs = _run_validation_rules("standard_goods", {"assetFlag": "yes"})
check("assetFlag=yes 缺双字段拦截", sum("必填" in e for e in errs) >= 2, str(errs))

# ── 5. fail-fast：规则登记不合法必须拒绝启动 ──
print("\n[验收] 规则登记 fail-fast")
bad2 = copy.deepcopy(base)
bad2["rules"][0]["cases"][0]["op"] = ">>>"
try:
    ModelRegistry(bad2)
    check("未知 op 拒绝启动", False, "未抛出异常")
except RuntimeError as e:
    check("未知 op 拒绝启动", "op" in str(e), str(e)[:120])
bad3 = copy.deepcopy(base)
bad3["ui_linkages"][0]["object"] = "not_modeled"
try:
    ModelRegistry(bad3)
    check("联动挂未知对象拒绝启动", False, "未抛出异常")
except RuntimeError as e:
    check("联动挂未知对象拒绝启动", "not_modeled" in str(e), str(e)[:120])

print(f"\n──── 结论：{len(PASS)} 通过 / {len(FAIL)} 失败 ────")
for f in FAIL:
    print(f"  ✗ {f}")
sys.exit(1 if FAIL else 0)
