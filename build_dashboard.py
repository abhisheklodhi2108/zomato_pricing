"""
Zomato — Dashboard Visualizations
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False

COLOR_PRIMARY = "#2F6F63"
COLOR_SECONDARY = "#C9A227"
COLOR_MUTED = "#9BA6A0"
COLOR_ACCENT = "#B5563C"

results_df = pd.read_csv("/home/claude/zomato/data/significance_test_results.csv")
roi_df = pd.read_csv("/home/claude/zomato/data/discount_roi_summary.csv")

fig, axes = plt.subplots(2, 2, figsize=(13, 10))
fig.suptitle("Zomato Differential Pricing — Discount Impact Dashboard", fontsize=16, fontweight="bold", y=0.98)

# ---------------------------------------------------------------------------
# CHART 1: Conversion rate with vs without discount, by segment
# ---------------------------------------------------------------------------
ax1 = axes[0, 0]
segs = results_df.sort_values("lift_pct_points", ascending=False)["segment"]
x = np.arange(len(segs))
width = 0.35
no_disc = results_df.set_index("segment").loc[segs, "conv_rate_no_discount"]
disc = results_df.set_index("segment").loc[segs, "conv_rate_discount"]

ax1.bar(x - width/2, no_disc, width, label="No Discount", color=COLOR_MUTED)
ax1.bar(x + width/2, disc, width, label="Discount Shown", color=COLOR_PRIMARY)
ax1.set_title("Conversion Rate: Discount vs. No Discount", fontweight="bold", fontsize=12)
ax1.set_ylabel("Conversion rate (%)")
ax1.set_xticks(x)
ax1.set_xticklabels(segs, fontsize=9)
ax1.legend(fontsize=9)

# ---------------------------------------------------------------------------
# CHART 2: Lift in percentage points, with significance flagged
# ---------------------------------------------------------------------------
ax2 = axes[0, 1]
lift_sorted = results_df.sort_values("lift_pct_points", ascending=True)
colors2 = [COLOR_PRIMARY if sig else COLOR_MUTED for sig in lift_sorted["significant_at_0.01"]]
bars2 = ax2.barh(lift_sorted["segment"], lift_sorted["lift_pct_points"], color=colors2)
ax2.set_title("Conversion Lift from Discount (pp)\ngray = not statistically significant (p>0.01)", fontweight="bold", fontsize=11)
ax2.set_xlabel("Lift (percentage points)")
for bar, val in zip(bars2, lift_sorted["lift_pct_points"]):
    ax2.text(val + 0.5, bar.get_y() + bar.get_height()/2, f"+{val}pp", va="center", fontsize=9)

# ---------------------------------------------------------------------------
# CHART 3: Discount cost per incremental converted user
# ---------------------------------------------------------------------------
ax3 = axes[1, 0]
roi_sorted = roi_df.sort_values("discount_cost_per_incremental_user", ascending=True)
colors3 = [COLOR_PRIMARY if v < 200 else COLOR_SECONDARY if v < 1000 else COLOR_ACCENT
           for v in roi_sorted["discount_cost_per_incremental_user"]]
bars3 = ax3.bar(roi_sorted["segment"], roi_sorted["discount_cost_per_incremental_user"], color=colors3)
ax3.set_title("Discount Cost per Incremental Converted User", fontweight="bold", fontsize=12)
ax3.set_ylabel("₹ spent per incremental conversion")
ax3.set_yscale("log")
for bar, val in zip(bars3, roi_sorted["discount_cost_per_incremental_user"]):
    ax3.text(bar.get_x() + bar.get_width()/2, val * 1.15, f"₹{val:,.0f}", ha="center", fontsize=9, fontweight="bold")

# ---------------------------------------------------------------------------
# CHART 4: Net revenue per user, discount vs no discount (the key business chart)
# ---------------------------------------------------------------------------
ax4 = axes[1, 1]
rev_df = pd.read_csv("/home/claude/zomato/data/segment_revenue_per_user.csv")
rev_pivot = rev_df.pivot(index="segment", columns="discount_shown", values="net_revenue_per_user")
rev_pivot = rev_pivot.reindex(segs.values)

x4 = np.arange(len(rev_pivot))
ax4.bar(x4 - width/2, rev_pivot[0], width, label="No Discount", color=COLOR_MUTED)
ax4.bar(x4 + width/2, rev_pivot[1], width, label="Discount Shown", color=COLOR_ACCENT)
ax4.set_title("Net Revenue per User: Discount vs. No Discount", fontweight="bold", fontsize=12)
ax4.set_ylabel("Net revenue per user (₹)")
ax4.set_xticks(x4)
ax4.set_xticklabels(rev_pivot.index, fontsize=9)
ax4.legend(fontsize=9)
ax4.axhline(0, color="black", linewidth=0.8)
ax4.text(0.02, 0.95, "Discount REDUCES net revenue/user\nfor active & high-frequency segments",
          transform=ax4.transAxes, fontsize=8, va="top", style="italic", color=COLOR_ACCENT)

plt.tight_layout(rect=[0, 0, 1, 0.96])
plt.savefig("/home/claude/zomato/dashboard.png", dpi=150, bbox_inches="tight")
print("Saved dashboard.png")
