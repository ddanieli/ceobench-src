# BossBench Notification Types — Complete Reference

All notifications appear in two views:

1. **Dashboard View** — Shown in the agent's daily system prompt. Format: `[ID] Title: Summary (truncated to 80 chars)...`
2. **Expanded View** — Retrieved via `expand_notification(id)`. Shows full summary, structured JSON details, and reference links.

**Expanded view format:**
```
=== Notification #<id> ===
Type: <type>
Day: <day>

Title: <title>

Summary:
<full summary text>

Details:
{ <structured JSON> }

Reference: <reference_type> #<reference_id>
```

---

## 1. Customer & Sales

### `large_customer_message` — New Enterprise Lead

**Trigger:** New enterprise customer enters the pipeline.

| View | Example |
|------|---------|
| **Dashboard** | `[42] New enterprise lead: 200 seats: A new enterprise customer interested (200 seats).` |
| **Expanded** | |

```
=== Notification #42 ===
Type: large_customer_message
Day: 15

Title: New enterprise lead: 200 seats

Summary:
A new enterprise customer interested (200 seats).

Details:
{
  "customer_id": 312,
  "thread_type": "new_lead",
  "seat_count": 200
}

Reference: thread #156
```

---

### `large_customer_message` — Enterprise Counter-Offer

**Trigger:** Enterprise customer responds to an agent's offer with a counter-proposal.

| View | Example |
|------|---------|
| **Dashboard** | `[55] Enterprise counter-offer (Customer #312): Customer 312 (200 seats) counter-offered $85.00/seat for Pla...` |
| **Expanded** | |

```
=== Notification #55 ===
Type: large_customer_message
Day: 18

Title: Enterprise counter-offer (Customer #312)

Summary:
Customer 312 (200 seats) counter-offered $85.00/seat for Plan 2, 12-month contract.

Details:
{
  "customer_id": 312,
  "thread_type": "counter_offer",
  "seat_count": 200,
  "counter_price": 85.0,
  "counter_plan": 2,
  "counter_months": 12
}

Reference: thread #156
```

---

### `large_customer_message` — Churn Risk

**Trigger:** An existing enterprise customer is considering cancellation (quality/price dissatisfaction).

| View | Example |
|------|---------|
| **Dashboard** | `[70] Churn risk: Enterprise customer 312: Enterprise customer (200 seats, $90.00/mo) is considering cancel...` |
| **Expanded** | |

```
=== Notification #70 ===
Type: large_customer_message
Day: 45

Title: Churn risk: Enterprise customer 312

Summary:
Enterprise customer (200 seats, $90.00/mo) is considering cancellation. Immediate attention needed.

Details:
{
  "customer_id": 312,
  "thread_type": "churn_risk",
  "seat_count": 200,
  "monthly_value": 18000.0,
  "current_plan": 2
}

Reference: thread #201
```

---

### `large_customer_message` — Plan Change Request

**Trigger:** Enterprise customer wants to upgrade or downgrade their plan.

| View | Example |
|------|---------|
| **Dashboard** | `[80] Plan change: Enterprise customer 312: Enterprise customer (200 seats) wants to upgrade from Plan 1 t...` |
| **Expanded** | |

```
=== Notification #80 ===
Type: large_customer_message
Day: 60

Title: Plan change: Enterprise customer 312

Summary:
Enterprise customer (200 seats) wants to upgrade from Plan 1 to Plan 2.

Details:
{
  "customer_id": 312,
  "thread_type": "plan_change",
  "seat_count": 200,
  "current_plan": 1,
  "target_plan": 2,
  "monthly_value": 8000.0
}

Reference: thread #220
```

---

### `deal_won`

**Trigger:** Enterprise customer accepts the agent's offer and signs a contract.

| View | Example |
|------|---------|
| **Dashboard** | `[60] Deal won: 200 seats at $90.00/seat: Enterprise customer (Customer #312) accepted the offer. Monthly ...` |
| **Expanded** | |

```
=== Notification #60 ===
Type: deal_won
Day: 20

Title: Deal won: 200 seats at $90.00/seat

Summary:
Enterprise customer (Customer #312) accepted the offer. Monthly value: $18000.00/mo. Contract: 12 months.

Details:
{
  "customer_id": 312,
  "thread_type": "new_lead",
  "agreed_price": 90.0,
  "agreed_plan": 2,
  "contract_months": 12,
  "contract_end_day": 380,
  "seat_count": 200,
  "monthly_value": 18000.0
}

Reference: thread #156
```

---

### `lead_lost` — Timeout (No Response)

**Trigger:** Agent didn't respond to an enterprise lead within the timeout window.

| View | Example |
|------|---------|
| **Dashboard** | `[50] Lead lost: No response for 5 days: Enterprise lead (Customer #400) was lost because no agent respond...` |
| **Expanded** | |

```
=== Notification #50 ===
Type: lead_lost
Day: 20

Title: Lead lost: No response for 5 days

Summary:
Enterprise lead (Customer #400) was lost because no agent responded within 5 days. Customer has moved on to other solutions.

Details:
{
  "customer_id": 400,
  "thread_type": "new_lead",
  "seat_count": 150,
  "days_waiting": 5
}

Reference: thread #180
```

---

### `lead_lost` — Ghosted (Max Turns)

**Trigger:** Enterprise lead stopped responding after reaching maximum negotiation turns.

| View | Example |
|------|---------|
| **Dashboard** | `[52] Lead ghosted: 150 seats: Enterprise lead (Customer #400) stopped responding after max negotiation tu...` |
| **Expanded** | |

```
=== Notification #52 ===
Type: lead_lost
Day: 25

Title: Lead ghosted: 150 seats

Summary:
Enterprise lead (Customer #400) stopped responding after max negotiation turns.

Details:
{
  "customer_id": 400,
  "thread_type": "new_lead",
  "seat_count": 150
}

Reference: thread #180
```

---

### `lead_lost` — Rejected

**Trigger:** Enterprise lead rejected the agent's offer and ended negotiations.

| View | Example |
|------|---------|
| **Dashboard** | `[53] Lead lost: 100 seats: Enterprise lead (Customer #410) rejected the offer.` |
| **Expanded** | |

```
=== Notification #53 ===
Type: lead_lost
Day: 22

Title: Lead lost: 100 seats

Summary:
Enterprise lead (Customer #410) rejected the offer.

Details:
{
  "customer_id": 410,
  "thread_type": "new_lead",
  "seat_count": 100
}

Reference: thread #185
```

---

### `contract_renewal`

**Trigger:** An enterprise customer's contract is about to expire.

| View | Example |
|------|---------|
| **Dashboard** | `[90] Contract renewal: 200 seats expiring in 14d: Enterprise customer (200 seats, Plan 2, $90.00/seat) c...` |
| **Expanded** | |

```
=== Notification #90 ===
Type: contract_renewal
Day: 366

Title: Contract renewal: 200 seats expiring in 14d

Summary:
Enterprise customer (200 seats, Plan 2, $90.00/seat) contract expires in 14 days. Send renewal offerings.

Details:
{
  "customer_id": 312,
  "thread_type": "renewal",
  "current_plan": 2,
  "current_price": 90.0,
  "contract_months": 12,
  "contract_end_day": 380,
  "days_until_expiry": 14,
  "seat_count": 200
}

Reference: thread #250
```

---

### `customer_churned`

**Trigger:** Enterprise contract expired without renewal.

| View | Example |
|------|---------|
| **Dashboard** | `[95] Contract expired: 200 seats lost: Enterprise customer contract expired without renewal. Lost revenue...` |
| **Expanded** | |

```
=== Notification #95 ===
Type: customer_churned
Day: 380

Title: Contract expired: 200 seats lost

Summary:
Enterprise customer contract expired without renewal. Lost revenue: $18000.00/mo.

Details:
{
  "customer_id": 312,
  "thread_type": "renewal",
  "seat_count": 200,
  "monthly_value": 18000.0,
  "churn_reason": "contract_expired"
}

Reference: customer #312
```

---

## 2. Venture Capital & Financing

### `vc_approach`

**Trigger:** A VC firm initiates investment discussions.

| View | Example |
|------|---------|
| **Dashboard** | `[100] New VC approach: Sequoia Capital: Sequoia Capital wants to invest $2,000,000 for 15.0% equity. Ter...` |
| **Expanded** | |

```
=== Notification #100 ===
Type: vc_approach
Day: 50

Title: New VC approach: Sequoia Capital

Summary:
Sequoia Capital wants to invest $2,000,000 for 15.0% equity. Terms: milestone tranching.
Use send_vc_deal with shareholder_id=5 to negotiate.

Details:
{
  "shareholder_id": 5,
  "vc_name": "Sequoia Capital",
  "vc_id": "sequoia",
  "investment_amount": 2000000,
  "initial_offer_pct": 0.15,
  "terms": {
    "anti_dilution": false,
    "milestone_tranching": true,
    "milestone_tranche_pct": 0.4,
    "milestone_revenue_multiplier": 2.0,
    "milestone_deadline_days": 180,
    "redemption_rights": false
  }
}

Reference: vc_thread #30
```

---

### `vc_counter_offer`

**Trigger:** VC responds with a counter-proposal during negotiation.

| View | Example |
|------|---------|
| **Dashboard** | `[105] VC counter-offer: Sequoia Capital: Sequoia Capital counters with 12.0% for $2,000,000. Turn 2.` |
| **Expanded** | |

```
=== Notification #105 ===
Type: vc_counter_offer
Day: 52

Title: VC counter-offer: Sequoia Capital

Summary:
Sequoia Capital counters with 12.0% for $2,000,000. Turn 2.

Details:
{
  "shareholder_id": 5,
  "vc_name": "Sequoia Capital",
  "offer_pct": 0.12,
  "offer_amount": 2000000,
  "turn": 2
}

Reference: vc_thread #30
```

---

### `vc_deal_accepted`

**Trigger:** Agent accepts a VC investment offer (via `accept_vc_deal` tool).

| View | Example |
|------|---------|
| **Dashboard** | `[110] VC deal accepted: Sequoia Capital: Sequoia Capital accepted 10.0% for $2,000,000. Settle with sett...` |
| **Expanded** | |

```
=== Notification #110 ===
Type: vc_deal_accepted
Day: 55

Title: VC deal accepted: Sequoia Capital

Summary:
Sequoia Capital accepted 10.0% for $2,000,000. Settle with settle_investments() before day 62.

Reference: vc_thread #30
```

---

### `vc_deal_settled`

**Trigger:** Agent calls `settle_accepted_vc_deals` to finalize the investment and issue shares.

| View | Example |
|------|---------|
| **Dashboard** | `[115] VC Deal Settled: Sequoia Capital: Sequoia Capital invested $2,000,000 for 10.0% equity` |
| **Expanded** | |

```
=== Notification #115 ===
Type: vc_deal_settled
Day: 57

Title: VC Deal Settled: Sequoia Capital

Summary:
Sequoia Capital invested $2,000,000 for 10.0% equity

Details:
{
  "vc_name": "Sequoia Capital",
  "amount": 2000000,
  "share_pct": 0.10,
  "new_shares": 111111,
  "price_per_share": 0.018,
  "thread_id": 30
}

Reference: vc_thread #30
```

---

### `vc_deal_expired`

**Trigger:** Accepted deal was not settled before the deadline.

| View | Example |
|------|---------|
| **Dashboard** | `[120] VC deal expired: Sequoia Capital: The accepted deal with Sequoia Capital for 10.0% ($2,000,000) ha...` |
| **Expanded** | |

```
=== Notification #120 ===
Type: vc_deal_expired
Day: 63

Title: VC deal expired: Sequoia Capital

Summary:
The accepted deal with Sequoia Capital for 10.0% ($2,000,000) has expired without settlement.

Details:
{
  "shareholder_id": 5,
  "vc_name": "Sequoia Capital"
}

Reference: vc_thread #30
```

---

### `vc_anti_dilution`

**Trigger:** Company valuation drops below VC's anti-dilution floor, bonus shares auto-issued.

| View | Example |
|------|---------|
| **Dashboard** | `[130] Anti-dilution triggered: Andreessen Horowitz: Andreessen Horowitz anti-dilution protection activat...` |
| **Expanded** | |

```
=== Notification #130 ===
Type: vc_anti_dilution
Day: 100

Title: Anti-dilution triggered: Andreessen Horowitz

Summary:
Andreessen Horowitz anti-dilution protection activated. Valuation dropped below floor ($5,000,000). 50,000 bonus shares issued.

Reference: vc_thread #35
```

---

### `vc_milestone_hit`

**Trigger:** MRR reaches the milestone target, tranche 2 of investment released.

| View | Example |
|------|---------|
| **Dashboard** | `[135] Milestone hit: Sequoia Capital tranche 2 released: MRR reached $50,000 (target: $40,000). Sequoia ...` |
| **Expanded** | |

```
=== Notification #135 ===
Type: vc_milestone_hit
Day: 120

Title: Milestone hit: Sequoia Capital tranche 2 released

Summary:
MRR reached $50,000 (target: $40,000). Sequoia Capital tranche 2 of $800,000 released.

Reference: vc_thread #30
```

---

### `vc_milestone_missed`

**Trigger:** Milestone deadline passed without hitting the MRR target, tranche 2 forfeited.

| View | Example |
|------|---------|
| **Dashboard** | `[140] Milestone missed: Sequoia Capital tranche 2 forfeited: MRR of $25,000 did not reach target $40,000...` |
| **Expanded** | |

```
=== Notification #140 ===
Type: vc_milestone_missed
Day: 230

Title: Milestone missed: Sequoia Capital tranche 2 forfeited

Summary:
MRR of $25,000 did not reach target $40,000 by deadline (day 230). Tranche 2 forfeited.

Reference: vc_thread #30
```

---

### `vc_redemption`

**Trigger:** VC exercises redemption rights (auto-triggered when eligible), buying back shares at a multiplier.

| View | Example |
|------|---------|
| **Dashboard** | `[145] Redemption exercised: Andreessen Horowitz: Andreessen Horowitz exercised redemption rights. Buyback...` |
| **Expanded** | |

```
=== Notification #145 ===
Type: vc_redemption
Day: 300

Title: Redemption exercised: Andreessen Horowitz

Summary:
Andreessen Horowitz exercised redemption rights. Buyback: $3,000,000 (1.5× investment). 200,000 shares returned.

Reference: vc_thread #35
```

---

### `dividend_declared`

**Trigger:** Agent declares a dividend (via `declare_dividend` tool).

| View | Example |
|------|---------|
| **Dashboard** | `[150] Dividend: $50,000: $0.050000 per share to 3 shareholders` |
| **Expanded** | |

```
=== Notification #150 ===
Type: dividend_declared
Day: 60

Title: Dividend: $50,000

Summary:
$0.050000 per share to 3 shareholders
```

---

### `vc_advisory`

**Trigger:** An existing VC investor sends strategic advice (random daily probability).

| View | Example |
|------|---------|
| **Dashboard** | `[155] Investor note from Sequoia Capital: Your MRR growth is impressive, but customer acquisition costs ...` |
| **Expanded** | |

```
=== Notification #155 ===
Type: vc_advisory
Day: 75

Title: Investor note from Sequoia Capital

Summary:
Your MRR growth is impressive, but customer acquisition costs are rising.
As investors focused on growth efficiency and unit economics, we recommend
prioritizing these areas for sustainable growth.

Reference: vc_advisory #5
```

---

## 3. Research & Development

### `research_complete`

**Trigger:** An R&D project finishes (product quality improvement).

| View | Example |
|------|---------|
| **Dashboard** | `[160] R&D Complete: Performance Optimization: Performance Optimization finished! Quality boost: +0.150.` |
| **Expanded** | |

```
=== Notification #160 ===
Type: research_complete
Day: 40

Title: R&D Complete: Performance Optimization

Summary:
Performance Optimization finished! Quality boost: +0.150.

Details:
{
  "project_id": 3,
  "quality_boost": 0.15
}
```

---

### `group_research_complete`

**Trigger:** Customer segment research finishes, improving parameter accuracy for that group.

| View | Example |
|------|---------|
| **Dashboard** | `[165] Research complete: SMB Tech: Group research on SMB Tech (D_I_1) is complete. Info level upgraded: 1...` |
| **Expanded** | |

```
=== Notification #165 ===
Type: group_research_complete
Day: 35

Title: Research complete: SMB Tech

Summary:
Group research on SMB Tech (D_I_1) is complete. Info level upgraded: 1 → 2.
Parameter accuracy is now ±25%. Use view_customer_groups to see updated estimates.

Details:
{
  "group_id": "D_I_1",
  "from_level": 1,
  "to_level": 2
}
```

Accuracy levels: Level 1 = ±50%, Level 2 = ±25%, Level 3 = ±10%, Level 4 = ±5%.

---

### `market_discovery`

**Trigger:** Agent discovers a new customer segment (via `discover_segment` tool).

| View | Example |
|------|---------|
| **Dashboard** | `[170] New segment discovered: Large Enterprise Finance: Market research revealed a new enterprise segmen...` |
| **Expanded** | |

```
=== Notification #170 ===
Type: market_discovery
Day: 30

Title: New segment discovered: Large Enterprise Finance

Summary:
Market research revealed a new enterprise segment: Large Enterprise Finance (D_E_3).
Info Level 1 — parameter estimates are noisy (±50%). Conduct further research to improve accuracy.
```

---

## 4. Social Media & Market Events

### `social_media_post` — Individual Customer Post

**Trigger:** A customer posts about the product on social media (positive, neutral, or negative).

| View | Example |
|------|---------|
| **Dashboard** | `[175] 😊 New positive social media post: A customer from group D_I_1 posted about NovaMind. 45 likes, 12 sh...` |
| **Expanded** | |

```
=== Notification #175 ===
Type: social_media_post
Day: 25

Title: 😊 New positive social media post

Summary:
A customer from group D_I_1 posted about NovaMind. 45 likes, 12 shares. Sentiment: positive.

Details:
{
  "post_id": 88,
  "customer_id": 250,
  "group_id": "D_I_1",
  "sentiment": "positive",
  "likes": 45,
  "shares": 12,
  "virality_score": 0.73
}

Reference: post #88
```

Sentiment emojis: 😊 positive, 😐 neutral, 😠 negative.

---

### `social_media_post` — Macro-Economic Posts (Aggregated)

**Trigger:** Multiple social media posts appear discussing the current economic climate.

| View | Example |
|------|---------|
| **Dashboard** | `[180] 📊 3 social media posts about economic conditions: 3 posts appeared discussing the current economic...` |
| **Expanded** | |

```
=== Notification #180 ===
Type: social_media_post
Day: 90

Title: 📊 3 social media posts about economic conditions

Summary:
3 posts appeared discussing the current economic climate (PMI: 52.3, trend: slow expansion).
Check social_media_posts table for details.

Details:
{
  "macro_posts": true,
  "count": 3,
  "pmi": 52.3
}
```

---

### `macro_economic_update`

**Trigger:** Quarterly PMI (Purchasing Managers' Index) publication.

| View | Example |
|------|---------|
| **Dashboard** | `[185] 📈 Economic Update: PMI 53.2 (Slow Expansion): The economy shows continued moderate growth with PM...` |
| **Expanded** | |

```
=== Notification #185 ===
Type: macro_economic_update
Day: 90

Title: 📈 Economic Update: PMI 53.2 (Slow Expansion)

Summary:
The economy shows continued moderate growth with PMI at 53.2, up from 51.8 last quarter.

Details:
{
  "pmi_value": 53.2,
  "pmi_change": 1.4,
  "pmi_trend": "slow_expansion",
  "cycle_phase": "expansion"
}
```

Trend emojis: 📈 rising, 📉 falling, ➡️ stable.

---

### `competitor_event`

**Trigger:** A competitor launches a product, raising market quality expectations.

| View | Example |
|------|---------|
| **Dashboard** | `[190] Competitor Event: Major Launch: A major competitor launched a new product. Market quality expectati...` |
| **Expanded** | |

```
=== Notification #190 ===
Type: competitor_event
Day: 80

Title: Competitor Event: Major Launch

Summary:
A major competitor launched a new product. Market quality expectations have risen by +0.200.
Social media buzz about the competitor will continue for 14 days.

Details:
{
  "boost_amount": 0.2,
  "severity": "major",
  "post_end_day": 94
}
```

Severity levels: `minor`, `moderate`, `major`.

---

## Summary Table

| # | Type | Category | Trigger | Has Details JSON | Reference Type |
|---|------|----------|---------|-----------------|----------------|
| 1 | `large_customer_message` | Sales | New lead, counter-offer, churn risk, plan change | ✅ | `thread` |
| 2 | `deal_won` | Sales | Customer accepts offer | ✅ | `thread` |
| 3 | `lead_lost` | Sales | Timeout, ghosted, rejected | ✅ | `thread` |
| 4 | `contract_renewal` | Sales | Contract expiring soon | ✅ | `thread` |
| 5 | `customer_churned` | Sales | Contract expired w/o renewal | ✅ | `customer` |
| 6 | `vc_approach` | VC | VC initiates investment | ✅ | `vc_thread` |
| 7 | `vc_counter_offer` | VC | VC counter-proposes | ✅ | `vc_thread` |
| 8 | `vc_deal_accepted` | VC | Agent accepts deal | ❌ | `vc_thread` |
| 9 | `vc_deal_settled` | VC | Investment finalized | ✅ | `vc_thread` |
| 10 | `vc_deal_expired` | VC | Deal not settled in time | ✅ | `vc_thread` |
| 11 | `vc_anti_dilution` | VC | Valuation drops below floor | ❌ | `vc_thread` |
| 12 | `vc_milestone_hit` | VC | MRR milestone reached | ❌ | `vc_thread` |
| 13 | `vc_milestone_missed` | VC | MRR milestone deadline passed | ❌ | `vc_thread` |
| 14 | `vc_redemption` | VC | VC exercises buyback | ❌ | `vc_thread` |
| 15 | `dividend_declared` | VC | Agent declares dividend | ❌ | — |
| 16 | `vc_advisory` | VC | VC sends strategic advice | ❌ | `vc_advisory` |
| 17 | `research_complete` | R&D | R&D project finishes | ✅ | — |
| 18 | `group_research_complete` | R&D | Segment research finishes | ✅ | — |
| 19 | `market_discovery` | R&D | New segment discovered | ❌ | — |
| 20 | `social_media_post` | Social | Customer post (individual) | ✅ | `post` |
| 21 | `social_media_post` | Social | Macro-economic posts (batch) | ✅ | — |
| 22 | `macro_economic_update` | Market | Quarterly PMI publication | ✅ | — |
| 23 | `competitor_event` | Market | Competitor product launch | ✅ | — |
