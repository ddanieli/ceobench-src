# BossBench Tool Reference

Complete reference for all 37 agent tools available in the BossBench SaaS simulation environment.

---

## Table of Contents

- [Business Configuration](#business-configuration)
  - [set_prices](#set_prices)
  - [set_model_tiers](#set_model_tiers)
  - [set_capacity_tier](#set_capacity_tier)
  - [set_usage_quotas](#set_usage_quotas)
  - [set_ads_strength](#set_ads_strength)
  - [set_lead_promotion](#set_lead_promotion)
  - [set_promotion](#set_promotion)
- [Marketing & Spend](#marketing--spend)
  - [set_daily_spend](#set_daily_spend)
  - [set_ad_channel_spend](#set_ad_channel_spend)
  - [set_targeted_ad_spend](#set_targeted_ad_spend)
  - [set_targeted_ops_spend](#set_targeted_ops_spend)
  - [set_targeted_dev_spend](#set_targeted_dev_spend)
- [Customer Communication](#customer-communication)
  - [send_enterprise_deal](#send_enterprise_deal)
  - [reject_enterprise_deal](#reject_enterprise_deal)
- [VC Negotiation](#vc-negotiation)
  - [list_potential_vcs](#list_potential_vcs)
  - [send_vc_deal](#send_vc_deal)
  - [reject_vc_deal](#reject_vc_deal)
- [Equity & Funding](#equity--funding)
  - [get_cap_table_info](#get_cap_table_info)
  - [settle_investments](#settle_investments)
  - [declare_dividend](#declare_dividend)
- [Analytics & Monitoring](#analytics--monitoring)
  - [python_exec](#python_exec)
  - [get_social_posts](#get_social_posts)
  - [expand_notification](#expand_notification)
  - [get_cost_info](#get_cost_info)
- [Market Discovery](#market-discovery)
  - [research_market](#research_market)
  - [research_group](#research_group)
  - [get_market_overview](#get_market_overview)
  - [get_group_insights](#get_group_insights)
- [R&D Research Projects](#rd-research-projects)
  - [start_research_project](#start_research_project)
  - [list_research_projects](#list_research_projects)
- [Automation](#automation)
  - [register_daily_calculation](#register_daily_calculation)
  - [remove_daily_calculation](#remove_daily_calculation)
  - [list_daily_calculations](#list_daily_calculations)
  - [register_script](#register_script)
  - [run_script](#run_script)
  - [list_scripts](#list_scripts)
  - [delete_script](#delete_script)
- [Simulation Control](#simulation-control)
  - [next_day](#next_day)
- [Session Management](#session-management)
  - [log_rationale](#log_rationale)
- [Help & Documentation](#help--documentation)
  - [list_all_tables](#list_all_tables)
  - [describe_tables](#describe_tables)
  - [get_tool_documentation](#get_tool_documentation)

---

## Business Configuration

### `set_prices`

Set monthly subscription prices for plans A, B, and C.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `A` | float | No | Monthly price in $ for Plan A (entry tier). Must be positive. |
| `B` | float | No | Monthly price in $ for Plan B (mid tier). Must be positive. |
| `C` | float | No | Monthly price in $ for Plan C (premium tier). Must be positive. |

At least one plan price must be provided. Omitted plans keep their current prices.

**Impact:** Affects customer acquisition (higher prices = fewer sign-ups), churn (price vs value), and revenue. Changes take effect on `next_day`.

#### Sample Input/Output

**Success cases:**

| Scenario | Input | Output |
|----------|-------|--------|
| Set all three plans | `{"A": 25, "B": 69, "C": 179}` | `Prices updated: A=$25.00, B=$69.00, C=$179.00` |
| Update only plan B | `{"B": 89}` | `Prices updated: B=$89.00` |
| Update two plans | `{"A": 19, "C": 149}` | `Prices updated: A=$19.00, C=$149.00` |

**Failure cases:**

| Scenario | Input | Output (stderr/message) |
|----------|-------|------------------------|
| Negative price | `{"A": -10}` | `Price for plan A must be positive` |
| Invalid plan key | `{"D": 50}` | `Invalid plan keys: {'D'}. Valid: {'A', 'B', 'C'}` |
| Empty input | `{}` | `Must provide at least one plan price` |

---

### `set_model_tiers`

Set AI model quality tiers for plans A, B, and C. Higher tiers = better quality but higher compute cost.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `A` | int | No | Model tier 1–5 for Plan A |
| `B` | int | No | Model tier 1–5 for Plan B |
| `C` | int | No | Model tier 1–5 for Plan C |

**Tier Info:**

| Tier | Cost/Unit | Quality | Model Class |
|------|-----------|---------|-------------|
| 1 | $0.0003 | 0.55 | Flash-Lite / 4o-mini |
| 2 | $0.002 | 0.65 | Haiku / Flash |
| 3 | $0.006 | 0.75 | Sonnet / GPT-4o |
| 4 | $0.012 | 0.85 | Opus / GPT-5 |
| 5 | $0.030 | 0.95 | o1 / o3 reasoning |

**Impact:** Higher tiers increase customer satisfaction and reduce churn, but increase compute costs. Each tier adds +0.10 quality.

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Set all tiers | `{"A": 2, "B": 3, "C": 5}` | `Model tiers updated: A=tier2, B=tier3, C=tier5` |
| Upgrade only plan C | `{"C": 5}` | `Model tiers updated: C=tier5` |
| Downgrade plan A | `{"A": 1}` | `Model tiers updated: A=tier1` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Tier out of range | `{"A": 0}` | `Tier for plan A must be 1-5` |
| Tier too high | `{"B": 6}` | `Tier for plan B must be 1-5` |

---

### `set_capacity_tier`

Set infrastructure capacity tier. Higher tiers handle more usage but cost more per day.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `tier` | int | Yes | Capacity tier (0–7) |

**Tier Info:**

| Tier | Capacity (units/day) | Cost/Day | Description |
|------|---------------------|----------|-------------|
| 0 | 50,000 | $85 | Serverless API (Together/Fireworks) |
| 1 | 200,000 | $215 | 1× H100 neocloud dedicated |
| 2 | 800,000 | $530 | 4× H100 reserved cluster |
| 3 | 2,500,000 | $1,330 | 8× H100 enterprise + auto-scaling |
| 4 | 8,000,000 | $4,000 | Multi-node hyperscale (16–32 H100s) |
| 5 | 25,000,000 | $10,000 | 64× H100 multi-rack cluster |
| 6 | 80,000,000 | $28,000 | 256× H100 dedicated pod |
| 7 | 300,000,000 | $75,000 | 1024+ GPU hyperscale fleet |

**Impact:** When usage exceeds capacity, overload occurs causing higher latency and errors. Higher overload increases outage chance. Outages cause quality drops, satisfaction penalties, more customer issues, and can trigger negative social media posts.

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Set tier 2 | `{"tier": 2}` | `Capacity tier set to 2: 800,000 units/day ($530/day) — 4x H100 reserved cluster` |
| Downgrade to serverless | `{"tier": 0}` | `Capacity tier set to 0: 50,000 units/day ($85/day) — Serverless API (Together/Fireworks)` |
| Max tier | `{"tier": 7}` | `Capacity tier set to 7: 300,000,000 units/day ($75,000/day) — 1024+ GPU hyperscale fleet` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Tier out of range | `{"tier": 10}` | `Capacity tier must be 0-7. Use get_cost_info to see all tiers.` |
| Negative tier | `{"tier": -1}` | `Capacity tier must be 0-7. Use get_cost_info to see all tiers.` |

---

### `set_usage_quotas`

Set daily usage quotas (rate limits) per customer for each plan. Exceeding quota degrades experience.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `A` | int | No | Daily usage quota for Plan A (units/day per customer) |
| `B` | int | No | Daily usage quota for Plan B (units/day per customer) |
| `C` | int | No | Daily usage quota for Plan C (units/day per customer) |

**Impact:** Quotas limit per-customer usage to control costs. Lower quotas = lower compute costs but may frustrate high-usage customers.

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Set all quotas | `{"A": 150, "B": 750, "C": 3000}` | `Usage quotas updated: A=150 units/day, B=750 units/day, C=3,000 units/day` |
| Only raise plan C | `{"C": 5000}` | `Usage quotas updated: C=5,000 units/day` |
| Tighten plan A | `{"A": 50}` | `Usage quotas updated: A=50 units/day` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Negative quota | `{"A": -50}` | `Quota for plan A cannot be negative` |
| Invalid plan key | `{"D": 100}` | `Invalid plan keys: {'D'}. Valid: {'A', 'B', 'C'}` |

---

### `set_ads_strength`

Set in-app advertising strength (0–1). Ads generate revenue but reduce perceived quality. Effects at global/group/individual levels are ADDITIVE, capped at 1.0 per customer.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `global_strength` | float | No | Global ads strength for all users (0.0–1.0). NULL/omit = no change. |
| `by_group` | dict | No | Per-group ads strength: `{group_id: strength}`. Additive with global. |
| `by_customer` | dict | No | Per-customer ads strength: `{customer_id: strength}`. Additive with global + group. |

**Impact:** Each customer's `quality_penalty = ads_quality_sensitivity × effective_ads_strength` (degrades satisfaction). Dollar return = `ads_return_sensitivity × effective_ads_strength` per customer per day (recorded as `ad_revenue` in ledger). Trade-off: higher ads → more revenue but lower satisfaction → more churn.

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Set global + group | `{"global_strength": 0.2, "by_group": {"S1": 0.1}}` | `Ads strength updated. Global: 0.20, Groups: {S1: 0.10}, Customers: {}` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Invalid group | `{"by_group": {"ZZ": 0.5}}` | `Invalid group IDs` |
| Out of range | `{"global_strength": 1.5}` | `Strength must be between 0 and 1` |

---

### `set_lead_promotion`

Set promotion (dollar deduction) for new leads. Applied automatically to first billing period only. Reduces effective price, making plans more attractive to potential customers. Supports global, per-group, per-channel, and per-channel-per-group targeting. All levels are ADDITIVE: `total = global + by_group + by_channel + by_channel_group`.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `global_promotion` | float | No | Global lead promotion in $/month. NULL/omit = no change. |
| `by_group` | dict | No | Per-group lead promotion: `{group_id: $/month}`. Additive with global. |
| `by_channel` | dict | No | Per-channel lead promotion: `{channel_id: $/month}`. Only applies to leads from that channel. Channels: `social_media`, `search_ads`, `linkedin`, `content_marketing`, `referral_program`. |
| `by_channel_group` | dict | No | Per-channel-per-group: `{channel_id: {group_id: $/month}}`. Most granular level. Additive with all other levels. |

**Impact:** Reduces effective price for new leads at first billing period. Higher promotion → more leads convert but lower first-period revenue. Channel-level promotions only apply to leads acquired through that specific ad channel (not organic/network leads). Only applies to first billing period — subsequent billing uses regular `set_promotion` only.

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Global + group | `{"global_promotion": 10.0, "by_group": {"S1": 5.0}}` | `Lead promotion updated. Global: $10.00/mo, Groups: {S1: $5.00}` |
| Channel-only | `{"by_channel": {"linkedin": 15.0, "search_ads": 10.0}}` | `Lead promotion updated. Global: $0.00/mo, Channels: {linkedin: $15.00, search_ads: $10.00}` |
| Channel×Group targeting | `{"by_channel_group": {"linkedin": {"E1": 20.0, "E2": 15.0}, "social_media": {"S1": 8.0}}}` | `Lead promotion updated. Global: $0.00/mo, Channel×Group: {linkedin→E1: $20.00, linkedin→E2: $15.00, social_media→S1: $8.00}` |
| All levels combined | `{"global_promotion": 3.0, "by_group": {"E1": 5.0}, "by_channel": {"linkedin": 10.0}, "by_channel_group": {"linkedin": {"E1": 7.0}}}` | `Lead promotion updated. Global: $3.00/mo, Groups: {E1: $5.00}, Channels: {linkedin: $10.00}, Channel×Group: {linkedin→E1: $7.00}` |

In the "all levels combined" example, an E1 lead from LinkedIn would get: $3 + $5 + $10 + $7 = $25/mo promotion.

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Invalid channel | `{"by_channel": {"tiktok": 10.0}}` | `Invalid channels: {'tiktok'}. Valid: [...]` |
| Invalid group in channel_group | `{"by_channel_group": {"linkedin": {"INVALID": 10.0}}}` | `Invalid group IDs for channel 'linkedin': {'INVALID'}. Valid: [...]` |
| Negative promotion | `{"global_promotion": -5.0}` | `Global lead promotion must be non-negative` |

---

### `set_promotion`

Set ongoing promotion (dollar deduction) for existing subscribers. Applied at each billing period. Satisfaction uses `(price - promotion)`. Additive across global/group/customer/group_plan levels.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `global_promotion` | float | No | Global promotion in $/month. NULL/omit = no change. |
| `by_group` | dict | No | Per-group promotion: `{group_id: $/month}` |
| `by_customer` | dict | No | Per-customer promotion: `{customer_id: $/month}` |
| `by_group_plan` | dict | No | Per-group-plan: `{group_id: {plan: $/month}}` |

**Impact:** Customers evaluate plans at `(list_price - promotion)` on billing day. Higher promotion → higher satisfaction, lower churn, but lower revenue per subscriber. Takes effect at next billing period.

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Multi-level | `{"global_promotion": 5.0, "by_group": {"E1": 10.0}, "by_group_plan": {"S1": {"A": 3.0}}}` | `Promotion updated. Global: $5.00/mo, Groups: {E1: $10.00}, Customers: {}, Group-Plans: {S1: {A: $3.00}}` |

---

## Marketing & Spend

### `set_daily_spend`

Set daily spending for advertising, operations, and development.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `advertising` | float | No | Daily advertising budget (non-negative) |
| `operations` | float | No | Daily operations budget (non-negative) |
| `development` | float | No | Daily development budget (non-negative) |

**Impact by category:**

- **Advertising:** Generates new leads. Each channel has a fixed leads-per-$1000 rate per customer group.
- **Operations:** CRITICAL — (1) Reduces outage probability: At $0 = ~3% daily outage risk (~1/month). At $500 = ~1.1% daily (~3/year). (2) Speeds up issue resolution: mean resolved/day = 1 + 0.01 × spend.
- **Development:** Improves product quality. Improvement = 0.001 × ln(1 + spend/1000).

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Set all three | `{"advertising": 800, "operations": 1200, "development": 600}` | `Daily spend updated: advertising=$800, operations=$1200, development=$600` |
| Only increase ops | `{"operations": 2000}` | `Daily spend updated: operations=$2000` |
| Cut ads to zero | `{"advertising": 0}` | `Daily spend updated: advertising=$0` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Negative spend | `{"advertising": -100}` | `Spend for advertising cannot be negative` |
| Invalid category | `{"marketing": 500}` | `Invalid spend categories: {'marketing'}. Valid: {'advertising', 'operations', 'development'}` |

---

### `set_ad_channel_spend`

Set per-channel advertising budget allocation as percentages.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `social_media` | float | No | Facebook, Instagram, TikTok ads — broad consumer reach |
| `search_ads` | float | No | Google/Bing search ads — intent-based targeting |
| `linkedin` | float | No | LinkedIn ads — professional/business audience |
| `content_marketing` | float | No | SEO, blogs, whitepapers — organic discovery |
| `referral_program` | float | No | Customer referral incentives — word-of-mouth |

Values are percentages (0.0–1.0), normalized to sum to 1.0.

**Impact:** Different channels reach different customer groups with varying effectiveness.

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Distribute across all | `{"social_media": 0.2, "search_ads": 0.3, "linkedin": 0.3, "content_marketing": 0.1, "referral_program": 0.1}` | `Ad channel allocation updated (total budget=$500/day): • Social Media Ads: 20% ($100/day) • Search Engine Ads: 30% ($150/day) ...` |
| Focus on two channels | `{"linkedin": 0.7, "content_marketing": 0.3}` | `Ad channel allocation updated (total budget=$500/day): • LinkedIn Ads: 70% ($350/day) • Content Marketing: 30% ($150/day)` |
| All to one channel | `{"search_ads": 1.0}` | `Ad channel allocation updated (total budget=$500/day): • Search Engine Ads: 100% ($500/day)` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Invalid channel | `{"tiktok": 0.5, "search_ads": 0.5}` | `Invalid channels: {'tiktok'}. Valid: {'social_media', 'search_ads', 'linkedin', 'content_marketing', 'referral_program'}` |
| All zeros | `{"social_media": 0, "search_ads": 0}` | `At least one channel must have non-zero percentage` |

---

### `set_targeted_ad_spend`

Set ADDITIONAL per-group per-channel ad spend on top of the overall channel allocation.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `targeted_spend` | dict | Yes | `{channel_id: {group_id: additional_$/day}}` |

Valid channels: `social_media`, `search_ads`, `linkedin`, `content_marketing`, `referral_program`
Valid groups: `S1–S3`, `E1–E3`, and discovered groups (`D_S01–D_S10`, `D_E01–D_E10`)

**Impact:** Extra dollars are deducted from cash daily as advertising cost. Each (channel, group) pair gets its normal allocation PLUS the targeted amount.

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Target two groups on LinkedIn | `{"targeted_spend": {"linkedin": {"E1": 200, "E2": 100}}}` | `Targeted ad spend updated (extra $300/day on top of channel allocation): • LinkedIn Ads → E1: +$200/day • LinkedIn Ads → E2: +$100/day` |
| Multi-channel targeting | `{"targeted_spend": {"linkedin": {"E1": 200}, "content_marketing": {"S3": 50}, "search_ads": {"D_S01": 100}}}` | `Targeted ad spend updated (extra $350/day on top of channel allocation): • LinkedIn Ads → E1: +$200/day • Content Marketing → S3: +$50/day • Search Engine Ads → D_S01: +$100/day` |
| Clear all targeting | `{"targeted_spend": {}}` | `Targeted ad spend cleared. No additional per-group ad spend.` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Invalid channel | `{"targeted_spend": {"tiktok": {"S1": 100}}}` | `Invalid channels: {'tiktok'}. Valid: {...}` |
| Invalid group | `{"targeted_spend": {"linkedin": {"INVALID": 100}}}` | `Invalid group IDs for channel 'linkedin': {'INVALID'}` |

---

### `set_targeted_ops_spend`

Set ADDITIONAL per-group operations spending on top of the global ops spend.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `targeted_spend` | dict | Yes | `{group_id: additional_$/day}` |

**Mechanics:** Each targeted group gets additional resolution capacity: `extra_mean_per_day = 0.053 × group_spend`.

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Target two enterprise groups | `{"targeted_spend": {"E1": 300, "E2": 200}}` | `Targeted ops spend updated (extra $500/day on top of global ops): • E1: +$300/day • E2: +$200/day` |
| Clear targeting | `{"targeted_spend": {}}` | `Targeted ops spend cleared. No additional per-group ops spend.` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Invalid group | `{"targeted_spend": {"INVALID": 100}}` | `Invalid group IDs: {'INVALID'}. Valid groups: S1, S2, S3, E1, E2, E3, ...` |

---

### `set_targeted_dev_spend`

Set ADDITIONAL per-group development spending on top of the global dev spend. Provides a CUMULATIVE per-group quality bonus that grows daily while spending continues. Investment persists even after spending stops.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `targeted_spend` | dict | Yes | `{group_id: additional_$/day}` |

**Mechanics:** Per-group quality bonus ACCUMULATES daily: `+0.0005 × log(1 + spend/500)` per day. At $500/day: +0.00035/day cumulative. After 30 days: +0.0105 total. Investment persists if spending stops.

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Target high-value segments | `{"targeted_spend": {"E1": 500, "S1": 200}}` | `Targeted dev spend updated (extra $700/day on top of global dev): • E1: +$500/day • S1: +$200/day` |
| Single group | `{"targeted_spend": {"D_E01": 300}}` | `Targeted dev spend updated (extra $300/day on top of global dev): • D_E01: +$300/day` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Invalid group | `{"targeted_spend": {"ZZ": 100}}` | `Invalid group IDs: {'ZZ'}. Valid groups: S1, S2, S3, E1, E2, E3, ...` |

---

## Customer Communication

### `send_enterprise_deal`

Send enterprise deal offerings. Compact tuple format: each deal = `[customer_id, [[plan, price_per_seat, contract_months], ...]]`.

If the customer has an open negotiation thread, replies to it. If no open thread, initiates renegotiation. Up to 3 offerings per deal. Late replies damage relationship (−0.02/day after 1 day grace). **No response within 3 days = customer LOST FOREVER.**

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `deals` | list | Yes | List of `[customer_id, offerings]`. Offerings = `[[plan, price_per_seat, contract_months], ...]`. `contract_months` defaults to 1 if omitted. |

**Impact:** Customer evaluates ALL offerings and picks the one with highest satisfaction. `Satisfaction = quality_perceived - quality_required(price) - contract_penalty`. Customer accepts if best satisfaction > 0, counter-offers otherwise. **WARNING:** if the customer rejects all offerings OR the thread times out, the customer CHURNS.

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Reply with 3 offerings | `{"deals": [[312, [["A", 9.0, 6], ["B", 14.0, 12], ["C", 22.0, 12]]]]}` | `Customer #312: reply sent with 3 offering(s)` |
| Initiate renegotiation | `{"deals": [[88, [["B", 12.0, 6], ["B", 11.0, 12]]]]}` | `Customer #88: renegotiation started (200 seats). 2 offering(s) sent.` |
| Batch | `{"deals": [[312, [["A", 9.0, 6]]], [88, [["B", 12.0, 6]]]]}` | `Sent 2/2 enterprise deals: Customer #312: reply sent with 1 offering(s) Customer #88: renegotiation started. 1 offering(s) sent.` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Customer not found | `{"deals": [[999, [["A", 9.0, 6]]]]}` | `Customer #999: not found` |
| Missing offerings | `{"deals": [[312, []]]}` | `Customer #312: offerings required` |
| Active thread exists | `{"deals": [[88, [["B", 11.0, 6]]]]}` | `Processed 0/1 deals (1 failed): Customer #88: already has an active negotiation thread` |

---

### `reject_enterprise_deal`

Reject one or more enterprise deals by customer_id. The system finds the customer's active negotiation thread automatically. New leads are lost, existing customers may churn.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `deals` | list | Yes | List of `{"customer_id": int}` dicts |

**Impact:** For `new_lead` threads: lead permanently lost. For `renegotiation`/`renewal` threads: customer CHURNS. For `churn_prevention`/`plan_change`: customer churns with reputation damage.

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Reject new lead | `{"deals": [{"customer_id": 312}]}` | `Processed 1/1 rejections: Customer #312: Rejected (new_lead). Lead marked as lost.` |
| Reject existing customer | `{"deals": [{"customer_id": 88}]}` | `Processed 1/1 rejections: Customer #88: Rejected (churn_prevention). Customer may cancel.` |
| Batch | `{"deals": [{"customer_id": 312}, {"customer_id": 88}]}` | `Processed 2/2 rejections: Customer #312: Rejected (new_lead). Lead marked as lost. Customer #88: Rejected (plan_change).` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| No active thread | `{"deals": [{"customer_id": 999}]}` | `Processed 0/1 rejections (1 failed): Customer #999: no active thread` |
| Already closed | `{"deals": [{"customer_id": 312}]}` | `Processed 0/1 rejections (1 failed): Customer #312: thread already closed` |

---

## VC Negotiation

### `list_potential_vcs`

List all predefined VC investors and their profiles.

**Parameters:** None.

#### Sample Input/Output

**Success:**

```
Input:  {}
Output:
=== Potential VC Investors ===

  Horizon Ventures (vc_01)
    Investment range: $100,000 – $500,000
    Description: Early-stage micro-VC focused on AI/ML startups
    Status: Available

  Catalyst Capital (vc_02)
    Investment range: $250,000 – $1,000,000
    Description: Seed-stage fund investing in developer tools
    Status: Active (shareholder_id=3)

  ...27 more VCs...

Total: 30 VCs (1 currently active)
```

---

### `send_vc_deal`

Send equity offers to one or more VCs. Terms have TWO effects: (1) NEGOTIATION — more VC-friendly terms lower the VC's equity target, making acceptance easier; (2) POST-DEAL — terms create ongoing obligations.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `deals` | list | Yes | List of deal dicts (see below) |

**Deal fields:**

| Field | Type | Required | Options | Negotiation Impact | Post-Deal Risk |
|-------|------|----------|---------|-------------------|----------------|
| `shareholder_id` | int | Yes | — | — | — |
| `share_pct` | float | Yes | — | Higher = easier acceptance | More dilution |
| `anti_dilution_floor` | float | No | 0.6, 0.7, 0.8, 0.9 | Up to −5% equity target | If valuation drops below floor × original, VC gets bonus shares |
| `milestone_tranche_pct` | float | No | 0.3, 0.4, 0.5, 0.6, 0.7 | Up to −2.7% equity target | Only receive tranche_pct upfront; rest requires MRR milestone |
| `milestone_revenue_multiplier` | float | No | 1.5, 2.0, 2.5, 3.0 | Up to −2.7% equity target | Tranche 2 needs MRR × multiplier |
| `milestone_deadline_days` | int | No | 60, 90, 120, 180 | Up to −2.7% equity target | Miss deadline = forfeit tranche 2 |
| `redemption_days` | int | No | 90, 120, 180, 270, 365 | Up to −3% equity target | VC forces buyback after N days |
| `redemption_buyback_multiplier` | float | No | 1.0, 1.1, 1.2, 1.3, 1.5 | Up to −3% equity target | Pay multiplier × invested at redemption |

Max combined term adjustment: ~19% equity target reduction.

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Accepted with terms | `{"deals": [{"shareholder_id": 2, "share_pct": 0.12, "anti_dilution_floor": 0.9}]}` | `Processed 1/1 deals: Apex Capital: ACCEPTED! 12.0% for $500,000. Term adjustment: +0.0350. Use settle_investments() to finalize.` |
| Batch: one accepted, one pending | `{"deals": [{"shareholder_id": 2, "share_pct": 0.12}, {"shareholder_id": 3, "share_pct": 0.05}]}` | `Processed 2/2 deals: Apex Capital: ACCEPTED! 12.0% for $500,000. Use settle_investments() to finalize. Summit Ventures: Offer sent (5.0%). Awaiting VC response...` |
| With milestone terms | `{"deals": [{"shareholder_id": 4, "share_pct": 0.1, "milestone_tranche_pct": 0.3, "milestone_revenue_multiplier": 3.0, "milestone_deadline_days": 60}]}` | `Processed 1/1 deals: Growth Partners: Offer sent (10.0%). Term adjustment: +0.0800. Awaiting VC response...` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Invalid term option | `{"deals": [{"shareholder_id": 2, "share_pct": 0.1, "anti_dilution_floor": 0.55}]}` | `anti_dilution_floor must be one of [0.6, 0.7, 0.8, 0.9]` |
| No open thread | `{"deals": [{"shareholder_id": 99, "share_pct": 0.1}]}` | `Shareholder #99: no open negotiation thread` |
| Already settled | `{"deals": [{"shareholder_id": 2, "share_pct": 0.1}]}` | `Apex Capital: thread already closed (settled)` |

---

### `reject_vc_deal`

Reject one or more VC deals. PERMANENTLY terminates the negotiation. **No relationship penalty** for VC rejections.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `deals` | list | Yes | List of `{"shareholder_id": int}` dicts |

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Reject single | `{"deals": [{"shareholder_id": 2}]}` | `Processed 1/1 rejections: Apex Capital: deal rejected.` |
| Reject multiple | `{"deals": [{"shareholder_id": 2}, {"shareholder_id": 3}]}` | `Processed 2/2 rejections: Apex Capital: deal rejected. Summit Ventures: deal rejected.` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Already settled | `{"deals": [{"shareholder_id": 2}]}` | `Apex Capital: thread already closed (settled)` |
| No open thread | `{"deals": [{"shareholder_id": 99}]}` | `Shareholder #99: no open negotiation thread` |

---

## Equity & Funding

### `get_cap_table_info`

View the current ownership (cap table), funding history, and dividend history.

**Parameters:** None.

#### Sample Input/Output

**Success:**

```
Input:  {}

Output (early stage — founder only):
=== Cap Table ===
Total Shares Outstanding: 10,000,000

Shareholder               Type    Shares      Ownership  Invested
---------------------------------------------------------------------------
Founder                   founder 10,000,000  100.0%     $0

--- Funding History (0 rounds) ---
No funding rounds yet.

--- Dividend History ---
No dividends declared yet.
```

```
Output (post-funding):
=== Cap Table ===
Total Shares Outstanding: 12,048,193

Shareholder               Type    Shares      Ownership  Invested
---------------------------------------------------------------------------
Founder                   founder 10,000,000  83.0%      $0
Apex Capital              vc      2,048,193   17.0%      $608,390

--- Funding History (1 rounds) ---
Day 15: Apex Capital invested $608,390 for 2,048,193 shares @ $0.2970/share

--- Dividend History ---
Day 30: $50,000 total ($0.0042/share)
  Founder: $41,500 | Apex Capital: $8,500

Cumulative dividends: $50,000
```

---

### `settle_investments`

Settle ALL accepted VC deals at once. Takes NO parameters. Automatically finds all accepted deals, validates they have the same price/share, issues shares, and adds investment cash. Also auto-rejects all remaining open VC threads.

**Parameters:** None.

**Impact:** CRITICAL — issues new shares (dilutes founder), adds cash, auto-rejects all open threads. Accepted deals expire if not settled before `expiry_day`. Settlement is irreversible.

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Settle one deal | `{}` | `=== Settlement Executed === Apex Capital: $500,000 → 1,764,706 shares (15.0% equity) @ $0.2833/share Total investment: $500,000 New total shares: 11,764,706 Founder ownership: 85.0%` |
| Settle two, auto-reject one | `{}` | `=== Settlement Executed === Auto-rejected 1 open thread(s): Growth Partners Apex Capital: $500,000 → 1,764,706 shares (15.0% equity) ... Summit Ventures: $300,000 → 882,353 shares (7.5% equity) ... Total investment: $800,000 Founder ownership: 79.1%` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| No accepted deals | `{}` | `No accepted VC deals to settle.` |
| Price mismatch | `{}` | `All accepted deals must use the same price/share. Got range $0.2833 - $0.5000.` |
| Over 100% dilution | `{}` | `Total accepted equity = 120.0% (>= 100%). Cannot settle.` |

---

### `declare_dividend`

Declare a dividend from RETAINED EARNINGS (cumulative profit), distributed pro-rata to all shareholders. You can ONLY distribute from profits — not from invested capital. **This is the PRIMARY way to extract value from the business.**

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `amount` | float | Yes | Total dividend amount to distribute |

**Impact:** Deducts cash from the business. Dividends distributed pro-rata by shares, so dilution directly reduces your dividend income. **Cumulative founder dividends are the PRIMARY objective.**

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Standard dividend | `{"amount": 100000}` | `=== Dividend Declared === Total: $100,000 | Per share: $0.008300 Founder: $83,000.00 (10,000,000 shares) Apex Capital: $17,000.00 (2,048,193 shares) Cumulative dividends paid: $150,000 (Founder: $124,500) Remaining retained earnings: $50,000` |
| Small dividend (founder only) | `{"amount": 10000}` | `=== Dividend Declared === Total: $10,000 | Per share: $0.001000 Founder: $10,000.00 (10,000,000 shares) Cumulative dividends paid: $10,000 (Founder: $10,000) Remaining retained earnings: $25,000` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Exceeds retained earnings | `{"amount": 1000000}` | `Amount exceeds retained earnings. Available: $150,000, Requested: $1,000,000` |
| No retained earnings | `{"amount": 5000}` | `No retained earnings available for dividends. Retained earnings: $-12,000` |
| Insufficient cash | `{"amount": 100000}` | `Insufficient cash. Available: $45,000, Requested: $100,000` |

---

## Analytics & Monitoring

### `python_exec`

Execute Python code for custom data analysis. Has read-only access to the full simulation database.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `code` | str | Yes | Python code to execute. Use `print()` to see output. |
| `timeout_seconds` | float | No | Maximum execution time (default 5.0 seconds) |

**Available in code:**

| Variable | Description |
|----------|-------------|
| `conn` | SQLite connection (read-only) with `row_factory=sqlite3.Row` |
| `rows(query, params)` | Execute query, return list of tuples |
| `row(query, params)` | Execute query, return single tuple or None |
| `pandas` / `pd` | `pd.read_sql(query, conn)` for DataFrames |
| `numpy` / `np` | NumPy |
| `sklearn` | LinearRegression, StandardScaler |
| `json`, `math`, `statistics` | Standard library modules |
| `Counter`, `defaultdict` | From collections |

**IMPORTANT:** STATELESS — each call runs in a FRESH context. Variables from previous calls are NOT available.

**Impact:** Read-only analysis. No side effects on simulation state.

#### Sample Input/Output

**Success:**

| Scenario | Input | Stdout |
|----------|-------|--------|
| Subscriber count | `{"code": "print(row('SELECT COUNT(*) FROM subscriptions WHERE status=\"subscribed\" AND end_day IS NULL')[0])"}` | `145` |
| Revenue by plan | `{"code": "for plan, cnt, mrr in rows('SELECT plan, COUNT(*), SUM(effective_price) FROM subscriptions WHERE status=\"subscribed\" AND end_day IS NULL GROUP BY plan'):\n    print(f'{plan}: {cnt} subs, ${mrr:,.0f} MRR')"}` | `A: 82 subs, $2,378 MRR`<br>`B: 48 subs, $3,792 MRR`<br>`C: 15 subs, $2,985 MRR` |
| 30-day churn rate | `{"code": "total = row('SELECT COUNT(*) FROM subscriptions WHERE status=\"subscribed\"')[0]\nchurned = row('SELECT COUNT(*) FROM subscriptions WHERE status=\"cancelled\" AND end_day > (SELECT MAX(day)-30 FROM service_day)')[0]\nprint(f'Churn: {churned}/{total} = {churned/total*100:.1f}%')"}` | `Churn: 12/145 = 8.3%` |
| Pandas analysis | `{"code": "df = pd.read_sql('SELECT day, SUM(amount) as rev FROM ledger WHERE category=\"subscription_payment\" AND day > (SELECT MAX(day)-7 FROM ledger) GROUP BY day', conn)\nprint(f'7-day revenue: ${df[\"rev\"].sum():,.0f}')\nprint(f'Avg daily: ${df[\"rev\"].mean():,.0f}')"}` | `7-day revenue: $2,891`<br>`Avg daily: $413` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Schema introspection blocked | `{"code": "rows('PRAGMA table_info(customers)')"}` | `Execution error: Schema introspection queries (PRAGMA, sqlite_master) are not allowed. Use describe_tables() instead.` |
| Syntax error | `{"code": "print('hello"}` | `Execution error: unterminated string literal (detected at line 1)` |
| Timeout | `{"code": "import time; time.sleep(600)"}` | `Execution timed out after 5.0 seconds` |

---

### `get_social_posts`

Search social media posts about your company. NOTE: Sentiment is NOT provided — you must infer it from the post content.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `days` | int | No | Days back to search (default 7) |
| `limit` | int | No | Max posts to return (default 50) |

#### Sample Input/Output

**Success:**

```
Input:  {"days": 7}

Output:
Found 23 posts in last 7 days.
Day 45: "Absolutely loving the new features! The AI quality has improved dramatically.
  10/10 would recommend." (15 likes, 3 shares, virality: 0.31)
Day 44: "Service was down for 2 hours yesterday. Frustrating when you're on a
  deadline." (8 likes, 1 share, virality: 0.12)
Day 43: "Good tool but getting pricey. Considering alternatives."
  (4 likes, 0 shares, virality: 0.05)
```

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Negative days | `{"days": -1}` | `Days must be a positive integer` |

---

### `expand_notification`

Get full details of one or more notifications from the inbox. Supports single or batch mode.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `notification_id` | int | No | Single notification ID |
| `notification_ids` | list[int] | No | Batch: list of notification IDs |

Provide one of `notification_id` or `notification_ids`.

#### Sample Input/Output

**Success:**

```
Input:  {"notification_id": 42}

Output:
=== Notification #42 ===
Type: enterprise_new_lead
Day: 45

Title: New enterprise lead from TechCorp (200 seats)

Summary:
A new enterprise customer interested (200 seats).

Details:
{"customer_id": 312, "thread_type": "new_lead", "seat_count": 200}
```

```
Input:  {"notification_ids": [42, 55, 60]}

Output:
Expanded 3 notification(s):

=== Notification #42 ===
Type: enterprise_new_lead
...

=== Notification #55 ===
Type: vc_approach
...

=== Notification #60 ===
Type: system_alert
...
```

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Not found | `{"notification_id": 99999}` | `Notification 99999 not found.` |
| All not found (batch) | `{"notification_ids": [99999, 88888]}` | `None of the notifications found: [99999, 88888]` |
| No IDs | `{}` | `Must provide notification_id or notification_ids.` |

---

### `get_cost_info`

Get current cost structure for compute and capacity.

**Parameters:** None.

#### Sample Input/Output

**Success:**

```
Input:  {}

Output:
=== Cost Structure ===

Model Tiers (cost per usage unit):
  Tier 1: $0.0003/unit (q=0.55) — Flash-Lite/4o-mini
  Tier 2: $0.0020/unit (q=0.65) — Haiku/Flash
  Tier 3: $0.0060/unit (q=0.75) — Sonnet/GPT-4o
  Tier 4: $0.0120/unit (q=0.85) — Opus/GPT-5
  Tier 5: $0.0300/unit (q=0.95) — o1/o3 reasoning

Capacity Tiers:
  Tier 0:     50,000 units/day    $85/day  — Serverless API
  Tier 1:    200,000 units/day   $215/day  — 1x H100 neocloud
  ...
```

---

## Market Discovery

### `research_market`

Conduct market research to discover new customer segments. Costs $25,000 per attempt with a 30% chance of discovering one random undiscovered group. Result is instant (no delay).

**Parameters:** None.

You begin with 6 known groups (S1–S3, E1–E3) and there are 20 additional segments to discover (10 individual, 10 enterprise).

#### Sample Input/Output

**Success:**

```
Input:  {}

Output:
=== Market Research Success ===
Cost: $25,000
Discovered: Niche Creators (D_S01) — Individual segment
Info Level: 1 (noisy estimates ±50%)
Remaining undiscovered segments: 19

--- Initial Estimates (±50% accuracy) ---
  Willingness to pay:   ~$85/mo
  Usage volume:         ~35 units/day
  Quality expectations: ~0.58
  Market cap:           ~185,000 customers
  Market cap growth:    ~9.2%/year

Use get_group_insights('D_S01') for full parameter estimates.
Use research_group('D_S01') to improve accuracy.
```

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| No discovery (70% chance) | `{}` | `Market research complete ($25,000). No new segments discovered this time. 19 undiscovered segments remain.` |
| Insufficient funds | `{}` | `Insufficient funds. Market research costs $25,000. Available: $12,000` |

---

### `research_group`

Start research on a discovered customer group to reach a specific info level. Any level (2, 3, or 4) can be targeted directly without requiring intermediate levels. Research takes several days; results delivered to inbox.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `group_id` | str | Yes | Group ID to research (e.g., `D_S01`) |
| `target_level` | int | No | Target info level (2, 3, or 4). Defaults to current_level + 1. |

**Cost & Duration:**

| Target Level | Cost | Duration | Accuracy |
|-------------|------|----------|----------|
| Level 2 | $60,000 | ~3 days | ±25% |
| Level 3 | $175,000 | ~5 days | ±10% |
| Level 4 | $350,000 | ~7 days | ±5% |

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Jump to Level 4 | `{"group_id": "D_S01", "target_level": 4}` | `=== Research Started === Group: Niche Creators (D_S01) Level: 1 → 4 Cost: $350,000 (deducted) Expected completion: day 22 (~7 days) New parameter accuracy: ±5%` |
| Default next level | `{"group_id": "D_E01"}` | `=== Research Started === Group: Government Agencies (D_E01) Level: 1 → 2 Cost: $60,000 (deducted) Expected completion: day 18 (~3 days) New parameter accuracy: ±25%` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Already in progress | `{"group_id": "D_S01", "target_level": 3}` | `Research already in progress for group 'D_S01'. Expected completion: day 18.` |
| Insufficient funds | `{"group_id": "D_E01", "target_level": 4}` | `Insufficient funds. Research Level 4 costs $350,000. Available: $45,000` |
| No downgrade | `{"group_id": "S1", "target_level": 2}` | `Group 'S1' is already at Level 4. Cannot research to Level 2.` |

---

### `get_market_overview`

Get an overview of all known customer segments, their info levels, undiscovered count, and macroeconomic conditions (ISM PMI).

**Parameters:** None.

#### Sample Input/Output

**Success:**

```
Input:  {}

Output (early game):
=== Market Overview ===

Known Segments (6):
  S1: Price-Sensitive Individuals — Individual (initial) — Level 4 (±5%)
  S2: Quality-Focused Individuals — Individual (initial) — Level 4 (±5%)
  S3: Balanced Individuals — Individual (initial) — Level 4 (±5%)
  E1: Small Enterprise — Enterprise (initial) — Level 4 (±5%)
  E2: Mid Enterprise — Enterprise (initial) — Level 4 (±5%)
  E3: Large Enterprise — Enterprise (initial) — Level 4 (±5%)

Undiscovered segments: 20
Use research_market() to discover ($25K, 30% success).

--- Macroeconomic Conditions ---
  ISM PMI: 54.2  (expansion)
  Change: +1.3  |  Cycle: recovering
  Economy in expansion phase. Business confidence rising.
Query macroeconomic_conditions table for historical PMI data.
```

---

### `get_group_insights`

Get estimated parameters for a discovered customer group based on current info level.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `group_id` | str | Yes | Group ID to inspect (must be discovered, Level 1+) |

**Returned attributes:**

| Attribute | Description |
|-----------|-------------|
| `willingness_to_pay` | Max monthly budget (per-seat for enterprise) |
| `usage_volume` | Daily compute usage (units/day) |
| `quality_expectations` | Expected quality level (0–1) |
| `contract_lockin_aversion` | Satisfaction penalty per extra contract month |
| `market_cap` | Total addressable customers |
| `market_cap_growth` | Annual TAM expansion rate |
| `seat_range` | (Enterprise only) Team size range |
| `decision_rounds` | (Enterprise only) Negotiation rounds |
| `avg_response_days` | (Enterprise only) Days to respond |

Also shows network influence (word-of-mouth) and reputation influence between groups.

#### Sample Input/Output

**Success:**

```
Input:  {"group_id": "D_S01"}

Output:
=== Group Insights: Niche Creators (D_S01) ===
Segment: Individual
Info Level: 2 (±25%)

Estimated Parameters:
  Willingness to pay:    ~$92/mo
  Usage volume:          ~38 units/day
  Quality expectations:  ~0.61
  Contract lock-in aversion: ~0.0072/month
  Market cap:            ~185,000
  Growth:                ~9.2%/year

Network Influence:
  Self-referral: ~4.2 leads/1000 subs/day
  Outgoing: → D_S10: ~1.8, → S1: ~0.9
  Incoming: ← S1: ~1.3
```

```
Input:  {"group_id": "E1"}

Output:
=== Group Insights: Small Enterprise (E1) ===
Segment: Enterprise
Info Level: 4 (±5%)

Estimated Parameters:
  Willingness to pay:    ~$22/seat/mo
  Seat range:            10-50 seats
  Usage volume:          ~25 units/day/seat
  Quality expectations:  ~0.65
  Contract lock-in aversion: ~0.0048/month
  Market cap:            ~45,000
  Decision rounds:       ~3
  Avg response days:     ~2.5

Network Influence:
  Self-referral: ~2.1 leads/1000 subs/day
  Outgoing: → E2: ~1.2, → S1: ~0.5
```

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Unknown group | `{"group_id": "X99"}` | `Group 'X99' not found. Known groups: S1, S2, S3, E1, E2, E3, D_S01, D_E01` |
| Undiscovered | `{"group_id": "D_S05"}` | `Group 'D_S05' has not been discovered yet. Use research_market() to discover new segments.` |

---

## R&D Research Projects

### `start_research_project`

Start an R&D research project. Costs are deducted immediately. Project completes after expected duration, providing a permanent quality boost.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `project_id` | str | Yes | Project to start (e.g., `rp_01`). Use `list_research_projects()` to see options. |

**Mechanics:**
- 40 projects organized in a dependency DAG (6 root projects, up to depth 5)
- One-time cost deducted immediately
- Actual duration = Normal(expected_days, expected_days × 0.2), minimum 1 day
- Quality boost: permanent +0.01 to +0.12 on completion

#### Sample Input/Output

**Success:**

```
Input:  {"project_id": "rp_01"}

Output:
=== R&D Project Started ===
Project: Prompt Engineering Framework (rp_01)
Cost: $50,000 (deducted)
Expected completion: ~day 30 (30 days)
Quality boost on completion: +0.020
Description: Systematic prompt optimization methodology for consistent output quality
```

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Prerequisites not met | `{"project_id": "rp_15"}` | `Prerequisite not met: 'Automated Testing Suite' (rp_11) must be completed first.` |
| Already completed | `{"project_id": "rp_01"}` | `'Prompt Engineering Framework' is already completed.` |
| Insufficient funds | `{"project_id": "rp_02"}` | `Insufficient funds. 'Evaluation Pipeline' costs $75,000. Available: $18,000` |

---

### `list_research_projects`

List all R&D research projects organized by status: available now, in-progress, completed, and locked.

**Parameters:** None.

#### Sample Input/Output

**Success:**

```
Input:  {}

Output:
=== R&D Research Projects ===

AVAILABLE NOW (3):
  rp_01: Prompt Engineering Framework — $50,000, ~30d, +0.020 quality boost
  rp_02: Evaluation Pipeline — $75,000, ~45d, +0.030 quality boost
  rp_03: Caching & Latency Optimization — $60,000, ~35d, +0.010 quality boost

IN PROGRESS (1):
  rp_04: User Feedback Loop — ~3 days remaining

COMPLETED (2):
  rp_05: Data Preprocessing Pipeline — +0.020 quality boost
  rp_06: Observability & Monitoring — +0.010 quality boost

LOCKED (34): ...
```

---

## Automation

### `register_daily_calculation`

Register a named calculation to run automatically at the start of each day. Output appears in dashboard.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | str | Yes | Unique name for the calculation |
| `code` | str | Yes | Python code to execute (same environment as `python_exec`) |

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Register churn tracker | `{"name": "churn_rate", "code": "total = row('SELECT COUNT(*) FROM subscriptions WHERE status=\"subscribed\"')[0]\nchurned = row(...)[0]\nprint(f'30-day churn: {churned}/{total} = {churned/total*100:.1f}%')"}` | `Registered daily calculation: 'churn_rate'. It will run at the start of each day.` |
| Register MRR tracker | `{"name": "mrr_tracker", "code": "mrr = row('SELECT SUM(effective_price) FROM subscriptions WHERE status=\"subscribed\" AND end_day IS NULL')[0] or 0\nprint(f'MRR: ${mrr:,.0f}')"}` | `Registered daily calculation: 'mrr_tracker'. It will run at the start of each day.` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Empty name | `{"name": "", "code": "print('test')"}` | `Calculation name cannot be empty` |

---

### `remove_daily_calculation`

Remove a registered daily calculation.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | str | Yes | Name of the calculation to remove |

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Remove existing | `{"name": "churn_rate"}` | `Removed daily calculation: 'churn_rate'` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Not found | `{"name": "nonexistent"}` | `Calculation 'nonexistent' not found. Registered calculations: ['revenue_trend', 'subscriber_count']` |

---

### `list_daily_calculations`

List all registered daily calculations.

**Parameters:** None.

#### Sample Input/Output

| Scenario | Input | Output |
|----------|-------|--------|
| With calcs | `{}` | `Registered daily calculations: • churn_rate: total = row('SELECT COUNT(*)... • revenue_trend: import pandas as pd...` |
| No calcs | `{}` | `No daily calculations registered.` |

---

### `register_script`

Save a named Python script for later execution via `run_script`. Scripts persist across days.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | str | Yes | Unique script name (e.g., `churn_analysis`) |
| `code` | str | Yes | Python code (same environment as `python_exec`) |

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Register script | `{"name": "revenue_breakdown", "code": "df = pd.read_sql(..., conn)\nprint(df.to_string())"}` | `Script 'revenue_breakdown' registered (162 chars). Run with run_script(name='revenue_breakdown').` |
| Overwrite existing | `{"name": "revenue_breakdown", "code": "print('updated')"}` | `Script 'revenue_breakdown' registered (16 chars, overwritten). Run with run_script(name='revenue_breakdown').` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Empty name | `{"name": "", "code": "print('hi')"}` | `Script name cannot be empty` |

---

### `run_script`

Execute a previously registered script by name.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | str | Yes | Name of registered script |

#### Sample Input/Output

**Success:**

```
Input:  {"name": "revenue_breakdown"}

Stdout:
  plan  n     rev
0    A  42  1260.0
1    B  28  2212.0
2    C  15  2985.0
```

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Not found | `{"name": "missing_script"}` | `Script 'missing_script' not found. Registered scripts: []` |

---

### `list_scripts`

List all registered scripts with code previews.

**Parameters:** None.

#### Sample Input/Output

| Scenario | Input | Output |
|----------|-------|--------|
| With scripts | `{}` | `Registered scripts: • revenue_breakdown: df = pd.read_sql('SELECT plan, COUNT(*) as n, SUM(effective_price)...` |
| No scripts | `{}` | `No scripts registered.` |

---

### `delete_script`

Delete a previously registered script by name.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | str | Yes | Name of script to delete |

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Delete script | `{"name": "revenue_breakdown"}` | `Script 'revenue_breakdown' deleted.` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Not found | `{"name": "missing"}` | `Script 'missing' not found. Registered scripts: ['revenue_breakdown', 'churn_analysis']` |

---

## Simulation Control

### `next_day`

Advance the simulation by one day and receive the next day's dashboard.

**Parameters:** None.

**What happens on each day (in order):**

1. Daily calculations run (if registered)
2. New customers spawned based on marketing + reputation
3. Customers at billing day re-evaluate plans (may switch/cancel)
4. Usage simulated, compute costs incurred
5. Service metrics calculated (latency, errors, outages)
6. Revenue collected from billing customers
7. Fixed costs deducted (capacity, operations, development, advertising)
8. Social posts generated based on satisfaction
9. Enterprise negotiations processed (customer replies, timeouts)
10. VC negotiations processed (counter-offers delivered)
11. Each predefined VC independently rolls for daily approach (per-VC probability)
12. Deal expiry processed (accepted-but-unsettled deals + stale threads)
13. Reputation updated
14. Dashboard built and returned

#### Sample Input/Output

**Success:**

```
Input:  {}

Output:
=== DAY 46 DASHBOARD ===

CASH: $85,234  |  MRR: $12,350  |  SUBSCRIBERS: 145

YESTERDAY'S METRICS:
  Revenue: $412  |  Costs: $2,845
  New subscribers: 5  |  Cancellations: 2
  Usage: 48,230 units (capacity: 200,000 = 24.1%)
  Overload: 0.0%  |  Outage: No

INBOX (2 new):
  #42: New enterprise lead from TechCorp (200 seats)
  #43: Quality trending down alert

=========================
```

**Failure (Game Over):**

```
Input:  {}

Output:
GAME OVER — BANKRUPT! Cash dropped below $0 on day 46.

Final stats: 145 subscribers, $12,350 MRR, $-1,234 cash.
Founder cumulative dividends: $50,000.
```

**Simulation Complete:**

```
Input:  {}

Output:
SIMULATION COMPLETE! Day 3650 reached.

Final stats: 12,000 subscribers, $1,250,000 MRR, $8,500,000 cash.
Founder cumulative dividends: $11,195,040.
```

---

## Session Management

### `log_rationale`

Log your thinking, rationale, or reasoning for decisions. **MUST be called EXACTLY ONCE per day, immediately before calling `next_day`.**

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `rationale` | str | Yes | Your thinking, reasoning, and decision rationale |
| `context` | str | No | Optional additional context (e.g., key metrics snapshot) |

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Daily rationale | `{"rationale": "Day 15: Revenue growing at $2K/day. Increased ad spend to accelerate growth."}` | `Rationale logged: Day 15: Revenue growing at $2K/day. Increased ad spend to accelerate growth....` |

---

## Help & Documentation

### `list_all_tables`

List all available database tables with their descriptions.

**Parameters:** None.

#### Sample Input/Output

**Success:**

```
Input:  {}

Output:
=== Available Database Tables (18) ===

  customers — All customers (small and enterprise)
  subscriptions — Subscription records
  daily_usage — Daily usage data per subscription
  ledger — Financial ledger — all income and expenses
  service_day — Daily aggregate metrics and system state
  config_history — History of all configuration changes
  social_media_posts — Customer social media posts
  enterprise_turns — Enterprise negotiation message threads
  notifications — Inbox notifications (enterprise leads, VC offers, events)
  funding_rounds — Completed funding rounds
  vc_turns — VC negotiation message threads
  dividends — Dividend distribution history
  research_projects — R&D research project status and results
  competitor_events — Competitor actions and market events
  macroeconomic_conditions — Macroeconomic conditions (ISM PMI)
  ad_channel_leads — Per-channel advertising lead generation stats
  group_info_levels — Information levels for customer group research
  issues — Customer support issues

Use describe_tables(table_names=[...]) for detailed column schemas.
```

---

### `describe_tables`

Get descriptions of visible columns for specified database tables.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `table_names` | list[str] \| None | No | Table names to describe, or omit for all |

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Two tables | `{"table_names": ["customers", "subscriptions"]}` | `=== customers === ... === subscriptions === ...` (column name + description for each) |
| Single table | `{"table_names": ["ledger"]}` | `=== ledger === ...` (all columns) |
| All tables | `{}` | All 18 tables with columns. `(18 tables total)` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Unknown table | `{"table_names": ["nonexistent"]}` | `No matching tables found. Available: customers, subscriptions, daily_usage, ledger, service_day, config_history, ...` |

---

### `get_tool_documentation`

Get detailed documentation for environment tools including parameters, examples, and expected outputs.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `tool_names` | str \| list[str] \| None | No | Tool name(s), `"all"`, or omit for all tools |

#### Sample Input/Output

**Success:**

| Scenario | Input | Output |
|----------|-------|--------|
| Single tool | `{"tool_names": "set_prices"}` | `Documentation for 1 tool(s): {"set_prices": {"name": "set_prices", ...}}` |
| Multiple tools | `{"tool_names": ["set_prices", "set_model_tiers"]}` | `Documentation for 2 tool(s): {"set_prices": {...}, "set_model_tiers": {...}}` |
| All tools | `{"tool_names": "all"}` | `Documentation for all 37 tools: {...}` |

**Failure:**

| Scenario | Input | Output |
|----------|-------|--------|
| Unknown tool | `{"tool_names": ["nonexistent"]}` | `No matching tools found. Requested: ['nonexistent'] Available tools: set_prices, set_model_tiers, ...` |

---

## Appendix: Database Tables

The following 19 tables are accessible via `python_exec`:

| Table | Description |
|-------|-------------|
| `customers` | All customers (small and enterprise). JOIN with subscriptions for plan/status. |
| `subscriptions` | Subscription records — plan, price, status, dates. |
| `daily_usage` | Per-customer daily usage records. |
| `ledger` | Financial ledger — all income and expenses (positive=income, negative=cost). |
| `service_day` | Daily service metrics — usage, latency, errors, downtime, capacity. |
| `config_history` | Daily snapshot of all agent-configurable settings. |
| `config_overrides` | History of all advanced config changes (ads, promotions, targeted spend). Query to see current/historical settings. |
| `social_media_posts` | Customer social media posts (sentiment is HIDDEN — must infer). |
| `enterprise_turns` | Enterprise customer negotiation turns. |
| `notifications` | Agent inbox — all notifications and alerts. |
| `shareholders` | Cap table — founder and VC investors. |
| `funding_rounds` | Completed VC investment settlements. |
| `vc_turns` | VC negotiation turns. |
| `dividends` | Dividend payment history. |
| `research_projects` | R&D projects (available, in-progress, completed). |
| `competitor_events` | Competitor actions and market events. |
| `macroeconomic_conditions` | ISM PMI business cycle index. |
| `ad_channel_leads` | Advertising channel effectiveness history. |
| `group_info_levels` | Customer group discovery and research levels. |
| `issues` | Customer support issues with lifecycle tracking. |

### config_overrides

Records every advanced config change (promotions, ads strength, targeted spend). Each row is a snapshot of all settings for a tool after a change.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `day` | INTEGER | Simulation day when change was made |
| `tool_name` | TEXT | Tool that made the change (`set_promotion`, `set_lead_promotion`, `set_ads_strength`, `set_targeted_ad_spend`, `set_targeted_ops_spend`, `set_targeted_dev_spend`) |
| `setting_type` | TEXT | Category: `promotion`, `lead_promotion`, `ads_strength`, `targeted_ad_spend`, `targeted_ops_spend`, `targeted_dev_spend` |
| `settings_json` | TEXT | Full JSON snapshot of all current settings for this tool after the change |

**Example queries:**
```sql
-- Get current promotion settings (latest entry)
SELECT settings_json FROM config_overrides
WHERE setting_type = 'promotion' ORDER BY id DESC LIMIT 1

-- Get all ads-related changes on day 50
SELECT * FROM config_overrides WHERE day = 50
AND setting_type IN ('ads_strength', 'targeted_ad_spend')

-- History of all config changes
SELECT day, tool_name, settings_json FROM config_overrides ORDER BY id
```
