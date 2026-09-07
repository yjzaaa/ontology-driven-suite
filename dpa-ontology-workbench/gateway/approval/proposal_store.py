# -*- coding: utf-8 -*-
"""提案/写操作台账：Port + JSON 文件适配器。

Port（ProposalStore）定义写操作台账的持久化契约；当前适配器为本地 JSON 文件，
未来切换 PostgreSQL 等后端只需新增同契约适配器，调用方（mvp_server）不改。

安全约定：审批 Token 只存 SHA-256 哈希，不落明文。
"""
import copy
import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Protocol


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class ProposalStore(Protocol):
    """写操作台账 Port。"""

    def save(self, proposal: dict) -> None: ...
    def get(self, proposal_id: str) -> dict | None: ...
    def update(self, proposal_id: str, state: str | None = None,
               extra: dict | None = None, history_event: dict | None = None) -> dict: ...
    def list(self) -> list[dict]: ...


class JsonProposalStore:
    """本地 JSON 文件适配器（原子写 + 线程锁）。"""

    def __init__(self, path: Path):
        self.path = Path(path)
        self._lock = threading.RLock()

    def _load(self) -> dict:
        if self.path.exists():
            with open(self.path, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _flush(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, self.path)  # 原子替换，避免半写状态

    def save(self, proposal: dict) -> None:
        with self._lock:
            data = self._load()
            data[proposal["proposal_id"]] = proposal
            self._flush(data)

    def get(self, proposal_id: str) -> dict | None:
        with self._lock:
            p = self._load().get(proposal_id)
            return copy.deepcopy(p) if p else None

    def update(self, proposal_id: str, state: str | None = None,
               extra: dict | None = None, history_event: dict | None = None) -> dict:
        with self._lock:
            data = self._load()
            p = data[proposal_id]
            if state is not None:
                p["state"] = state
            if extra:
                p.update(extra)
            if history_event:
                history_event = {"ts": _now(), **history_event}
                p.setdefault("history", []).append(history_event)
            p["updated"] = _now()
            self._flush(data)
            return copy.deepcopy(p)

    def list(self) -> list[dict]:
        with self._lock:
            return [copy.deepcopy({**p, "token_hash": "(hidden)"})
                    for p in self._load().values()]
