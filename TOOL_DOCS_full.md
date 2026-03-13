# BossBench Tool Documentation (Full)

**Total tools in TOOL_DOCS:** 37

## Business Configuration

### set_prices

**Description:** Set monthly subscription prices for plans A, B, and C.

**Parameters:**
- `A` (float): Monthly price for plan A (must be positive)
- `B` (float): Monthly price for plan B (must be positive)
- `C` (float): Monthly price for plan C (must be positive)

**Returns:**
- success: Prices updated: A=$29.00, B=$79.00, C=$199.00
- failure: Missing price for plan X / Price for plan X must be positive

**Impact:**
Affects customer acquisition (higher prices = fewer sign-ups), churn (price vs value), and revenue. Changes take effect on next_day.

**Example Call:**
```json
{
  "tool": "set_prices",
  "arguments": {
    "A": 25,
    "B": 69,
    "C": 179
  }
}
```

**[INTERNAL] Notes:**
> Price stored in config_history. Affects Q_required via asymmetric sigmoid: Q_req(price) uses steepness_left (price < c_max/2) or steepness_right (price >= c_max/2). Enterprise customers negotiate off list price.

**Sample I/O:**

*SUCCESS examples:*
- **Set all three plans**: input=`{"A": 25, "B": 69, "C": 179}` → output=`Prices updated: A=$25.00, B=$69.00, C=$179.00`
- **Update only plan B**: input=`{"B": 89}` → output=`Prices updated: B=$89.00`
- **Update two plans**: input=`{"A": 19, "C": 149}` → output=`Prices updated: A=$19.00, C=$149.00`

*FAILURE examples:*
- **Negative price**: input=`{"A": -10}` → output=`Price for plan A must be positive`
- **Invalid plan key**: input=`{"D": 50}` → output=`Invalid plan keys: {'D'}. Valid: {'A', 'B', 'C'}`
- **Empty input**: input=`{}` → output=`Must provide at least one plan price`

---

### set_model_tiers

**Description:** Set AI model quality tiers for plans A, B, and C. Higher tiers = better quality but higher compute cost.

**Parameters:**
- `A` (int): Model tier for plan A (1-5)
- `B` (int): Model tier for plan B (1-5)
- `C` (int): Model tier for plan C (1-5)

**Returns:**
- success: Model tiers updated: A=tier2, B=tier3, C=tier4
- failure: Missing tier for plan X / Tier for plan X must be 1-5

**Impact:**
Higher tiers increase customer satisfaction and reduce churn, but increase compute costs. Each tier adds +0.10 quality. Higher tiers use more capable (and expensive) models.

**Tier Info:**
- Tier 1: cost=$0.0003, quality=0.55, class=Flash-Lite/4o-mini
- Tier 2: cost=$0.002, quality=0.65, class=Haiku/Flash
- Tier 3: cost=$0.006, quality=0.75, class=Sonnet/GPT-4o
- Tier 4: cost=$0.012, quality=0.85, class=Opus/GPT-5
- Tier 5: cost=$0.03, quality=0.95, class=o1/o3 reasoning

**Example Call:**
```json
{
  "tool": "set_model_tiers",
  "arguments": {
    "A": 2,
    "B": 3,
    "C": 5
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Set all tiers**: input=`{"A": 2, "B": 3, "C": 5}` → output=`Model tiers updated: A=tier2, B=tier3, C=tier5`
- **Upgrade only plan C**: input=`{"C": 5}` → output=`Model tiers updated: C=tier5`
- **Downgrade plan A**: input=`{"A": 1}` → output=`Model tiers updated: A=tier1`

*FAILURE examples:*
- **Tier out of range**: input=`{"A": 0}` → output=`Tier for plan A must be 1-5`
- **Tier too high**: input=`{"B": 6}` → output=`Tier for plan B must be 1-5`

---

### set_capacity_tier

**Description:** Set infrastructure capacity tier. Higher tiers handle more usage but cost more per day.

**Parameters:**
- `tier` (int): Capacity tier (0-7)

**Returns:**
- success: Capacity tier set to 1: 200,000 units/day, $215/day
- failure: Capacity tier must be 0-7. Use get_cost_info to see all tiers.

**Impact:**
When usage exceeds capacity, overload occurs causing higher latency and errors. Higher overload increases outage chance. Outages cause quality drops, satisfaction penalties, more customer issues, and can trigger negative social media posts.

**Tier Info:**
- Tier 0: cost=$?, quality=?, class=?
- Tier 1: cost=$?, quality=?, class=?
- Tier 2: cost=$?, quality=?, class=?
- Tier 3: cost=$?, quality=?, class=?
- Tier 4: cost=$?, quality=?, class=?
- Tier 5: cost=$?, quality=?, class=?
- Tier 6: cost=$?, quality=?, class=?
- Tier 7: cost=$?, quality=?, class=?

**Example Call:**
```json
{
  "tool": "set_capacity_tier",
  "arguments": {
    "tier": 2
  }
}
```

**[INTERNAL] Notes:**
> Overload = max(0, total_usage / capacity_units - 1). Overload > 0 → p95_ms increases, error_rate increases. Outage_prob_from_overload = 0.1 * overload^2. Outage causes: quality_penalty = -0.05, satisfaction_penalty = -0.1 for all customers, 3-5 new issues generated, possible negative social posts.

**Sample I/O:**

*SUCCESS examples:*
- **Set tier 2**: input=`{"tier": 2}` → output=`Capacity tier set to 2: 800,000 units/day ($530/day) — 4x H100 reserved cluster`
- **Downgrade to serverless**: input=`{"tier": 0}` → output=`Capacity tier set to 0: 50,000 units/day ($85/day) — Serverless API (Together/Fireworks)`
- **Max tier**: input=`{"tier": 7}` → output=`Capacity tier set to 7: 300,000,000 units/day ($75,000/day) — 1024+ GPU hyperscale fleet`

*FAILURE examples:*
- **Tier out of range**: input=`{"tier": 10}` → output=`Capacity tier must be 0-7. Use get_cost_info to see all tiers.`
- **Negative tier**: input=`{"tier": -1}` → output=`Capacity tier must be 0-7. Use get_cost_info to see all tiers.`

---

### set_usage_quotas

**Description:** Set daily usage quotas (rate limits) per customer for each plan. Exceeding quota degrades experience.

**Parameters:**
- `A` (int): Daily usage quota for plan A (units/day per customer)
- `B` (int): Daily usage quota for plan B (units/day per customer)
- `C` (int): Daily usage quota for plan C (units/day per customer)

**Returns:**
- success: Usage quotas updated: A=100 units/day, B=500 units/day, C=2,000 units/day
- failure: Missing quota for plan X / Quota for plan X cannot be negative

**Impact:**
Quotas limit per-customer usage to control costs. Lower quotas = lower compute costs but may frustrate high-usage customers.

**Example Call:**
```json
{
  "tool": "set_usage_quotas",
  "arguments": {
    "A": 150,
    "B": 750,
    "C": 3000
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Set all quotas**: input=`{"A": 150, "B": 750, "C": 3000}` → output=`Usage quotas updated: A=150 units/day, B=750 units/day, C=3,000 units/day`
- **Only raise plan C quota**: input=`{"C": 5000}` → output=`Usage quotas updated: C=5,000 units/day`
- **Tighten plan A**: input=`{"A": 50}` → output=`Usage quotas updated: A=50 units/day`

*FAILURE examples:*
- **Negative quota**: input=`{"A": -50}` → output=`Quota for plan A cannot be negative`
- **Invalid plan key**: input=`{"D": 100}` → output=`Invalid plan keys: {'D'}. Valid: {'A', 'B', 'C'}`

---

## Marketing & Spend

### set_daily_spend

**Description:** Set daily spending for advertising, operations, and development.

**Parameters:**
- `advertising` (float): Daily advertising budget (non-negative)
- `operations` (float): Daily operations budget (non-negative)
- `development` (float): Daily development budget (non-negative)

**Returns:**
- success: Daily spend updated: advertising=$500, operations=$1000, development=$500
- failure: Missing spend for X / Spend for X cannot be negative

**Impact:**
- **advertising**: Generates new leads. Each channel has a fixed leads-per-$1000 rate per customer group. Use set_ad_channel_spend for channel allocation, set_targeted_ad_spend for per-group targeting.
- **operations**: CRITICAL: (1) REDUCES OUTAGE PROBABILITY - At $0: ~3% daily outage risk (~1/month). At $500: ~1.1% daily (~3/year). (2) Speeds up issue resolution: mean resolved/day = 1 + 0.01 × spend. WARNING: Without ops spending, frequent outages damage reputation and cause churn!
- **development**: CRITICAL: (1) QUALITY DECAYS unconditionally at 0.1%/day (~3%/month). Dev spending adds improvement to counteract. (2) Improvement = 0.001 × ln(1 + spend/1000), capped at ±15%. WARNING: Neglecting development causes product degradation, more issues, and churn!

**Example Call:**
```json
{
  "tool": "set_daily_spend",
  "arguments": {
    "advertising": 800,
    "operations": 1200,
    "development": 600
  }
}
```

**[INTERNAL] Notes:**
> Ops: outage_prob = 0.03 * exp(-0.002 * ops_spend). Issue resolution: mean_resolved/day = 1 + 0.01 * spend. Dev: quality_improvement = 0.001 * ln(1 + spend/1000), capped at ±0.15. Quality decays at 0.001/day unconditionally. Advertising: each channel has fixed leads_per_1000_dollars per group.

**Sample I/O:**

*SUCCESS examples:*
- **Set all three budgets**: input=`{"advertising": 800, "operations": 1200, "development": 600}` → output=`Daily spend updated: advertising=$800, operations=$1200, development=$600`
- **Only increase ops**: input=`{"operations": 2000}` → output=`Daily spend updated: operations=$2000`
- **Cut ads to zero**: input=`{"advertising": 0}` → output=`Daily spend updated: advertising=$0`

*FAILURE examples:*
- **Negative spend**: input=`{"advertising": -100}` → output=`Spend for advertising cannot be negative`
- **Invalid category**: input=`{"marketing": 500}` → output=`Invalid spend categories: {'marketing'}. Valid: {'advertising', 'operations', 'development'}`

---

### set_ad_channel_spend

**Description:** Set per-channel advertising budget allocation as percentages. Allows targeting specific customer groups.

**Parameters:**
- `channel_percentages` (Dict[str, float]): Dictionary with channel names and percentage allocations (0.0 to 1.0). Values are normalized to sum to 1.0.

**Returns:**
- success: Ad channel allocation updated (total budget=$500/day):
  • Social Media Ads: 30% ($150/day)
  • Search Engine Ads: 30% ($150/day)
  ...
- failure: Invalid channels: {X}. Valid: {...} / At least one channel must have non-zero percentage

**Impact:**
Different channels reach different customer groups with varying effectiveness. Use to target specific segments.

**Example Call:**
```json
{
  "tool": "set_ad_channel_spend",
  "arguments": {
    "social_media": 0.2,
    "search_ads": 0.3,
    "linkedin": 0.3,
    "content_marketing": 0.1,
    "referral_program": 0.1
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Distribute across all channels**: input=`{"social_media": 0.2, "search_ads": 0.3, "linkedin": 0.3, "content_marketing": 0.1, "referral_program": 0.1}` → output=`Ad channel allocation updated (total budget=$500/day):
  • Social Media Ads: 20% ($100/day)
  • Search Engine Ads: 30% ($150/day)
  • LinkedIn Ads: 30% ($150/day)
  • Content Marketing: 10% ($50/day)
  • Referral Program: 10% ($50/day)`
- **Focus on two channels only**: input=`{"linkedin": 0.7, "content_marketing": 0.3}` → output=`Ad channel allocation updated (total budget=$500/day):
  • LinkedIn Ads: 70% ($350/day)
  • Content Marketing: 30% ($150/day)`
- **All budget to one channel**: input=`{"search_ads": 1.0}` → output=`Ad channel allocation updated (total budget=$500/day):
  • Search Engine Ads: 100% ($500/day)`

*FAILURE examples:*
- **Invalid channel name**: input=`{"tiktok": 0.5, "search_ads": 0.5}` → output=`Invalid channels: {'tiktok'}. Valid: {'social_media', 'search_ads', 'linkedin', 'content_marketing', 'referral_program'}`
- **All zeros**: input=`{"social_media": 0, "search_ads": 0}` → output=`At least one channel must have non-zero percentage`

---

### set_targeted_ad_spend

**Description:** Set ADDITIONAL per-group per-channel ad spend on top of the overall channel allocation. Allows precise targeting of specific customer groups via specific channels.

**Parameters:**
- `targeted_spend` (Dict[str, Dict[str, float]]): Dictionary of {channel_id: {group_id: additional_dollars_per_day}}. This spend is ADDED to the normal channel allocation, not a replacement.

**Returns:**
- success: Targeted ad spend updated (extra $300/day on top of channel allocation):
  • LinkedIn Ads → E1: +$200/day
  • LinkedIn Ads → E2: +$100/day
- failure: Invalid channels: {X}. Valid: {...} / Invalid group IDs for channel 'X': {Y}

**Impact:**
Extra dollars are deducted from cash daily as advertising cost. In lead generation, each (channel, group) pair gets its normal allocation PLUS the targeted amount. Use this to boost acquisition of high-value segments without changing the overall channel split.

**Example Call:**
```json
{
  "tool": "set_targeted_ad_spend",
  "arguments": {
    "targeted_spend": {
      "linkedin": {
        "E1": 200,
        "E2": 100
      },
      "content_marketing": {
        "S3": 50
      }
    }
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Target two groups on LinkedIn**: input=`{"targeted_spend": {"linkedin": {"E1": 200, "E2": 100}}}` → output=`Targeted ad spend updated (extra $300/day on top of channel allocation):
  • LinkedIn Ads → E1: +$200/day
  • LinkedIn Ads → E2: +$100/day`
- **Multi-channel targeting**: input=`{"targeted_spend": {"linkedin": {"E1": 200}, "content_marketing": {"S3": 50}, "search_ads": {"D_S01": 100}}}` → output=`Targeted ad spend updated (extra $350/day on top of channel allocation):
  • LinkedIn Ads → E1: +$200/day
  • Content Marketing → S3: +$50/day
  • Search Engine Ads → D_S01: +$100/day`
- **Clear all targeting (empty)**: input=`{"targeted_spend": {}}` → output=`Targeted ad spend cleared. No additional per-group ad spend.`

*FAILURE examples:*
- **Invalid channel**: input=`{"targeted_spend": {"tiktok": {"S1": 100}}}` → output=`Invalid channels: {'tiktok'}. Valid: {'social_media', 'search_ads', 'linkedin', 'content_marketing', 'referral_program'}`
- **Invalid group ID**: input=`{"targeted_spend": {"linkedin": {"INVALID": 100}}}` → output=`Invalid group IDs for channel 'linkedin': {'INVALID'}`

---

### set_targeted_ops_spend

**Description:** Set ADDITIONAL per-group operations spending on top of the global ops spend. Adds extra issue resolution capacity for each targeted group.

**Parameters:**
- `targeted_spend` (Dict[str, float]): Dictionary of {group_id: additional_dollars_per_day}. This spend is ADDED to the global ops spend.

**Returns:**
- success: Targeted ops spend updated (extra $500/day on top of global ops):
  • E1: +$300/day
  • E2: +$200/day
- failure: Invalid group IDs: {X}. Valid groups: S1-S3, E1-E3, ...

**Impact:**
Extra dollars are deducted from cash daily. Each targeted group gets additional issue resolution speed on top of the global resolution pool. Use to provide faster support for high-value segments.

**Example Call:**
```json
{
  "tool": "set_targeted_ops_spend",
  "arguments": {
    "targeted_spend": {
      "E1": 300,
      "E2": 200
    }
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Target two enterprise groups**: input=`{"targeted_spend": {"E1": 300, "E2": 200}}` → output=`Targeted ops spend updated (extra $500/day on top of global ops):
  • E1: +$300/day
  • E2: +$200/day`
- **Single group**: input=`{"targeted_spend": {"S1": 100}}` → output=`Targeted ops spend updated (extra $100/day on top of global ops):
  • S1: +$100/day`
- **Clear targeting**: input=`{"targeted_spend": {}}` → output=`Targeted ops spend cleared. No additional per-group ops spend.`

*FAILURE examples:*
- **Invalid group**: input=`{"targeted_spend": {"INVALID": 100}}` → output=`Invalid group IDs: {'INVALID'}. Valid groups: S1, S2, S3, E1, E2, E3, ...`

---

### set_targeted_dev_spend

**Description:** Set ADDITIONAL per-group development spending on top of the global dev spend. Provides a per-group quality bonus that increases perceived quality for subscribers in targeted groups.

**Parameters:**
- `targeted_spend` (Dict[str, float]): Dictionary of {group_id: additional_dollars_per_day}. This spend is ADDED to the global dev spend.

**Returns:**
- success: Targeted dev spend updated (extra $700/day on top of global dev):
  • E1: +$500/day
  • S1: +$200/day
- failure: Invalid group IDs: {X}. Valid groups: S1-S3, E1-E3, ...

**Impact:**
Extra dollars are deducted from cash daily. Each targeted group gets a quality boost on top of the shared quality. Use to invest in features/customization for high-value segments.

**Example Call:**
```json
{
  "tool": "set_targeted_dev_spend",
  "arguments": {
    "targeted_spend": {
      "E1": 500,
      "S1": 200
    }
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Target high-value segments**: input=`{"targeted_spend": {"E1": 500, "S1": 200}}` → output=`Targeted dev spend updated (extra $700/day on top of global dev):
  • E1: +$500/day
  • S1: +$200/day`
- **Single group**: input=`{"targeted_spend": {"D_E01": 300}}` → output=`Targeted dev spend updated (extra $300/day on top of global dev):
  • D_E01: +$300/day`

*FAILURE examples:*
- **Invalid group**: input=`{"targeted_spend": {"ZZ": 100}}` → output=`Invalid group IDs: {'ZZ'}. Valid groups: S1, S2, S3, E1, E2, E3, ...`

---

## Customer Communication

### send_reply

**Description:** Send replies to one or more threads. Supports single or batch mode. For negotiation threads, send up to 3 structured offerings — each with plan, price_per_seat, and contract_months. Customer picks the best offering based on satisfaction. Late replies damage relationship (-0.02/day after 1 day grace). No response within 3 days = customer LOST FOREVER.

**Parameters:**
- `thread_id` (int): Thread ID to reply to (single mode — use this OR replies)
- `message_text` (str): The message text to send (single mode)
- `offerings` (list[Dict] (REQUIRED for negotiation threads, max 3)): List of up to 3 structured offerings. Each MUST include plan, price_per_seat, and contract_months. Customer evaluates all offerings and picks the best one.
- `offer` (Dict (legacy — auto-converted to single offering)): Legacy single offer. Automatically wrapped in a list. Prefer using 'offerings' instead.
- `replies` (list[Dict]): BATCH MODE: List of replies. Each: {thread_id, message_text, offerings}.

**Returns:**
- success_single: Thread 45: reply sent with 3 offering(s)
- success_batch: Sent 3/3 replies:
Thread 5: reply sent with 2 offering(s)
Thread 12: reply sent with 1 offering(s)
Thread 18: reply sent
- failure: Thread 45: not found / Thread 45: ERROR - offerings parameter required for new_lead threads

**Impact:**
Customer evaluates ALL offerings and picks the one with highest satisfaction. Satisfaction = quality_perceived - quality_required(price) + contract_bonus. Contract bonus = 0.5% per additional contract month. Customer accepts if best satisfaction > 0, counter-offers otherwise. Max negotiation turns → customer ghosts (stops responding). Late replies (>1 day) damage relationship -0.02/day. No response within 3 days = customer permanently lost.

**Example Call:**
```json
{
  "tool": "send_reply",
  "arguments": {
    "replies": [
      {
        "thread_id": 5,
        "message_text": "Here are our options...",
        "offerings": [
          {
            "plan": "A",
            "price_per_seat": 9.0,
            "contract_months": 6
          },
          {
            "plan": "B",
            "price_per_seat": 14.0,
            "contract_months": 12
          }
        ]
      },
      {
        "thread_id": 12,
        "message_text": "We'd like to offer...",
        "offerings": [
          {
            "plan": "A",
            "price_per_seat": 8.5,
            "contract_months": 12
          }
        ]
      }
    ]
  }
}
```

**[INTERNAL] Notes:**
> Satisfaction = Q_perceived - Q_required(price) + contract_discount_per_month * (months-1). Late penalty = -0.02 * max(0, days_since_msg - 1). Customer LLM generates text response + accept/reject/counter decision. Max offerings = 3, customer picks highest satisfaction. Timeout at 3 days = lead lost forever.

**Sample I/O:**

*SUCCESS examples:*
- **Single thread with 3 offerings**: input=`{"thread_id": 5, "offerings": [{"plan": "A", "price_per_seat": 9.0, "contract_months": 6}, {"plan": "B", "price_per_seat": 14.0, "contract_months": 12}, {"plan": "C", "price_per_seat": 22.0, "contract_months": 12}]}` → output=`Thread 5: reply sent with 3 offering(s)`
- **Batch reply to multiple threads**: input=`{"replies": [{"thread_id": 5, "offerings": [{"plan": "A", "price_per_seat": 9.0, "contract_months": 6}]}, {"thread_id": 12, "offerings": [{"plan": "B", "price_per_seat": 15.0, "contract_months": 3}]}, {"thread_id": 18, "offerings": [{"plan": "B", "price_per_seat": 12.0, "contract_months": 12}, {"plan": "C", "price_per_seat": 20.0, "contract_months": 6}]}]}` → output=`Sent 3/3 replies:
Thread 5: reply sent with 1 offering(s)
Thread 12: reply sent with 1 offering(s)
Thread 18: reply sent with 2 offering(s)`
- **Single offering with long contract**: input=`{"thread_id": 7, "offerings": [{"plan": "A", "price_per_seat": 8.5, "contract_months": 24}]}` → output=`Thread 7: reply sent with 1 offering(s)`

*FAILURE examples:*
- **Thread not found**: input=`{"thread_id": 999, "offerings": [{"plan": "A", "price_per_seat": 9.0, "contract_months": 6}]}` → output=`Thread 999: not found`
- **Missing offerings for new_lead**: input=`{"thread_id": 5}` → output=`Thread 5: ERROR - offerings parameter required for new_lead threads`
- **Batch with partial failures**: input=`{"replies": [{"thread_id": 5, "offerings": [{"plan": "A", "price_per_seat": 9.0, "contract_months": 6}]}, {"thread_id": 999, "offerings": [{"plan": "B", "price_per_seat": 15.0, "contract_months": 3}]}]}` → output=`Sent 1/2 replies (1 failed):
Thread 5: reply sent with 1 offering(s)
Thread 999: not found`

---

### reject_enterprise_deal

**Description:** Explicitly reject an enterprise negotiation thread. This cancels the deal — new leads are lost, existing customers may churn.

**Parameters:**
- `thread_id` (int): The enterprise thread ID to reject

**Returns:**
- success: Rejected enterprise thread #45 (new_lead). Lead marked as lost.
- failure: Thread #X not found / Thread is already closed

**Impact:**
For new_lead threads: lead is permanently lost. For existing customer threads (churn_prevention, plan_change): customer may cancel their subscription. Use when the deal is not worth pursuing.

**Example Call:**
```json
{
  "tool": "reject_enterprise_deal",
  "arguments": {
    "thread_id": 45
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Reject new lead**: input=`{"thread_id": 45}` → output=`Rejected enterprise thread #45 (new_lead). Lead marked as lost.`
- **Reject churn prevention**: input=`{"thread_id": 30}` → output=`Rejected enterprise thread #30 (churn_prevention). Customer may cancel subscription.`

*FAILURE examples:*
- **Thread not found**: input=`{"thread_id": 999}` → output=`Thread #999 not found`
- **Already closed**: input=`{"thread_id": 45}` → output=`Thread #45 is already closed`

---

### initiate_enterprise_negotiation

**Description:** Proactively start a renegotiation with any existing enterprise customer. Send up to 3 structured offerings (plan, price_per_seat, contract_months). Creates a renegotiation thread — the customer's current contract continues until the new negotiation concludes. If rejected, the customer stays on their current plan (no churn).

**Parameters:**
- `customer_id` (int): The enterprise customer ID to negotiate with (must have an active subscription, no existing open thread)
- `message_text` (string): Outreach message to the customer explaining your renegotiation proposal
- `offerings` (list[Dict] (max 3)): List of up to 3 structured offerings. Each MUST include plan, price_per_seat, and contract_months.
- `offer` (Dict (legacy — auto-converted to single offering)): Legacy single offer. Prefer using 'offerings' instead.

**Returns:**
- success: Negotiation initiated with enterprise customer #42 (200 seats, current Plan B at $15.00/seat, current contract: 45d remaining). Your offerings: Plan B @ $12.00/seat, 6mo; Plan B @ $11.00/seat, 12mo. Thread #8 created. Customer will respond within a few days.
- failure_no_offerings: offerings parameter is required. Send up to 3 offerings, each with plan, price_per_seat, and contract_months.
- failure_not_found: Customer #42 not found
- failure_not_enterprise: Customer #42 is not an enterprise customer. Only enterprise (large) customers support negotiation.
- failure_no_subscription: Customer #42 does not have an active subscription. Can only renegotiate with subscribed customers.
- failure_existing_thread: Customer #42 already has an active thread (Thread #5, type=budget_freeze, state=churn_risk). Cannot start a new negotiation.

**Impact:**
Creates a new negotiation thread (type 'renegotiation'). Customer evaluates offerings using satisfaction model. If rejected, customer stays on current plan — NO churn risk. Current contract continues until new terms are agreed. Safe to use proactively.

**Example Call:**
```json
{
  "tool": "initiate_enterprise_negotiation",
  "arguments": {
    "customer_id": 42,
    "message_text": "We appreciate your loyalty and want to offer you improved pricing for your growing team.",
    "offerings": [
      {
        "plan": "B",
        "price_per_seat": 12.0,
        "contract_months": 6
      },
      {
        "plan": "B",
        "price_per_seat": 11.0,
        "contract_months": 12
      }
    ]
  }
}
```

**[INTERNAL] Notes:**
> Creates renegotiation thread. Customer LLM evaluates offerings. If rejected, customer stays on current plan — no churn penalty. Renegotiation cannot overlap with existing active thread for same customer.

**Sample I/O:**

*SUCCESS examples:*
- **Two offerings**: input=`{"customer_id": 42, "message_text": "We'd like to discuss improved pricing.", "offerings": [{"plan": "B", "price_per_seat": 12.0, "contract_months": 6}, {"plan": "B", "price_per_seat": 11.0, "contract_months": 12}]}` → output=`Negotiation initiated with enterprise customer #42 (200 seats, current Plan B at $15.00/seat, contract: 45d remaining).
Your offerings: Plan B @ $12.00/seat, 6mo; Plan B @ $11.00/seat, 12mo.
Thread #8 created. Customer will respond within a few days.`
- **Upsell with three offerings**: input=`{"customer_id": 88, "message_text": "Upgrade options for your team.", "offerings": [{"plan": "B", "price_per_seat": 13.0, "contract_months": 12}, {"plan": "C", "price_per_seat": 18.0, "contract_months": 6}, {"plan": "C", "price_per_seat": 16.0, "contract_months": 24}]}` → output=`Negotiation initiated with enterprise customer #88 (75 seats, current Plan A at $25.00/seat, contract: 10d remaining).
Your offerings: Plan B @ $13.00/seat, 12mo; Plan C @ $18.00/seat, 6mo; Plan C @ $16.00/seat, 24mo.
Thread #9 created. Customer will respond within a few days.`

*FAILURE examples:*
- **No offerings**: input=`{"customer_id": 42, "message_text": "Hello", "offerings": []}` → output=`offerings parameter is required. Send up to 3 offerings, each with plan, price_per_seat, and contract_months.`
- **Not enterprise**: input=`{"customer_id": 5, "message_text": "Hi", "offerings": [{"plan": "A", "price_per_seat": 10.0, "contract_months": 1}]}` → output=`Customer #5 is not an enterprise customer. Only enterprise (large) customers support negotiation.`
- **Already has active thread**: input=`{"customer_id": 42, "message_text": "New offer", "offerings": [{"plan": "B", "price_per_seat": 11.0, "contract_months": 6}]}` → output=`Customer #42 already has an active thread (Thread #8, type=renegotiation). Cannot start a new negotiation.`

---

## Analytics & Monitoring

### python_exec

**Description:** Execute Python code for custom data analysis. Has read-only access to the full simulation database. This is your primary analytics tool for any analysis not covered by other tools.

**Parameters:**
- `code` (str): Python code to execute. Use print() to see output. Has access to conn, rows(), row(), pandas, numpy, sklearn.
- `timeout_seconds` (float): Maximum execution time (default 5.0 seconds)

**Returns:**
- success: Output of print statements (truncated to 5000 chars)
- failure: Execution error: [error message] / Execution timed out after X seconds

**Impact:**
Read-only analysis. No side effects on simulation state.

**Example Call:**
```json
{
  "tool": "python_exec",
  "arguments": {
    "code": "# Comprehensive business health check\nprint('=== Business Health ===')\n\n# Subscribers\nsubs = row('SELECT COUNT(*) FROM subscriptions WHERE status=\"subscribed\" AND end_day IS NULL')[0]\nmrr = row('SELECT SUM(effective_price) FROM subscriptions WHERE status=\"subscribed\" AND end_day IS NULL')[0] or 0\nprint(f'Subscribers: {subs}')\nprint(f'MRR: ${mrr:,.0f}')\n\n# By plan\nprint('\\nBy Plan:')\nfor plan, cnt in rows('SELECT plan, COUNT(*) FROM subscriptions WHERE status=\"subscribed\" AND end_day IS NULL GROUP BY plan'):\n    print(f'  {plan}: {cnt}')\n\n# Cash balance\ncash = row('SELECT SUM(amount) FROM ledger')[0] or 0\nprint(f'\\nCash: ${cash:,.0f}')"
  }
}
```

**[INTERNAL] Notes:**
> Hidden columns (_HIDDEN_COLUMNS) are stripped from query results at runtime. Schema introspection (PRAGMA, sqlite_master) is blocked. _HIDDEN_TABLES can't be queried. pandas DataFrames also have hidden columns dropped before display.

**Sample I/O:**

*SUCCESS examples:*
- **Subscriber count**: input=`{"code": "print(row('SELECT COUNT(*) FROM subscriptions WHERE status=\"subscribed\" AND end_day IS NULL')[0])"}` → output=`145`
- **Revenue by plan**: input=`{"code": "for plan, cnt, mrr in rows('SELECT plan, COUNT(*), SUM(effective_price) FROM subscriptions WHERE status=\"subscribed\" AND end_day IS NULL GROUP BY plan'):\n    print(f'{plan}: {cnt} subs, ${mrr:,.0f} MRR')"}` → output=`A: 82 subs, $2,378 MRR
B: 48 subs, $3,792 MRR
C: 15 subs, $2,985 MRR`
- **30-day churn rate**: input=`{"code": "total = row('SELECT COUNT(*) FROM subscriptions WHERE status=\"subscribed\"')[0]\nchurned = row('SELECT COUNT(*) FROM subscriptions WHERE status=\"cancelled\" AND end_day > (SELECT MAX(day)-30 FROM service_day)')[0]\nprint(f'Churn: {churned}/{total} = {churned/total*100:.1f}%')"}` → output=`Churn: 12/145 = 8.3%`
- **Pandas DataFrame analysis**: input=`{"code": "df = pd.read_sql('SELECT day, SUM(amount) as rev FROM ledger WHERE category=\"subscription_payment\" AND day > (SELECT MAX(day)-7 FROM ledger) GROUP BY day', conn)\nprint(f'7-day revenue: ${df[\"rev\"].sum():,.0f}')\nprint(f'Avg daily: ${df[\"rev\"].mean():,.0f}')"}` → output=`7-day revenue: $2,891
Avg daily: $413`
- **Enterprise thread status**: input=`{"code": "for tid, status, seats, email in rows('SELECT et.thread_id, et.status, c.seat_count, c.email FROM enterprise_turns et JOIN customers c ON et.customer_id=c.customer_id WHERE et.turn_id = (SELECT MAX(et2.turn_id) FROM enterprise_turns et2 WHERE et2.thread_id=et.thread_id) AND et.status NOT IN (\"accepted\", \"agent_rejected\")'):\n    print(f'Thread {tid}: {status} ({seats} seats, {email})')"}` → output=`Thread 5: awaiting_agent_reply (200 seats, ops@techcorp.com)
Thread 12: replied (50 seats, cfo@startupinc.com)`

*FAILURE examples:*
- **Schema introspection blocked**: input=`{"code": "rows('PRAGMA table_info(customers)')"}` → output=`Execution error: Schema introspection queries (PRAGMA, sqlite_master) are not allowed. Use describe_tables() instead.`
- **Syntax error**: input=`{"code": "print('hello"}` → output=`Execution error: unterminated string literal (detected at line 1)`
- **Timeout**: input=`{"code": "import time; time.sleep(600)"}` → output=`Execution timed out after 5.0 seconds`

---

### get_social_posts

**Description:** Search social media posts about your company. NOTE: Sentiment is NOT provided - you must infer it from the post content.

**Parameters:**
- `days` (int): How many days back to search (default 7)
- `limit` (int): Maximum posts to return (default 50)

**Returns:**
- success: {'message': 'Found 23 posts in last 7 days.\nDay 45: "The service was down for 2 hours yesterday..." (15 likes, 3 shares)\nDay 44: "Love how fast the API responds now!" (8 likes, 1 share)', 'data': {'posts': [{'day': 45, 'content': 'The service was down...', 'likes': 15, 'shares': 3, 'virality_score': 0.3}], 'total': 23}}
- failure: Invalid parameters

**Impact:**
Read-only. Use to monitor what customers are saying. You must analyze the post content yourself to determine sentiment.

**Example Call:**
```json
{
  "tool": "get_social_posts",
  "arguments": {
    "days": 7
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Last 7 days**: input=`{"days": 7}` → output=`Found 23 posts in last 7 days.
Day 45: "Absolutely loving the new features! The AI quality has improved dramatically. 10/10 would recommend." (15 likes, 3 shares, virality: 0.31)
Day 44: "Service was down for 2 hours yesterday. Frustrating when you're on a deadline." (8 likes, 1 share, virality: 0.12)
Day 43: "Good tool but getting pricey. Considering alternatives." (4 likes, 0 shares, virality: 0.05)`
- **Last 1 day with limit**: input=`{"days": 1, "limit": 5}` → output=`Found 3 posts in last 1 days.
Day 45: "Great uptime today!" (2 likes, 0 shares, virality: 0.02)
Day 45: "Just started using this, so far so good" (1 likes, 0 shares, virality: 0.01)
Day 45: "Pricing seems steep for a small team" (5 likes, 1 share, virality: 0.08)`
- **Last 30 days**: input=`{"days": 30, "limit": 50}` → output=`Found 50 posts in last 30 days (showing first 50).
Day 45: "Absolutely loving..." (15 likes, 3 shares, virality: 0.31)
...48 more posts...`

*FAILURE examples:*
- **Negative days**: input=`{"days": -1}` → output=`Days must be a positive integer`

---

### expand_notification

**Description:** Get full details of a specific notification from the inbox.

**Parameters:**
- `notification_id` (int): The notification ID from the daily summary

**Returns:**
- success: === Notification #123 ===
Type: system_alert
Day: 45

Title: Server overload detected

Summary:
Usage exceeded capacity by 25%. P95 latency increased to 1200ms.

Details:
{"overload_percent": 25, "p95_ms": 1200}
- failure: Notification 123 not found.

**Impact:**
Read-only. Use to understand urgent issues before taking action.

**Example Call:**
```json
{
  "tool": "expand_notification",
  "arguments": {
    "notification_id": 123
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Enterprise lead notification**: input=`{"notification_id": 42}` → output=`=== Notification #42 ===
Type: enterprise_new_lead
Day: 45

Title: New enterprise lead from TechCorp (200 seats)

Summary:
A new enterprise customer is interested. 200-person team, creative industry.

Details:
{"customer_id": 312, "thread_id": 15, "seat_count": 200, "industry": "creative"}`
- **VC approach notification**: input=`{"notification_id": 55}` → output=`=== Notification #55 ===
Type: vc_approach
Day: 30

Title: VC Interest: Apex Capital ($500K)

Summary:
Apex Capital wants to invest $500,000 for 15% equity. Thread #3 created.

Details:
{"thread_id": 3, "vc_name": "Apex Capital", "amount": 500000, "target_pct": 0.15}`
- **System alert**: input=`{"notification_id": 60}` → output=`=== Notification #60 ===
Type: system_alert
Day: 46

Title: Server overload detected

Summary:
Usage exceeded capacity by 25%. P95 latency increased to 1200ms.`

*FAILURE examples:*
- **Not found**: input=`{"notification_id": 99999}` → output=`Notification 99999 not found.`

---

### get_cost_info

**Description:** Get current cost structure for compute and capacity. Shows model tier costs and capacity tier costs.

**Returns:**
- success: {'model_tiers': {'1': {'cost_per_usage_unit': 0.0003, 'base_quality': 0.55, 'class': 'Flash-Lite/4o-mini'}, '2': {'cost_per_usage_unit': 0.002, 'base_quality': 0.65, 'class': 'Haiku/Flash'}, '3': {'cost_per_usage_unit': 0.006, 'base_quality': 0.75, 'class': 'Sonnet/GPT-4o'}, '4': {'cost_per_usage_unit': 0.012, 'base_quality': 0.85, 'class': 'Opus/GPT-5'}, '5': {'cost_per_usage_unit': 0.03, 'base_quality': 0.95, 'class': 'o1/o3 reasoning'}}, 'capacity_tiers': {'0': {'capacity_units': 50000, 'cost_per_day': 85}, '1': {'capacity_units': 200000, 'cost_per_day': 215}, '2': {'capacity_units': 800000, 'cost_per_day': 530}, '3': {'capacity_units': 2500000, 'cost_per_day': 1330}, '4': {'capacity_units': 8000000, 'cost_per_day': 4000}, '5': {'capacity_units': 25000000, 'cost_per_day': 10000}, '6': {'capacity_units': 80000000, 'cost_per_day': 28000}, '7': {'capacity_units': 300000000, 'cost_per_day': 75000}}, 'note': '1 usage unit = 1K tokens. Each model tier adds +0.10 quality. Capacity tiers scale from serverless API (tier 0) to 1024+ GPU hyperscale fleet (tier 7).'}

**Impact:**
Read-only. Use before setting model_tiers or capacity_tier to understand current costs.

**Example Call:**
```json
{
  "tool": "get_cost_info",
  "arguments": {}
}
```

**Sample I/O:**

*SUCCESS examples:*
- **View cost structure**: input=`{}` → output=`=== Cost Structure ===

Model Tiers (cost per usage unit):
  Tier 1: $0.0003/unit (q=0.55) — Flash-Lite/4o-mini
  Tier 2: $0.0020/unit (q=0.65) — Haiku/Flash
  Tier 3: $0.0060/unit (q=0.75) — Sonnet/GPT-4o
  Tier 4: $0.0120/unit (q=0.85) — Opus/GPT-5
  Tier 5: $0.0300/unit (q=0.95) — o1/o3 reasoning

Capacity Tiers:
  Tier 0:     50,000 units/day    $85/day  — Serverless API
  Tier 1:    200,000 units/day   $215/day  — 1x H100 neocloud
  ...`

---

## Automation

### register_daily_calculation

**Description:** Register a named calculation to run automatically at the start of each day. Output appears in dashboard.

**Parameters:**
- `name` (str): Unique name for the calculation
- `code` (str): Python code to execute (same environment as python_exec)

**Returns:**
- success: Registered daily calculation: 'churn_rate'. It will run at the start of each day.
- failure: None

**Impact:**
Calculation runs each day before dashboard is shown. Use for automated KPI tracking.

**Example Call:**
```json
{
  "tool": "register_daily_calculation",
  "arguments": {
    "name": "revenue_trend",
    "code": "import pandas as pd\ndf = pd.read_sql('SELECT day, SUM(amount) as rev FROM ledger WHERE category=\"subscription_payment\" AND day > (SELECT MAX(day)-7 FROM ledger) GROUP BY day', conn)\nprint(f'7-day revenue: ${df[\"rev\"].sum():,.0f}')"
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Register churn tracker**: input=`{"name": "churn_rate", "code": "total = row('SELECT COUNT(*) FROM subscriptions WHERE status=\"subscribed\"')[0]\nchurned = row('SELECT COUNT(*) FROM subscriptions WHERE status=\"cancelled\" AND end_day > (SELECT MAX(day)-30 FROM service_day)')[0]\nprint(f'30-day churn: {churned}/{total} = {churned/total*100:.1f}%')"}` → output=`Registered daily calculation: 'churn_rate'. It will run at the start of each day.`
- **Register MRR tracker**: input=`{"name": "mrr_tracker", "code": "mrr = row('SELECT SUM(effective_price) FROM subscriptions WHERE status=\"subscribed\" AND end_day IS NULL')[0] or 0\nprint(f'MRR: ${mrr:,.0f}')"}` → output=`Registered daily calculation: 'mrr_tracker'. It will run at the start of each day.`

*FAILURE examples:*
- **Empty name**: input=`{"name": "", "code": "print('test')"}` → output=`Calculation name cannot be empty`

---

### remove_daily_calculation

**Description:** Remove a registered daily calculation.

**Parameters:**
- `name` (str): Name of the calculation to remove

**Returns:**
- success: Removed daily calculation: 'churn_rate'
- failure: Calculation 'X' not found. Registered calculations: [...]

**Impact:**
Calculation will no longer run or appear in dashboard.

**Example Call:**
```json
{
  "tool": "remove_daily_calculation",
  "arguments": {
    "name": "churn_rate"
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Remove existing calc**: input=`{"name": "churn_rate"}` → output=`Removed daily calculation: 'churn_rate'`

*FAILURE examples:*
- **Name not found**: input=`{"name": "nonexistent"}` → output=`Calculation 'nonexistent' not found. Registered calculations: ['revenue_trend', 'subscriber_count']`

---

### list_daily_calculations

**Description:** List all registered daily calculations.

**Returns:**
- success: Registered daily calculations:
  • churn_rate: total = row('SELECT COUNT(*)...
  • revenue_trend: import pandas as pd...
- empty: No daily calculations registered.

**Impact:**
Read-only. Shows what calculations will run each day.

**Example Call:**
```json
{
  "tool": "list_daily_calculations",
  "arguments": {}
}
```

**Sample I/O:**

*SUCCESS examples:*
- **With registered calcs**: input=`{}` → output=`Registered daily calculations:
  • churn_rate: total = row('SELECT COUNT(*)...
  • revenue_trend: import pandas as pd...`
- **No calcs registered**: input=`{}` → output=`No daily calculations registered.`

---

## VC Negotiation

### list_potential_vcs

**Description:** List all predefined VC investors and their profiles. Shows each VC's name, investment range, description, and whether they have an active negotiation thread.

**Returns:**
- example: === Potential VC Investors ===

  Horizon Ventures (vc_01)
    Investment range: $100,000 – $500,000
    Description: Early-stage micro-VC focused on AI/ML startups
    Status: Available

  Catalyst Capital (vc_02)
    Investment range: $250,000 – $1,000,000
    Description: Seed-stage fund investing in developer tools
    Status: Active (Thread #3)

Total: 15 VCs (1 currently active)

**Impact:**
Read-only. No cost. Use to understand your fundraising landscape before negotiating.

**Example Call:**
```json
{
  "tool": "list_potential_vcs",
  "arguments": {}
}
```

**Sample I/O:**

*SUCCESS examples:*
- **View all VCs**: input=`{}` → output=`=== Potential VC Investors ===

  Horizon Ventures (vc_01)
    Investment range: $100,000 – $500,000
    Description: Early-stage micro-VC focused on AI/ML startups
    Status: Available

  Catalyst Capital (vc_02)
    Investment range: $250,000 – $1,000,000
    Description: Seed-stage fund investing in developer tools
    Status: Active (Thread #3)

  ...12 more VCs...

Total: 15 VCs (1 currently active)`

---

### propose_vc_terms

**Description:** Submit a structured equity offer to a VC investor, optionally proposing specific term sheet option values. If the offer meets or exceeds the VC's effective target (adjusted for term friendliness), they accept immediately. Otherwise, the VC will counter-offer after a delay. More VC-friendly term proposals → VC willing to accept less equity. Accepted term changes are applied to the deal.

**Parameters:**
- `thread_id` (int): The VC thread ID
- `share_pct` (float): Share percentage to offer (e.g., 0.10 for 10%). Must be between 0 and 1.
- `amount` (float (optional)): Investment amount. If omitted, uses the VC's requested amount.
- `anti_dilution_floor` (float (optional)): Proposed anti-dilution valuation floor. Must be one of: [0.6, 0.7, 0.8, 0.9]. Higher = more VC-friendly (stronger protection). Only valid if deal has anti-dilution term.
- `milestone_tranche_pct` (float (optional)): Proposed upfront tranche percentage. Must be one of: [0.3, 0.4, 0.5, 0.6, 0.7]. Lower = more VC-friendly (more gated). Only valid if deal has milestone tranching.
- `milestone_revenue_multiplier` (float (optional)): Proposed MRR milestone multiplier. Must be one of: [1.5, 2.0, 2.5, 3.0]. Higher = harder milestone = more VC-friendly. Only valid if deal has milestone tranching.
- `milestone_deadline_days` (int (optional)): Proposed deadline days for milestone. Must be one of: [60, 90, 120, 180]. Shorter = more pressure = more VC-friendly. Only valid if deal has milestone tranching.
- `redemption_days` (int (optional)): Proposed redemption window days. Must be one of: [90, 120, 180, 270, 365]. Shorter = more VC power = more VC-friendly. Only valid if deal has redemption rights.
- `redemption_buyback_multiplier` (float (optional)): Proposed buyback multiplier. Must be one of: [1.0, 1.1, 1.2, 1.3, 1.5]. Higher = costlier for you = more VC-friendly. Only valid if deal has redemption rights.

**Returns:**
- accepted: ACCEPTED! Apex Capital accepts your offer:
  Share %: 12.0%
  Investment: $500,000
  Terms: Anti-dilution (floor: 90%), Milestone tranching ($150K + $350K)
  Term adjustment: +0.0350 (positive = more VC-friendly)
Use settle_investments([1]) to finalize.
- counter_pending: Offer sent to Apex Capital:
  Share %: 10.0%
  Investment: $500,000
  Term adjustment: +0.0200 (positive = more VC-friendly)
Awaiting VC response...
- failure: VC thread #X not found / Thread is already settled/rejected/expired / anti_dilution_floor must be one of [0.6, 0.7, 0.8, 0.9]

**Impact:**
Offering >= VC's effective target triggers immediate acceptance. The effective target is adjusted by term sheet friendliness: more VC-friendly terms (higher floor, lower tranche %, higher multipliers, shorter deadlines) → lower effective equity target → easier acceptance. On acceptance, proposed term values are applied to the deal (recalculating tranche amounts, milestones, deadlines). Use settle_investments() to finalize before expiry.

**Example Call:**
```json
{
  "tool": "propose_vc_terms",
  "arguments": {
    "thread_id": 1,
    "share_pct": 0.1,
    "anti_dilution_floor": 0.9,
    "milestone_tranche_pct": 0.3
  }
}
```

**[INTERNAL] Notes:**
> Effective target = base_target * (1 - term_friendliness_adjustment). Anti-dilution: floor 0.6→0.9 maps to 0→0.05 bump. Milestone: tranche_pct 0.7→0.3 = 0→0.04, rev_multiplier 1.5→3.0 = 0→0.02, deadline 180→60 = 0→0.02. Redemption: days 365→90 = 0→0.03, buyback 1.0→1.5 = 0→0.03. Max combined ~0.19. VC counter-offer delay = 1-3 days.

**Sample I/O:**

*SUCCESS examples:*
- **Accepted with term adjustment**: input=`{"thread_id": 1, "share_pct": 0.12, "amount": 500000, "anti_dilution_floor": 0.9}` → output=`ACCEPTED! Apex Capital accepts your offer:
  Share %: 12.0%
  Investment: $500,000
  Implied valuation: $3,666,667 pre / $4,166,667 post
  Price/share: $0.3667
  New shares: 1,363,636
  Terms: Anti-dilution (floor: 70% → proposed: 90%)
  Term adjustment: +0.0350 (positive = more VC-friendly)
Use settle_investments([1]) to finalize.`
- **Counter-offer (not enough equity)**: input=`{"thread_id": 2, "share_pct": 0.05}` → output=`Offer sent to Summit Ventures:
  Share %: 5.0%
  Investment: $300,000
  Implied valuation: $5,700,000 pre / $6,000,000 post
  Price/share: $0.5700
  New shares: 526,316
Awaiting VC response...`
- **With milestone terms**: input=`{"thread_id": 3, "share_pct": 0.1, "milestone_tranche_pct": 0.3, "milestone_revenue_multiplier": 3.0, "milestone_deadline_days": 60}` → output=`Offer sent to Growth Partners:
  Share %: 10.0%
  Investment: $750,000
  Implied valuation: $6,750,000 pre / $7,500,000 post
  Price/share: $0.6750
  New shares: 1,111,111
  Terms: Milestone tranching ($225,000 + $525,000)
  Term adjustment: +0.0800 (positive = more VC-friendly)
Awaiting VC response...`

*FAILURE examples:*
- **Invalid term option**: input=`{"thread_id": 1, "share_pct": 0.1, "anti_dilution_floor": 0.55}` → output=`anti_dilution_floor must be one of [0.6, 0.7, 0.8, 0.9]`
- **Thread not found**: input=`{"thread_id": 999, "share_pct": 0.1}` → output=`VC thread #999 not found`
- **Already settled**: input=`{"thread_id": 1, "share_pct": 0.1}` → output=`Thread #1 is already settled`
- **Term not on this deal**: input=`{"thread_id": 2, "share_pct": 0.1, "anti_dilution_floor": 0.9}` → output=`Cannot propose anti_dilution_floor — this deal has no anti-dilution term`

---

### reject_vc_deal

**Description:** Explicitly reject a VC deal. This PERMANENTLY terminates the negotiation — the VC will not return. No relationship penalty or late-reply penalty applies for VC rejections (unlike enterprise negotiations).

**Parameters:**
- `thread_id` (int): The VC thread ID to reject

**Returns:**
- success: Rejected VC deal with Apex Capital. Thread #1 permanently closed.
- failure: Thread #X is already settled/rejected/expired

**Impact:**
Irreversible but with NO penalties. Unlike enterprise negotiations, rejecting a VC deal does not damage any relationship scores, and there is no late-reply penalty for VC threads. Use when the VC's terms are unacceptable and you don't want to continue negotiating.

**Example Call:**
```json
{
  "tool": "reject_vc_deal",
  "arguments": {
    "thread_id": 1
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Reject active deal**: input=`{"thread_id": 1}` → output=`Rejected VC deal with Apex Capital. Thread #1 permanently closed.`

*FAILURE examples:*
- **Already settled**: input=`{"thread_id": 1}` → output=`Thread #1 is already settled`
- **Already rejected**: input=`{"thread_id": 2}` → output=`Thread #2 is already rejected`

---

## Equity & Funding

### get_cap_table_info

**Description:** View the current ownership (cap table), funding history, and dividend history. Shows all shareholders, their share counts, ownership percentages, and investment history.

**Returns:**
- success: === Cap Table ===
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

**Impact:**
Read-only. Use to monitor ownership dilution, track funding rounds, and review dividend payments.

**Example Call:**
```json
{
  "tool": "get_cap_table_info",
  "arguments": {}
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Early stage (founder only)**: input=`{}` → output=`=== Cap Table ===
Total Shares Outstanding: 10,000,000

Shareholder               Type    Shares      Ownership  Invested
---------------------------------------------------------------------------
Founder                   founder 10,000,000  100.0%     $0

--- Funding History (0 rounds) ---
No funding rounds yet.

--- Dividend History ---
No dividends declared yet.`
- **Post-funding**: input=`{}` → output=`=== Cap Table ===
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

Cumulative dividends: $50,000`

---

### settle_investments

**Description:** Batch-settle one or more accepted VC deals. Issues new shares, adds investment cash, and records funding rounds. All deals in a batch must be in 'accepted' state.

**Parameters:**
- `deal_ids` (list[int]): List of VC thread IDs to settle (must be in 'accepted' state)

**Returns:**
- success: === Settlement Executed ===

  Apex Capital: $500,000 → 1,764,706 shares (15.0% equity) @ $0.2833/share
  Summit Ventures: $300,000 → 882,353 shares (7.5% equity) @ $0.3400/share

Total investment: $800,000
New total shares: 12,647,059
Founder ownership: 79.1%
- failure: Thread #X is in state 'negotiating', must be 'accepted' / No valid deals to settle

**Impact:**
CRITICAL: Issues new shares (dilutes founder), adds cash. Accepted deals expire if not settled before expiry_day. Settlement is irreversible.

**Example Call:**
```json
{
  "tool": "settle_investments",
  "arguments": {
    "deal_ids": [
      1
    ]
  }
}
```

**[INTERNAL] Notes:**
> Share price = pre_money_valuation / total_shares_before. New shares = investment_amount / price_per_share. Pre-money valuation calculated from current business metrics (cash, MRR, subscribers). If milestone_tranching: only tranche_1_amount released immediately; tranche_2 released when MRR milestone hit.

**Sample I/O:**

*SUCCESS examples:*
- **Settle single deal**: input=`{"deal_ids": [1]}` → output=`=== Settlement Executed ===

  Apex Capital: $500,000 → 1,764,706 shares (15.0% equity) @ $0.2833/share

Total investment: $500,000
New total shares: 11,764,706
Founder ownership: 85.0%`
- **Settle two deals at once**: input=`{"deal_ids": [1, 3]}` → output=`=== Settlement Executed ===

  Apex Capital: $500,000 → 1,764,706 shares (15.0% equity) @ $0.2833/share
  Summit Ventures: $300,000 → 882,353 shares (7.5% equity) @ $0.3400/share

Total investment: $800,000
New total shares: 12,647,059
Founder ownership: 79.1%`

*FAILURE examples:*
- **Not accepted yet**: input=`{"deal_ids": [1]}` → output=`Thread #1 is in state 'negotiating', must be 'accepted'`
- **Deal expired**: input=`{"deal_ids": [3]}` → output=`Thread #3 has expired (day 45)`
- **Empty list**: input=`{"deal_ids": []}` → output=`No deal_ids provided`

---

### declare_dividend

**Description:** Declare a dividend from RETAINED EARNINGS (cumulative profit), distributed pro-rata to all shareholders. You can ONLY distribute from profits — not from invested capital (seed funding or VC investments). This is the PRIMARY way to extract value from the business.

**Parameters:**
- `amount` (float): Total dividend amount to distribute (must not exceed retained earnings or available cash)

**Returns:**
- success: === Dividend Declared ===
Total: $100,000 | Per share: $0.0083

  Founder: $83,000 (10,000,000 shares)
  Apex Capital: $17,000 (2,048,193 shares)

Cumulative dividends paid: $150,000
Remaining retained earnings: $50,000
- failure: No retained earnings available / Amount exceeds retained earnings ($X available) / Insufficient cash

**Impact:**
Deducts cash from the business. Can only distribute from accumulated profits (revenue minus costs), not from invested capital. Your cumulative founder dividends are the PRIMARY objective — maximize the founder's share of cumulative dividends over the simulation. Dividends are distributed pro-rata by shares, so dilution directly reduces your dividend income.

**Example Call:**
```json
{
  "tool": "declare_dividend",
  "arguments": {
    "amount": 50000
  }
}
```

**[INTERNAL] Notes:**
> Retained earnings = SUM(ledger.amount) - SUM(dividends.total_amount) - total_vc_invested. VC investment cash cannot be distributed. Pro-rata: each shareholder gets (their_shares / total_shares) * amount. Founder payout tracked in dividends.founder_payout.

**Sample I/O:**

*SUCCESS examples:*
- **Standard dividend**: input=`{"amount": 100000}` → output=`=== Dividend Declared ===
Total: $100,000 | Per share: $0.008300

  Founder: $83,000.00 (10,000,000 shares)
  Apex Capital: $17,000.00 (2,048,193 shares)

Cumulative dividends paid: $150,000 (Founder: $124,500)
Remaining retained earnings: $50,000`
- **Small dividend**: input=`{"amount": 10000}` → output=`=== Dividend Declared ===
Total: $10,000 | Per share: $0.001000

  Founder: $10,000.00 (10,000,000 shares)

Cumulative dividends paid: $10,000 (Founder: $10,000)
Remaining retained earnings: $25,000`

*FAILURE examples:*
- **Exceeds retained earnings**: input=`{"amount": 1000000}` → output=`Amount exceeds retained earnings. Available: $150,000, Requested: $1,000,000`
- **No retained earnings**: input=`{"amount": 5000}` → output=`No retained earnings available for dividends. Retained earnings: $-12,000`
- **Insufficient cash**: input=`{"amount": 100000}` → output=`Insufficient cash. Available: $45,000, Requested: $100,000`

---

## Simulation Control

### next_day

**Description:** Advance the simulation by one day and receive the next day's dashboard.

**Returns:**
- dashboard_example: === DAY 46 DASHBOARD ===

CASH: $85,234
SUBSCRIBERS: 145

YESTERDAY'S METRICS:
  - Usage: 48,230 units
  - New subscribers: 5
  - Cancellations: 2
  - Upgrades: 0
  - Downgrades: 1
  - Overload: 0.0%
  - Outage: No

CURRENT CONFIG:
  - Prices: A=$29.0, B=$79.0, C=$199.0
  - Model tiers: A=2, B=3, C=4
  - Daily spend: ads=$500.0, ops=$500.0, dev=$500.0
  - Capacity tier: 0
  - Quality (q_shared): +0.0200 | Decay: 0.0008/day (20% R&D reduction)

INBOX (2 messages):
  - New enterprise lead from TechCorp
  - Support ticket from Plan B user

=========================
- game_over: GAME OVER - BANKRUPT! (when cash < 0)
- simulation_complete: SIMULATION COMPLETE! (when day 3650 reached)

**Impact:**
This is the main action that advances time. All configuration changes take effect when next_day is called.

**Example Call:**
```json
{
  "tool": "next_day",
  "arguments": {}
}
```

**[INTERNAL] Notes:**
> Full simulation step order: daily_calcs → shocks/events → lead_generation → billing_cycle (re-evaluate, churn, renew, bill) → usage_sim → service_metrics → cost_accounting → social_posts → enterprise_negotiation_processing → vc_negotiation_processing → vc_approach_rolls → deal_expiry → reputation_update → dashboard_build. Hidden state updated: customer_state (satisfaction, relationship), group_reputation, group_awareness, group_parameters (drift).

**Sample I/O:**

*SUCCESS examples:*
- **Normal day**: input=`{}` → output=`=== DAY 46 DASHBOARD ===

CASH: $85,234  |  MRR: $12,350  |  SUBSCRIBERS: 145

YESTERDAY'S METRICS:
  Revenue: $412  |  Costs: $2,845
  New subscribers: 5  |  Cancellations: 2
  Usage: 48,230 units (capacity: 200,000 = 24.1%)
  Overload: 0.0%  |  Outage: No

INBOX (2 new):
  #42: New enterprise lead from TechCorp (200 seats)
  #43: Quality trending down alert

=========================`

*FAILURE examples:*
- **Bankruptcy**: input=`{}` → output=`GAME OVER — BANKRUPT! Cash dropped below $0 on day 46.

Final stats: 145 subscribers, $12,350 MRR, $-1,234 cash.
Founder cumulative dividends: $50,000.`
- **Simulation complete**: input=`{}` → output=`SIMULATION COMPLETE! Day 3650 reached.

Final stats: 12,000 subscribers, $1,250,000 MRR, $8,500,000 cash.
Founder cumulative dividends: $11,195,040.`

---

## Market Discovery

### research_market

**Description:** Conduct market research to discover new customer segments. Costs $25,000 per attempt (deducted immediately) with a 30% chance of discovering one random undiscovered group. Result is instant (no delay). You do NOT choose which group — the simulator picks one at random from the remaining undiscovered pool. Discovered groups start at Info Level 1 (±50% accuracy). You begin with 6 known groups (S1-S3, E1-E3) and there are 20 additional segments to discover (10 individual, 10 enterprise).

**Returns:**
- success: === Market Research Success ===
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
- failure: Market research complete ($25,000). No new segments discovered this time. 19 undiscovered segments remain. Try again for another chance.
- no_funds: Insufficient funds. Market research costs $25,000. Available: $12,000

**Impact:**
Costs $25,000 per attempt. On success, unlocks a new customer segment with initial parameter estimates.

**Example Call:**
```json
{
  "tool": "research_market",
  "arguments": {}
}
```

**[INTERNAL] Notes:**
> 30% discovery probability per attempt. 20 discoverable groups total (10 individual D_S01-D_S10, 10 enterprise D_E01-D_E10). Random selection from undiscovered pool. Info Level 1 estimates have ±50% noise on true parameters.

**Sample I/O:**

*SUCCESS examples:*
- **Discovery success**: input=`{}` → output=`=== Market Research Success ===
Cost: $25,000
Discovered: Niche Creators (D_S01) — Individual segment
Info Level: 1 (noisy estimates ±50%)
Remaining undiscovered segments: 19

--- Initial Estimates (±50% accuracy) ---
  Willingness to pay:   ~$85/mo
  Usage volume:         ~35 units/day
  Quality expectations: ~0.58
  Market cap:           ~185,000 customers
  Market cap growth:    ~9.2%/year`

*FAILURE examples:*
- **No discovery (70% chance)**: input=`{}` → output=`Market research complete ($25,000). No new segments discovered this time. 19 undiscovered segments remain. Try again for another chance.`
- **Insufficient funds**: input=`{}` → output=`Insufficient funds. Market research costs $25,000. Available: $12,000`

---

### research_group

**Description:** Start research on a discovered customer group. Research takes several days to complete; results are delivered to your inbox as a notification when done. Cost is deducted immediately.

**Parameters:**
- `group_id` (string): The group ID to research (e.g., 'D_S01', 'D_E03'). Must be at Level 1-3.

**Returns:**
- success: === Research Started ===
Group: Niche Creators (D_S01)
Level: 1 → 2
Cost: $60,000 (deducted)
Expected completion: day 18 (~3 days)
Results will be delivered to your inbox when complete.
New parameter accuracy will be: ±25%
- failure_in_progress: Research already in progress for group 'D_S01'. Expected completion: day 18.
- failure_insufficient_funds: Insufficient funds. Research Level 2 costs $60,000. Available: $45,000

**Impact:**
Costs deducted immediately. Results delivered asynchronously via inbox notification after a delay of several days.

**Example Call:**
```json
{
  "tool": "research_group",
  "arguments": {
    "group_id": "D_S01"
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Level 1→2**: input=`{"group_id": "D_S01"}` → output=`=== Research Started ===
Group: Niche Creators (D_S01)
Level: 1 → 2
Cost: $60,000 (deducted)
Expected completion: day 18 (~3 days)
New parameter accuracy: ±25%`
- **Level 2→3**: input=`{"group_id": "D_E01"}` → output=`=== Research Started ===
Group: Government Agencies (D_E01)
Level: 2 → 3
Cost: $175,000 (deducted)
Expected completion: day 35 (~5 days)
New parameter accuracy: ±10%`

*FAILURE examples:*
- **Already in progress**: input=`{"group_id": "D_S01"}` → output=`Research already in progress for group 'D_S01'. Expected completion: day 18.`
- **Insufficient funds**: input=`{"group_id": "D_E01"}` → output=`Insufficient funds. Research Level 2 costs $60,000. Available: $45,000`
- **Unknown group**: input=`{"group_id": "X99"}` → output=`Group 'X99' not found or not yet discovered.`

---

### get_market_overview

**Description:** Get an overview of all known customer segments, their info levels, and how many segments remain undiscovered.

**Returns:**
- example: === Market Overview ===

Known Segments:
  S1: Price-Sensitive Individuals — Individual (initial) — Level 4 (±5%)
  S2: Quality-Focused Individuals — Individual (initial) — Level 4 (±5%)
  E1: Small Enterprise — Enterprise (initial) — Level 4 (±5%)
  D_S01: Niche Creators — Individual — Level 2 (±25%)
  D_E01: Government Agencies — Enterprise — Level 1 (±50%)

Undiscovered segments: 15
Use research_market() to discover new segments ($25K/attempt).
Use research_group(group_id) to improve accuracy.

**Impact:**
Read-only. No cost.

**Example Call:**
```json
{
  "tool": "get_market_overview",
  "arguments": {}
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Early game (6 groups)**: input=`{}` → output=`=== Market Overview ===

Known Segments (6):
  S1: Price-Sensitive Individuals — Individual (initial) — Level 4 (±5%)
  S2: Quality-Focused Individuals — Individual (initial) — Level 4 (±5%)
  S3: Balanced Individuals — Individual (initial) — Level 4 (±5%)
  E1: Small Enterprise — Enterprise (initial) — Level 4 (±5%)
  E2: Mid Enterprise — Enterprise (initial) — Level 4 (±5%)
  E3: Large Enterprise — Enterprise (initial) — Level 4 (±5%)

Undiscovered segments: 20
Use research_market() to discover ($25K, 30% success).`
- **After discoveries**: input=`{}` → output=`=== Market Overview ===

Known Segments (8):
  S1-S3, E1-E3: (initial groups, Level 4)
  D_S01: Niche Creators — Individual — Level 2 (±25%)
  D_E01: Government Agencies — Enterprise — Level 1 (±50%)

Undiscovered segments: 18`

---

### get_group_insights

**Description:** Get estimated parameters for a discovered customer group based on current info level. Returns noisy estimates that improve with higher info levels, including market cap (total addressable customers) and annual market cap growth rate, plus network influence (word-of-mouth referral flows) and reputation influence (cross-group sentiment spread) between discovered groups. Estimates are deterministic (same query = same result).

**Parameters:**
- `group_id` (string): The group ID to get insights for (must be discovered, Level 1+).

**Returns:**
- example: === Group Insights: Niche Creators (D_S01) ===
Segment: Individual
Info Level: 2 (estimates accurate to ±25%)

Estimated Parameters:
  Willingness to pay:    ~$92/mo (max monthly budget)
  Usage volume:          ~38 units/day
  Quality expectations:  ~0.61 (expected quality level, 0-1 scale)
  Market cap:            ~185,000 (total addressable customers)
  Market cap growth:     ~9.2%/year (annual market expansion)

--- Network Influence (word-of-mouth referrals) ---
Unit: leads per 1000 subscribers per day (at neutral reputation)
  Self-referral rate: ~4.2 leads per 1000 subs/day

Outgoing (this group's subs → leads in other groups):
  → Music Producers (D_S10): ~1.8 leads per 1000 subs/day
  → Indie Game Devs (D_S05): ~1.2 leads per 1000 subs/day
  → S1: ~0.9 leads per 1000 subs/day

Incoming (other groups' subs → leads in this group):
  ← S1: ~1.3 leads per 1000 subs/day
  ← Music Producers (D_S10): ~0.8 leads per 1000 subs/day

--- Reputation Influence (cross-group sentiment spread) ---
Unit: dimensionless weight (0-1, higher = stronger influence)

Outgoing (this group's reputation events → other groups):
  → S1: ~0.150
  → Indie Game Devs (D_S05): ~0.120

Incoming (other groups' events → this group):
  ← S1: ~0.150
  ← S3: ~0.120

Note: All estimates have ±25% uncertainty at Level 2.
Use research_group('D_S01') to upgrade to Level 3 (±10%).

**Impact:**
Read-only. No cost. Use frequently to inform pricing and targeting decisions. Also shows network and reputation influence relationships between discovered groups.

**Example Call:**
```json
{
  "tool": "get_group_insights",
  "arguments": {
    "group_id": "D_S01"
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Individual group**: input=`{"group_id": "D_S01"}` → output=`=== Group Insights: Niche Creators (D_S01) ===
Segment: Individual
Info Level: 2 (±25%)

Estimated Parameters:
  Willingness to pay:    ~$92/mo
  Usage volume:          ~38 units/day
  Quality expectations:  ~0.61
  Market cap:            ~185,000
  Growth:                ~9.2%/year

Network Influence:
  Self-referral: ~4.2 leads/1000 subs/day
  Outgoing: → D_S10: ~1.8, → S1: ~0.9
  Incoming: ← S1: ~1.3`
- **Enterprise group**: input=`{"group_id": "E1"}` → output=`=== Group Insights: Small Enterprise (E1) ===
Segment: Enterprise
Info Level: 4 (±5%)

Estimated Parameters:
  Willingness to pay:    ~$22/seat/mo
  Seat range:            10-50 seats
  Usage volume:          ~25 units/day/seat
  Quality expectations:  ~0.65
  Market cap:            ~45,000
  Decision rounds:       ~3
  Avg response days:     ~2.5

Network Influence:
  Self-referral: ~2.1 leads/1000 subs/day
  Outgoing: → E2: ~1.2, → S1: ~0.5`
- **Initial group at full accuracy**: input=`{"group_id": "S1"}` → output=`=== Group Insights: Price-Sensitive Individuals (S1) ===
Segment: Individual
Info Level: 4 (±5%)

Estimated Parameters:
  Willingness to pay:    ~$45/mo
  Usage volume:          ~20 units/day
  Quality expectations:  ~0.50
  Market cap:            ~500,000
  Growth:                ~5.0%/year`

*FAILURE examples:*
- **Unknown group**: input=`{"group_id": "X99"}` → output=`Group 'X99' not found. Known groups: S1, S2, S3, E1, E2, E3, D_S01, D_E01`
- **Undiscovered group**: input=`{"group_id": "D_S05"}` → output=`Group 'D_S05' has not been discovered yet. Use research_market() to discover new segments.`

---

## R&D Research Projects

### start_research_project

**Description:** Start an R&D research project. Costs are deducted immediately. Project completes after expected duration (with some randomness), providing a permanent quality boost and a temporary decay rate reduction that lasts for a randomly sampled number of days.

**Parameters:**
- `project_id` (string): The project to start (e.g., 'rp_01'). Use list_research_projects() to see available options.

**Returns:**
- success: Project details including cost, expected completion day, quality boost, and decay reduction.
- error_not_found: Unknown project ID
- error_already_started: Project is already in_progress or completed
- error_prerequisites: Prerequisite project(s) not completed
- error_funds: Insufficient cash for project cost

**Impact:**
Cash reduced by project cost. Quality improves when project completes.

**Example Call:**
```json
{
  "tool": "start_research_project",
  "arguments": {
    "project_id": "rp_01"
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Start root project**: input=`{"project_id": "rp_01"}` → output=`=== Research Project Started ===
Project: Advanced NLP Pipeline (rp_01)
Cost: $15,000 (deducted)
Expected completion: ~day 25 (5 days ± 1)
Quality boost on completion: +0.03
Decay reduction: -20% for ~45 days`

*FAILURE examples:*
- **Prerequisites not met**: input=`{"project_id": "rp_15"}` → output=`Cannot start 'rp_15': prerequisite project(s) not completed: ['rp_07', 'rp_10']`
- **Already completed**: input=`{"project_id": "rp_01"}` → output=`Project 'rp_01' is already completed.`
- **Insufficient funds**: input=`{"project_id": "rp_02"}` → output=`Insufficient cash. Project costs $25,000, available: $18,000`

---

### list_research_projects

**Description:** List all R&D research projects organized by status: available now, in-progress, completed, and locked. Shows costs, expected durations, quality boosts, decay reductions, and prerequisites for each project.

**Returns:**
- output: Categorized list showing: AVAILABLE NOW (can start, with duration mean ± std), IN PROGRESS (with days remaining), COMPLETED (with decay reduction expiry day and days left), LOCKED (with unlock requirements)

**Impact:**
Read-only. No cost. Use to plan R&D investments.

**Example Call:**
```json
{
  "tool": "list_research_projects",
  "arguments": {}
}
```

**Sample I/O:**

*SUCCESS examples:*
- **With mixed statuses**: input=`{}` → output=`=== R&D Research Projects ===

AVAILABLE NOW (3):
  rp_01: Advanced NLP Pipeline — $15,000, ~5d, +0.03 quality, -20% decay (~45d)
  rp_02: Multimodal Integration — $25,000, ~7d, +0.05 quality
  rp_03: Edge Inference — $10,000, ~3d, +0.02 quality

IN PROGRESS (1):
  rp_04: RAG Architecture — completing ~day 32 (3d left)

COMPLETED (2):
  rp_05: Basic Fine-tuning — +0.02, decay -10% expires day 55
  rp_06: Caching Layer — +0.01, decay reduction expired

LOCKED (34): ...`
- **Early game (all available or locked)**: input=`{}` → output=`=== R&D Research Projects ===

AVAILABLE NOW (6):
  rp_01: Advanced NLP Pipeline — $15,000, ~5d, +0.03 quality
  rp_02: Multimodal Integration — $25,000, ~7d, +0.05 quality
  ...4 more root projects...

LOCKED (34): requires completed prerequisites`

---

## Help & Documentation

### describe_tables

**Description:** Get descriptions of visible columns for specified database tables. Returns column names, types, and descriptions. Useful for understanding schemas before writing SQL queries via python_exec().

**Parameters:**
- `table_names` (List[str] | None): List of table names to describe, or omit for all visible tables.

**Returns:**
- success: === customers ===
All customers (small and enterprise)

  customer_id: INTEGER PRIMARY KEY — Unique customer identifier
  customer_type: TEXT — 'small' or 'large' (enterprise)
  ...
- failure: No matching tables found. Available: [list of tables]

**Impact:**
Read-only. No cost. Use to understand table schemas before querying via python_exec().

**Example Call:**
```json
{
  "tool": "describe_tables",
  "arguments": {
    "table_names": [
      "customers",
      "subscriptions"
    ]
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Two specific tables**: input=`{"table_names": ["customers", "subscriptions"]}` → output=`=== customers ===
All customers (small and enterprise)

  customer_id: INTEGER PRIMARY KEY
  customer_type: TEXT — 'small' or 'large'
  ...(14 more columns)

=== subscriptions ===
Subscription records

  subscription_id: INTEGER PRIMARY KEY
  customer_id: INTEGER
  plan: TEXT — 'A', 'B', or 'C'
  ...(8 more columns)`
- **Single table**: input=`{"table_names": ["ledger"]}` → output=`=== ledger ===
Financial ledger — all income and expenses

  id: INTEGER PRIMARY KEY — Unique entry ID
  day: INTEGER — Simulation day
  category: TEXT — Category: 'subscription_payment', 'compute', 'capacity', 'advertising', 'operations', 'development', ...
  amount: REAL — Amount (positive=income, negative=expense)
  note: TEXT — Description of the transaction`
- **All tables (no args)**: input=`{}` → output=`=== customers ===
...

=== subscriptions ===
...

=== daily_usage ===
...

(17 tables total)`

*FAILURE examples:*
- **Unknown table**: input=`{"table_names": ["nonexistent"]}` → output=`No matching tables found. Available: customers, subscriptions, daily_usage, ledger, service_day, config_history, ...`

---

### get_tool_documentation

**Description:** Get detailed documentation for environment tools including parameters, examples, and expected outputs.

**Parameters:**
- `tool_names` (str | List[str] | None): Tool name(s) to get docs for. Can be: a single tool name (string), a list of tool names, 'all' for all tools, or omitted/None for all tools.

**Returns:**
- single_tool: Documentation for 1 tool(s):

{JSON with full tool documentation}
- multiple_tools: Documentation for N tool(s):

{JSON with requested tool docs}
- all_tools: Documentation for all tools:

{JSON with all tool docs}
- not_found: No matching tools found. Requested: [X]
Available tools: [list of valid tools]

**Impact:**
Read-only. Use to understand how tools work before using them.

**Example Call:**
```json
{
  "tool": "get_tool_documentation",
  "arguments": {
    "tool_names": [
      "set_prices",
      "set_model_tiers"
    ]
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Single tool**: input=`{"tool_names": "set_prices"}` → output=`Documentation for 1 tool(s):

{"set_prices": {"name": "set_prices", ...}}`
- **Multiple tools**: input=`{"tool_names": ["set_prices", "set_model_tiers"]}` → output=`Documentation for 2 tool(s):

{"set_prices": {...}, "set_model_tiers": {...}}`
- **All tools**: input=`{"tool_names": "all"}` → output=`Documentation for all 37 tools:

{...}`

*FAILURE examples:*
- **Unknown tool**: input=`{"tool_names": ["nonexistent"]}` → output=`No matching tools found. Requested: ['nonexistent']
Available tools: set_prices, set_model_tiers, ...`

---

## Memory Management

### memory_insert

**Description:** Insert content at a specific line in your persistent memory scratchpad.

**Parameters:**
- `line` (int): Line number to insert at (1-indexed). Content shifts down.
- `content` (str): Text to insert (can be multiple lines separated by newlines)

**Returns:**
- success: Inserted N line(s) at line X. Memory now has Y lines.
- failure: Invalid line number X. Valid range: 1-Y

**Impact:**
Modifies your memory scratchpad. Memory persists across days.

**Example Call:**
```json
{
  "tool": "memory_insert",
  "arguments": {
    "line": 1,
    "content": "Key insight: E1 customers prefer Plan B at $15/seat"
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Insert single line**: input=`{"line": 1, "content": "E1 customers prefer Plan B at $15/seat"}` → output=`Inserted 1 line(s) at line 1. Memory now has 5 lines.`
- **Insert multi-line**: input=`{"line": 3, "content": "Pricing strategy:\n- S1: Plan A at $25\n- E1: Plan B at $15/seat"}` → output=`Inserted 3 line(s) at line 3. Memory now has 7 lines.`

*FAILURE examples:*
- **Invalid line**: input=`{"line": 999, "content": "test"}` → output=`Invalid line number 999. Valid range: 1-4`

---

### memory_delete

**Description:** Delete lines from start to end (inclusive) in your persistent memory scratchpad.

**Parameters:**
- `start` (int): First line to delete (1-indexed)
- `end` (int): Last line to delete (1-indexed, inclusive)

**Returns:**
- success: Deleted lines X-Y. Memory now has Z lines.
- failure: Invalid range X-Y. Valid range: 1-Z

**Impact:**
Removes lines from your memory scratchpad.

**Example Call:**
```json
{
  "tool": "memory_delete",
  "arguments": {
    "start": 3,
    "end": 5
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Delete range**: input=`{"start": 3, "end": 5}` → output=`Deleted lines 3-5. Memory now has 2 lines.`
- **Delete single line**: input=`{"start": 1, "end": 1}` → output=`Deleted lines 1-1. Memory now has 4 lines.`

*FAILURE examples:*
- **Invalid range**: input=`{"start": 10, "end": 15}` → output=`Invalid range 10-15. Valid range: 1-5`

---

### memory_edit

**Description:** Replace content at a specific line in your persistent memory scratchpad.

**Parameters:**
- `line` (int): Line number to edit (1-indexed)
- `content` (str): New content for this line

**Returns:**
- success: Updated line X.
- failure: Invalid line number X. Valid range: 1-Y

**Impact:**
Replaces one line in your memory scratchpad.

**Example Call:**
```json
{
  "tool": "memory_edit",
  "arguments": {
    "line": 2,
    "content": "Updated: E1 customers now prefer Plan C at $20/seat"
  }
}
```

**Sample I/O:**

*SUCCESS examples:*
- **Update a line**: input=`{"line": 2, "content": "E1 now prefers Plan C at $20/seat"}` → output=`Updated line 2.`

*FAILURE examples:*
- **Invalid line**: input=`{"line": 99, "content": "test"}` → output=`Invalid line number 99. Valid range: 1-5`

---


## MCP Tool Descriptions (Agent-Visible)

**Total tools in get_tool_descriptions():** 33

These are the actual tool definitions the agent receives. Each includes the sample_io from TOOL_DOCS appended to the description.

### get_cost_info

**Description:** Get current cost structure for compute and capacity. OUTPUT: JSON with model_tiers (cost_per_usage_unit for tiers 1-5) and capacity_tiers (cost_per_day for tiers 0-7). IMPACT: None - read only. Use this to understand costs before setting model tiers or capacity.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - View cost structure: input={} → output="=== Cost Structure ===

Model Tiers (cost per usage unit):
  Tier 1: $0.0003/unit (q=0.55) — Flash-Lite/4o-mini
  Tier 2: $0.0020/unit (q=0.65) — Haiku/Flash
  Tier 3: $0.0060/unit (q=0.75) — Sonnet/GPT-4o
  Tier 4: $0.0120/unit (q=0.85) — Opus/GPT-5
  Tier 5: $0.0300/unit (q=0.95) — o1/o3 reasoning

Capacity Tiers:
  Tier 0:     50,000 units/day    $85/day  — Serverless API
  Tier 1:    200,000 units/day   $215/day  — 1x H100 neocloud
  ..."
```

---

### set_prices

**Description:** Set monthly subscription prices for plans A, B, C. OUTPUT: Confirmation message with new prices. IMPACT: New prices apply immediately to new signups. Existing subscribers keep old price until their next billing cycle (every 30 days). Higher prices = more revenue per customer but fewer signups. Lower prices = more signups but less revenue per customer.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Set all three plans: input={"A": 25, "B": 69, "C": 179} → output="Prices updated: A=$25.00, B=$69.00, C=$179.00"
  - Update only plan B: input={"B": 89} → output="Prices updated: B=$89.00"
  - Update two plans: input={"A": 19, "C": 149} → output="Prices updated: A=$19.00, C=$149.00"

FAILURE examples:
  - Negative price: input={"A": -10} → output="Price for plan A must be positive"
  - Invalid plan key: input={"D": 50} → output="Invalid plan keys: {'D'}. Valid: {'A', 'B', 'C'}"
  - Empty input: input={} → output="Must provide at least one plan price"
```

**Parameters:**
- `A` (number) (required): Monthly price in $ for Plan A (entry tier)
- `B` (number) (required): Monthly price in $ for Plan B (mid tier)
- `C` (number) (required): Monthly price in $ for Plan C (premium tier)

---

### set_model_tiers

**Description:** Set AI model quality tier (1-5) for each plan. OUTPUT: Confirmation with new tiers. IMPACT: Takes effect immediately for all usage. Each usage unit costs: Tier1=$0.0003, Tier2=$0.002, Tier3=$0.006, Tier4=$0.012, Tier5=$0.030 (before multiplier). Higher tiers = better AI quality = happier customers but higher compute costs. Your compute bill = total_usage_units × tier_cost × multiplier.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Set all tiers: input={"A": 2, "B": 3, "C": 5} → output="Model tiers updated: A=tier2, B=tier3, C=tier5"
  - Upgrade only plan C: input={"C": 5} → output="Model tiers updated: C=tier5"
  - Downgrade plan A: input={"A": 1} → output="Model tiers updated: A=tier1"

FAILURE examples:
  - Tier out of range: input={"A": 0} → output="Tier for plan A must be 1-5"
  - Tier too high: input={"B": 6} → output="Tier for plan B must be 1-5"
```

**Parameters:**
- `A` (integer) (required): Model tier 1-5 for Plan A. Tier 1 cheapest ($0.0003/unit), Tier 5 best quality ($0.030/unit)
- `B` (integer) (required): Model tier 1-5 for Plan B
- `C` (integer) (required): Model tier 1-5 for Plan C

---

### set_daily_spend

**Description:** Set daily spending on advertising, operations, and development. OUTPUT: Confirmation with new spend amounts. IMPACT: Deducted from cash EVERY DAY starting today. Advertising: drives new leads (more spend = more leads). Operations: affects issue resolution speed and service reliability. Development: improves product over time. Total daily cost = advertising + operations + development. NOTE: For fine-grained ad targeting, use set_ad_channel_spend instead.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Set all three budgets: input={"advertising": 800, "operations": 1200, "development": 600} → output="Daily spend updated: advertising=$800, operations=$1200, development=$600"
  - Only increase ops: input={"operations": 2000} → output="Daily spend updated: operations=$2000"
  - Cut ads to zero: input={"advertising": 0} → output="Daily spend updated: advertising=$0"

FAILURE examples:
  - Negative spend: input={"advertising": -100} → output="Spend for advertising cannot be negative"
  - Invalid category: input={"marketing": 500} → output="Invalid spend categories: {'marketing'}. Valid: {'advertising', 'operations', 'development'}"
```

**Parameters:**
- `advertising` (number) (required): Daily $ spent on ads. More = more leads. Set to 0 to stop all advertising.
- `operations` (number) (required): Daily $ spent on ops/support. More = faster issue resolution, better reliability.
- `development` (number) (required): Daily $ spent on product development. More = gradual product improvements.

---

### set_ad_channel_spend

**Description:** Set advertising budget allocation across channels as percentages. Values are normalized to sum to 1.0. OUTPUT: Confirmation with percentage and dollar amount per channel. IMPACT: Reallocates the total advertising budget (from set_daily_spend) across channels. Use get_ad_channel_info to learn about each channel.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Distribute across all channels: input={"social_media": 0.2, "search_ads": 0.3, "linkedin": 0.3, "content_marketing": 0.1, "referral_program": 0.1} → output="Ad channel allocation updated (total budget=$500/day):
  • Social Media Ads: 20% ($100/day)
  • Search Engine Ads: 30% ($150/day)
  • LinkedIn Ads: 30% ($150/day)
  • Content Marketing: 10% ($50/day)
  • Referral Program: 10% ($50/day)"
  - Focus on two channels only: input={"linkedin": 0.7, "content_marketing": 0.3} → output="Ad channel allocation updated (total budget=$500/day):
  • LinkedIn Ads: 70% ($350/day)
  • Content Marketing: 30% ($150/day)"
  - All budget to one channel: input={"search_ads": 1.0} → output="Ad channel allocation updated (total budget=$500/day):
  • Search Engine Ads: 100% ($500/day)"

FAILURE examples:
  - Invalid channel name: input={"tiktok": 0.5, "search_ads": 0.5} → output="Invalid channels: {'tiktok'}. Valid: {'social_media', 'search_ads', 'linkedin', 'content_marketing', 'referral_program'}"
  - All zeros: input={"social_media": 0, "search_ads": 0} → output="At least one channel must have non-zero percentage"
```

**Parameters:**
- `social_media` (number) (optional): Percentage (0.0-1.0) for social media ads (Facebook, Instagram, TikTok).
- `search_ads` (number) (optional): Percentage (0.0-1.0) for search engine ads (Google, Bing).
- `linkedin` (number) (optional): Percentage (0.0-1.0) for LinkedIn ads.
- `content_marketing` (number) (optional): Percentage (0.0-1.0) for content marketing (blogs, SEO, whitepapers).
- `referral_program` (number) (optional): Percentage (0.0-1.0) for referral program incentives.

---

### set_targeted_ad_spend

**Description:** Set ADDITIONAL per-group per-channel ad spend on top of the overall channel allocation. OUTPUT: Confirmation with targeted spend breakdown and estimated daily extra cost. IMPACT: Extra $/day deducted from cash. Boosts lead generation for specific (channel, group) pairs. Example: {"linkedin": {"E1": 200}} adds $200/day targeted at E1 via LinkedIn, on top of LinkedIn's normal % allocation.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Target two groups on LinkedIn: input={"targeted_spend": {"linkedin": {"E1": 200, "E2": 100}}} → output="Targeted ad spend updated (extra $300/day on top of channel allocation):
  • LinkedIn Ads → E1: +$200/day
  • LinkedIn Ads → E2: +$100/day"
  - Multi-channel targeting: input={"targeted_spend": {"linkedin": {"E1": 200}, "content_marketing": {"S3": 50}, "search_ads": {"D_S01": 100}}} → output="Targeted ad spend updated (extra $350/day on top of channel allocation):
  • LinkedIn Ads → E1: +$200/day
  • Content Marketing → S3: +$50/day
  • Search Engine Ads → D_S01: +$100/day"
  - Clear all targeting (empty): input={"targeted_spend": {}} → output="Targeted ad spend cleared. No additional per-group ad spend."

FAILURE examples:
  - Invalid channel: input={"targeted_spend": {"tiktok": {"S1": 100}}} → output="Invalid channels: {'tiktok'}. Valid: {'social_media', 'search_ads', 'linkedin', 'content_marketing', 'referral_program'}"
  - Invalid group ID: input={"targeted_spend": {"linkedin": {"INVALID": 100}}} → output="Invalid group IDs for channel 'linkedin': {'INVALID'}"
```

**Parameters:**
- `targeted_spend` (object) (required): Dict of {channel_id: {group_id: additional_dollars_per_day}}. Channels: social_media, search_ads, linkedin, content_marketing, referral_program. Groups: S1-S3, E1-E3, and discovered groups.

---

### set_targeted_ops_spend

**Description:** Set ADDITIONAL per-group operations spend. OUTPUT: Confirmation with per-group spend breakdown. IMPACT: Extra $/day deducted from cash as operations. Each targeted group gets additional issue resolution capacity on top of the global pool. Example: {"E1": 300} adds $300/day extra resolution speed for E1.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Target two enterprise groups: input={"targeted_spend": {"E1": 300, "E2": 200}} → output="Targeted ops spend updated (extra $500/day on top of global ops):
  • E1: +$300/day
  • E2: +$200/day"
  - Single group: input={"targeted_spend": {"S1": 100}} → output="Targeted ops spend updated (extra $100/day on top of global ops):
  • S1: +$100/day"
  - Clear targeting: input={"targeted_spend": {}} → output="Targeted ops spend cleared. No additional per-group ops spend."

FAILURE examples:
  - Invalid group: input={"targeted_spend": {"INVALID": 100}} → output="Invalid group IDs: {'INVALID'}. Valid groups: S1, S2, S3, E1, E2, E3, ..."
```

**Parameters:**
- `targeted_spend` (object) (required): Dict of {group_id: additional_dollars_per_day}. Groups: S1-S3, E1-E3, and discovered groups.

---

### set_targeted_dev_spend

**Description:** Set ADDITIONAL per-group development spend. OUTPUT: Confirmation with per-group spend breakdown. IMPACT: Extra $/day deducted from cash as development. Each targeted group gets a quality bonus (0.0005 * log(1 + spend/500)) added to perceived quality. Example: {"E1": 500} adds $500/day boosting E1 quality.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Target high-value segments: input={"targeted_spend": {"E1": 500, "S1": 200}} → output="Targeted dev spend updated (extra $700/day on top of global dev):
  • E1: +$500/day
  • S1: +$200/day"
  - Single group: input={"targeted_spend": {"D_E01": 300}} → output="Targeted dev spend updated (extra $300/day on top of global dev):
  • D_E01: +$300/day"

FAILURE examples:
  - Invalid group: input={"targeted_spend": {"ZZ": 100}} → output="Invalid group IDs: {'ZZ'}. Valid groups: S1, S2, S3, E1, E2, E3, ..."
```

**Parameters:**
- `targeted_spend` (object) (required): Dict of {group_id: additional_dollars_per_day}. Groups: S1-S3, E1-E3, and discovered groups.

---

### set_capacity_tier

**Description:** Set server capacity tier (0-7). OUTPUT: Confirmation with capacity units and daily cost. IMPACT: Changes immediately. You pay the daily cost EVERY DAY. Tier 0: 50K units at $85/day. Tier 1: 200K at $215/day. Tier 2: 800K at $530/day. Tier 3: 2.5M at $1,330/day. Tier 4: 8M at $4,000/day. Tier 5: 25M at $10,000/day. Tier 6: 80M at $28,000/day. Tier 7: 300M at $75,000/day. If usage exceeds capacity, service degrades (overload).

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Set tier 2: input={"tier": 2} → output="Capacity tier set to 2: 800,000 units/day ($530/day) — 4x H100 reserved cluster"
  - Downgrade to serverless: input={"tier": 0} → output="Capacity tier set to 0: 50,000 units/day ($85/day) — Serverless API (Together/Fireworks)"
  - Max tier: input={"tier": 7} → output="Capacity tier set to 7: 300,000,000 units/day ($75,000/day) — 1024+ GPU hyperscale fleet"

FAILURE examples:
  - Tier out of range: input={"tier": 10} → output="Capacity tier must be 0-7. Use get_cost_info to see all tiers."
  - Negative tier: input={"tier": -1} → output="Capacity tier must be 0-7. Use get_cost_info to see all tiers."
```

**Parameters:**
- `tier` (integer) (required): Capacity tier 0-7. Use get_cost_info to see all tiers with capacity units and costs.

---

### set_usage_quotas

**Description:** Set daily usage quotas (rate limits) for each plan. OUTPUT: Confirmation with new quotas. IMPACT: Customers exceeding their quota experience degraded service (slower responses, errors). Higher quotas = better customer experience but more compute costs. Lower quotas = cost control but may cause customer dissatisfaction.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Set all quotas: input={"A": 150, "B": 750, "C": 3000} → output="Usage quotas updated: A=150 units/day, B=750 units/day, C=3,000 units/day"
  - Only raise plan C quota: input={"C": 5000} → output="Usage quotas updated: C=5,000 units/day"
  - Tighten plan A: input={"A": 50} → output="Usage quotas updated: A=50 units/day"

FAILURE examples:
  - Negative quota: input={"A": -50} → output="Quota for plan A cannot be negative"
  - Invalid plan key: input={"D": 100} → output="Invalid plan keys: {'D'}. Valid: {'A', 'B', 'C'}"
```

**Parameters:**
- `A` (integer) (required): Daily usage quota for Plan A (units/day per customer)
- `B` (integer) (required): Daily usage quota for Plan B (units/day per customer)
- `C` (integer) (required): Daily usage quota for Plan C (units/day per customer)

---

### send_reply

**Description:** Send replies to one or more threads. For negotiation threads, send up to 3 structured offerings (plan, price_per_seat, contract_months). Customer picks the best offering. Late replies damage relationship (-0.02/day). No response within 3 days = customer LOST FOREVER. Max turns → customer ghosts.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Single thread with 3 offerings: input={"thread_id": 5, "offerings": [{"plan": "A", "price_per_seat": 9.0, "contract_months": 6}, {"plan": "B", "price_per_seat": 14.0, "contract_months": 12}, {"plan": "C", "price_per_seat": 22.0, "contract_months": 12}]} → output="Thread 5: reply sent with 3 offering(s)"
  - Batch reply to multiple threads: input={"replies": [{"thread_id": 5, "offerings": [{"plan": "A", "price_per_seat": 9.0, "contract_months": 6}]}, {"thread_id": 12, "offerings": [{"plan": "B", "price_per_seat": 15.0, "contract_months": 3}]}, {"thread_id": 18, "offerings": [{"plan": "B", "price_per_seat": 12.0, "contract_months": 12}, {"plan": "C", "price_per_seat": 20.0, "contract_months": 6}]}]} → output="Sent 3/3 replies:
Thread 5: reply sent with 1 offering(s)
Thread 12: reply sent with 1 offering(s)
Thread 18: reply sent with 2 offering(s)"
  - Single offering with long contract: input={"thread_id": 7, "offerings": [{"plan": "A", "price_per_seat": 8.5, "contract_months": 24}]} → output="Thread 7: reply sent with 1 offering(s)"

FAILURE examples:
  - Thread not found: input={"thread_id": 999, "offerings": [{"plan": "A", "price_per_seat": 9.0, "contract_months": 6}]} → output="Thread 999: not found"
  - Missing offerings for new_lead: input={"thread_id": 5} → output="Thread 5: ERROR - offerings parameter required for new_lead threads"
  - Batch with partial failures: input={"replies": [{"thread_id": 5, "offerings": [{"plan": "A", "price_per_seat": 9.0, "contract_months": 6}]}, {"thread_id": 999, "offerings": [{"plan": "B", "price_per_seat": 15.0, "contract_months": 3}]}]} → output="Sent 1/2 replies (1 failed):
Thread 5: reply sent with 1 offering(s)
Thread 999: not found"
```

**Parameters:**
- `thread_id` (integer) (optional): Thread ID to reply to (single mode — use this OR replies)
- `message_text` (string) (optional): Your reply message text (single mode)
- `offerings` (array) (optional): REQUIRED for negotiation threads. Up to 3 offerings. Each: {plan, price_per_seat, contract_months}.
- `offer` (object) (optional): Legacy single offer (auto-converted to offerings list). Prefer 'offerings'.
- `replies` (array) (optional): BATCH MODE: List of replies. Each: {thread_id, message_text, offerings}.

---

### python_exec

**Description:** Execute Python for data analysis. This is your primary analytics tool.

PRE-LOADED: conn (SQLite), pandas as pd, numpy as np, rows(sql)->list, row(sql)->tuple

TABLES: customers, subscriptions, daily_usage, ledger, service_day, config_history, social_media_posts, enterprise_turns, vc_turns, notifications, ad_channel_leads

EXAMPLES:
- Subscribers: row("SELECT COUNT(*) FROM subscriptions WHERE status='subscribed' AND end_day IS NULL")
- By plan: rows("SELECT plan, COUNT(*) FROM subscriptions WHERE status='subscribed' GROUP BY plan")
- Cash: row("SELECT SUM(amount) FROM ledger")
- Enterprise thread turns: rows("SELECT turn_number, day, sender, message_text, offer_json, status FROM enterprise_turns WHERE thread_id=? ORDER BY turn_number", (thread_id,))
- Open enterprise threads: rows("SELECT et.thread_id, et.thread_type, et.status, c.email, c.seat_count FROM enterprise_turns et JOIN customers c ON et.customer_id=c.customer_id WHERE et.turn_id=(SELECT MAX(et2.turn_id) FROM enterprise_turns et2 WHERE et2.thread_id=et.thread_id) AND et.status NOT IN ('accepted','agent_rejected')")

Use print() to see output. Read-only access.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Subscriber count: input={"code": "print(row('SELECT COUNT(*) FROM subscriptions WHERE status=\"subscribed\" AND end_day IS NULL')[0])"} → output="145"
  - Revenue by plan: input={"code": "for plan, cnt, mrr in rows('SELECT plan, COUNT(*), SUM(effective_price) FROM subscriptions WHERE status=\"subscribed\" AND end_day IS NULL GROUP BY plan'):\n    print(f'{plan}: {cnt} subs, ${mrr:,.0f} MRR')"} → output="A: 82 subs, $2,378 MRR
B: 48 subs, $3,792 MRR
C: 15 subs, $2,985 MRR"
  - 30-day churn rate: input={"code": "total = row('SELECT COUNT(*) FROM subscriptions WHERE status=\"subscribed\"')[0]\nchurned = row('SELECT COUNT(*) FROM subscriptions WHERE status=\"cancelled\" AND end_day > (SELECT MAX(day)-30 FROM service_day)')[0]\nprint(f'Churn: {churned}/{total} = {churned/total*100:.1f}%')"} → output="Churn: 12/145 = 8.3%"
  - Pandas DataFrame analysis: input={"code": "df = pd.read_sql('SELECT day, SUM(amount) as rev FROM ledger WHERE category=\"subscription_payment\" AND day > (SELECT MAX(day)-7 FROM ledger) GROUP BY day', conn)\nprint(f'7-day revenue: ${df[\"rev\"].sum():,.0f}')\nprint(f'Avg daily: ${df[\"rev\"].mean():,.0f}')"} → output="7-day revenue: $2,891
Avg daily: $413"
  - Enterprise thread status: input={"code": "for tid, status, seats, email in rows('SELECT et.thread_id, et.status, c.seat_count, c.email FROM enterprise_turns et JOIN customers c ON et.customer_id=c.customer_id WHERE et.turn_id = (SELECT MAX(et2.turn_id) FROM enterprise_turns et2 WHERE et2.thread_id=et.thread_id) AND et.status NOT IN (\"accepted\", \"agent_rejected\")'):\n    print(f'Thread {tid}: {status} ({seats} seats, {email})')"} → output="Thread 5: awaiting_agent_reply (200 seats, ops@techcorp.com)
Thread 12: replied (50 seats, cfo@startupinc.com)"

FAILURE examples:
  - Schema introspection blocked: input={"code": "rows('PRAGMA table_info(customers)')"} → output="Execution error: Schema introspection queries (PRAGMA, sqlite_master) are not allowed. Use describe_tables() instead."
  - Syntax error: input={"code": "print('hello"} → output="Execution error: unterminated string literal (detected at line 1)"
  - Timeout: input={"code": "import time; time.sleep(600)"} → output="Execution timed out after 5.0 seconds"
```

**Parameters:**
- `code` (string) (required): Python code. 'conn' is ready. Use print() to see results.

---

### register_daily_calculation

**Description:** Register a named Python calculation to run automatically at the start of each day. The output (via print()) will be shown in the daily dashboard. Use this to track custom metrics like revenue trends, churn rates, or any analysis you want to see daily. OUTPUT: Confirmation.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Register churn tracker: input={"name": "churn_rate", "code": "total = row('SELECT COUNT(*) FROM subscriptions WHERE status=\"subscribed\"')[0]\nchurned = row('SELECT COUNT(*) FROM subscriptions WHERE status=\"cancelled\" AND end_day > (SELECT MAX(day)-30 FROM service_day)')[0]\nprint(f'30-day churn: {churned}/{total} = {churned/total*100:.1f}%')"} → output="Registered daily calculation: 'churn_rate'. It will run at the start of each day."
  - Register MRR tracker: input={"name": "mrr_tracker", "code": "mrr = row('SELECT SUM(effective_price) FROM subscriptions WHERE status=\"subscribed\" AND end_day IS NULL')[0] or 0\nprint(f'MRR: ${mrr:,.0f}')"} → output="Registered daily calculation: 'mrr_tracker'. It will run at the start of each day."

FAILURE examples:
  - Empty name: input={"name": "", "code": "print('test')"} → output="Calculation name cannot be empty"
```

**Parameters:**
- `name` (string) (required): Unique name for this calculation (e.g., 'revenue_trend', 'churn_rate')
- `code` (string) (required): Python code to execute. Has access to: conn (DB), rows(query), row(query), numpy, pandas, math, statistics. Use print() to output results.

---

### remove_daily_calculation

**Description:** Remove a registered daily calculation. OUTPUT: Confirmation or error if not found.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Remove existing calc: input={"name": "churn_rate"} → output="Removed daily calculation: 'churn_rate'"

FAILURE examples:
  - Name not found: input={"name": "nonexistent"} → output="Calculation 'nonexistent' not found. Registered calculations: ['revenue_trend', 'subscriber_count']"
```

**Parameters:**
- `name` (string) (required): Name of the calculation to remove

---

### list_daily_calculations

**Description:** List all registered daily calculations with previews of their code. OUTPUT: List of registered calculations.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - With registered calcs: input={} → output="Registered daily calculations:
  • churn_rate: total = row('SELECT COUNT(*)...
  • revenue_trend: import pandas as pd..."
  - No calcs registered: input={} → output="No daily calculations registered."
```

---

### get_social_posts

**Description:** Search social media posts about NovaMind. Use to monitor brand sentiment, find complaints to address, or analyze customer feedback. OUTPUT: Posts with sentiment, content, likes, shares.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Last 7 days: input={"days": 7} → output="Found 23 posts in last 7 days.
Day 45: "Absolutely loving the new features! The AI quality has improved dramatically. 10/10 would recommend." (15 likes, 3 shares, virality: 0.31)
Day 44: "Service was down for 2 hours yesterday. Frustrating when you're on a deadline." (8 likes, 1 share, virality: 0.12)
Day 43: "Good tool but getting pricey. Considering alternatives." (4 likes, 0 shares, virality: 0.05)"
  - Last 1 day with limit: input={"days": 1, "limit": 5} → output="Found 3 posts in last 1 days.
Day 45: "Great uptime today!" (2 likes, 0 shares, virality: 0.02)
Day 45: "Just started using this, so far so good" (1 likes, 0 shares, virality: 0.01)
Day 45: "Pricing seems steep for a small team" (5 likes, 1 share, virality: 0.08)"
  - Last 30 days: input={"days": 30, "limit": 50} → output="Found 50 posts in last 30 days (showing first 50).
Day 45: "Absolutely loving..." (15 likes, 3 shares, virality: 0.31)
...48 more posts..."

FAILURE examples:
  - Negative days: input={"days": -1} → output="Days must be a positive integer"
```

**Parameters:**
- `sentiment` (string) (optional): Optional: filter by sentiment
- `days` (integer) (optional): How many days back to search (default 7)
- `limit` (integer) (optional): Max posts to return (default 50)

---

### expand_notification

**Description:** Get full details of a notification. The daily summary shows brief headlines - use this to see complete information for any notification you want to investigate.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Enterprise lead notification: input={"notification_id": 42} → output="=== Notification #42 ===
Type: enterprise_new_lead
Day: 45

Title: New enterprise lead from TechCorp (200 seats)

Summary:
A new enterprise customer is interested. 200-person team, creative industry.

Details:
{"customer_id": 312, "thread_id": 15, "seat_count": 200, "industry": "creative"}"
  - VC approach notification: input={"notification_id": 55} → output="=== Notification #55 ===
Type: vc_approach
Day: 30

Title: VC Interest: Apex Capital ($500K)

Summary:
Apex Capital wants to invest $500,000 for 15% equity. Thread #3 created.

Details:
{"thread_id": 3, "vc_name": "Apex Capital", "amount": 500000, "target_pct": 0.15}"
  - System alert: input={"notification_id": 60} → output="=== Notification #60 ===
Type: system_alert
Day: 46

Title: Server overload detected

Summary:
Usage exceeded capacity by 25%. P95 latency increased to 1200ms."

FAILURE examples:
  - Not found: input={"notification_id": 99999} → output="Notification 99999 not found."
```

**Parameters:**
- `notification_id` (integer) (required): The notification ID from the daily summary

---

### list_potential_vcs

**Description:** List all known VC investors and their profiles. Shows investment range, description, and whether they have an active negotiation. OUTPUT: VC profiles with status. IMPACT: Read-only, free.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - View all VCs: input={} → output="=== Potential VC Investors ===

  Horizon Ventures (vc_01)
    Investment range: $100,000 – $500,000
    Description: Early-stage micro-VC focused on AI/ML startups
    Status: Available

  Catalyst Capital (vc_02)
    Investment range: $250,000 – $1,000,000
    Description: Seed-stage fund investing in developer tools
    Status: Active (Thread #3)

  ...12 more VCs...

Total: 15 VCs (1 currently active)"
```

---

### propose_vc_terms

**Description:** Send an email with an equity offer/counter-offer to a VC investor. You must write a message explaining your proposal and specify the share %. IMPACT: Sends offer to VC, schedules VC reply. OUTPUT: Offer details with implied valuation.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Accepted with term adjustment: input={"thread_id": 1, "share_pct": 0.12, "amount": 500000, "anti_dilution_floor": 0.9} → output="ACCEPTED! Apex Capital accepts your offer:
  Share %: 12.0%
  Investment: $500,000
  Implied valuation: $3,666,667 pre / $4,166,667 post
  Price/share: $0.3667
  New shares: 1,363,636
  Terms: Anti-dilution (floor: 70% → proposed: 90%)
  Term adjustment: +0.0350 (positive = more VC-friendly)
Use settle_investments([1]) to finalize."
  - Counter-offer (not enough equity): input={"thread_id": 2, "share_pct": 0.05} → output="Offer sent to Summit Ventures:
  Share %: 5.0%
  Investment: $300,000
  Implied valuation: $5,700,000 pre / $6,000,000 post
  Price/share: $0.5700
  New shares: 526,316
Awaiting VC response..."
  - With milestone terms: input={"thread_id": 3, "share_pct": 0.1, "milestone_tranche_pct": 0.3, "milestone_revenue_multiplier": 3.0, "milestone_deadline_days": 60} → output="Offer sent to Growth Partners:
  Share %: 10.0%
  Investment: $750,000
  Implied valuation: $6,750,000 pre / $7,500,000 post
  Price/share: $0.6750
  New shares: 1,111,111
  Terms: Milestone tranching ($225,000 + $525,000)
  Term adjustment: +0.0800 (positive = more VC-friendly)
Awaiting VC response..."

FAILURE examples:
  - Invalid term option: input={"thread_id": 1, "share_pct": 0.1, "anti_dilution_floor": 0.55} → output="anti_dilution_floor must be one of [0.6, 0.7, 0.8, 0.9]"
  - Thread not found: input={"thread_id": 999, "share_pct": 0.1} → output="VC thread #999 not found"
  - Already settled: input={"thread_id": 1, "share_pct": 0.1} → output="Thread #1 is already settled"
  - Term not on this deal: input={"thread_id": 2, "share_pct": 0.1, "anti_dilution_floor": 0.9} → output="Cannot propose anti_dilution_floor — this deal has no anti-dilution term"
```

**Parameters:**
- `thread_id` (integer) (required): The VC thread ID
- `share_pct` (number) (required): Share percentage to offer (e.g., 0.10 for 10%)
- `message_text` (string) (required): Email message to the VC explaining your offer or counter-offer
- `amount` (number) (optional): Investment amount (optional, defaults to VC's requested amount)

---

### reject_vc_deal

**Description:** Explicitly reject a VC deal. Terminates the negotiation permanently — cannot be undone. No relationship penalty or late-reply penalty applies. IMPACT: Thread marked as rejected.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Reject active deal: input={"thread_id": 1} → output="Rejected VC deal with Apex Capital. Thread #1 permanently closed."

FAILURE examples:
  - Already settled: input={"thread_id": 1} → output="Thread #1 is already settled"
  - Already rejected: input={"thread_id": 2} → output="Thread #2 is already rejected"
```

**Parameters:**
- `thread_id` (integer) (required): The VC thread ID to reject

---

### reject_enterprise_deal

**Description:** Explicitly reject an enterprise negotiation. Terminates it permanently. For new leads, the lead is lost. IMPACT: Thread cancelled, negotiation ended.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Reject new lead: input={"thread_id": 45} → output="Rejected enterprise thread #45 (new_lead). Lead marked as lost."
  - Reject churn prevention: input={"thread_id": 30} → output="Rejected enterprise thread #30 (churn_prevention). Customer may cancel subscription."

FAILURE examples:
  - Thread not found: input={"thread_id": 999} → output="Thread #999 not found"
  - Already closed: input={"thread_id": 45} → output="Thread #45 is already closed"
```

**Parameters:**
- `thread_id` (integer) (required): The enterprise thread ID to reject

---

### initiate_enterprise_negotiation

**Description:** Proactively start a negotiation with any existing enterprise customer by sending an outreach email with an offer. You must write a message and include an offer with price_per_seat (like send_reply for negotiation threads). Creates a renegotiation thread. Customer will respond within a few days. IMPACT: New negotiation thread created.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Two offerings: input={"customer_id": 42, "message_text": "We'd like to discuss improved pricing.", "offerings": [{"plan": "B", "price_per_seat": 12.0, "contract_months": 6}, {"plan": "B", "price_per_seat": 11.0, "contract_months": 12}]} → output="Negotiation initiated with enterprise customer #42 (200 seats, current Plan B at $15.00/seat, contract: 45d remaining).
Your offerings: Plan B @ $12.00/seat, 6mo; Plan B @ $11.00/seat, 12mo.
Thread #8 created. Customer will respond within a few days."
  - Upsell with three offerings: input={"customer_id": 88, "message_text": "Upgrade options for your team.", "offerings": [{"plan": "B", "price_per_seat": 13.0, "contract_months": 12}, {"plan": "C", "price_per_seat": 18.0, "contract_months": 6}, {"plan": "C", "price_per_seat": 16.0, "contract_months": 24}]} → output="Negotiation initiated with enterprise customer #88 (75 seats, current Plan A at $25.00/seat, contract: 10d remaining).
Your offerings: Plan B @ $13.00/seat, 12mo; Plan C @ $18.00/seat, 6mo; Plan C @ $16.00/seat, 24mo.
Thread #9 created. Customer will respond within a few days."

FAILURE examples:
  - No offerings: input={"customer_id": 42, "message_text": "Hello", "offerings": []} → output="offerings parameter is required. Send up to 3 offerings, each with plan, price_per_seat, and contract_months."
  - Not enterprise: input={"customer_id": 5, "message_text": "Hi", "offerings": [{"plan": "A", "price_per_seat": 10.0, "contract_months": 1}]} → output="Customer #5 is not an enterprise customer. Only enterprise (large) customers support negotiation."
  - Already has active thread: input={"customer_id": 42, "message_text": "New offer", "offerings": [{"plan": "B", "price_per_seat": 11.0, "contract_months": 6}]} → output="Customer #42 already has an active thread (Thread #8, type=renegotiation). Cannot start a new negotiation."
```

**Parameters:**
- `customer_id` (integer) (required): The enterprise customer ID to negotiate with (must have active subscription)
- `message_text` (string) (required): The outreach email message to the customer explaining your renegotiation proposal
- `offer` (object) (required): Structured offer. MUST include 'price_per_seat'. Optionally include 'plan'.

---

### get_cap_table

**Description:** View the current cap table showing all shareholders, ownership percentages, funding history, and dividend history. OUTPUT: Detailed cap table. IMPACT: Read-only.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Early stage (founder only): input={} → output="=== Cap Table ===
Total Shares Outstanding: 10,000,000

Shareholder               Type    Shares      Ownership  Invested
---------------------------------------------------------------------------
Founder                   founder 10,000,000  100.0%     $0

--- Funding History (0 rounds) ---
No funding rounds yet.

--- Dividend History ---
No dividends declared yet."
  - Post-funding: input={} → output="=== Cap Table ===
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

Cumulative dividends: $50,000"
```

---

### settle_investments

**Description:** Execute accepted VC deals — issues shares and receives investment cash. All deals must be 'accepted' and not expired. Validates same price/share across deals. IMPACT: Shares issued, cash received, deals marked settled.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Settle single deal: input={"deal_ids": [1]} → output="=== Settlement Executed ===

  Apex Capital: $500,000 → 1,764,706 shares (15.0% equity) @ $0.2833/share

Total investment: $500,000
New total shares: 11,764,706
Founder ownership: 85.0%"
  - Settle two deals at once: input={"deal_ids": [1, 3]} → output="=== Settlement Executed ===

  Apex Capital: $500,000 → 1,764,706 shares (15.0% equity) @ $0.2833/share
  Summit Ventures: $300,000 → 882,353 shares (7.5% equity) @ $0.3400/share

Total investment: $800,000
New total shares: 12,647,059
Founder ownership: 79.1%"

FAILURE examples:
  - Not accepted yet: input={"deal_ids": [1]} → output="Thread #1 is in state 'negotiating', must be 'accepted'"
  - Deal expired: input={"deal_ids": [3]} → output="Thread #3 has expired (day 45)"
  - Empty list: input={"deal_ids": []} → output="No deal_ids provided"
```

**Parameters:**
- `deal_ids` (array) (required): List of VC thread IDs to settle

---

### declare_dividend

**Description:** Declare a dividend from retained earnings (cumulative profit), distributed pro-rata by shares. Can only distribute from profits, NOT from invested capital (seed funding or VC investments). IMPACT: Cash reduced, dividend recorded. OUTPUT: Payout details per shareholder, remaining retained earnings.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Standard dividend: input={"amount": 100000} → output="=== Dividend Declared ===
Total: $100,000 | Per share: $0.008300

  Founder: $83,000.00 (10,000,000 shares)
  Apex Capital: $17,000.00 (2,048,193 shares)

Cumulative dividends paid: $150,000 (Founder: $124,500)
Remaining retained earnings: $50,000"
  - Small dividend: input={"amount": 10000} → output="=== Dividend Declared ===
Total: $10,000 | Per share: $0.001000

  Founder: $10,000.00 (10,000,000 shares)

Cumulative dividends paid: $10,000 (Founder: $10,000)
Remaining retained earnings: $25,000"

FAILURE examples:
  - Exceeds retained earnings: input={"amount": 1000000} → output="Amount exceeds retained earnings. Available: $150,000, Requested: $1,000,000"
  - No retained earnings: input={"amount": 5000} → output="No retained earnings available for dividends. Retained earnings: $-12,000"
  - Insufficient cash: input={"amount": 100000} → output="Insufficient cash. Available: $45,000, Requested: $100,000"
```

**Parameters:**
- `amount` (number) (required): Total dividend amount to distribute

---

### research_market

**Description:** Conduct market research to discover new customer segments. Cost: $25,000 per attempt. Each attempt has a 30% chance to discover one new group at Info Level 1 (±50% accuracy). OUTPUT: Discovered group name, segment type, and initial parameter estimates. Use get_group_insights() for detailed estimates.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Discovery success: input={} → output="=== Market Research Success ===
Cost: $25,000
Discovered: Niche Creators (D_S01) — Individual segment
Info Level: 1 (noisy estimates ±50%)
Remaining undiscovered segments: 19

--- Initial Estimates (±50% accuracy) ---
  Willingness to pay:   ~$85/mo
  Usage volume:         ~35 units/day
  Quality expectations: ~0.58
  Market cap:           ~185,000 customers
  Market cap growth:    ~9.2%/year"

FAILURE examples:
  - No discovery (70% chance): input={} → output="Market research complete ($25,000). No new segments discovered this time. 19 undiscovered segments remain. Try again for another chance."
  - Insufficient funds: input={} → output="Insufficient funds. Market research costs $25,000. Available: $12,000"
```

---

### research_group

**Description:** Start research on a discovered group to improve parameter accuracy. Research takes several days; results are delivered to your inbox when complete. Costs (deducted immediately): Level 1→2 ($60K, ~3 days, ±25%), Level 2→3 ($175K, ~5 days, ±10%), Level 3→4 ($350K, ~7 days, ±5%). OUTPUT: Confirmation with expected completion day.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Level 1→2: input={"group_id": "D_S01"} → output="=== Research Started ===
Group: Niche Creators (D_S01)
Level: 1 → 2
Cost: $60,000 (deducted)
Expected completion: day 18 (~3 days)
New parameter accuracy: ±25%"
  - Level 2→3: input={"group_id": "D_E01"} → output="=== Research Started ===
Group: Government Agencies (D_E01)
Level: 2 → 3
Cost: $175,000 (deducted)
Expected completion: day 35 (~5 days)
New parameter accuracy: ±10%"

FAILURE examples:
  - Already in progress: input={"group_id": "D_S01"} → output="Research already in progress for group 'D_S01'. Expected completion: day 18."
  - Insufficient funds: input={"group_id": "D_E01"} → output="Insufficient funds. Research Level 2 costs $60,000. Available: $45,000"
  - Unknown group: input={"group_id": "X99"} → output="Group 'X99' not found or not yet discovered."
```

**Parameters:**
- `group_id` (string) (required): The group to research (must be at Level 1-3)

---

### get_market_overview

**Description:** Get an overview of all known customer segments, their info levels, and discovery status. Shows discovered groups with noise labels. OUTPUT: List of known segments with info levels, undiscovered count.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Early game (6 groups): input={} → output="=== Market Overview ===

Known Segments (6):
  S1: Price-Sensitive Individuals — Individual (initial) — Level 4 (±5%)
  S2: Quality-Focused Individuals — Individual (initial) — Level 4 (±5%)
  S3: Balanced Individuals — Individual (initial) — Level 4 (±5%)
  E1: Small Enterprise — Enterprise (initial) — Level 4 (±5%)
  E2: Mid Enterprise — Enterprise (initial) — Level 4 (±5%)
  E3: Large Enterprise — Enterprise (initial) — Level 4 (±5%)

Undiscovered segments: 20
Use research_market() to discover ($25K, 30% success)."
  - After discoveries: input={} → output="=== Market Overview ===

Known Segments (8):
  S1-S3, E1-E3: (initial groups, Level 4)
  D_S01: Niche Creators — Individual — Level 2 (±25%)
  D_E01: Government Agencies — Enterprise — Level 1 (±50%)

Undiscovered segments: 18"
```

---

### get_group_insights

**Description:** Get estimated parameters for a discovered customer group. Returns noisy estimates of budget, usage volume, quality expectations, market cap (total addressable customers), and annual market cap growth rate. Enterprise groups also show team size and negotiation patience. Accuracy depends on info level (±50%/±25%/±10%/±5%). Same query always returns same estimates.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Individual group: input={"group_id": "D_S01"} → output="=== Group Insights: Niche Creators (D_S01) ===
Segment: Individual
Info Level: 2 (±25%)

Estimated Parameters:
  Willingness to pay:    ~$92/mo
  Usage volume:          ~38 units/day
  Quality expectations:  ~0.61
  Market cap:            ~185,000
  Growth:                ~9.2%/year

Network Influence:
  Self-referral: ~4.2 leads/1000 subs/day
  Outgoing: → D_S10: ~1.8, → S1: ~0.9
  Incoming: ← S1: ~1.3"
  - Enterprise group: input={"group_id": "E1"} → output="=== Group Insights: Small Enterprise (E1) ===
Segment: Enterprise
Info Level: 4 (±5%)

Estimated Parameters:
  Willingness to pay:    ~$22/seat/mo
  Seat range:            10-50 seats
  Usage volume:          ~25 units/day/seat
  Quality expectations:  ~0.65
  Market cap:            ~45,000
  Decision rounds:       ~3
  Avg response days:     ~2.5

Network Influence:
  Self-referral: ~2.1 leads/1000 subs/day
  Outgoing: → E2: ~1.2, → S1: ~0.5"
  - Initial group at full accuracy: input={"group_id": "S1"} → output="=== Group Insights: Price-Sensitive Individuals (S1) ===
Segment: Individual
Info Level: 4 (±5%)

Estimated Parameters:
  Willingness to pay:    ~$45/mo
  Usage volume:          ~20 units/day
  Quality expectations:  ~0.50
  Market cap:            ~500,000
  Growth:                ~5.0%/year"

FAILURE examples:
  - Unknown group: input={"group_id": "X99"} → output="Group 'X99' not found. Known groups: S1, S2, S3, E1, E2, E3, D_S01, D_E01"
  - Undiscovered group: input={"group_id": "D_S05"} → output="Group 'D_S05' has not been discovered yet. Use research_market() to discover new segments."
```

**Parameters:**
- `group_id` (string) (required): The group to get insights for (must be discovered, Level 1+)

---

### start_research_project

**Description:** Start an R&D research project. Costs are deducted immediately. Project completes after expected duration, providing permanent quality boost and temporary decay rate reduction (lasts for a sampled number of days). Use list_research_projects() to see available options. OUTPUT: Project details, expected completion day. IMPACT: Cash reduced by project cost.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Start root project: input={"project_id": "rp_01"} → output="=== Research Project Started ===
Project: Advanced NLP Pipeline (rp_01)
Cost: $15,000 (deducted)
Expected completion: ~day 25 (5 days ± 1)
Quality boost on completion: +0.03
Decay reduction: -20% for ~45 days"

FAILURE examples:
  - Prerequisites not met: input={"project_id": "rp_15"} → output="Cannot start 'rp_15': prerequisite project(s) not completed: ['rp_07', 'rp_10']"
  - Already completed: input={"project_id": "rp_01"} → output="Project 'rp_01' is already completed."
  - Insufficient funds: input={"project_id": "rp_02"} → output="Insufficient cash. Project costs $25,000, available: $18,000"
```

**Parameters:**
- `project_id` (string) (required): The project to start (e.g., 'rp_01'). Use list_research_projects() to see available options.

---

### list_research_projects

**Description:** List all R&D research projects -- available, in-progress, and completed. Shows costs, expected durations, quality boosts, decay reduction durations, and prerequisites. OUTPUT: Categorized list of all 40 projects. IMPACT: None - read only.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - With mixed statuses: input={} → output="=== R&D Research Projects ===

AVAILABLE NOW (3):
  rp_01: Advanced NLP Pipeline — $15,000, ~5d, +0.03 quality, -20% decay (~45d)
  rp_02: Multimodal Integration — $25,000, ~7d, +0.05 quality
  rp_03: Edge Inference — $10,000, ~3d, +0.02 quality

IN PROGRESS (1):
  rp_04: RAG Architecture — completing ~day 32 (3d left)

COMPLETED (2):
  rp_05: Basic Fine-tuning — +0.02, decay -10% expires day 55
  rp_06: Caching Layer — +0.01, decay reduction expired

LOCKED (34): ..."
  - Early game (all available or locked): input={} → output="=== R&D Research Projects ===

AVAILABLE NOW (6):
  rp_01: Advanced NLP Pipeline — $15,000, ~5d, +0.03 quality
  rp_02: Multimodal Integration — $25,000, ~7d, +0.05 quality
  ...4 more root projects...

LOCKED (34): requires completed prerequisites"
```

---

### describe_tables

**Description:** Get descriptions of visible columns for specified database tables. Returns column names, types, and descriptions. Useful for understanding schemas before writing SQL queries via python_exec(). OUTPUT: Column descriptions for requested tables. IMPACT: None - read only.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Two specific tables: input={"table_names": ["customers", "subscriptions"]} → output="=== customers ===
All customers (small and enterprise)

  customer_id: INTEGER PRIMARY KEY
  customer_type: TEXT — 'small' or 'large'
  ...(14 more columns)

=== subscriptions ===
Subscription records

  subscription_id: INTEGER PRIMARY KEY
  customer_id: INTEGER
  plan: TEXT — 'A', 'B', or 'C'
  ...(8 more columns)"
  - Single table: input={"table_names": ["ledger"]} → output="=== ledger ===
Financial ledger — all income and expenses

  id: INTEGER PRIMARY KEY — Unique entry ID
  day: INTEGER — Simulation day
  category: TEXT — Category: 'subscription_payment', 'compute', 'capacity', 'advertising', 'operations', 'development', ...
  amount: REAL — Amount (positive=income, negative=expense)
  note: TEXT — Description of the transaction"
  - All tables (no args): input={} → output="=== customers ===
...

=== subscriptions ===
...

=== daily_usage ===
...

(17 tables total)"

FAILURE examples:
  - Unknown table: input={"table_names": ["nonexistent"]} → output="No matching tables found. Available: customers, subscriptions, daily_usage, ledger, service_day, config_history, ..."
```

**Parameters:**
- `table_names` (array) (optional): List of table names to describe, or omit for all visible tables. Available: customers, subscriptions, daily_usage, ledger, service_day, config_history, social_media_posts, enterprise_turns, vc_turns, notifications, shareholders, funding_rounds, dividends, research_projects, ad_channel_leads, group_info_levels, issues

---

### next_day

**Description:** End your turn for today and advance to the next day. OUTPUT: Daily dashboard showing cash, subscribers, MRR, open issues, yesterday's metrics (usage, new subscribers, cancellations, upgrades/downgrades, overload, outage, P95 latency, error rate, revenue/costs), equity & funding (founder ownership, shares, VC negotiations, dividends, retained earnings), current config (prices, model tiers, quotas, capacity tier, daily spend), daily calculation results, and inbox. IMPACT: Simulation advances to next day. Call this when you have finished all actions for today. You MUST call this to proceed - the day will not advance until you do.

**Agent-visible sample I/O:**
```
SAMPLE INPUTS/OUTPUTS:

SUCCESS examples:
  - Normal day: input={} → output="=== DAY 46 DASHBOARD ===

CASH: $85,234  |  MRR: $12,350  |  SUBSCRIBERS: 145

YESTERDAY'S METRICS:
  Revenue: $412  |  Costs: $2,845
  New subscribers: 5  |  Cancellations: 2
  Usage: 48,230 units (capacity: 200,000 = 24.1%)
  Overload: 0.0%  |  Outage: No

INBOX (2 new):
  #42: New enterprise lead from TechCorp (200 seats)
  #43: Quality trending down alert

========================="

FAILURE examples:
  - Bankruptcy: input={} → output="GAME OVER — BANKRUPT! Cash dropped below $0 on day 46.

Final stats: 145 subscribers, $12,350 MRR, $-1,234 cash.
Founder cumulative dividends: $50,000."
  - Simulation complete: input={} → output="SIMULATION COMPLETE! Day 3650 reached.

Final stats: 12,000 subscribers, $1,250,000 MRR, $8,500,000 cash.
Founder cumulative dividends: $11,195,040."
```

---
