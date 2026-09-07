# -*- coding: utf-8 -*-
"""ActionEngine 测试：typed 校验 / 规则阻断 / 提案生成 / 写回（零额外依赖，直接 python 跑）。

运行：python test_engine.py
"""
from engine import ActionEngine, PolicyError, load_engine

# 本地沙箱数据（id/dic_name/dic_type/ids 供定位与 JMESPath 取用）
LOCALDB = {
    "pr_approval": [
        {"id": "9305733", "dic_name": "Vendor_type", "dic_type": "Vendor_type",
         "active_status": "Active", "ids": [9305733]},
        {"id": "9999", "dic_name": "ESN", "dic_type": "ESN",
         "active_status": "Active", "ids": [9999]},
    ]
}


def fresh_engine() -> ActionEngine:
    return load_engine("models", LOCALDB)


def test_typed_input_valid():
    eng = fresh_engine()
    p = eng.run({"record_id": "9305733", "active_status": "Inactive"}, ctx={"thread_id": "t1", "actor": "admin"})
    assert p["state"] == "PENDING_APPROVAL", p
    print("PASS test_typed_input_valid")


def test_typed_input_invalid_enum():
    eng = fresh_engine()
    try:
        eng.run({"record_id": "9305733", "active_status": "Enabled"}, ctx={})
        raise AssertionError("非法枚举未拦截")
    except Exception as e:
        assert "active_status" in str(e) or "is not one of" in str(e) or "enum" in str(e), str(e)
    print("PASS test_typed_input_invalid_enum")


def test_typed_input_missing_required():
    eng = fresh_engine()
    try:
        eng.run({"record_id": "9305733"}, ctx={})
        raise AssertionError("缺必填未拦截")
    except Exception as e:
        assert "required" in str(e) or "active_status" in str(e), str(e)
    print("PASS test_typed_input_missing_required")


def test_typed_input_additional_property_blocked():
    eng = fresh_engine()
    try:
        eng.run({"record_id": "9305733", "active_status": "Inactive", "credential": "hack"}, ctx={})
        raise AssertionError("额外字段未拦截（additionalProperties: false）")
    except Exception as e:
        assert "credential" in str(e) or "Additional" in str(e), str(e)
    print("PASS test_typed_input_additional_property_blocked")


def test_rule_blocks_forbidden_type():
    """禁止更新的子表类型（ESN）被 M3 规则阻断。"""
    eng = fresh_engine()
    try:
        eng.run({"record_id": "9999", "active_status": "Inactive"}, ctx={})
        raise AssertionError("禁止更新类型未被规则阻断")
    except PolicyError as e:
        assert "禁止更新" in str(e), str(e)
    print("PASS test_rule_blocks_forbidden_type")


def test_proposal_payload_jmespath_composed():
    """提案的 form 是 JMESPath 从 {input, target} 组合出的 DPA 载荷。"""
    eng = fresh_engine()
    p = eng.run({"record_id": "9305733", "active_status": "Inactive"}, ctx={"thread_id": "t1", "actor": "admin"})
    form = p["form"]
    assert form["ActiveStatu"] == "Inactive", form        # ← input.active_status
    assert form["DicType"] == "Vendor_type", form          # ← target.dic_type
    assert form["JsonIds"] == [9305733], form              # ← target.ids
    print("PASS test_proposal_payload_jmespath_composed")


def test_writeback_requires_approval():
    eng = fresh_engine()
    p = eng.run({"record_id": "9305733", "active_status": "Inactive"}, ctx={})
    try:
        eng.writeback_on_approval(p["proposal_id"])
        raise AssertionError("未审批不应允许写回")
    except PolicyError as e:
        assert "已批准" in str(e) or "APPROVED" in str(e), str(e)
    print("PASS test_writeback_requires_approval")


def test_writeback_after_approval():
    eng = fresh_engine()
    p = eng.run({"record_id": "9305733", "active_status": "Inactive"}, ctx={})
    eng.approve(p["proposal_id"], actor="approver")
    receipt = eng.writeback_on_approval(p["proposal_id"])
    assert receipt["status"] == "SUCCEEDED", receipt
    assert receipt["code"] == "LOCAL_SANDBOX_APPLIED", receipt
    assert receipt["payload"]["ActiveStatu"] == "Inactive", receipt
    print("PASS test_writeback_after_approval")


def test_unknown_rule_op_fails_fast():
    """未知规则操作符 fail-fast（封闭词表，不静默通过）。"""
    eng = fresh_engine()
    bad_rule = {"model_id": "masterdata.m3.bad", "when": {"field": "target.x", "op": "sql_inject", "value": 1},
                "then": {"effect": "block", "message": "x"}}
    eng.rules = [bad_rule]
    try:
        eng.run({"record_id": "9305733", "active_status": "Inactive"}, ctx={})
        raise AssertionError("未知操作符未 fail-fast")
    except ValueError as e:
        assert "封闭词表" in str(e) or "未知规则操作符" in str(e), str(e)
    print("PASS test_unknown_rule_op_fails_fast")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for t in tests:
        t()
        passed += 1
    print(f"\n=== {passed}/{len(tests)} 全部通过 ===")


if __name__ == "__main__":
    main()