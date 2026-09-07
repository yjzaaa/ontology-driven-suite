# -*- coding: utf-8 -*-
"""ActionEngine：声明式写行为引擎（通用解释器，零业务知识）。

设计要点（对齐 Palantir Action Type + WriteBack）：
- 所有业务逻辑都在 YAML 声明里；本文件只做「解释执行」，不含任何业务动作知识。
- 新增业务写操作 = 只改 YAML，本文件零改动。
- 五段流水线：validate → locate → rules → compose → proposal（写回另算）。

职责边界：
- typed 校验    → jsonschema（按 input_schema）
- 定位          → target.locator（local_source + key_field）
- 规则求值      → 结构化 when-then，封闭词表 RULE_OPS，fail-closed
- 参数组合      → JMESPath（替代旧的 "{input.xxx}" 字符串模板 + _dig + 正则）
- 写回          → writeback 声明驱动，经 MI 防腐层（local_json 沙箱 / DPA_HTTP）
"""
import json
import secrets
import time

import jmespath
import jsonschema
import yaml

# 封闭规则词表（引擎知识，业务取值在 YAML）。启动时校验，非法词表 fail-fast。
RULE_OPS = {"equals", "not_equals", "in", "not_in", "required", "pattern", "nonempty_positive_ints"}


class PolicyError(Exception):
    """策略/规则阻断（fail-closed）。"""


class ActionEngine:
    """解释执行声明式 Action 的引擎。"""

    def __init__(self, action: dict, mi: dict, rules: list, localdb: dict):
        self.action = action
        self.mi = mi
        self.rules = rules            # [M3 rule, ...]
        self.localdb = localdb        # {source_name: [row, ...]}
        self._proposals: dict = {}    # 提案台账（spike 用内存，生产接 ProposalStore）

    # ---------------- 1) typed 输入校验 ----------------
    def validate_input(self, inputs: dict) -> dict:
        schema = self.action["input_schema"]
        jsonschema.validate(inputs, schema)   # 不合法直接抛（fail-closed，不静默降级）
        return inputs

    # ---------------- 2) 目标定位 ----------------
    def locate(self, inputs: dict) -> dict:
        loc = self.action["target"]["locator"]
        source, key = loc["local_source"], loc["key_field"]
        record_id = inputs.get("record_id")
        for row in self.localdb.get(source, []):
            if str(row.get(key)) == str(record_id):
                return row
        raise PolicyError(f"未找到目标记录：{source}.{key}={record_id}")

    # ---------------- 3) 结构化规则求值 ----------------
    def apply_rules(self, inputs: dict, target: dict) -> None:
        env = {"input": inputs, "target": target}
        for rule in self.rules:
            when, then = rule["when"], rule["then"]
            value = jmespath.search(when["field"], env)
            hit = self._match(when["op"], value, when.get("value"))
            if not hit:
                continue
            if then["effect"] == "block":
                raise PolicyError(then.get("message") or f"规则 {rule['model_id']} 阻断")
            # warn / derive 可在此扩展（spike 只实现 block）

    @staticmethod
    def _match(op: str, value, expected) -> bool:
        if op not in RULE_OPS:
            raise ValueError(f"未知规则操作符: {op}（封闭词表：{sorted(RULE_OPS)}）")
        if op == "equals":
            return value == expected
        if op == "not_equals":
            return value != expected
        if op == "in":
            return value in expected
        if op == "not_in":
            return value not in expected
        if op == "required":
            return value not in (None, "")
        if op == "pattern":
            import re
            return bool(re.match(str(expected), str(value)))
        if op == "nonempty_positive_ints":
            return isinstance(value, list) and len(value) > 0 and all(isinstance(v, int) and v > 0 for v in value)
        return False

    # ---------------- 4) JMESPath 参数组合（替代 _dig + 正则） ----------------
    def compose_payload(self, inputs: dict, target: dict) -> dict:
        env = {"input": inputs, "target": target}
        out = {}
        for field, expr in (self.mi.get("param_mapping") or {}).items():
            out[field] = jmespath.compile(expr).search(env)
        return out

    # ---------------- 5) 生成提案（授权恒在网关侧） ----------------
    def create_proposal(self, inputs: dict, target: dict, payload: dict, ctx: dict) -> dict:
        pid = f"prop_{secrets.token_hex(4)}"
        label = f"{target.get('dic_name')}({target.get('id')})"
        proposal = {
            "proposal_id": pid,
            "action_id": self.action["model_id"],
            "mi_ref": self.mi["model_id"],
            "state": "PENDING_APPROVAL",
            "risk": self.action["approval"]["risk"],
            "display": f"{self.action['name']['zh']}：{label}",
            "change": f"active_status → {inputs['active_status']}",
            "target": {"id": target.get("id"), "label": label},
            "form": payload,                    # JMESPath 组合出的 DPA 载荷
            "writeback": self.action["writeback"],
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "thread_id": ctx.get("thread_id", ""),
            "actor": ctx.get("actor", ""),
            "history": [{"event": "created", "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")}],
        }
        self._proposals[pid] = proposal
        return proposal

    # ---------------- 主流程：validate → locate → rules → compose → proposal ----------------
    def run(self, inputs: dict, ctx: dict | None = None) -> dict:
        ctx = ctx or {}
        validated = self.validate_input(inputs)     # 1. typed 校验
        target = self.locate(validated)             # 2. 定位
        self.apply_rules(validated, target)         # 3. 规则（fail-closed）
        payload = self.compose_payload(validated, target)  # 4. JMESPath 组合
        return self.create_proposal(validated, target, payload, ctx)  # 5. 提案

    # ---------------- 写回：审批后经 MI 防腐层（对齐 WriteBack） ----------------
    def writeback_on_approval(self, proposal_id: str, ctx: dict | None = None) -> dict:
        ctx = ctx or {}
        p = self._proposals.get(proposal_id)
        if p is None:
            raise PolicyError(f"提案不存在: {proposal_id}")
        if p.get("state") != "APPROVED":
            raise PolicyError("仅已批准提案可写回")
        wb = self.action["writeback"]
        # 沙箱：local_json；真实 DPA_HTTP 由 execution.write_adapters 承担（此处 spike 不落真实 DPA）
        receipt = {
            "status": "SUCCEEDED",
            "code": "LOCAL_SANDBOX_APPLIED",
            "backend": wb.get("via"),
            "timing": wb.get("timing"),
            "payload": p["form"],
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        p["state"] = "EXECUTED"
        p["receipt"] = receipt
        p["history"].append({"event": "executed", "ts": receipt["ts"]})
        return receipt

    def approve(self, proposal_id: str, actor: str) -> dict:
        p = self._proposals[proposal_id]
        p["state"] = "APPROVED"
        p["history"].append({"event": "approved", "actor": actor, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")})
        return p


# ---------------- 装配：从 YAML 加载声明 ----------------
def load_engine(models_dir: str, localdb: dict) -> ActionEngine:
    def _load(name):
        with open(f"{models_dir}/{name}", encoding="utf-8") as f:
            return yaml.safe_load(f)

    action = _load("action-update-subtable.yaml")
    mi = _load("mi-update-subtable.yaml")
    rule = _load("rule-allow-update.yaml")
    rules = [rule] if action.get("rules") else []
    return ActionEngine(action, mi, rules, localdb)


if __name__ == "__main__":
    # 最小自测：一条本地记录 → 走完整流水线
    localdb = {
        "pr_approval": [
            {"id": "9305733", "dic_name": "Vendor_type", "dic_type": "Vendor_type",
             "active_status": "Active", "ids": [9305733]},
        ]
    }
    engine = load_engine("models", localdb)
    proposal = engine.run({"record_id": "9305733", "active_status": "Inactive"},
                          ctx={"thread_id": "demo", "actor": "admin"})
    print("提案：", json.dumps({k: proposal[k] for k in ("proposal_id", "state", "display", "change", "form")}, ensure_ascii=False, indent=2))
    engine.approve(proposal["proposal_id"], actor="admin")
    receipt = engine.writeback_on_approval(proposal["proposal_id"])
    print("写回：", json.dumps(receipt, ensure_ascii=False, indent=2))