# Zomato — Differential Pricing Analysis

## The Story
Zomato ran a promotion offering 70% off (up to ₹140) on orders above ₹99 — but not every user saw the same offer at the same time. Deep discounts move orders, but they also cost margin on every order, including from users who would've ordered anyway with no discount at all.

## Problem Statement
Zomato's promotional discounting varies by user segment and timing rather than being applied uniformly. Blanket discounting is easy to justify with a short-term order spike, but it can mask a large share of spend going to users whose behavior the discount didn't actually change.

## Open Question
Which users did the discount genuinely change the behavior of, versus which users were shown a discount they would have converted without? And would targeting the offer more precisely — by segment, recency, or order history — have generated more net revenue than showing it broadly?

## Assumptions (stated before analysis)
- Within each user segment, discount exposure was randomly assigned during the campaign window — this lets us measure a clean lift, similar to an embedded A/B test, rather than needing complex causal matching
- Order value and item cost are independent of discount status (the discount doesn't change what people order, only whether they order)
- Users are analyzed independently — no household/shared-account effects modeled
- Synthetic dataset created to simulate realistic operational scenarios — not proprietary Zomato data

## Data Schema (Fact/Dimension)

**`dim_users`** — grain: one row per user
- `user_id` (PK), `segment` (new / active / lapsed / high_frequency), `signup_date`, `city_tier`, `historical_order_count`, `days_since_last_order`

**`fact_orders`** — grain: one row per order (during the 30-day campaign window)
- `order_id` (PK), `user_id` (FK), `order_date`, `discount_shown` (bool — treatment flag), `discount_depth_pct`, `order_value`, `discount_amount`, `converted` (bool — did they order at all that period), `channel`

**`dim_campaign`** — grain: one row describing the offer
- `campaign_id`, `offer_description` ("70% off up to ₹140 above ₹99"), `start_date`, `end_date`

## Event Schema (for the funnel view)
```
user_saw_offer_banner
viewed_restaurant
added_to_cart
applied_discount_code
payment_success (converted = true)
```

## Status
- [x] Story, problem statement, schema defined
- [ ] Synthetic data generation
- [ ] SQL segmentation
- [ ] Statistical test + light ML (uplift)
- [ ] Dashboard
- [ ] Business decision + executive summary
