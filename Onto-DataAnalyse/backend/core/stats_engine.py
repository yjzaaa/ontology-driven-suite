"""统计计算引擎：同环比 / 3σ 异常检测 / RFM / ABC 分类"""
from __future__ import annotations

import math
import statistics
from typing import Any


def mom_yoy(rows: list[dict], period_key: str, value_key: str) -> dict:
    """
    计算时序数据的同环比。
    rows 形如 [{'period':'2026-03', 'gmv': 1000000}, ...]，按 period 升序
    返回：{
        'series': [{'period':..., 'value':..., 'mom':..., 'mom_pct':..., 'yoy':..., 'yoy_pct':...}],
        'latest': {同上},
        'trend': 'up'|'down'|'flat'
    }
    """
    if not rows:
        return {"series": [], "latest": None, "trend": "flat"}

    rows = sorted(rows, key=lambda r: r[period_key])
    series: list[dict] = []
    by_period = {r[period_key]: float(r.get(value_key) or 0) for r in rows}
    periods = list(by_period.keys())

    for i, p in enumerate(periods):
        v = by_period[p]
        item = {"period": p, "value": v, "mom": None, "mom_pct": None,
                "yoy": None, "yoy_pct": None}
        # 环比：上一期
        if i > 0:
            prev = by_period[periods[i - 1]]
            if prev:
                item["mom"] = round(v - prev, 2)
                item["mom_pct"] = round((v - prev) / prev * 100, 2)
        # 同比：往前 12 期（仅当粒度为月时有意义）
        if i >= 12:
            yoy_prev = by_period[periods[i - 12]]
            if yoy_prev:
                item["yoy"] = round(v - yoy_prev, 2)
                item["yoy_pct"] = round((v - yoy_prev) / yoy_prev * 100, 2)
        series.append(item)

    latest = series[-1] if series else None
    # 趋势判定：最近 3 期斜率正负
    trend = "flat"
    if len(series) >= 3:
        recent = [s["value"] for s in series[-3:]]
        if recent[-1] > recent[0] * 1.03:
            trend = "up"
        elif recent[-1] < recent[0] * 0.97:
            trend = "down"

    return {"series": series, "latest": latest, "trend": trend}


def anomaly_3sigma(rows: list[dict], period_key: str, value_key: str) -> dict:
    """
    3σ 异常检测。返回偏离均值 ±3σ 的数据点。
    """
    if len(rows) < 3:
        return {"mean": 0, "std": 0, "anomalies": [], "thresholds": {"upper": 0, "lower": 0}}
    values = [float(r.get(value_key) or 0) for r in rows]
    mean = statistics.fmean(values)
    std = statistics.pstdev(values)
    upper = mean + 3 * std
    lower = mean - 3 * std
    anomalies = []
    for r in rows:
        v = float(r.get(value_key) or 0)
        if v > upper or v < lower:
            anomalies.append({
                "period": r.get(period_key),
                "value": v,
                "deviation_sigma": round((v - mean) / std, 2) if std else 0,
                "direction": "high" if v > upper else "low",
            })
    return {
        "mean": round(mean, 2),
        "std": round(std, 2),
        "thresholds": {"upper": round(upper, 2), "lower": round(lower, 2)},
        "anomalies": anomalies,
    }


def rfm_score(rows: list[dict], r_key: str = "recency_days",
              f_key: str = "frequency", m_key: str = "monetary") -> dict:
    """
    RFM 评分：每个维度按分位数切分 5 段（1~5 分）。
    输入：[{'user_id':..., 'recency_days':30, 'frequency':3, 'monetary':2500}, ...]
    输出：{
      'scored': [{user_id, r_score, f_score, m_score, rfm_segment}],
      'segment_counts': {'重要价值': 100, '一般价值': 300, ...}
    }
    """
    if not rows:
        return {"scored": [], "segment_counts": {}}

    def _q_breaks(values: list[float], reverse: bool = False) -> list[float]:
        if not values:
            return []
        sv = sorted(values, reverse=reverse)
        n = len(sv)
        return [sv[int(n * q)] for q in (0.2, 0.4, 0.6, 0.8)]

    def _score(v: float, breaks: list[float]) -> int:
        for i, b in enumerate(breaks):
            if v < b:
                return i + 1
        return 5

    r_vals = [float(r.get(r_key) or 0) for r in rows]
    f_vals = [float(r.get(f_key) or 0) for r in rows]
    m_vals = [float(r.get(m_key) or 0) for r in rows]
    # R: 越小越好（distance）
    r_breaks = _q_breaks(r_vals, reverse=False)
    f_breaks = _q_breaks(f_vals, reverse=True)
    m_breaks = _q_breaks(m_vals, reverse=True)

    seg_def = {
        (True, True, True): "重要价值客户",
        (True, True, False): "重要发展客户",
        (True, False, True): "重要保持客户",
        (True, False, False): "重要挽留客户",
        (False, True, True): "一般价值客户",
        (False, True, False): "一般发展客户",
        (False, False, True): "一般保持客户",
        (False, False, False): "一般挽留客户",
    }
    scored = []
    counts: dict[str, int] = {}
    for row in rows:
        r = float(row.get(r_key) or 0)
        f = float(row.get(f_key) or 0)
        m = float(row.get(m_key) or 0)
        # R 越小分越高（最近购买）
        r_score = 6 - _score(r, r_breaks)
        f_score = _score(f, f_breaks[::-1])    # 频次越高分越高，需反向
        m_score = _score(m, m_breaks[::-1])
        # 二分段：是否高于均值
        r_high = r_score >= 3
        f_high = f_score >= 3
        m_high = m_score >= 3
        seg = seg_def[(r_high, f_high, m_high)]
        scored.append({**row, "r_score": r_score, "f_score": f_score,
                       "m_score": m_score, "rfm_segment": seg})
        counts[seg] = counts.get(seg, 0) + 1
    return {"scored": scored, "segment_counts": counts}


def abc_classification(rows: list[dict], value_key: str) -> dict:
    """
    ABC 分类：按 value 降序，A 类累计 ≤80%，B 类 80-95%，C 类 >95%
    """
    if not rows:
        return {"items": [], "summary": {"A": 0, "B": 0, "C": 0}}
    sorted_rows = sorted(rows, key=lambda r: float(r.get(value_key) or 0), reverse=True)
    total = sum(float(r.get(value_key) or 0) for r in sorted_rows)
    if total <= 0:
        return {"items": [], "summary": {"A": 0, "B": 0, "C": 0}}
    cum = 0.0
    items = []
    counts = {"A": 0, "B": 0, "C": 0}
    for r in sorted_rows:
        v = float(r.get(value_key) or 0)
        cum += v
        ratio = cum / total
        cls = "A" if ratio <= 0.80 else ("B" if ratio <= 0.95 else "C")
        items.append({**r, "cum_ratio": round(ratio, 4), "abc_class": cls})
        counts[cls] += 1
    return {"items": items, "summary": counts, "total": total}


# ============================================================
# 统一调度入口（场景执行器调用）
# ============================================================
def run_algorithm(name: str, rows: list[dict], **kwargs) -> dict:
    if name == "mom_yoy":
        return mom_yoy(rows, kwargs.get("period_key", "period"),
                       kwargs.get("value_key", "value"))
    if name == "anomaly_3sigma":
        return anomaly_3sigma(rows, kwargs.get("period_key", "period"),
                              kwargs.get("value_key", "value"))
    if name == "rfm_score":
        return rfm_score(rows, kwargs.get("r_key", "recency_days"),
                         kwargs.get("f_key", "frequency"),
                         kwargs.get("m_key", "monetary"))
    if name == "abc_classification":
        return abc_classification(rows, kwargs.get("value_key", "value"))
    raise ValueError(f"未知统计算法：{name}")
