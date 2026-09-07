# -*- coding: utf-8 -*-
"""写执行适配器层：全平台唯一允许知道写目标技术细节的地方。

适配器按 WRITE_MODE 切换（适配器模式，切换后端不改调用方）：
  local_json —— 本地沙箱：变更落平台自己的 JSON 写操作库（明确标记：未发送至 DPA）
  dpa_http   —— 真实执行：转发同源 Cookie，经 DPA 原 HTTP/业务链写入（边界 #2）

诚实纪律：local_json 模式的成功码是 LOCAL_SANDBOX_APPLIED，
不得伪装成已写入 DPA；切换 dpa_http 后才产生对 DPA 的真实写。
"""
import json
import os
import threading
import time
import urllib.request
from pathlib import Path

COOKIE_NAME = "UserToken"  # 事实：Operator.TokenName（T04.1 事实链）


def _dig(obj: dict, path: str):
    """按 a.b.c 点路径取值（本地叠加声明用）。"""
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


class LocalJsonWriteAdapter:
    """本地 JSON 写操作库适配器（MVP 沙箱）：追加日志 + 同步更新本地库。"""

    def __init__(self, path: Path, localdb_dir: Path | None = None):
        self.path = Path(path)
        self.localdb_dir = Path(localdb_dir) if localdb_dir else None
        self._lock = threading.Lock()

    def _apply_local_update(self, mi: dict, arguments: dict) -> None:
        """按 MI 的 local_update 声明更新本地库行，保证后续读可见（读写自洽）。"""
        spec = mi.get("local_update")
        if not spec or not self.localdb_dir:
            return
        path = self.localdb_dir / f"{spec['source']}.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        pks = _dig(arguments, spec["pk"].strip("{}"))
        if not isinstance(pks, list):
            pks = [pks]
        pks = {str(p) for p in pks}
        patched = 0
        for row in doc["rows"]:
            if str(row.get(spec["match_column"])) in pks:
                for col, tpl in spec.get("set", {}).items():
                    row[col] = _dig(arguments, tpl.strip("{}"))
                if spec.get("touch"):
                    row[spec["touch"]] = time.strftime("%Y-%m-%d %H:%M:%S")
                patched += 1
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, path)  # 原子替换

    def execute(self, mi: dict, arguments: dict, cookie_header: str = "") -> dict:
        record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "mi": mi["id"],
                  "form": arguments.get("form", arguments),
                  "applied_to": "local_json",
                  "note": "本地沙箱落库，未发送至 DPA"}
        with self._lock:
            data = []
            if self.path.exists():
                data = json.loads(self.path.read_text(encoding="utf-8"))
            data.append(record)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
            os.replace(tmp, self.path)  # 原子替换
            self._apply_local_update(mi, arguments)
        return {"status": "SUCCEEDED", "code": "LOCAL_SANDBOX_APPLIED",
                "backend": "local_json", "record": record}


class DpaHttpWriteAdapter:
    """真实 DPA 执行适配器：转发同源 Cookie，走 DPA 原业务链（边界 #2）。"""

    def __init__(self, base_url: str):
        self.base = base_url.rstrip("/")

    def execute(self, mi: dict, arguments: dict, cookie_header: str = "") -> dict:
        if mi.get("retries", 0) != 0:
            raise ValueError("写请求禁止重试")
        if COOKIE_NAME not in cookie_header:
            return {"status": "FAILED", "code": "DPA_SESSION_EXPIRED",
                    "message": "浏览器未携带 DPA 会话 Cookie：请先在本浏览器登录测试环境 DPA"}
        body = json.dumps(arguments.get("form", {})).encode()
        req = urllib.request.Request(
            self.base + mi["url_path"], data=body, method=mi.get("method", "POST"),
            headers={"Content-Type": "application/json",
                     "Cookie": cookie_header,  # 同源转发，仅此一处
                     "X-Requested-With": "XMLHttpRequest"})
        try:
            with urllib.request.urlopen(req, timeout=mi.get("timeout_seconds", 15)) as resp:
                payload, code = resp.read().decode("utf-8", "replace"), resp.status
        except urllib.error.HTTPError as e:
            payload, code = e.read().decode("utf-8", "replace"), e.code
        except Exception as e:  # 平台故障分轨
            return {"status": "FAILED", "code": "DPA_UNREACHABLE", "message": str(e)}
        mapped = mi.get("error_mapping", {})
        if code == 200:
            return {"status": "SUCCEEDED", "code": "OK", "backend": "dpa_http",
                    "dpa_response": payload[:500]}
        return {"status": "FAILED", "code": mapped.get(str(code), f"HTTP_{code}"),
                "backend": "dpa_http", "dpa_response": payload[:500]}


def get_write_adapter(mode: str, dpa_base: str, applied_path: Path, localdb_dir: Path | None = None):
    if mode == "dpa_http":
        return DpaHttpWriteAdapter(dpa_base)
    return LocalJsonWriteAdapter(applied_path, localdb_dir)
