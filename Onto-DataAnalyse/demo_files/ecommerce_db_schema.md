# 电商平台数据库设计文档

> 本文档描述某中型 B2C 电商平台的核心数据库结构（SQLite 演示版）
> 数据库文件：`demo_ecommerce.db` · 共 12 张表 · 覆盖交易/商品/用户/营销/物流五大业务域
> 所有时间字段统一为 Asia/Shanghai 本地时间（ISO 8601 格式）

## 业务域概览

| 域 | 包含表 | 说明 |
|----|--------|------|
| 用户域 | t_user, t_user_behavior | 注册用户与浏览/搜索/加购等行为 |
| 商品域 | t_product, t_sku, t_category | 商品 SPU / SKU / 3 级类目 |
| 店铺域 | t_shop | 平台商家店铺信息 |
| 交易域 | t_order, t_order_item, t_logistics, t_refund | 订单主表与明细、物流、退款 |
| 营销域 | t_campaign, t_coupon_usage | 营销活动与优惠券领用使用 |

---

## 1. t_user — 用户主表

| 字段名 | 类型 | 含义 | 备注 |
|--------|------|------|------|
| user_id | TEXT | 用户唯一 ID | 主键，格式：`USR-00001` |
| nickname | TEXT | 昵称 | |
| gender | TEXT | 性别 | M 男 / F 女 / U 未知 |
| age_range | TEXT | 年龄段 | 18-25 / 26-35 / 36-45 / 46-55 / 55+ |
| province | TEXT | 省份 | |
| city | TEXT | 城市 | |
| register_channel | TEXT | 注册渠道 | APP / PC / MINI（小程序） / H5 |
| user_level | TEXT | 用户等级 | 普通 / VIP1 / VIP2 / VIP3 |
| register_date | TEXT | 注册时间 | ISO 8601 |
| last_login_date | TEXT | 最后登录时间 | |
| gmt_create | TEXT | 记录创建时间 | |

---

## 2. t_category — 商品类目（3 级树形）

| 字段名 | 类型 | 含义 | 备注 |
|--------|------|------|------|
| category_id | TEXT | 类目 ID | 主键。ID 体现层级：L1 `CAT-001`，L2 `CAT-001-01`，L3 `CAT-001-01-01` |
| category_name | TEXT | 类目名称 | |
| parent_id | TEXT | 上级类目 ID | L1 为 NULL |
| level | INTEGER | 层级 | 1（一级）/ 2（二级）/ 3（三级，叶子） |
| sort_order | INTEGER | 排序 | |
| gmt_create | TEXT | 创建时间 | |

**一级类目**：CAT-001 服装 / CAT-002 3C数码 / CAT-003 家居家电 / CAT-004 食品生鲜 / CAT-005 美妆个护

---

## 3. t_shop — 店铺

| 字段名 | 类型 | 含义 | 备注 |
|--------|------|------|------|
| shop_id | TEXT | 店铺 ID | 主键，格式：`SHOP-0001` |
| shop_name | TEXT | 店铺名 | |
| shop_level | INTEGER | 店铺评级 | 1~5 星 |
| main_category | TEXT | 主营类目 | 外键 → t_category.category_id（一级类目） |
| province | TEXT | 店铺所在省 | |
| deposit | REAL | 保证金（元） | |
| status | INTEGER | 状态 | 1 营业 / 0 暂停 |
| gmt_create | TEXT | 创建时间 | |

---

## 4. t_product — 商品 SPU

| 字段名 | 类型 | 含义 | 备注 |
|--------|------|------|------|
| product_id | TEXT | 商品 SPU ID | 主键，格式：`PRD-00001` |
| product_name | TEXT | 商品名 | |
| category_id | TEXT | 所属类目 | 外键 → t_category.category_id（一般指向 L3 叶子类目） |
| shop_id | TEXT | 所属店铺 | 外键 → t_shop.shop_id |
| brand | TEXT | 品牌 | |
| status | INTEGER | 上下架状态 | 1 上架 / 2 下架 / 3 删除 |
| list_price | REAL | 标准售价（元） | |
| avg_rating | REAL | 平均评分 | 1~5 |
| review_count | INTEGER | 评价数 | |
| gmt_create | TEXT | 上架时间 | |
| gmt_modified | TEXT | 最后修改时间 | |

---

## 5. t_sku — 商品 SKU（最小可售单元）

| 字段名 | 类型 | 含义 | 备注 |
|--------|------|------|------|
| sku_id | TEXT | SKU 唯一 ID | 主键，格式：`SKU-000001` |
| product_id | TEXT | 所属 SPU | 外键 → t_product.product_id |
| sku_name | TEXT | SKU 名称（含规格） | |
| color | TEXT | 颜色 | |
| size | TEXT | 尺寸 | S/M/L/XL/XXL/均码 |
| stock | INTEGER | 当前库存 | |
| sale_price | REAL | 销售价（元） | 最终前台展示价 |
| cost_price | REAL | 成本价（元） | |
| gmt_create | TEXT | 创建时间 | |

---

## 6. t_order — 订单主表

| 字段名 | 类型 | 含义 | 备注 |
|--------|------|------|------|
| order_id | TEXT | 订单唯一 ID | 主键，格式：`ORD-000001` |
| buyer_id | TEXT | 买家 ID | 外键 → t_user.user_id |
| seller_id | TEXT | 卖家店铺 ID | 外键 → t_shop.shop_id |
| status | INTEGER | 订单状态 | **1 待付款 / 2 已付款 / 3 已发货 / 4 已签收 / 5 已取消 / 6 退款完成** |
| payment_amount | REAL | 实付金额（元） | 优惠分摊后的最终支付金额，**计算 GMV 用这个** |
| original_amount | REAL | 原始金额（元） | 优惠前商品总价 |
| discount_amount | REAL | 优惠金额（元） | 含券、活动等所有优惠 |
| refund_amount | REAL | 已退款金额（元） | 累计 |
| channel | TEXT | 下单渠道 | APP / PC / MINI / H5 |
| device_type | TEXT | 设备类型 | iOS / Android / Windows / Mac |
| gmt_create | TEXT | 下单时间 | |
| gmt_payment | TEXT | 支付完成时间 | 未支付时为空 |
| gmt_modified | TEXT | 最后修改时间 | |

> **业务规则**：**有效订单** = status NOT IN (5, 6)；退款完成订单从 GMV 中扣减 refund_amount。

---

## 7. t_order_item — 订单明细

| 字段名 | 类型 | 含义 | 备注 |
|--------|------|------|------|
| item_id | TEXT | 明细 ID | 主键，格式：`ITM-0000001` |
| order_id | TEXT | 所属订单 | 外键 → t_order.order_id |
| product_id | TEXT | 商品 SPU | 外键 → t_product.product_id |
| sku_id | TEXT | 商品 SKU | 外键 → t_sku.sku_id |
| quantity | INTEGER | 购买数量 | |
| unit_price | REAL | 标准单价（元） | |
| pay_price | REAL | 实付单价（元） | 分摊订单优惠后的单价 |
| category_id | TEXT | 类目 ID | 冗余字段，外键 → t_category.category_id |
| gmt_create | TEXT | 创建时间 | |

---

## 8. t_user_behavior — 用户行为

| 字段名 | 类型 | 含义 | 备注 |
|--------|------|------|------|
| behavior_id | TEXT | 行为 ID | 主键，格式：`BHV-0000001` |
| user_id | TEXT | 用户 ID | 外键 → t_user.user_id |
| behavior_type | TEXT | 行为类型 | VIEW / SEARCH / ADD_CART / COLLECT / SHARE |
| target_type | TEXT | 对象类型 | PRODUCT / CATEGORY / SHOP |
| target_id | TEXT | 对象 ID | |
| session_id | TEXT | 会话 ID | 同一次访问内的行为共享 |
| channel | TEXT | 渠道 | APP / PC / MINI / H5 |
| device_type | TEXT | 设备 | |
| gmt_create | TEXT | 行为时间 | |

---

## 9. t_campaign — 营销活动

| 字段名 | 类型 | 含义 | 备注 |
|--------|------|------|------|
| campaign_id | TEXT | 活动 ID | 主键，格式：`CMP-001` |
| campaign_name | TEXT | 活动名 | |
| campaign_type | TEXT | 活动类型 | 满减 / 折扣 / 秒杀 / 拼团 / 大促 |
| start_time | TEXT | 活动开始时间 | |
| end_time | TEXT | 活动结束时间 | |
| budget | REAL | 预算（元） | |
| target_category | TEXT | 主要面向类目 | 外键 → t_category.category_id；NULL 表示全平台 |
| gmt_create | TEXT | 创建时间 | |

---

## 10. t_coupon_usage — 优惠券领用使用

| 字段名 | 类型 | 含义 | 备注 |
|--------|------|------|------|
| usage_id | TEXT | 记录 ID | 主键 |
| coupon_code | TEXT | 券码 | |
| campaign_id | TEXT | 关联活动 | 外键 → t_campaign.campaign_id |
| user_id | TEXT | 领取用户 | 外键 → t_user.user_id |
| order_id | TEXT | 使用订单 | 外键 → t_order.order_id（未使用时为空） |
| coupon_amount | REAL | 券面额（元） | |
| status | TEXT | 状态 | ISSUED 已领取 / USED 已使用 / EXPIRED 已过期 |
| issued_at | TEXT | 领取时间 | |
| used_at | TEXT | 使用时间 | |

---

## 11. t_logistics — 物流记录

| 字段名 | 类型 | 含义 | 备注 |
|--------|------|------|------|
| logistics_id | TEXT | 物流 ID | 主键 |
| order_id | TEXT | 关联订单 | 外键 → t_order.order_id |
| carrier | TEXT | 承运商 | 顺丰 / 中通 / 京东物流 / EMS / 圆通 |
| tracking_no | TEXT | 运单号 | |
| ship_time | TEXT | 发货时间 | |
| delivery_time | TEXT | 签收时间 | |
| province | TEXT | 收货省 | |
| city | TEXT | 收货市 | |
| status | TEXT | 物流状态 | SHIPPED / IN_TRANSIT / DELIVERED / EXCEPTION |

---

## 12. t_refund — 退款记录

| 字段名 | 类型 | 含义 | 备注 |
|--------|------|------|------|
| refund_id | TEXT | 退款 ID | 主键 |
| order_id | TEXT | 关联订单 | 外键 → t_order.order_id |
| user_id | TEXT | 用户 ID | 外键 → t_user.user_id |
| refund_type | TEXT | 退款类型 | 仅退款 / 退货退款 |
| refund_amount | REAL | 退款金额（元） | |
| reason | TEXT | 退款原因 | 质量问题 / 尺寸不合 / 不喜欢 / 物流问题 / 其他 |
| status | TEXT | 处理状态 | PENDING / AGREED / REJECTED / COMPLETED |
| apply_time | TEXT | 申请时间 | |
| complete_time | TEXT | 完成时间 | |

---

## 表关系总览

```
t_user ──N──→ t_order ──N──→ t_order_item ──N──→ t_sku
                │                  │                │
                │                  └──N──→ t_product ──N──→ t_category（3 级树）
                │                                            t_product ──N──→ t_shop
                ├──N──→ t_logistics（一对一）
                ├──N──→ t_refund（一对多，部分退款）
                └──N──→ t_coupon_usage（一对一，使用时）

t_user ──N──→ t_user_behavior（浏览/搜索/加购等）
t_user ──N──→ t_coupon_usage（领取，多张券）

t_campaign ──N──→ t_coupon_usage（一个活动可发多种券）
```

## 关键业务规则

- **有效订单**：status NOT IN (5 已取消, 6 退款完成)
- **GMV 口径**：SUM(t_order.payment_amount) WHERE 有效订单
- **退款率口径**：SUM(t_refund.refund_amount) / GMV（按月统计）
- **新用户**：首次下单成功且状态非 5 的用户，按首单日所属周期判定
- **活跃用户**：统计周期内有过任一登录/浏览/搜索/加购/下单的用户
- **复购用户**：统计周期内有 ≥2 笔有效订单的用户
- **测试订单排除**：用户 ID 在测试名单中，或订单金额 ≤ 0.01 元
- **时区**：所有时间字段均按 UTC+8（Asia/Shanghai）解读，存储不带时区后缀

## 数据量参考（演示库）

| 表 | 行数 | 时间范围 |
|----|------|----------|
| t_user | 2,000 | 历史累计 |
| t_category | 30 | 静态 |
| t_shop | 50 | 静态 |
| t_product | 500 | 静态 |
| t_sku | ~1,500 | 静态 |
| t_campaign | 30 | 近 12 个月 |
| t_order | ~15,000 | 2025-06 ~ 2026-05 |
| t_order_item | ~21,000 | 同上 |
| t_logistics | ~13,000 | 同上 |
| t_refund | ~500 | 同上 |
| t_coupon_usage | 5,000 | 近 12 个月 |
| t_user_behavior | 80,000 | 近 6 个月 |
