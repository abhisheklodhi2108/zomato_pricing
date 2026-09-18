# Zomato Differential Pricing — Executive Summary

## The Question
Zomato ran a 70%-off (up to Rs 140) promotion, but different users saw it at different times. Did the discount actually change behavior, or was Zomato paying full discount cost on orders that would have happened anyway?

## What We Found
The discount works completely differently depending on who sees it. For lapsed users (haven't ordered in 60+ days), it drives a real, statistically significant 26.3-percentage-point jump in conversion, at a cost of about Rs 116 per incremental customer gained. For new users, it's nearly as strong: +23.0 points at Rs 144 per incremental customer.

For high-frequency users, the story flips. The discount barely moves their behavior (+2.9 points, and this isn't even statistically distinguishable from zero) - these users were ordering anyway. Worse, because the discount still applies to their orders, net revenue per user actually drops by about Rs 134 when they're shown the discount versus when they're not. The same pattern, smaller, shows up for active users too.

## The Decision
Stop showing this discount broadly. Target it specifically at lapsed and new users, where it's genuinely profitable and effective. Pull it back from active and high-frequency users, where it's quietly losing money.

## What We're Being Upfront About
An early version of the uplift model got the segment ranking backwards - it said active users had the highest response to the discount, when the more reliable statistical test showed lapsed users clearly in the lead. The cause was a modeling oversight (missing interaction terms between segment and discount), caught specifically because it contradicted a simpler, more trustworthy test. Fixed and documented rather than reported as-is.

This analysis runs on a synthetic dataset built to simulate realistic promotional targeting - not actual Zomato data.

## The One-Line Takeaway
The same discount is either a great investment or a quiet loss, entirely depending on who you show it to - and right now it's probably being shown to too many of the wrong people.
