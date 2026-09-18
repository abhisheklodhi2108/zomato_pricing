"""
Zomato — SQL Segmentation
Loads users + orders into SQLite, runs segment-level analysis on the
embedded randomized discount assignment.
"""

import sqlite3
import pandas as pd

conn = sqlite3.connect("/home/claude/zomato/zomato.db")

users = pd.read_csv("/home/claude/zomato/data/dim_users.csv")
orders = pd.read_csv("/home/claude/zomato/data/fact_orders.csv")

orders_clean = orders[~orders["order_id"].str.endswith("_DUP")].copy()
orders_clean = orders_clean[orders_clean["order_value"] > 0].copy()
orders_clean["channel"] = orders_clean["channel"].fillna("app")

users.to_sql("users", conn, if_exists="replace", index=False)
orders_clean.to_sql("orders", conn, if_exists="replace", index=False)

def run(label, query):
    print(f"\n{'='*72}\n{label}\n{'='*72}")
    df = pd.read_sql_query(query, conn)
    print(df.to_string(index=False))
    return df

q1 = run("Q1 — Conversion rate by segment x discount exposure", """
SELECT
    segment,
    discount_shown,
    COUNT(*) AS users_in_group,
    SUM(converted) AS converted_count,
    ROUND(100.0 * SUM(converted) / COUNT(*), 1) AS conversion_rate_pct
FROM users
GROUP BY segment, discount_shown
ORDER BY segment, discount_shown
""")

q2 = run("Q2 — Discount spend by segment (redeemed orders only)", """
SELECT
    u.segment,
    COUNT(o.order_id) AS discounted_orders,
    ROUND(SUM(o.discount_amount), 2) AS total_discount_spend,
    ROUND(AVG(o.discount_amount), 2) AS avg_discount_per_order,
    ROUND(SUM(o.net_revenue), 2) AS total_net_revenue
FROM orders o
JOIN users u ON o.user_id = u.user_id
WHERE o.discount_shown = 1
GROUP BY u.segment
ORDER BY total_discount_spend DESC
""")

q3 = run("Q3 — Net revenue per user by segment x discount", """
SELECT
    u.segment,
    u.discount_shown,
    COUNT(DISTINCT u.user_id) AS users_in_group,
    ROUND(COALESCE(SUM(o.net_revenue), 0), 2) AS total_net_revenue,
    ROUND(COALESCE(SUM(o.net_revenue), 0) / COUNT(DISTINCT u.user_id), 2) AS net_revenue_per_user
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.segment, u.discount_shown
ORDER BY u.segment, u.discount_shown
""")

q4 = run("Q4 — Conversion rate by city tier x discount exposure", """
SELECT
    city_tier,
    discount_shown,
    ROUND(100.0 * SUM(converted) / COUNT(*), 1) AS conversion_rate_pct
FROM users
GROUP BY city_tier, discount_shown
ORDER BY city_tier, discount_shown
""")

conn.close()
q1.to_csv("/home/claude/zomato/data/segment_lift.csv", index=False)
q2.to_csv("/home/claude/zomato/data/segment_discount_spend.csv", index=False)
q3.to_csv("/home/claude/zomato/data/segment_revenue_per_user.csv", index=False)
print("\n\nSaved query results to data/*.csv")
