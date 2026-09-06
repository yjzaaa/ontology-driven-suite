-- ============================================================
-- 演示电商数据库 DDL（12 张表）
-- 用于本体驱动数据分析演示，所有时间字段统一 ISO8601 / UTC+8
-- ============================================================

-- ---------- 1. 用户表 ----------
CREATE TABLE IF NOT EXISTS t_user (
    user_id          TEXT PRIMARY KEY,
    nickname         TEXT NOT NULL,
    gender           TEXT,                  -- M / F / U
    age_range        TEXT,                  -- 18-25 / 26-35 / 36-45 / 46-55 / 55+
    province         TEXT,
    city             TEXT,
    register_channel TEXT,                  -- APP / PC / MINI / H5
    user_level       TEXT,                  -- 普通 / VIP1 / VIP2 / VIP3
    register_date    TEXT NOT NULL,
    last_login_date  TEXT,
    gmt_create       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_user_register_date ON t_user(register_date);
CREATE INDEX IF NOT EXISTS idx_user_level ON t_user(user_level);

-- ---------- 2. 商品类目（3 级） ----------
CREATE TABLE IF NOT EXISTS t_category (
    category_id   TEXT PRIMARY KEY,
    category_name TEXT NOT NULL,
    parent_id     TEXT,                     -- 上级类目，1 级为 NULL
    level         INTEGER NOT NULL,         -- 1 / 2 / 3
    sort_order    INTEGER DEFAULT 0,
    gmt_create    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_category_parent ON t_category(parent_id);
CREATE INDEX IF NOT EXISTS idx_category_level ON t_category(level);

-- ---------- 3. 店铺 ----------
CREATE TABLE IF NOT EXISTS t_shop (
    shop_id        TEXT PRIMARY KEY,
    shop_name      TEXT NOT NULL,
    shop_level     INTEGER,                 -- 1 ~ 5 星
    main_category  TEXT,                    -- 主营类目 category_id
    province       TEXT,
    deposit        REAL,                    -- 保证金（元）
    status         INTEGER DEFAULT 1,       -- 1 营业 0 暂停
    gmt_create     TEXT NOT NULL
);

-- ---------- 4. 商品 SPU ----------
CREATE TABLE IF NOT EXISTS t_product (
    product_id    TEXT PRIMARY KEY,
    product_name  TEXT NOT NULL,
    category_id   TEXT NOT NULL,            -- → t_category.category_id
    shop_id       TEXT NOT NULL,            -- → t_shop.shop_id
    brand         TEXT,
    status        INTEGER DEFAULT 1,        -- 1 上架 2 下架 3 删除
    list_price    REAL,                     -- 标准售价
    avg_rating    REAL,                     -- 平均评分 1~5
    review_count  INTEGER DEFAULT 0,
    gmt_create    TEXT NOT NULL,
    gmt_modified  TEXT
);
CREATE INDEX IF NOT EXISTS idx_product_category ON t_product(category_id);
CREATE INDEX IF NOT EXISTS idx_product_shop ON t_product(shop_id);

-- ---------- 5. 商品 SKU ----------
CREATE TABLE IF NOT EXISTS t_sku (
    sku_id       TEXT PRIMARY KEY,
    product_id   TEXT NOT NULL,             -- → t_product.product_id
    sku_name     TEXT NOT NULL,
    color        TEXT,
    size         TEXT,
    stock        INTEGER DEFAULT 0,
    sale_price   REAL,
    cost_price   REAL,
    gmt_create   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sku_product ON t_sku(product_id);

-- ---------- 6. 订单主表 ----------
CREATE TABLE IF NOT EXISTS t_order (
    order_id         TEXT PRIMARY KEY,
    buyer_id         TEXT NOT NULL,         -- → t_user.user_id
    seller_id        TEXT NOT NULL,         -- → t_shop.shop_id
    status           INTEGER NOT NULL,      -- 1待付款 2已付款 3已发货 4已签收 5已取消 6退款完成
    payment_amount   REAL NOT NULL,         -- 实付金额（优惠后）
    original_amount  REAL NOT NULL,         -- 原始金额
    discount_amount  REAL DEFAULT 0,        -- 优惠金额
    refund_amount    REAL DEFAULT 0,        -- 退款累计金额
    channel          TEXT,                  -- APP / PC / MINI / H5
    device_type      TEXT,                  -- iOS / Android / Windows / Mac
    gmt_create       TEXT NOT NULL,         -- 下单时间
    gmt_payment      TEXT,                  -- 支付完成时间
    gmt_modified     TEXT
);
CREATE INDEX IF NOT EXISTS idx_order_buyer ON t_order(buyer_id);
CREATE INDEX IF NOT EXISTS idx_order_seller ON t_order(seller_id);
CREATE INDEX IF NOT EXISTS idx_order_status ON t_order(status);
CREATE INDEX IF NOT EXISTS idx_order_create ON t_order(gmt_create);

-- ---------- 7. 订单明细 ----------
CREATE TABLE IF NOT EXISTS t_order_item (
    item_id      TEXT PRIMARY KEY,
    order_id     TEXT NOT NULL,             -- → t_order.order_id
    product_id   TEXT NOT NULL,             -- → t_product.product_id
    sku_id       TEXT NOT NULL,             -- → t_sku.sku_id
    quantity     INTEGER NOT NULL,
    unit_price   REAL NOT NULL,             -- 标准单价
    pay_price    REAL NOT NULL,             -- 实付单价（分摊优惠后）
    category_id  TEXT,                      -- 冗余 → t_category.category_id
    gmt_create   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_item_order ON t_order_item(order_id);
CREATE INDEX IF NOT EXISTS idx_item_product ON t_order_item(product_id);
CREATE INDEX IF NOT EXISTS idx_item_category ON t_order_item(category_id);

-- ---------- 8. 用户行为 ----------
CREATE TABLE IF NOT EXISTS t_user_behavior (
    behavior_id    TEXT PRIMARY KEY,
    user_id        TEXT NOT NULL,           -- → t_user.user_id
    behavior_type  TEXT NOT NULL,           -- VIEW / SEARCH / ADD_CART / COLLECT / SHARE
    target_type    TEXT,                    -- PRODUCT / CATEGORY / SHOP
    target_id      TEXT,
    session_id     TEXT,                    -- 会话 ID（同一次访问内的行为共享）
    channel        TEXT,                    -- APP / PC / MINI / H5
    device_type    TEXT,
    gmt_create     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_behavior_user ON t_user_behavior(user_id);
CREATE INDEX IF NOT EXISTS idx_behavior_create ON t_user_behavior(gmt_create);
CREATE INDEX IF NOT EXISTS idx_behavior_type ON t_user_behavior(behavior_type);

-- ---------- 9. 营销活动 ----------
CREATE TABLE IF NOT EXISTS t_campaign (
    campaign_id     TEXT PRIMARY KEY,
    campaign_name   TEXT NOT NULL,
    campaign_type   TEXT,                   -- 满减 / 折扣 / 秒杀 / 拼团 / 大促
    start_time      TEXT NOT NULL,
    end_time        TEXT NOT NULL,
    budget          REAL,                   -- 营销预算（元）
    target_category TEXT,                   -- 主要面向类目（可空）
    gmt_create      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_campaign_time ON t_campaign(start_time, end_time);

-- ---------- 10. 优惠券使用记录 ----------
CREATE TABLE IF NOT EXISTS t_coupon_usage (
    usage_id      TEXT PRIMARY KEY,
    coupon_code   TEXT NOT NULL,
    campaign_id   TEXT NOT NULL,            -- → t_campaign.campaign_id
    user_id       TEXT NOT NULL,            -- → t_user.user_id
    order_id      TEXT,                     -- → t_order.order_id（已使用时填）
    coupon_amount REAL NOT NULL,            -- 券面额
    status        TEXT NOT NULL,            -- ISSUED / USED / EXPIRED
    issued_at     TEXT NOT NULL,
    used_at       TEXT
);
CREATE INDEX IF NOT EXISTS idx_coupon_user ON t_coupon_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_coupon_order ON t_coupon_usage(order_id);
CREATE INDEX IF NOT EXISTS idx_coupon_status ON t_coupon_usage(status);

-- ---------- 11. 物流记录 ----------
CREATE TABLE IF NOT EXISTS t_logistics (
    logistics_id   TEXT PRIMARY KEY,
    order_id       TEXT NOT NULL,           -- → t_order.order_id
    carrier        TEXT,                    -- 顺丰/中通/京东物流/EMS/圆通
    tracking_no    TEXT,
    ship_time      TEXT,                    -- 发货时间
    delivery_time  TEXT,                    -- 签收时间
    province       TEXT,                    -- 收货省
    city           TEXT,
    status         TEXT NOT NULL            -- SHIPPED / IN_TRANSIT / DELIVERED / EXCEPTION
);
CREATE INDEX IF NOT EXISTS idx_logistics_order ON t_logistics(order_id);
CREATE INDEX IF NOT EXISTS idx_logistics_status ON t_logistics(status);

-- ---------- 12. 退款记录 ----------
CREATE TABLE IF NOT EXISTS t_refund (
    refund_id      TEXT PRIMARY KEY,
    order_id       TEXT NOT NULL,           -- → t_order.order_id
    user_id        TEXT NOT NULL,           -- → t_user.user_id
    refund_type    TEXT NOT NULL,           -- 仅退款 / 退货退款
    refund_amount  REAL NOT NULL,
    reason         TEXT,                    -- 质量问题/不喜欢/尺寸不合/物流问题/其他
    status         TEXT NOT NULL,           -- PENDING / AGREED / REJECTED / COMPLETED
    apply_time     TEXT NOT NULL,
    complete_time  TEXT
);
CREATE INDEX IF NOT EXISTS idx_refund_order ON t_refund(order_id);
CREATE INDEX IF NOT EXISTS idx_refund_status ON t_refund(status);
CREATE INDEX IF NOT EXISTS idx_refund_time ON t_refund(apply_time);
