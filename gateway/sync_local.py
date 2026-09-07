# -*- coding: utf-8 -*-
"""本地库引导同步：测试库（一次性只读）→ gateway/data/localdb/*.json

之后 Gateway 运行时只读写操作本地库，不再连接真实库。
重跑本脚本即可用测试库当前事实刷新本地快照。
"""
import json
import os
import time
from pathlib import Path

import pyodbc

from config import DB_CONN, DPA_TEST_REVISION, ROOT

LOCALDB = ROOT / "gateway/data/localdb"

TABLES = {
    "pr_approval": "tb_Master_Data_PR_Online_Approval",
}


def main() -> None:
    LOCALDB.mkdir(parents=True, exist_ok=True)
    conn = pyodbc.connect(DB_CONN, timeout=15)
    try:
        cur = conn.cursor()
        for name, table in TABLES.items():
            cur.execute(f"SELECT * FROM {table}")  # 引导同步：只读，白名单表
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, [None if v is None else str(v) for v in r]))
                    for r in cur.fetchall()]
            doc = {"table": table, "revision": DPA_TEST_REVISION,
                   "synced_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                   "row_count": len(rows), "rows": rows}
            out = LOCALDB / f"{name}.json"
            tmp = out.with_suffix(".tmp")
            tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
            os.replace(tmp, out)
            print(f"{table}: {len(rows)} 行 → {out.name}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
