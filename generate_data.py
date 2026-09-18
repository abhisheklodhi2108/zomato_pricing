"""
Zomato — Differential Pricing Synthetic Data Generator
Users are segmented (new/active/lapsed/high_frequency). Within each segment,
discount exposure is RANDOMLY assigned during the campaign window - this
mirrors an embedded A/B test, letting us measure genuine causal lift rather
than just correlation. Baseline conversion rate and discount sensitivity
both vary by segment, which is where the real finding will come from.

Synthetic dataset created to simulate realistic operational scenarios -
not proprietary Zomato data.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

rng = np.random.default_rng(21)

N_USERS = 9000
CAMPAIGN_START = datetime(2026, 3, 1)
CAMPAIGN_DAYS = 30

SEGMENTS = ["new", "active", "lapsed", "high_frequency"]
SEGMENT_WEIGHTS = [0.20, 0.35, 0.25, 0.20]

# Baseline conversion rate (no discount) and discount sensitivity (lift) differ
# by segment - this is the real signal the analysis should uncover
SEGMENT_PROFILE = {
    # baseline_conv_rate: chance of ordering in the 30-day window with NO discount
    # discount_lift: ADDITIONAL probability added when shown the discount
    "new":             {"baseline_conv_rate": 0.18, "discount_lift": 0.22},
    "active":          {"baseline_conv_rate": 0.55, "discount_lift": 0.08},
    "lapsed":          {"baseline_conv_rate": 0.10, "discount_lift": 0.28},
    "high_frequency":  {"baseline_conv_rate": 0.78, "discount_lift": 0.04},
}

CITY_TIERS = ["tier_1", "tier_2", "tier_3"]

# ---------------------------------------------------------------------------
# USERS
# ---------------------------------------------------------------------------
user_ids = [f"U{300000+i}" for i in range(N_USERS)]
segment = rng.choice(SEGMENTS, size=N_USERS, p=SEGMENT_WEIGHTS)
city_tier = rng.choice(CITY_TIERS, size=N_USERS, p=[0.45, 0.35, 0.20])

historical_orders = np.where(
    segment == "high_frequency", rng.poisson(18, N_USERS),
    np.where(segment == "active", rng.poisson(6, N_USERS),
    np.where(segment == "lapsed", rng.poisson(4, N_USERS),
    rng.poisson(0, N_USERS)))  # new users: 0 history
)

days_since_last_order = np.where(
    segment == "lapsed", rng.integers(60, 180, N_USERS),
    np.where(segment == "new", rng.integers(9999, 10000, N_USERS),  # never ordered
    np.where(segment == "high_frequency", rng.integers(0, 5, N_USERS),
    rng.integers(3, 21, N_USERS)))  # active
)

signup_offsets = rng.integers(0, 700, N_USERS)
signup_dates = [CAMPAIGN_START - timedelta(days=int(o)) for o in signup_offsets]

users = pd.DataFrame({
    "user_id": user_ids,
    "segment": segment,
    "city_tier": city_tier,
    "signup_date": [d.date().isoformat() for d in signup_dates],
    "historical_order_count": historical_orders,
    "days_since_last_order": days_since_last_order,
})

# ---------------------------------------------------------------------------
# RANDOM DISCOUNT ASSIGNMENT within each segment (the embedded A/B test)
# 50/50 split within each segment
# ---------------------------------------------------------------------------
users["discount_shown"] = rng.random(N_USERS) < 0.5

# ---------------------------------------------------------------------------
# CONVERSION during the campaign window - driven by segment baseline + lift
# ---------------------------------------------------------------------------
def conv_prob(row):
    profile = SEGMENT_PROFILE[row["segment"]]
    p = profile["baseline_conv_rate"]
    if row["discount_shown"]:
        p += profile["discount_lift"]
    return min(p, 0.95)

users["conv_probability"] = users.apply(conv_prob, axis=1)
users["converted"] = rng.random(N_USERS) < users["conv_probability"]

# ---------------------------------------------------------------------------
# ORDERS - one row per converted user (assume 1 order in window for simplicity,
# some users order more than once - add a Poisson extra-orders layer)
# ---------------------------------------------------------------------------
order_rows = []
oid = 0
for _, row in users[users["converted"]].iterrows():
    n_orders = 1 + rng.poisson(0.3)  # most convert once, some order multiple times
    for _ in range(n_orders):
        oid += 1
        order_offset = rng.integers(0, CAMPAIGN_DAYS)
        order_date = CAMPAIGN_START + timedelta(days=int(order_offset))
        base_value = rng.normal(220, 60)
        base_value = max(99, base_value)  # promo requires order above ₹99

        if row["discount_shown"]:
            discount_pct = 0.70
            discount_amount = min(base_value * discount_pct, 140)
        else:
            discount_amount = 0.0

        order_rows.append({
            "order_id": f"O{900000+oid}",
            "user_id": row["user_id"],
            "order_date": order_date.date().isoformat(),
            "discount_shown": row["discount_shown"],
            "discount_amount": round(discount_amount, 2),
            "order_value": round(base_value, 2),
            "net_revenue": round(base_value - discount_amount, 2),
            "channel": rng.choice(["app", "web"], p=[0.94, 0.06]),
        })

orders = pd.DataFrame(order_rows)

# ---------------------------------------------------------------------------
# INJECT MESSINESS
# ---------------------------------------------------------------------------
# ~1.2% duplicate orders (double-tap checkout bug)
dupe_orders = orders.sample(frac=0.012, random_state=5).copy()
dupe_orders["order_id"] = dupe_orders["order_id"] + "_DUP"
orders = pd.concat([orders, dupe_orders], ignore_index=True)

# ~2% missing channel (logging gap)
mask_missing_channel = rng.random(len(orders)) < 0.02
orders.loc[mask_missing_channel, "channel"] = np.nan

# ~0.5% negative order_value glitch (refund logging)
mask_negative = rng.random(len(orders)) < 0.005
orders.loc[mask_negative, "order_value"] = -abs(orders.loc[mask_negative, "order_value"])

# ---------------------------------------------------------------------------
# SAVE
# ---------------------------------------------------------------------------
users_out = users.drop(columns=["conv_probability"])
users_out.to_csv("/home/claude/zomato/data/dim_users.csv", index=False)
orders.to_csv("/home/claude/zomato/data/fact_orders.csv", index=False)

print("Users:", users_out.shape)
print("Orders:", orders.shape)
print("\nConversion rate by segment x discount_shown:")
print(users.groupby(["segment", "discount_shown"])["converted"].mean().round(3))
print("\nOverall conversion rate:", round(users["converted"].mean() * 100, 1), "%")
