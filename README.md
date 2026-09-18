# Zomato Differential Pricing — Who Should See the Discount?

A Business Analyst case study: Zomato ran a 70%-off (up to Rs 140) promotion, but different users saw it at different times. Did the discount actually change behavior, or was Zomato paying full discount cost on orders that would have happened anyway?

## The Problem
Blanket discounting is easy to justify with a short-term order spike, but it can mask a large share of spend going to users whose behavior the discount didn't actually change. The open question: **which users did the discount genuinely convert, and would targeting it more precisely generate more net revenue than showing it broadly?**

## Approach: Data → SQL → Statistical Testing → Uplift Model → Dashboard → Business Decision

| Step | File | What it does |
|---|---|---|
| 1. Design | `01_story_and_schema.md` | Problem framing, fact/dim schema, assumptions stated up front |
| 2. Data | `generate_data.py` | Synthetic dataset: 9,000 users across 4 segments, with discount exposure **randomly assigned within each segment** — an embedded A/B test, enabling genuine causal measurement rather than just correlation |
| 3. SQL | `02_sql_segmentation.py` | Segment-level conversion rate, discount spend, and net revenue per user |
| 4. Statistics + ML | `03_stats_and_uplift_model.py` | Chi-square significance testing per segment, plus a Logistic Regression uplift model. **A real bug was caught and fixed here** — the first model version had no segment-discount interaction term, so it couldn't actually represent differential treatment effects. Documented rather than hidden. |
| 5. Dashboard | `build_dashboard.py`, `dashboard.png` | 4-panel view: conversion lift by segment, cost per incremental conversion, and the key finding — net revenue per user actually *drops* for high-frequency users when shown the discount |
| 6. Findings & Decision | `04_findings_and_business_decision.md`, `executive_summary.md` | Full write-up and a one-page summary for a non-technical reader |

## Headline Results
- **Lapsed users:** +26.3 percentage point conversion lift (p<0.000001) — Rs 115.88 per incremental customer
- **High-frequency users:** +2.9pp lift, **not statistically significant** (p=0.129) — and net revenue per user *drops* by Rs 133.57 when shown the discount, because it eats margin on orders they'd have placed anyway

## The Bug — Caught and Fixed
An uplift model without a segment x discount interaction term produced a segment ranking that contradicted the chi-square ground truth. Root-caused to the missing interaction term, fixed, and the corrected model now matches the statistical test exactly. Full writeup in `04_findings_and_business_decision.md`.

## Business Decision
Stop broad discounting. Target the promotion specifically at lapsed and new users, where it's statistically significant and profitable. Pull back from active and high-frequency users, where it's quietly losing money.

## Data
All data is **synthetic — created to simulate realistic operational scenarios, not proprietary Zomato data.**

## Tech Stack
Python, pandas, SQL (SQLite), SciPy (chi-square testing), scikit-learn (Logistic Regression uplift model), matplotlib
