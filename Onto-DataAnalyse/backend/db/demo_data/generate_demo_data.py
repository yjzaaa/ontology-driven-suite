"""演示电商数据生成脚本

运行方式：
    python -m backend.db.demo_data.generate_demo_data

特性：
- random.seed(42) 保证可重复
- 数据满足 5 个分析特征：
  1. 近 3 个月 GMV 环比下降（2026-03/04/05）
  2. 服装类目（CAT-001）近 2 个月大幅下滑
  3. ~40% 用户最近 30 天无购买（流失分析基础）
  4. 2025-11 大促峰值（GMV 约平均月份 2.5 倍）
  5. 2025-12 退款率上升（由服装类目质量问题驱动）
"""
from __future__ import annotations

import random
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from backend.config.settings import settings

random.seed(42)

# ============================================================
# 全局参考时间
# ============================================================
TODAY = datetime(2026, 5, 17)                    # 数据生成基准日（演示文档"今天"）
DATA_START = datetime(2025, 6, 1)                # 数据起点（往前 12 个月）

# 每月订单目标（共 12 个月，合计 ~15,000）
MONTHLY_ORDER_COUNTS = {
    (2025, 6):  1000, (2025, 7):  1050, (2025, 8):  1100, (2025, 9):  1200,
    (2025, 10): 1200, (2025, 11): 2800,                                       # 11月大促
    (2025, 12): 1400, (2026, 1):  1300, (2026, 2):  1200,
    (2026, 3):  1050,                                                          # 近3月下滑开始
    (2026, 4):   900,                                                          # 持续下滑
    (2026, 5):   550,                                                          # 当月（17 天）
}

# 类目权重（订单按类目分布），按月切换以体现"服装类目衰退"
CATEGORY_WEIGHTS_DEFAULT = {
    "CAT-001": 0.30,  # 服装
    "CAT-002": 0.22,  # 3C 数码
    "CAT-003": 0.18,  # 家居家电
    "CAT-004": 0.16,  # 食品生鲜
    "CAT-005": 0.14,  # 美妆个护
}
CATEGORY_WEIGHTS_BY_MONTH = {
    (2026, 3): {"CAT-001": 0.25, "CAT-002": 0.24, "CAT-003": 0.20, "CAT-004": 0.17, "CAT-005": 0.14},
    (2026, 4): {"CAT-001": 0.18, "CAT-002": 0.26, "CAT-003": 0.22, "CAT-004": 0.18, "CAT-005": 0.16},
    (2026, 5): {"CAT-001": 0.12, "CAT-002": 0.28, "CAT-003": 0.23, "CAT-004": 0.19, "CAT-005": 0.18},
}

# 退款基线 ~3%；2025-12 服装类目退款率显著抬升（~15%）
def refund_rate(category_id: str, ym: tuple[int, int]) -> float:
    if ym == (2025, 12) and category_id == "CAT-001":
        return 0.15
    if ym in ((2026, 1), (2026, 2)) and category_id == "CAT-001":
        return 0.08   # 余波
    return 0.03

# 取消订单率 ~5%
CANCEL_RATE = 0.05

# 4 大渠道与设备
CHANNELS = ["APP", "PC", "MINI", "H5"]
CHANNEL_WEIGHTS = [0.55, 0.20, 0.15, 0.10]
DEVICE_BY_CHANNEL = {
    "APP": ["iOS", "Android"],
    "PC": ["Windows", "Mac"],
    "MINI": ["iOS", "Android"],
    "H5": ["iOS", "Android", "Windows"],
}

PROVINCES = [
    "广东", "江苏", "浙江", "山东", "河南", "四川", "湖北", "湖南",
    "上海", "北京", "福建", "安徽", "河北", "陕西", "辽宁",
]
CITY_BY_PROV = {p: [f"{p}市辖{i}区" for i in range(1, 4)] for p in PROVINCES}

CARRIERS = ["顺丰", "中通", "京东物流", "EMS", "圆通"]
CARRIER_WEIGHTS = [0.30, 0.25, 0.20, 0.10, 0.15]

REFUND_REASONS = ["质量问题", "尺寸不合", "不喜欢", "物流问题", "其他"]
REFUND_REASONS_QUALITY = ["质量问题", "尺寸不合", "其他"]  # 服装 12月偏向质量类


# ============================================================
# 工具函数
# ============================================================
def _id(prefix: str, n: int, width: int = 6) -> str:
    return f"{prefix}-{n:0{width}d}"


def _weighted_choice(weights: dict[str, float]) -> str:
    items = list(weights.keys())
    probs = list(weights.values())
    return random.choices(items, weights=probs, k=1)[0]


def _random_datetime_in_month(year: int, month: int) -> datetime:
    """月内均匀采样一个时间点，但 5 月只到 TODAY"""
    start = datetime(year, month, 1)
    if year == TODAY.year and month == TODAY.month:
        end = TODAY
    elif month == 12:
        end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        end = datetime(year, month + 1, 1) - timedelta(seconds=1)
    seconds = (end - start).total_seconds()
    return start + timedelta(seconds=random.uniform(0, seconds))


def _iso(dt: datetime) -> str:
    # 所有时间统一存为 Asia/Shanghai 本地时间（不带 +08:00 时区后缀，
    # 以便 SQLite strftime 直接按本地时间解析；本系统所有时间均按 UTC+8 解读）
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def _connect() -> sqlite3.Connection:
    p = Path(settings.DEMO_DB_PATH)
    if not p.is_absolute():
        p = settings.PROJECT_ROOT / p.as_posix().lstrip("./")
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        p.unlink()
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    return conn


def _exec_ddl(conn: sqlite3.Connection) -> None:
    ddl_path = Path(__file__).parent / "create_demo_tables.sql"
    conn.executescript(ddl_path.read_text(encoding="utf-8"))


# ============================================================
# 类目（30 个：5 L1 + 15 L2 + 10 L3）
# ============================================================
def gen_categories() -> list[dict]:
    cats: list[dict] = []
    L1 = [
        ("CAT-001", "服装"),
        ("CAT-002", "3C数码"),
        ("CAT-003", "家居家电"),
        ("CAT-004", "食品生鲜"),
        ("CAT-005", "美妆个护"),
    ]
    L2_MAP = {
        "CAT-001": ["女装", "男装", "童装"],
        "CAT-002": ["手机", "电脑", "数码配件"],
        "CAT-003": ["大家电", "厨房用品", "家居装饰"],
        "CAT-004": ["休闲零食", "新鲜水果", "生鲜冻品"],
        "CAT-005": ["护肤", "彩妆", "个人护理"],
    }
    L3_LIST = [
        ("CAT-001-01", "连衣裙", "CAT-001-01-PAR"),  # placeholder, will fix below
    ]

    for cid, name in L1:
        cats.append({"id": cid, "name": name, "parent": None, "level": 1})

    l2_seq = 0
    l2_id_map: dict[str, str] = {}     # parent_l1 -> list of l2 ids（不用，但保留）
    for l1_id, _ in L1:
        for l2_name in L2_MAP[l1_id]:
            l2_seq += 1
            l2_id = f"{l1_id}-{l2_seq:02d}"
            cats.append({"id": l2_id, "name": l2_name, "parent": l1_id, "level": 2})
            l2_id_map.setdefault(l1_id, []).append(l2_id)

    # 10 个 L3 节点（叶子类目），ID 沿用父级前缀 + 二级序号便于层级查询
    l3_specs = [
        ("连衣裙", l2_id_map["CAT-001"][0]),    # 女装
        ("T恤",   l2_id_map["CAT-001"][0]),
        ("男士衬衫", l2_id_map["CAT-001"][1]),  # 男装
        ("智能手机", l2_id_map["CAT-002"][0]),  # 手机
        ("笔记本电脑", l2_id_map["CAT-002"][1]),
        ("智能空调", l2_id_map["CAT-003"][0]),  # 大家电
        ("不粘炒锅", l2_id_map["CAT-003"][1]),  # 厨房用品
        ("坚果礼盒", l2_id_map["CAT-004"][0]),  # 休闲零食
        ("补水面膜", l2_id_map["CAT-005"][0]),  # 护肤
        ("哑光口红", l2_id_map["CAT-005"][1]),  # 彩妆
    ]
    l3_seq_under_parent: dict[str, int] = {}
    for name, parent_id in l3_specs:
        l3_seq_under_parent[parent_id] = l3_seq_under_parent.get(parent_id, 0) + 1
        l3_id = f"{parent_id}-{l3_seq_under_parent[parent_id]:02d}"
        cats.append({"id": l3_id, "name": name, "parent": parent_id, "level": 3})

    return cats


# ============================================================
# 店铺（50 个）
# ============================================================
def gen_shops(categories: list[dict]) -> list[dict]:
    l1_ids = [c["id"] for c in categories if c["level"] == 1]
    shops = []
    for i in range(1, 51):
        main_cat = random.choice(l1_ids)
        shops.append({
            "shop_id": _id("SHOP", i, 4),
            "shop_name": f"{random.choice(['优选', '臻品', '云尚', '潮流', '匠心', '甄选', '尚品', '惠购'])}-{i:03d}号店",
            "shop_level": random.choices([5, 4, 3, 2, 1], weights=[0.20, 0.35, 0.25, 0.15, 0.05])[0],
            "main_category": main_cat,
            "province": random.choice(PROVINCES),
            "deposit": random.choice([10000, 30000, 50000, 100000, 200000]),
            "gmt_create": _iso(DATA_START - timedelta(days=random.randint(180, 720))),
        })
    return shops


# ============================================================
# 商品 SPU & SKU
# ============================================================
def gen_products_and_skus(categories: list[dict], shops: list[dict]) -> tuple[list[dict], list[dict]]:
    l3_cats = [c for c in categories if c["level"] == 3]
    cat_by_l1: dict[str, list[dict]] = {}
    for l3 in l3_cats:
        # 找到 L3 的 L1 祖先
        parent = next((c for c in categories if c["id"] == l3["parent"]), None)
        if parent:
            grand = next((c for c in categories if c["id"] == parent["parent"]), None)
            if grand:
                cat_by_l1.setdefault(grand["id"], []).append(l3)

    shops_by_cat: dict[str, list[dict]] = {}
    for s in shops:
        shops_by_cat.setdefault(s["main_category"], []).append(s)

    # 按 L1 分布商品数量（服装最多以体现衰退影响）
    products_per_l1 = {
        "CAT-001": 180,   # 服装
        "CAT-002": 120,   # 3C
        "CAT-003": 80,    # 家居家电
        "CAT-004": 70,    # 食品
        "CAT-005": 50,    # 美妆
    }

    brands_by_l1 = {
        "CAT-001": ["雅致", "都会", "本色", "悦己", "简约", "原创"],
        "CAT-002": ["米跃", "极客", "智云", "数擎", "锐界"],
        "CAT-003": ["家美", "厨匠", "宜居", "暖意", "万象"],
        "CAT-004": ["谷源", "鲜达", "稻馨", "果园", "山野"],
        "CAT-005": ["颜悦", "净肤", "妆韵", "肌研", "蜜素"],
    }

    products: list[dict] = []
    skus: list[dict] = []
    pidx = 0
    sidx = 0
    for l1_id, count in products_per_l1.items():
        l3_options = cat_by_l1.get(l1_id, [])
        shop_options = shops_by_cat.get(l1_id, shops)  # 兜底
        if not l3_options:
            # 用 L2 兜底
            l3_options = [c for c in categories if c["parent"] == l1_id]
        for _ in range(count):
            pidx += 1
            leaf = random.choice(l3_options)
            shop = random.choice(shop_options)
            list_price = round(random.uniform(*{
                "CAT-001": (49, 599),
                "CAT-002": (199, 7999),
                "CAT-003": (89, 4999),
                "CAT-004": (15, 299),
                "CAT-005": (29, 599),
            }[l1_id]), 2)
            brand = random.choice(brands_by_l1[l1_id])
            product = {
                "product_id": _id("PRD", pidx, 5),
                "product_name": f"{brand}·{leaf['name']}-款式{pidx % 200 + 1:03d}",
                "category_id": leaf["id"],
                "shop_id": shop["shop_id"],
                "brand": brand,
                "status": random.choices([1, 2], weights=[0.92, 0.08])[0],
                "list_price": list_price,
                "avg_rating": round(random.uniform(3.8, 4.95), 2),
                "review_count": random.randint(0, 5000),
                "gmt_create": _iso(DATA_START - timedelta(days=random.randint(0, 600))),
                "gmt_modified": _iso(TODAY - timedelta(days=random.randint(0, 90))),
                "_l1": l1_id,                    # 内部用
            }
            products.append(product)
            # 每个 SPU 生成 2~4 个 SKU（控制总量 ~1500）
            num_sku = random.randint(2, 4)
            for sk in range(num_sku):
                sidx += 1
                sku_price = round(list_price * random.uniform(0.85, 1.0), 2)
                skus.append({
                    "sku_id": _id("SKU", sidx, 6),
                    "product_id": product["product_id"],
                    "sku_name": f"{product['product_name']}-规格{sk+1}",
                    "color": random.choice(["黑", "白", "蓝", "红", "灰", "粉", "绿", "棕"]),
                    "size": random.choice(["S", "M", "L", "XL", "XXL", "均码"]),
                    "stock": random.randint(0, 500),
                    "sale_price": sku_price,
                    "cost_price": round(sku_price * random.uniform(0.4, 0.7), 2),
                    "gmt_create": product["gmt_create"],
                })

    return products, skus


# ============================================================
# 用户（2000）
# ============================================================
def gen_users() -> list[dict]:
    users = []
    for i in range(1, 2001):
        register_days_ago = random.choices(
            [random.randint(0, 30), random.randint(30, 180), random.randint(180, 720), random.randint(720, 1800)],
            weights=[0.10, 0.25, 0.40, 0.25],
        )[0]
        reg_date = TODAY - timedelta(days=register_days_ago)
        prov = random.choice(PROVINCES)
        users.append({
            "user_id": _id("USR", i, 5),
            "nickname": f"用户{i:05d}",
            "gender": random.choices(["M", "F", "U"], weights=[0.45, 0.50, 0.05])[0],
            "age_range": random.choices(
                ["18-25", "26-35", "36-45", "46-55", "55+"],
                weights=[0.18, 0.40, 0.25, 0.12, 0.05],
            )[0],
            "province": prov,
            "city": random.choice(CITY_BY_PROV[prov]),
            "register_channel": random.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0],
            "user_level": random.choices(
                ["普通", "VIP1", "VIP2", "VIP3"],
                weights=[0.55, 0.25, 0.15, 0.05],
            )[0],
            "register_date": _iso(reg_date),
            "last_login_date": _iso(TODAY - timedelta(days=random.randint(0, 90))),
            "gmt_create": _iso(reg_date),
        })
    return users


def _pareto_user_weights(users: list[dict]) -> list[float]:
    """少数用户贡献多数订单 — 帕累托分布"""
    n = len(users)
    # 20% 高频用户、60% 中频、20% 低频/无购
    weights = []
    for i, _ in enumerate(users):
        if i < n * 0.2:
            w = random.uniform(8, 25)
        elif i < n * 0.8:
            w = random.uniform(0.5, 4)
        else:
            w = random.uniform(0.0, 0.3)   # 大概率不会买
        weights.append(w)
    random.shuffle(weights)
    return weights


# ============================================================
# 营销活动（30）
# ============================================================
def gen_campaigns() -> list[dict]:
    campaigns = []
    # 重要：11月大促一定要有，并标记面向全类目
    big = {
        "campaign_id": "CMP-2025-NOV-DASHU",
        "campaign_name": "11.11 全平台大促",
        "campaign_type": "大促",
        "start_time": _iso(datetime(2025, 11, 1)),
        "end_time": _iso(datetime(2025, 11, 11, 23, 59, 59)),
        "budget": 8_000_000,
        "target_category": None,
        "gmt_create": _iso(datetime(2025, 10, 1)),
    }
    campaigns.append(big)

    # 12月服装清仓（呼应退款率上升）
    apparel_clearance = {
        "campaign_id": "CMP-2025-DEC-APPAREL",
        "campaign_name": "年终服装清仓节",
        "campaign_type": "折扣",
        "start_time": _iso(datetime(2025, 12, 5)),
        "end_time": _iso(datetime(2025, 12, 25)),
        "budget": 1_200_000,
        "target_category": "CAT-001",
        "gmt_create": _iso(datetime(2025, 11, 20)),
    }
    campaigns.append(apparel_clearance)

    types = ["满减", "折扣", "秒杀", "拼团"]
    cats = ["CAT-001", "CAT-002", "CAT-003", "CAT-004", "CAT-005", None]
    for i in range(3, 31):
        start = DATA_START + timedelta(days=random.randint(0, 350))
        end = start + timedelta(days=random.randint(3, 21))
        if end > TODAY:
            end = TODAY
        campaigns.append({
            "campaign_id": _id("CMP", i, 3),
            "campaign_name": f"{random.choice(['周末', '月初', '月末', '节日', '新品', '会员', '清仓'])}-{random.choice(types)}活动",
            "campaign_type": random.choice(types),
            "start_time": _iso(start),
            "end_time": _iso(end),
            "budget": random.choice([50_000, 100_000, 300_000, 500_000, 800_000]),
            "target_category": random.choice(cats),
            "gmt_create": _iso(start - timedelta(days=random.randint(7, 30))),
        })
    return campaigns


# ============================================================
# 订单 + 订单明细（核心）
# ============================================================
def gen_orders(users, shops, products, skus, categories, campaigns):
    user_weights = _pareto_user_weights(users)

    # 按 L1 分类索引商品（用于按类目权重选商品）
    products_by_l1: dict[str, list[dict]] = {}
    for p in products:
        products_by_l1.setdefault(p["_l1"], []).append(p)

    sku_by_product: dict[str, list[dict]] = {}
    for sku in skus:
        sku_by_product.setdefault(sku["product_id"], []).append(sku)

    shop_by_id = {s["shop_id"]: s for s in shops}

    orders: list[dict] = []
    items: list[dict] = []
    refunds: list[dict] = []
    logistics: list[dict] = []
    coupon_usages: list[dict] = []

    order_seq = 0
    item_seq = 0
    refund_seq = 0
    log_seq = 0
    cu_seq = 0

    for (year, month), count in MONTHLY_ORDER_COUNTS.items():
        weights_for_month = CATEGORY_WEIGHTS_BY_MONTH.get((year, month), CATEGORY_WEIGHTS_DEFAULT)
        for _ in range(count):
            order_seq += 1
            buyer = random.choices(users, weights=user_weights, k=1)[0]
            l1 = _weighted_choice(weights_for_month)
            candidate_products = products_by_l1.get(l1, products)
            # 选 1~3 个商品（来自同一类目下不同商家可能性更高，但简化为同 L1 内）
            n_items = random.choices([1, 2, 3], weights=[0.65, 0.27, 0.08])[0]
            chosen = random.sample(candidate_products, k=min(n_items, len(candidate_products)))
            # 按第一个商品所属店铺作为 seller
            seller_id = chosen[0]["shop_id"]

            channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0]
            device = random.choice(DEVICE_BY_CHANNEL[channel])
            create_dt = _random_datetime_in_month(year, month)
            payment_dt = create_dt + timedelta(minutes=random.randint(1, 60))

            # 订单状态：5% 取消、余下按时间和退款率分布
            if random.random() < CANCEL_RATE:
                status = 5     # 已取消
            else:
                # 已支付/已发货/已签收（时间越早，越可能签收）
                age_days = (TODAY - create_dt).days
                if age_days > 21:
                    status_pool = [4, 4, 4, 3]
                elif age_days > 7:
                    status_pool = [3, 3, 4, 2]
                else:
                    status_pool = [2, 2, 3]
                status = random.choice(status_pool)

            # 生成订单项并汇总金额
            order_orig = 0.0
            order_pay = 0.0
            this_order_items: list[dict] = []
            for prod in chosen:
                qty = random.randint(1, 3)
                # 选一个 SKU
                cand_skus = sku_by_product.get(prod["product_id"]) or []
                if not cand_skus:
                    continue
                sku = random.choice(cand_skus)
                unit_price = sku["sale_price"]
                discount = random.choice([0.0, 0.0, 0.05, 0.10, 0.15])
                pay_price = round(unit_price * (1 - discount), 2)
                order_orig += unit_price * qty
                order_pay += pay_price * qty
                item_seq += 1
                this_order_items.append({
                    "item_id": _id("ITM", item_seq, 7),
                    "order_id": _id("ORD", order_seq, 6),
                    "product_id": prod["product_id"],
                    "sku_id": sku["sku_id"],
                    "quantity": qty,
                    "unit_price": unit_price,
                    "pay_price": pay_price,
                    "category_id": prod["category_id"],
                    "gmt_create": _iso(create_dt),
                    "_l1": l1,
                })

            order_id = _id("ORD", order_seq, 6)
            discount_amount = round(order_orig - order_pay, 2)

            order = {
                "order_id": order_id,
                "buyer_id": buyer["user_id"],
                "seller_id": seller_id,
                "status": status,
                "payment_amount": round(order_pay, 2),
                "original_amount": round(order_orig, 2),
                "discount_amount": discount_amount,
                "refund_amount": 0.0,
                "channel": channel,
                "device_type": device,
                "gmt_create": _iso(create_dt),
                "gmt_payment": _iso(payment_dt) if status != 5 else None,
                "gmt_modified": _iso(payment_dt + timedelta(hours=random.randint(0, 72))),
            }

            # 物流（status >= 3 即已发货）
            if status in (3, 4):
                log_seq += 1
                ship_dt = payment_dt + timedelta(hours=random.randint(2, 48))
                delivered_dt = ship_dt + timedelta(days=random.randint(1, 7)) if status == 4 else None
                logistics.append({
                    "logistics_id": _id("LOG", log_seq, 6),
                    "order_id": order_id,
                    "carrier": random.choices(CARRIERS, weights=CARRIER_WEIGHTS)[0],
                    "tracking_no": f"SF{random.randint(10**11, 10**12 - 1)}",
                    "ship_time": _iso(ship_dt),
                    "delivery_time": _iso(delivered_dt) if delivered_dt else None,
                    "province": buyer["province"],
                    "city": buyer["city"],
                    "status": "DELIVERED" if status == 4 else "IN_TRANSIT",
                })

            # 退款：根据 (类目, 月份) 退款率决定；退款必然发生在订单已支付之后
            if status in (2, 3, 4):
                primary_l1 = this_order_items[0]["_l1"] if this_order_items else l1
                primary_cat = (
                    "CAT-001" if primary_l1 == "CAT-001" else primary_l1
                )
                rate = refund_rate(primary_cat, (year, month))
                if random.random() < rate:
                    refund_seq += 1
                    refund_amt = round(order_pay * random.uniform(0.5, 1.0), 2)
                    apply_dt = payment_dt + timedelta(days=random.randint(1, 14))
                    complete_dt = apply_dt + timedelta(days=random.randint(1, 5))
                    is_apparel_dec = primary_l1 == "CAT-001" and (year, month) == (2025, 12)
                    reasons = REFUND_REASONS_QUALITY if is_apparel_dec else REFUND_REASONS
                    refunds.append({
                        "refund_id": _id("RFD", refund_seq, 5),
                        "order_id": order_id,
                        "user_id": buyer["user_id"],
                        "refund_type": random.choice(["仅退款", "退货退款"]),
                        "refund_amount": refund_amt,
                        "reason": random.choice(reasons),
                        "status": "COMPLETED",
                        "apply_time": _iso(apply_dt),
                        "complete_time": _iso(complete_dt),
                    })
                    order["refund_amount"] = refund_amt
                    # 全额退款则订单状态升级为 6
                    if refund_amt >= order_pay * 0.95:
                        order["status"] = 6

            orders.append(order)
            items.extend(this_order_items)

            # 优惠券使用：约 35% 订单使用优惠券
            if status in (2, 3, 4, 6) and discount_amount > 0 and random.random() < 0.5:
                cu_seq += 1
                coupon_usages.append({
                    "usage_id": _id("CPN-USE", cu_seq, 5),
                    "coupon_code": f"CP{random.randint(10000, 99999)}",
                    "campaign_id": random.choice(campaigns)["campaign_id"],
                    "user_id": buyer["user_id"],
                    "order_id": order_id,
                    "coupon_amount": round(discount_amount, 2),
                    "status": "USED",
                    "issued_at": _iso(create_dt - timedelta(days=random.randint(1, 30))),
                    "used_at": _iso(payment_dt),
                })

    # 补充未使用 / 已过期的优惠券（让 t_coupon_usage 总数 ~5000）
    while cu_seq < 5000:
        cu_seq += 1
        issue_dt = TODAY - timedelta(days=random.randint(30, 200))
        status = random.choices(["ISSUED", "EXPIRED"], weights=[0.5, 0.5])[0]
        coupon_usages.append({
            "usage_id": _id("CPN-USE", cu_seq, 5),
            "coupon_code": f"CP{random.randint(10000, 99999)}",
            "campaign_id": random.choice(campaigns)["campaign_id"],
            "user_id": random.choice(users)["user_id"],
            "order_id": None,
            "coupon_amount": random.choice([5, 10, 20, 50, 100]),
            "status": status,
            "issued_at": _iso(issue_dt),
            "used_at": None,
        })

    # 把 _l1 字段从 items 移除，准备入库
    for it in items:
        it.pop("_l1", None)

    return orders, items, refunds, logistics, coupon_usages


# ============================================================
# 用户行为（80,000，近 6 个月）
# ============================================================
def gen_user_behaviors(users, products):
    behaviors = []
    six_months_ago = TODAY - timedelta(days=180)
    user_pool_weights = _pareto_user_weights(users)
    total_seconds = int((TODAY - six_months_ago).total_seconds())
    btypes = ["VIEW", "VIEW", "VIEW", "VIEW", "SEARCH", "ADD_CART", "COLLECT", "SHARE"]
    for i in range(1, 80001):
        user = random.choices(users, weights=user_pool_weights, k=1)[0]
        dt = six_months_ago + timedelta(seconds=random.randint(0, total_seconds))
        channel = random.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0]
        btype = random.choice(btypes)
        target_type = "PRODUCT" if btype in ("VIEW", "ADD_CART", "COLLECT") else random.choice(["PRODUCT", "CATEGORY", "SHOP"])
        target_id = random.choice(products)["product_id"] if target_type == "PRODUCT" else None
        # 同一用户同一会话内的行为共享 session_id
        session_id = f"SES-{user['user_id']}-{dt.strftime('%Y%m%d')}-{random.randint(0, 4)}"
        behaviors.append({
            "behavior_id": _id("BHV", i, 7),
            "user_id": user["user_id"],
            "behavior_type": btype,
            "target_type": target_type,
            "target_id": target_id,
            "session_id": session_id,
            "channel": channel,
            "device_type": random.choice(DEVICE_BY_CHANNEL[channel]),
            "gmt_create": _iso(dt),
        })
    return behaviors


# ============================================================
# 入库
# ============================================================
def _insert_batch(conn: sqlite3.Connection, table: str, rows: list[dict], extra_drop: list[str] | None = None):
    if not rows:
        return
    sample = {k: v for k, v in rows[0].items() if not k.startswith("_") and k not in (extra_drop or [])}
    cols = list(sample.keys())
    placeholders = ",".join(["?"] * len(cols))
    sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders})"
    payload = []
    for r in rows:
        payload.append(tuple(r.get(c) for c in cols))
    conn.executemany(sql, payload)


def generate_all() -> dict:
    """生成全部数据并写入 demo DB"""
    conn = _connect()
    try:
        _exec_ddl(conn)

        print("→ 生成类目...")
        cats = gen_categories()
        _insert_batch(conn, "t_category", [{
            "category_id": c["id"], "category_name": c["name"], "parent_id": c["parent"],
            "level": c["level"], "sort_order": i, "gmt_create": _iso(DATA_START - timedelta(days=400)),
        } for i, c in enumerate(cats)])

        print("→ 生成店铺...")
        shops = gen_shops(cats)
        _insert_batch(conn, "t_shop", shops)

        print("→ 生成商品与 SKU...")
        products, skus = gen_products_and_skus(cats, shops)
        _insert_batch(conn, "t_product", products, extra_drop=["_l1"])
        _insert_batch(conn, "t_sku", skus)

        print("→ 生成用户...")
        users = gen_users()
        _insert_batch(conn, "t_user", users)

        print("→ 生成营销活动...")
        campaigns = gen_campaigns()
        _insert_batch(conn, "t_campaign", campaigns)

        print(f"→ 生成订单 / 订单明细 / 退款 / 物流 / 优惠券使用（耗时较长）...")
        orders, items, refunds, logistics, coupon_usages = gen_orders(
            users, shops, products, skus, cats, campaigns
        )
        _insert_batch(conn, "t_order", orders)
        _insert_batch(conn, "t_order_item", items)
        _insert_batch(conn, "t_refund", refunds)
        _insert_batch(conn, "t_logistics", logistics)
        _insert_batch(conn, "t_coupon_usage", coupon_usages)

        print("→ 生成用户行为（80,000 条）...")
        behaviors = gen_user_behaviors(users, products)
        _insert_batch(conn, "t_user_behavior", behaviors)

        conn.commit()

        summary = {
            "t_user": len(users),
            "t_category": len(cats),
            "t_shop": len(shops),
            "t_product": len(products),
            "t_sku": len(skus),
            "t_campaign": len(campaigns),
            "t_order": len(orders),
            "t_order_item": len(items),
            "t_refund": len(refunds),
            "t_logistics": len(logistics),
            "t_coupon_usage": len(coupon_usages),
            "t_user_behavior": len(behaviors),
        }
        return summary
    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    summary = generate_all()
    print("\n演示数据生成完成：")
    for k, v in summary.items():
        print(f"  {k}: {v:>7,} 条")
