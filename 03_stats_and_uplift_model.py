"""
Zomato — Statistical Testing + Light ML (Uplift)
Tests whether the discount's effect on conversion is statistically
significant within each segment, then fits a logistic regression to
estimate per-user uplift (P(convert|discount) - P(convert|no discount)).
"""

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

pd.set_option("display.width", 120)

users = pd.read_csv("/home/claude/zomato/data/dim_users.csv")

# ---------------------------------------------------------------------------
# CHI-SQUARE TEST per segment: is discount_shown independent of converted?
# ---------------------------------------------------------------------------
print("=" * 72)
print("CHI-SQUARE TEST: discount effect on conversion, by segment")
print("=" * 72)

results = []
for seg in users["segment"].unique():
    sub = users[users["segment"] == seg]
    contingency = pd.crosstab(sub["discount_shown"], sub["converted"])
    chi2, p_value, dof, expected = chi2_contingency(contingency)

    rate_no_discount = sub[~sub["discount_shown"]]["converted"].mean()
    rate_discount = sub[sub["discount_shown"]]["converted"].mean()
    lift_pct_points = (rate_discount - rate_no_discount) * 100

    results.append({
        "segment": seg,
        "conv_rate_no_discount": round(rate_no_discount * 100, 1),
        "conv_rate_discount": round(rate_discount * 100, 1),
        "lift_pct_points": round(lift_pct_points, 1),
        "chi2_stat": round(chi2, 2),
        "p_value": round(p_value, 6),
        "significant_at_0.01": p_value < 0.01,
    })

results_df = pd.DataFrame(results).sort_values("lift_pct_points", ascending=False)
print(results_df.to_string(index=False))

# ---------------------------------------------------------------------------
# LIGHT ML: Logistic Regression predicting conversion, with discount as a
# feature, then estimate individual uplift by scoring each user twice
# (once as if discount_shown=1, once as if discount_shown=0)
# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("UPLIFT MODEL (Logistic Regression)")
print("=" * 72)

model_df = users.copy()
model_df = pd.get_dummies(model_df, columns=["segment", "city_tier"], drop_first=True)

segment_dummy_cols = [c for c in model_df.columns if c.startswith("segment_")]
city_dummy_cols = [c for c in model_df.columns if c.startswith("city_tier_")]

# CRITICAL: add segment x discount INTERACTION terms. Without these, a logistic
# regression applies one global discount coefficient to every segment, which
# cannot represent "the discount works differently for lapsed vs. active users"
# - the entire point of an uplift model. This was caught after the first run
# produced a segment ranking that contradicted the chi-square ground truth.
for col in segment_dummy_cols:
    model_df[f"{col}_x_discount"] = model_df[col].astype(int) * model_df["discount_shown"].astype(int)
interaction_cols = [f"{c}_x_discount" for c in segment_dummy_cols]

feature_cols = segment_dummy_cols + city_dummy_cols + interaction_cols + [
    "historical_order_count", "days_since_last_order", "discount_shown"
]

X = model_df[feature_cols].astype(float)
y = model_df["converted"].astype(int)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

logreg = LogisticRegression(max_iter=1000)
logreg.fit(X_scaled, y)

# Score each user twice: with discount forced on, then forced off.
# Interaction columns must be recomputed for each scenario, not just discount_shown.
X_discount_on = X.copy()
X_discount_on["discount_shown"] = 1
for col in segment_dummy_cols:
    X_discount_on[f"{col}_x_discount"] = X_discount_on[col] * 1

X_discount_off = X.copy()
X_discount_off["discount_shown"] = 0
for col in segment_dummy_cols:
    X_discount_off[f"{col}_x_discount"] = X_discount_off[col] * 0

prob_on = logreg.predict_proba(scaler.transform(X_discount_on))[:, 1]
prob_off = logreg.predict_proba(scaler.transform(X_discount_off))[:, 1]

users["predicted_uplift"] = prob_on - prob_off

print("\nAverage predicted uplift by segment (from the model, cross-check vs. chi-square lift):")
print(users.groupby("segment")["predicted_uplift"].mean().round(3).sort_values(ascending=False))

coef_df = pd.DataFrame({"feature": feature_cols, "coefficient": logreg.coef_[0]}).sort_values(
    "coefficient", ascending=False
)
print("\nModel coefficients (standardized):")
print(coef_df.to_string(index=False))

# ---------------------------------------------------------------------------
# DISCOUNT ROI SUMMARY — the business-facing number
# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("DISCOUNT ROI BY SEGMENT")
print("=" * 72)

orders = pd.read_csv("/home/claude/zomato/data/fact_orders.csv")
orders_clean = orders[~orders["order_id"].str.endswith("_DUP")]
orders_clean = orders_clean[orders_clean["order_value"] > 0]

discount_spend_by_seg = (
    orders_clean[orders_clean["discount_shown"] == True]
    .merge(users[["user_id", "segment"]], on="user_id")
    .groupby("segment")["discount_amount"].sum()
)

roi_summary = results_df.set_index("segment").join(discount_spend_by_seg.rename("total_discount_spend"))
roi_summary["incremental_converted_users"] = (
    roi_summary["lift_pct_points"] / 100 * users.groupby("segment").size()
).round(0)
roi_summary["discount_cost_per_incremental_user"] = (
    roi_summary["total_discount_spend"] / roi_summary["incremental_converted_users"]
).round(2)

print(roi_summary[["lift_pct_points", "total_discount_spend", "incremental_converted_users",
                     "discount_cost_per_incremental_user"]].to_string())

results_df.to_csv("/home/claude/zomato/data/significance_test_results.csv", index=False)
roi_summary.to_csv("/home/claude/zomato/data/discount_roi_summary.csv")
users[["user_id", "segment", "predicted_uplift"]].to_csv("/home/claude/zomato/data/user_uplift_scores.csv", index=False)
print("\nSaved: significance_test_results.csv, discount_roi_summary.csv, user_uplift_scores.csv")
