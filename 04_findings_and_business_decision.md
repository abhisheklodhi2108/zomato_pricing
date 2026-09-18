# Zomato Differential Pricing — Findings & Business Decision

## Setup
9,000 synthetic users across 4 segments (new, active, lapsed, high_frequency). Discount exposure was **randomly assigned within each segment** (50/50 split) — this mirrors an embedded A/B test, letting us measure genuine causal lift rather than relying on observational matching.

## Statistical Results (Chi-Square Test)

| Segment | Conv. Rate (No Discount) | Conv. Rate (Discount) | Lift | p-value | Significant? |
|---|---|---|---|---|---|
| Lapsed | 10.4% | 36.7% | **+26.3pp** | <0.000001 | Yes |
| New | 17.3% | 40.3% | **+23.0pp** | <0.000001 | Yes |
| Active | 55.7% | 64.1% | +8.4pp | 0.000002 | Yes |
| High-frequency | 79.0% | 81.9% | +2.9pp | 0.129 | No — not significant |

**The discount barely moves high-frequency users at all, and the effect isn't statistically distinguishable from zero.** These users were converting anyway.

## Discount ROI by Segment

| Segment | Total Discount Spend | Incremental Converted Users | Cost per Incremental User |
|---|---|---|---|
| Lapsed | Rs 68,254 | 589 | **Rs 115.88** |
| New | Rs 58,601 | 407 | **Rs 143.98** |
| Active | Rs 170,362 | 265 | Rs 642.88 |
| High-frequency | Rs 123,821 | 53 | **Rs 2,336.25** |

The same discount costs **20x more per incremental customer** when shown to high-frequency users versus lapsed users. Nearly 70% of the total discount budget went to active + high-frequency users, who together produced only 24% of the total incremental conversions.

## The Key Business Finding: Net Revenue per User

| Segment | No Discount | Discount Shown | Change |
|---|---|---|---|
| Active | Rs 156.50 | Rs 74.59 | **-Rs 81.91** |
| High-frequency | Rs 226.91 | Rs 93.34 | **-Rs 133.57** |
| Lapsed | Rs 28.94 | Rs 43.09 | +Rs 14.15 |
| New | Rs 47.79 | Rs 45.76 | -Rs 2.03 (roughly flat) |

**For active and high-frequency users, showing the discount actually reduces net revenue per user** — the discount eats margin on orders these users would have placed anyway, and the small conversion lift doesn't make up for it. Lapsed users are the one segment where the discount is clearly net-positive.

## One Real Bug — Caught and Fixed

The first version of the uplift model (Logistic Regression scoring each user with discount forced on vs. off) produced a segment ranking that **contradicted the chi-square ground truth**: it ranked active users as having the highest predicted uplift and lapsed users third — the opposite of what the significance testing showed.

**Root cause:** the model had no interaction term between segment and discount status — just a single global `discount_shown` coefficient applied uniformly to every user. A model like this literally cannot represent "the discount works differently for lapsed vs. active users," which is the entire premise of an uplift model. The differences it was showing were an artifact of other features (like `days_since_last_order`) shifting where each segment sits on the logistic curve, not a real captured interaction.

**Fix:** added `segment x discount_shown` interaction terms for each segment. After the fix, the model's predicted uplift ranking (lapsed 0.262 > new 0.231 > active 0.084 > high_frequency 0.029) matches the chi-square ground truth exactly in order.

**Why this matters:** a wrong-direction ranking that contradicts a simpler, more trustworthy analysis (the chi-square test) is a signal to check the model's structure, not to report the mismatch as an interesting finding. This is the same discipline as the SQL bug caught in the Sukino project — an unexpected result is a checkpoint, not a headline.

## Business Decision

- **Decision:** Stop showing the 70%-off promotion broadly. Target it specifically at **lapsed and new users**, where it drives large, statistically significant, and profitable conversion lift. Discontinue or sharply reduce exposure to active and high-frequency users, where it measurably reduces net revenue per user.
- **Why:** Lapsed and new users show the largest lift (26.3pp and 23.0pp) at the lowest cost per incremental conversion (Rs 115.88 and Rs 143.98). Active and high-frequency users show smaller, and in the high-frequency case statistically insignificant, lift — while actually losing money on net revenue per user.
- **Risks:** Removing the discount from active/high-frequency users could feel like a downgrade if not communicated carefully, and lapsed/new users targeted repeatedly may become desensitized to future promotions over time.
- **Next experiment:** Test whether a smaller discount depth (e.g. 40% instead of 70%) still captures most of the lapsed/new lift at a lower cost per incremental user — the current analysis only tested a single discount depth.

## Assumptions Restated
- Discount exposure was randomly assigned within segment (a modeling assumption for this synthetic case, not necessarily true of Zomato's actual targeting logic)
- Order value and product mix are unaffected by discount status
- Users behave independently (no shared-account effects)

## Status
- [x] SQL segmentation complete
- [x] Chi-square significance testing complete
- [x] Uplift model built, bug caught and fixed
- [x] Dashboard complete
- [x] Business decision documented
