# BossBench — Tool & Table Documentation (Internal + External)

> **Legend:** 🟢 = External (agent-visible) | 🔴 = Internal-only (hidden from agent)
> **Last updated:** 2026-02-16 — V2 entity-based addressing (customer_id/shareholder_id, thread_id removed from agent surfaces)

---

# Part 1 — Tool Documentation

There are two layers of tool docs:

1. **`tool_docs.json`** (🟢 External) — served to the agent via `get_tool_documentation()`. Contains: name, category, description, parameters, returns, impact, example_call.
2. **`TOOL_DOCS` dict in `tools.py`** (🔴 Internal extras) — same entries plus `internal_notes` (hidden formulas/mechanics) and `sample_io` (example input/output pairs used for MCP description enrichment).

---

## Business Configuration

### `set_prices`

**Category:** Business Configuration
**Parameters:** `A`, `B`, `C` (float, partial update OK — omitted plans keep current price)

🟢 **Description:** Set monthly subscription prices for plans A, B, and C.

🟢 **Returns:**
- Success: `"Prices updated: B=$79.00"`
- Failure: `"Must provide at least one plan price"` / `"Price for plan X must be positive"`

🟢 **Impact:** Affects customer acquisition (higher prices = fewer sign-ups), churn (price vs value), and revenue. Changes take effect on next_day.

🟢 **Example:**
```json
{"tool": "set_prices", "arguments": {"B": 79, "C": 199}}
```

🔴 **Internal notes:** Price stored in config_history. Affects Q_required via asymmetric sigmoid: Q_req(price) uses steepness_left (price < c_max/2) or steepness_right (price >= c_max/2). Enterprise customers negotiate off list price.

🔴 **Sample I/O:**
| Label | Input | Output |
|-------|-------|--------|
| Set all three plans | `{"A": 25, "B": 69, "C": 179}` | `Prices updated: A=$25.00, B=$69.00, C=$179.00` |
| Update only plan B | `{"B": 89}` | `Prices updated: B=$89.00` |
| Negative price | `{"A": -10}` | `Price for plan A must be positive` |
| Empty input | `{}` | `Must provide at least one plan price` |

---

### `set_model_tiers`

**Category:** Business Configuration
**Parameters:** `A`, `B`, `C` (int 1-5, partial update OK)

🟢 **Tier info:**

| Tier | Cost/unit | Quality | Class |
|------|-----------|---------|-------|
| 1 | $0.0003 | 0.55 | Flash-Lite/4o-mini |
| 2 | $0.002 | 0.65 | Haiku/Flash |
| 3 | $0.006 | 0.75 | Sonnet/GPT-4o |
| 4 | $0.012 | 0.85 | Opus/GPT-5 |
| 5 | $0.030 | 0.95 | o1/o3 reasoning |

🟢 **Impact:** Higher tiers increase customer satisfaction and reduce churn, but increase compute costs. Each tier adds +0.10 quality.

🔴 **Sample I/O:**
| Label | Input | Output |
|-------|-------|--------|
| Set all tiers | `{"A": 2, "B": 3, "C": 5}` | `Model tiers updated: A=tier2, B=tier3, C=tier5` |
| Tier out of range | `{"A": 0}` | `Tier for plan A must be 1-5` |

---

### `set_capacity_tier`

**Category:** Business Configuration
**Parameters:** `tier` (int 0-7)

🟢 **Tier info:**

| Tier | Capacity (units/day) | Cost/day | Description |
|------|---------------------|----------|-------------|
| 0 | 50,000 | $85 | Serverless API (Together/Fireworks) |
| 1 | 200,000 | $215 | 1x H100 neocloud dedicated |
| 2 | 800,000 | $530 | 4x H100 reserved cluster |
| 3 | 2,500,000 | $1,330 | 8x H100 enterprise + auto-scaling |
| 4 | 8,000,000 | $4,000 | Multi-node hyperscale (16-32 H100s) |
| 5 | 25,000,000 | $10,000 | 64x H100 multi-rack cluster |
| 6 | 80,000,000 | $28,000 | 256x H100 dedicated pod |
| 7 | 300,000,000 | $75,000 | 1024+ GPU hyperscale fleet |

🟢 **Impact:** When usage exceeds capacity, overload occurs causing higher latency and errors. Higher overload increases outage chance. Outages cause quality drops, satisfaction penalties, more customer issues, and can trigger negative social media posts.

🔴 **Internal notes:** Overload = max(0, total_usage / capacity_units - 1). Overload > 0 → p95_ms increases, error_rate increases. Outage_prob_from_overload = 0.1 * overload^2. Outage causes: quality_penalty = -0.05, satisfaction_penalty = -0.1 for all customers, 3-5 new issues generated, possible negative social posts.

---

### `set_usage_quotas`

**Category:** Business Configuration
**Parameters:** `A`, `B`, `C` (int, all 3 required)

🟢 **Impact:** Quotas limit per-customer usage to control costs. Lower quotas = lower compute costs but may frustrate high-usage customers.

🟢 **Example:**
```json
{"tool": "set_usage_quotas", "arguments": {"A": 150, "B": 750, "C": 3000}}
```

---

## Marketing & Spend

### `set_daily_spend`

**Category:** Marketing & Spend
**Parameters:** `advertising`, `operations`, `development` (float, partial update OK)

🟢 **Impact by category:**

| Category | Impact |
|----------|--------|
| advertising | Generates new leads. Each channel has a fixed leads-per-$1000 rate per customer group. |
| operations | CRITICAL: (1) Reduces outage probability — $0: ~3%/day, $500: ~1.1%/day. (2) Speeds issue resolution: mean resolved/day = 1 + 0.01 × spend. |
| development | CRITICAL: (1) Quality decays 0.1%/day unconditionally. Dev adds improvement = 0.001 × ln(1 + spend/1000), capped at ±15%. |

🔴 **Internal notes:** Ops: outage_prob = 0.03 * exp(-0.002 * ops_spend). Issue resolution: mean_resolved/day = 1 + 0.01 * spend. Dev: quality_improvement = 0.001 * ln(1 + spend/1000), capped at ±0.15. Quality decays at 0.001/day unconditionally. Advertising: each channel has fixed leads_per_1000_dollars per group.

---

### `set_ad_channel_spend`

**Category:** Marketing & Spend
**Parameters:** Channel percentages (0.0 to 1.0), normalized to sum to 1.0. Partial update OK.

🟢 **Channels:**

| Channel | Description |
|---------|-------------|
| social_media | Facebook, Instagram, TikTok ads — broad consumer reach |
| search_ads | Google/Bing search ads — intent-based targeting |
| linkedin | LinkedIn ads — professional/business audience |
| content_marketing | SEO, blogs, whitepapers — organic discovery |
| referral_program | Customer referral incentives — word-of-mouth |

---

### `set_targeted_ad_spend`

**Category:** Marketing & Spend
**Parameters:** `targeted_spend: Dict[str, Dict[str, float]]` — `{channel: {group: $/day}}`

🟢 **Description:** Set ADDITIONAL per-group per-channel ad spend on top of the overall channel allocation.

🟢 **Groups:** S1-S3, E1-E3, and discovered groups (D_S01-D_S10, D_E01-D_E10)

🟢 **Example:**
```json
{"tool": "set_targeted_ad_spend", "arguments": {"targeted_spend": {"linkedin": {"E1": 200, "E2": 100}, "content_marketing": {"S3": 50}}}}
```

---

### `set_targeted_ops_spend`

**Category:** Marketing & Spend
**Parameters:** `targeted_spend: Dict[str, float]` — `{group: $/day}`

🟢 **Description:** ADDITIONAL per-group operations spending on top of the global ops spend.

🔴 **Internal mechanics:** extra_mean_per_day = 0.053 × group_spend

---

### `set_targeted_dev_spend`

**Category:** Marketing & Spend
**Parameters:** `targeted_spend: Dict[str, float]` — `{group: $/day}`

🟢 **Description:** ADDITIONAL per-group development spending. Provides per-group quality bonus.

🔴 **Internal mechanics:** quality_bonus = 0.0005 × log(1 + spend/500). At $500/day: +0.00035, at $2000/day: +0.00075. Only affects subscribers in the targeted group (not global q_shared).

---

## Customer Communication (Enterprise)

### `send_enterprise_deal` ⭐ V2 Entity-Based

**Category:** Customer Communication
**Parameters:** `deals: list[Dict]` — each dict has `customer_id` (required) plus `offerings` (list of up to 3 offerings)

🟢 **Description:** Send enterprise deal offerings. List-based. Address by customer_id — system auto-resolves to active thread (reply) or creates renegotiation thread. Always pass a list of deals — single deal = list of length 1.

🟢 **Offering fields:** `plan` (str), `price_per_seat` (float), `contract_months` (int)

🟢 **Returns:**
- Success: `"Processed 2/2 deals:\n  Message #42: reply sent with 2 offering(s)\n  Customer #88: renegotiation initiated, 2 offering(s) sent"`
- Failure: `"Message #42: not found"` / `"Customer #88: already has an active thread"` / `"offerings required"`

🟢 **Impact:** Customer evaluates ALL offerings and picks the one with highest satisfaction. Satisfaction = quality_perceived - quality_required(price) + contract_bonus. Contract bonus = 0.5% per additional contract month. Customer accepts if best satisfaction > 0, counter-offers otherwise. Max negotiation turns → customer ghosts. Late replies (>1 day) damage relationship -0.02/day. No response within 3 days = customer permanently lost. For renegotiation (customer_id mode): creates new thread, safe — rejection does NOT cause churn.

🟢 **Strategy tips:**
- Send multiple offerings at different price/plan/contract combinations
- Longer contracts give customers a satisfaction bonus (contract_discount_per_month × (months-1))
- Include at least one offering per plan tier for first response to new leads
- Use customer_id to proactively renegotiate with existing enterprise customers — safe, rejection does NOT cause churn

🟢 **Example:**
```json
{
  "tool": "send_enterprise_deal",
  "arguments": {
    "deals": [
      {"customer_id": 42, "offerings": [{"plan": "A", "price_per_seat": 9.00, "contract_months": 6}, {"plan": "B", "price_per_seat": 14.00, "contract_months": 12}]},
      {"customer_id": 88, "offerings": [{"plan": "B", "price_per_seat": 12.00, "contract_months": 6}]}
    ]
  }
}
```

🔴 **Internal notes:** customer_id mode: looks up active thread by customer_id (auto-replies if open, creates renegotiation if no open thread but has active subscription). Satisfaction = Q_perceived - Q_required(price) + contract_discount_per_month * (months-1). Late penalty = -0.02 * max(0, days_since_msg - 1). Max offerings = 3.

🔴 **Sample I/O:**
| Label | Input | Output |
|-------|-------|--------|
| Reply with 3 offerings | `{"deals": [{"customer_id": 42, "offerings": [...3 items...]}]}` | `Processed 1/1 deals: Customer #42: reply sent with 3 offering(s)` |
| Initiate renegotiation | `{"deals": [{"customer_id": 88, "offerings": [...]}]}` | `Processed 1/1 deals: Customer #88: renegotiation initiated (200 seats, current Plan B @ $15.00/seat). 2 offering(s) sent.` |
| Customer not found | `{"deals": [{"customer_id": 999, "offerings": [...]}]}` | `Processed 0/1 deals (1 failed): Customer #999: no active thread or subscription` |
| Missing offerings | `{"deals": [{"customer_id": 42}]}` | `Processed 0/1 deals (1 failed): Customer #42: offerings required` |

---

### `reject_enterprise_deal` ⭐ V2 Entity-Based

**Category:** Customer Communication
**Parameters:** `deals: list[Dict]` — each has `customer_id`

🟢 **Impact:** For new_lead threads: lead is permanently lost. For existing customer threads (churn_prevention, plan_change): customer may cancel. Use when the deal is not worth pursuing.

🟢 **Example:**
```json
{"tool": "reject_enterprise_deal", "arguments": {"deals": [{"customer_id": 42}]}}
```

🔴 **Sample I/O:**
| Label | Input | Output |
|-------|-------|--------|
| Reject by customer_id | `{"deals": [{"customer_id": 42}]}` | `Processed 1/1 rejections: Customer #42: Rejected (new_lead). Lead marked as lost.` |
| Reject by customer_id | `{"deals": [{"customer_id": 88}]}` | `Processed 1/1 rejections: Customer #88: Rejected active thread (churn_prevention). Customer may cancel.` |
| Already closed | `{"deals": [{"customer_id": 42}]}` | `Processed 0/1 rejections (1 failed): Customer #42: thread already closed` |

---

## VC Negotiation

### `send_vc_deal` ⭐ V2 Entity-Based

**Category:** VC Negotiation
**Parameters:** `deals: list[Dict]` — each has `shareholder_id` (required), `share_pct` (required), plus optional term proposals

🟢 **Description:** Submit equity offers to one or more VCs. List-based. Each deal includes share_pct and optional term sheet proposals. If the offer meets or exceeds the VC's effective target (adjusted for term friendliness), they accept immediately. Otherwise, the VC will counter-offer after a delay.

🟢 **Deal fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| shareholder_id | int | Yes | The VC shareholder_id to address |
| share_pct | float | Yes | Share % to offer (0.10 = 10%) |
| anti_dilution_floor | float | No | One of [0.6, 0.7, 0.8, 0.9]. Higher = more VC-friendly |
| milestone_tranche_pct | float | No | One of [0.3, 0.4, 0.5, 0.6, 0.7]. Lower = more VC-friendly |
| milestone_revenue_multiplier | float | No | One of [1.5, 2.0, 2.5, 3.0]. Higher = more VC-friendly |
| milestone_deadline_days | int | No | One of [60, 90, 120, 180]. Shorter = more VC-friendly |
| redemption_days | int | No | One of [90, 120, 180, 270, 365]. Shorter = more VC-friendly |
| redemption_buyback_multiplier | float | No | One of [1.0, 1.1, 1.2, 1.3, 1.5]. Higher = more VC-friendly |

🟢 **Key formula:** `implied_check = share_pct / (1 - share_pct) × valuation`

🟢 **Acceptance logic:** If implied_check ≥ VC's minimum → accepted. VC-friendly terms boost effective valuation → easier acceptance at lower equity.

🟢 **Strategy tips:**
- Check VC's check range, valuation, and term sheet via python_exec (query vc_turns + shareholders)
- Trade-off: more VC-friendly terms reduce the equity % needed for acceptance
- Anti-dilution: higher floor = more protection for VC but bigger dilution risk if valuation drops
- Milestone tranching: lower tranche_pct = less cash upfront; higher rev multiplier = harder to unlock tranche 2
- Redemption: shorter window = VC can demand buyback sooner; higher multiplier = costlier buyback
- You can propose term changes AND equity in the same call — optimize the combination

🟢 **Example:**
```json
{"tool": "send_vc_deal", "arguments": {"deals": [{"shareholder_id": 15, "share_pct": 0.10, "anti_dilution_floor": 0.9, "milestone_tranche_pct": 0.3}]}}
```

🔴 **Internal notes:** Effective target = base_target * (1 - term_friendliness_adjustment). Anti-dilution: floor 0.6→0.9 maps to 0→0.05 bump. Milestone: tranche_pct 0.7→0.3 = 0→0.04, rev_multiplier 1.5→3.0 = 0→0.02, deadline 180→60 = 0→0.02. Redemption: days 365→90 = 0→0.03, buyback 1.0→1.5 = 0→0.03. Max combined ~0.19. VC counter-offer delay = 1-3 days.

🔴 **Sample I/O:**
| Label | Input | Output |
|-------|-------|--------|
| Accepted with term adjustment | `{"deals": [{"shareholder_id": 15, "share_pct": 0.12, "anti_dilution_floor": 0.9}]}` | `Processed 1/1 deals: Shareholder #15: ACCEPTED! Apex Capital accepts 12.0% for $500,000. Term adjustment: +0.0350. Use settle_investments() to finalize.` |
| Batch: one accepted, one pending | `{"deals": [{"shareholder_id": 15, "share_pct": 0.12}, {"shareholder_id": 22, "share_pct": 0.05}]}` | `Processed 2/2 deals: Shareholder #15: ACCEPTED!... Shareholder #22: Offer sent... Awaiting VC response...` |
| Invalid term option | `{"deals": [{"shareholder_id": 15, "share_pct": 0.1, "anti_dilution_floor": 0.55}]}` | `Shareholder #15: anti_dilution_floor must be one of [0.6, 0.7, 0.8, 0.9]` |

---

### `reject_vc_deal` ⭐ V2 Entity-Based

**Category:** VC Negotiation
**Parameters:** `deals: list[Dict]` — each has `shareholder_id`

🟢 **Impact:** PERMANENTLY terminates the negotiation — the VC will not return. NO penalties (unlike enterprise rejections).

🟢 **Example:**
```json
{"tool": "reject_vc_deal", "arguments": {"deals": [{"shareholder_id": 15}]}}
```

🔴 **Sample I/O:**
| Label | Input | Output |
|-------|-------|--------|
| Reject single | `{"deals": [{"shareholder_id": 15}]}` | `Processed 1/1 rejections: Shareholder #15: Rejected deal with Apex Capital.` |
| Already settled | `{"deals": [{"shareholder_id": 15}]}` | `Processed 0/1 rejections (1 failed): Shareholder #15: thread already closed (settled)` |

---

### `list_potential_vcs`

**Category:** VC Negotiation
**Parameters:** None

🟢 **Returns:** All predefined VCs with name, investment range, description, and whether they have an active negotiation thread.

---

## Equity & Funding

### `settle_investments` ⭐ REDESIGNED

**Category:** Equity & Funding
**Parameters:** **NONE** — takes no parameters

🟢 **Description:** Settle ALL accepted VC deals at once. Automatically finds all accepted deals, validates they have the same price/share (1% tolerance) and total dilution < 100%, issues shares, and adds investment cash. Also auto-rejects all remaining open (non-accepted) VC threads.

🟢 **Returns:**
- Success: Settlement details with per-VC breakdown, total investment, new share counts, founder ownership %
- Failure: `"No accepted VC deals to settle."` / `"All accepted deals must use the same price/share."` / `"Total accepted equity = 120.0% (>= 100%). Cannot settle."`

🟢 **Impact:** CRITICAL — issues new shares (dilutes founder), adds cash, auto-rejects all open threads. Accepted deals expire if not settled before expiry_day. Irreversible.

🟢 **Strategy tips:**
- Settle accepted deals promptly — they expire!
- All open VC threads are auto-rejected when you settle — accept all desired deals first
- If accepted deals have mismatched price/share, reject some before settling

🔴 **Internal notes:** Finds threads with close_reason='accepted', auto-rejects open threads (closed=0). Validates same price/share (1% tolerance) and total dilution < 100%. new_shares = (share_pct / (1-share_pct)) × existing_total. Marks settled threads with close_reason='settled'.

🔴 **Sample I/O:**
| Label | Input | Output |
|-------|-------|--------|
| Settle one deal | `{}` | `=== Settlement Executed ===\n  Apex Capital: $500,000 → 1,764,706 shares (15.0%)...` |
| Settle two, auto-reject one | `{}` | `Auto-rejected 1 open thread(s): Growth Partners\n  Apex Capital:... Summit Ventures:...` |
| No accepted deals | `{}` | `No accepted VC deals to settle.` |
| Price mismatch | `{}` | `All accepted deals must use the same price/share. Got range $0.2833 - $0.5000.` |

---

### `get_cap_table_info`

**Category:** Equity & Funding
**Parameters:** None

🟢 **Returns:** Shareholders, share counts, ownership %, funding history, dividend history.

---

### `declare_dividend`

**Category:** Equity & Funding
**Parameters:** `amount` (float)

🟢 **Description:** Declare a dividend from RETAINED EARNINGS only. Distributed pro-rata to all shareholders. Cannot distribute invested capital (VC money).

🟢 **Impact:** Founder's cumulative dividends = PRIMARY objective. Dilution reduces your share of every future dividend.

🟢 **Strategy tips:**
- Founder's cumulative dividends is the MAIN success metric
- Can ONLY distribute from profits — VC investment money cannot be paid as dividends
- Retained earnings = cumulative revenue - cumulative costs - prior dividends
- Keep enough cash runway (30+ days of expenses) before declaring

🔴 **Internal notes:** Retained earnings = SUM(ledger.amount) - SUM(dividends.total_amount) - total_vc_invested. Pro-rata: each shareholder gets (their_shares / total_shares) * amount. Founder payout tracked in dividends.founder_payout.

---

## Analytics & Monitoring

### `python_exec`

**Category:** Analytics & Monitoring
**Parameters:** `code` (str), `timeout_seconds` (float, default 5.0)

🟢 **Available in code:**

| Variable | Description |
|----------|-------------|
| `conn` | SQLite connection (read-only) with row_factory=sqlite3.Row |
| `rows(query, params)` | Execute query, return list of tuples |
| `row(query, params)` | Execute query, return single tuple or None |
| `pd` | pandas |
| `np` | numpy |
| `sklearn` | LinearRegression, StandardScaler |
| `json`, `math`, `statistics` | Standard library |
| `Counter`, `defaultdict` | from collections |

🟢 **Key notes:**
- STATELESS: each call runs in a FRESH context. Variables don't persist.
- Use `describe_tables()` for schema info. PRAGMA/sqlite_master blocked.

🟢 **Example queries:**

```python
# Active subscribers
row('SELECT COUNT(*) FROM subscriptions WHERE status="subscribed" AND end_day IS NULL')[0]

# Open enterprise threads (latest turn per thread)
rows('''SELECT et.thread_id, et.closed, et.close_reason, c.seat_count, c.email
    FROM enterprise_turns et JOIN customers c ON et.customer_id=c.customer_id
    WHERE et.turn_id = (SELECT MAX(et2.turn_id) FROM enterprise_turns et2
      WHERE et2.thread_id=et.thread_id) AND et.closed = 0''')

# Active VC negotiations
rows('''SELECT vt.thread_id, s.name, vt.closed, vt.close_reason,
    vt.current_offer_share_pct, vt.current_offer_amount, vt.expiry_day
    FROM vc_turns vt JOIN shareholders s ON vt.shareholder_id=s.shareholder_id
    WHERE vt.turn_id = (SELECT MAX(vt2.turn_id) FROM vc_turns vt2
      WHERE vt2.thread_id=vt.thread_id) AND vt.closed = 0''')

# Accepted deals awaiting settlement
rows('''SELECT vt.thread_id, s.name, vt.current_offer_share_pct, vt.current_offer_amount
    FROM vc_turns vt JOIN shareholders s ON vt.shareholder_id=s.shareholder_id
    WHERE vt.turn_id = (SELECT MAX(vt2.turn_id) FROM vc_turns vt2
      WHERE vt2.thread_id=vt.thread_id) AND vt.close_reason="accepted"''')
```

🔴 **Internal notes:** Hidden tables (events, customer_state, group_reputation, etc.) are blocked. Hidden columns (sentiment, satisfaction, steepness_*, c_max, willingness_to_pay, etc.) are stripped from query results at runtime. pandas DataFrames also have hidden columns dropped.

---

### `get_social_posts`

**Parameters:** `days` (int, default 7), `limit` (int, default 50)

🟢 **Note:** Sentiment column is HIDDEN — agent must infer sentiment from post content.

---

### `expand_notification`

**Parameters:** `notification_id` (int)

🟢 **Returns:** Full details of a specific notification from the inbox.

---

### `get_cost_info`

**Parameters:** None

🟢 **Returns:** Model tier costs + capacity tier costs.

---

## Automation

### `register_daily_calculation`

**Parameters:** `name` (str), `code` (str — same env as python_exec)

🟢 **Description:** Register a named calculation to run automatically at the start of each day. Output appears in dashboard.

### `remove_daily_calculation`

**Parameters:** `name` (str)

### `list_daily_calculations`

**Parameters:** None

---

## Market Discovery

### `research_market`

**Parameters:** None
**Cost:** $25,000/attempt, 30% chance of discovering one random undiscovered group

🟢 **What happens:**
1. $25,000 deducted from cash
2. 30% chance to discover one undiscovered group
3. If successful: group set to Info Level 1, initial parameter estimates returned (±50% accuracy)
4. 20 additional segments to discover (10 individual, 10 enterprise)

---

### `research_group`

**Parameters:** `group_id` (str, e.g. 'D_S01', 'D_E03')

🟢 **Cost and duration:**

| Level | Cost | Duration | Accuracy |
|-------|------|----------|----------|
| 1→2 | $60,000 | ~3 days | ±25% |
| 2→3 | $175,000 | ~5 days | ±10% |
| 3→4 | $350,000 | ~7 days | ±5% |

Results delivered asynchronously via inbox notification.

---

### `get_market_overview`

**Parameters:** None

🟢 **Returns:** All known segments, info levels, undiscovered count.

---

### `get_group_insights`

**Parameters:** `group_id` (str)

🟢 **Returns:** Estimated parameters (noisy based on info level): willingness_to_pay, usage_volume, quality_expectations, market_cap, growth_rate, network influence (word-of-mouth), reputation influence (cross-group sentiment).

---

## R&D Research Projects

### `start_research_project`

**Parameters:** `project_id` (str)

🟢 **Description:** Start an R&D project. Cost deducted immediately. Provides permanent quality boost + temporary decay reduction on completion.

🔴 **Internal:** duration = Normal(expected_days, expected_days * 0.2). 40 projects in dependency DAG, up to depth 5. Quality boost range: 0.01-0.12.

---

### `list_research_projects`

**Parameters:** None

🟢 **Returns:** All projects by status: available, in-progress, completed, locked. Shows costs, durations, boosts, prerequisites.

---

## Simulation Control

### `next_day`

**Parameters:** None

🟢 **What happens (sequence):**
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
14. Dashboard built and returned (includes Equity & Funding section)

---

## Help & Documentation

### `describe_tables`

**Parameters:** `table_names: list[str]` or None for all

🟢 **Available tables:** customers, subscriptions, daily_usage, ledger, service_day, config_history, social_media_posts, enterprise_turns, notifications, shareholders, funding_rounds, vc_turns, dividends, research_projects, ad_channel_leads, group_info_levels, issues

---

### `get_tool_documentation`

**Parameters:** `tool_names: str | list[str] | None`

🟢 **Available tools (34 total):** set_prices, set_model_tiers, set_daily_spend, set_ad_channel_spend, set_targeted_ad_spend, set_targeted_ops_spend, set_targeted_dev_spend, set_capacity_tier, set_usage_quotas, send_enterprise_deal, python_exec, register_daily_calculation, remove_daily_calculation, list_daily_calculations, get_social_posts, expand_notification, get_cost_info, get_tool_documentation, describe_tables, next_day, list_potential_vcs, send_vc_deal, reject_vc_deal, reject_enterprise_deal, get_cap_table_info, settle_investments, declare_dividend, research_market, research_group, get_market_overview, get_group_insights, start_research_project, list_research_projects

---

## Agent Memory (MCP-only)

### `memory_insert` / `memory_delete` / `memory_edit`

**Parameters:** `line`+`content` / `start`+`end` / `line`+`content`

> Only available to MCP agent (Claude Code), not baseline agent. Schema defined in `get_mcp_tool_definitions()`.

---

# Part 2 — Table Documentation

## 🟢 Agent-Visible Tables

### `customers`

| Column | Type | 🟢/🔴 | Description |
|--------|------|--------|-------------|
| customer_id | INTEGER PK | 🟢 | Unique customer identifier |
| customer_type | TEXT | 🟢 | 'small' or 'large' (enterprise) |
| group_id | TEXT | 🟢 | Segment: S1-S3, E1-E3, D_S01-D_S10, D_E01-D_E10 |
| email | TEXT | 🟢 | |
| seat_count | INTEGER | 🟢 | Enterprise only |
| acquisition_source | TEXT | 🟢 | How they found us |
| signup_day | INTEGER | 🟢 | |
| steepness_left | REAL | 🔴 | Satisfaction curve parameter |
| steepness_right | REAL | 🔴 | Satisfaction curve parameter |
| c_max | REAL | 🔴 | Satisfaction curve parameter |
| usage_demand | REAL | 🔴 | Latent preference |
| expected_quality | REAL | 🔴 | Latent preference |
| quality_sensitivity | REAL | 🔴 | Latent preference |
| price_sensitivity | REAL | 🔴 | Latent preference |
| willingness_to_pay | REAL | 🔴 | Max monthly budget |
| usage_scale | REAL | 🔴 | Usage multiplier |
| patience | REAL | 🔴 | Tolerance for issues |
| reply_delay_mean | REAL | 🔴 | Enterprise negotiation timing |
| reply_delay_std | REAL | 🔴 | Enterprise negotiation timing |
| negotiation_rate | REAL | 🔴 | |
| max_negotiation_turns | INTEGER | 🔴 | |
| initial_offer_factor | REAL | 🔴 | |
| persona_communication | TEXT | 🔴 | LLM prompt attribute |

---

### `subscriptions`

| Column | Type | 🟢/🔴 | Description |
|--------|------|--------|-------------|
| subscription_id | INTEGER PK | 🟢 | |
| customer_id | INTEGER FK | 🟢 | |
| plan | TEXT | 🟢 | 'A', 'B', 'C' |
| listed_price | REAL | 🟢 | List price per seat (before promotions; enterprise may have negotiated price) |
| promotion | REAL | 🟢 | Total promotion $ currently applied |
| effective_price | REAL | 🟢 | Actual price = listed_price - promotion (floored at 0) |
| contract_months | INTEGER | 🟢 | |
| start_day | INTEGER | 🟢 | |
| end_day | INTEGER | 🟢 | NULL = active |
| status | TEXT | 🟢 | 'subscribed' or 'cancelled' |
| billing_day_mod30 | INTEGER | 🟢 | |
| billing_period_usage | REAL | 🔴 | |
| daily_usage_rate | REAL | 🔴 | Agent sees actual usage via daily_usage table |

---

### `enterprise_turns` ⭐ REFACTORED

| Column | Type | 🟢/🔴 | Description |
|--------|------|--------|-------------|
| turn_id | INTEGER PK | 🟢 | Internal turn identifier |
| thread_id | INTEGER | 🟢 | Groups turns in same negotiation (internal grouping) |
| customer_id | INTEGER FK | 🟢 | |
| thread_type | TEXT | 🟢 | 'new_lead', 'plan_change', 'budget_freeze', 'churn_prevention', 'renegotiation', 'renewal', 'general' |
| turn_number | INTEGER | 🟢 | 0-indexed within thread |
| sender | TEXT | 🟢 | 'customer', 'agent', 'system' |
| message_text | TEXT | 🟢 | Nullable |
| offer_json | TEXT | 🟢 | JSON structured offer data |
| day | INTEGER | 🟢 | Simulation day |
| email | TEXT | 🟢 | |
| **closed** | INTEGER | 🟢 | **0=open, 1=terminal** (replaces old `status` column) |
| **close_reason** | TEXT | 🟢 | **NULL while open; 'accepted', 'agent_rejected', 'timeout', 'ghosted', 'lost' when closed** |
| next_reply_day | INTEGER | 🔴 | Day when customer will reply |
| current_offer_price | REAL | 🔴 | Internal tracking |

**Enterprise close_reason lifecycle:**
```
NULL (open) → 'accepted'        (customer accepts offer)
           → 'agent_rejected'   (agent explicitly rejects)
           → 'timeout'          (max turns reached)
           → 'ghosted'          (customer stops responding)
           → 'lost'             (new_lead rejected → permanently lost)
```

---

### `vc_turns` ⭐ REFACTORED

| Column | Type | 🟢/🔴 | Description |
|--------|------|--------|-------------|
| turn_id | INTEGER PK | 🟢 | Internal turn identifier |
| thread_id | INTEGER | 🟢 | Groups turns (internal grouping) |
| shareholder_id | INTEGER FK | 🟢 | → shareholders table |
| turn_number | INTEGER | 🟢 | 0-indexed |
| sender | TEXT | 🟢 | 'vc', 'agent', 'system' |
| message_text | TEXT | 🟢 | Nullable |
| offer_json | TEXT | 🟢 | JSON: {share_pct, amount, price_per_share, ...} |
| day | INTEGER | 🟢 | |
| expiry_day | INTEGER | 🟢 | Deadline to settle accepted deal |
| **closed** | INTEGER | 🟢 | **0=open, 1=terminal** (replaces old `status` column) |
| **close_reason** | TEXT | 🟢 | **NULL → 'accepted' → 'settled' (or 'agent_rejected', 'timeout', 'expired')** |
| current_offer_share_pct | REAL | 🟢 | Current equity % being discussed |
| current_offer_amount | REAL | 🟢 | Current investment $ amount |
| has_anti_dilution | INTEGER | 🟢 | Term sheet flag (0/1) |
| has_milestone_tranching | INTEGER | 🟢 | Term sheet flag (0/1) |
| has_redemption_rights | INTEGER | 🟢 | Term sheet flag (0/1) |
| anti_dilution_floor | REAL | 🟢 | Chosen option value |
| milestone_tranche_pct | REAL | 🟢 | Chosen option value |
| milestone_revenue_multiplier | REAL | 🟢 | Chosen option value |
| milestone_deadline_days_chosen | INTEGER | 🟢 | Chosen option value |
| redemption_days_chosen | INTEGER | 🟢 | Chosen option value |
| redemption_buyback_multiplier | REAL | 🟢 | Chosen option value |
| milestone_revenue_target | REAL | 🟢 | Computed target |
| milestone_deadline_day | INTEGER | 🟢 | Computed deadline |
| tranche_1_amount | REAL | 🟢 | |
| tranche_2_amount | REAL | 🟢 | |
| next_reply_day | INTEGER | 🔴 | When VC will reply |
| original_valuation | REAL | 🔴 | |
| anti_dilution_triggered | INTEGER | 🔴 | |
| tranche_2_released | INTEGER | 🔴 | |

**VC close_reason lifecycle:**
```
NULL (open) → 'accepted'        (VC accepts offer)
                → 'settled'     (settle_investments() called — shares issued)
                → 'expired'     (not settled before expiry_day)
           → 'agent_rejected'   (agent explicitly rejects)
           → 'timeout'          (no response / stale)
           → 'expired'          (deal expires)
```

---

### Other 🟢 Visible Tables

#### `daily_usage`
| Column | Type | Description |
|--------|------|-------------|
| day | INTEGER | Simulation day |
| customer_id | INTEGER FK | |
| usage_units | REAL | Actual (quota-capped) usage |

#### `ledger`
| Column | Type | Description |
|--------|------|-------------|
| day | INTEGER | |
| category | TEXT | 'subscription_payment', 'advertising_cost', 'operations_cost', 'development_cost', 'capacity_cost', 'compute_cost', 'research_cost', 'vc_investment', 'dividend_payment', etc. |
| amount | REAL | Positive = income, negative = cost |
| description | TEXT | Human-readable |

#### `service_day`
| Column | Type | Description |
|--------|------|-------------|
| day | INTEGER | |
| total_usage_units | REAL | |
| capacity_units | REAL | |
| p95_ms | REAL | P95 latency in milliseconds |
| error_rate | REAL | |
| downtime_minutes | REAL | |

#### `config_history`
Daily snapshot of all agent-configurable settings (prices, tiers, spend, quotas, etc.).

#### `social_media_posts`
| Column | Type | 🟢/🔴 | Description |
|--------|------|--------|-------------|
| day | INTEGER | 🟢 | |
| customer_id | INTEGER | 🟢 | |
| content | TEXT | 🟢 | Post text |
| likes | INTEGER | 🟢 | |
| shares | INTEGER | 🟢 | |
| virality_score | REAL | 🟢 | |
| sentiment | TEXT | 🔴 | HIDDEN — agent must infer from content |
| reputation_impact | REAL | 🔴 | |
| influence_score | REAL | 🔴 | |

#### `notifications`
| Column | Type | Description |
|--------|------|-------------|
| notification_id | INTEGER PK | |
| day | INTEGER | |
| type | TEXT | 'social_media_post', 'large_customer_message', 'service_alert', 'financial_alert', 'cancellation' |
| title | TEXT | |
| summary | TEXT | |
| details_json | TEXT | |
| reference_id | INTEGER | Related entity ID |
| reference_type | TEXT | 'thread', 'post', 'event' |

#### `shareholders`
| Column | Type | 🟢/🔴 | Description |
|--------|------|--------|-------------|
| shareholder_id | INTEGER PK | 🟢 | |
| name | TEXT | 🟢 | |
| shareholder_type | TEXT | 🟢 | 'founder' or 'vc' |
| shares_held | INTEGER | 🟢 | |
| investment_min | REAL | 🟢 | VC check range min |
| investment_max | REAL | 🟢 | VC check range max |
| vc_alpha | REAL | 🔴 | Internal VC parameter |
| turns_this_year | INTEGER | 🔴 | |
| year_start_day | INTEGER | 🔴 | |

#### `funding_rounds`
| Column | Type | 🟢/🔴 | Description |
|--------|------|--------|-------------|
| day | INTEGER | 🟢 | |
| investor_shareholder_id | INTEGER FK | 🟢 | |
| shares_issued | INTEGER | 🟢 | |
| price_per_share | REAL | 🟢 | |
| total_amount | REAL | 🟢 | |
| pre_money_valuation | REAL | 🔴 | |
| post_money_valuation | REAL | 🔴 | |

#### `dividends`
| Column | Type | Description |
|--------|------|-------------|
| dividend_id | INTEGER PK | |
| day | INTEGER | |
| total_amount | REAL | Total declared |
| per_share_amount | REAL | |
| total_shares_at_time | REAL | Snapshot |
| founder_payout | REAL | Founder's share |

#### `research_projects`
| Column | Type | 🟢/🔴 | Description |
|--------|------|--------|-------------|
| project_id | TEXT PK | 🟢 | |
| status | TEXT | 🟢 | 'available', 'in_progress', 'completed' |
| cost | REAL | 🟢 | |
| quality_boost | REAL | 🟢 | |
| decay_reduction | REAL | 🟢 | |
| actual_completion_day | INTEGER | 🔴 | Hidden for non-completed projects |

#### `ad_channel_leads`
| Column | Type | Description |
|--------|------|-------------|
| day | INTEGER | |
| channel | TEXT | |
| group_id | TEXT | |
| leads_generated | INTEGER | |
| spend | REAL | |

#### `group_info_levels`
| Column | Type | Description |
|--------|------|-------------|
| group_id | TEXT | |
| info_level | INTEGER | 0-4 |
| group_name | TEXT | |
| segment_type | TEXT | 'individual' or 'enterprise' |

#### `issues`
| Column | Type | Description |
|--------|------|-------------|
| issue_id | INTEGER PK | |
| customer_id | INTEGER FK | |
| group_id | TEXT | |
| open_day | INTEGER | |
| days_open | INTEGER | |
| status | TEXT | 'open' or 'resolved' |
| resolved_day | INTEGER | NULL if still open |
| resolution_type | TEXT | 'ops_resolved' |

---

## 🔴 Hidden Tables (agent cannot query at all)

| Table | Purpose |
|-------|---------|
| events | Internal shock/event tracking |
| api_costs | Meta-simulation API cost tracking |
| customer_state | Internal satisfaction, relationship, open_issue_days |
| group_reputation | Internal reputation per group |
| group_awareness | Internal awareness per group |
| reputation_history | Internal reputation change history |
| global_state | Internal simulation state |
| feature_tests | Internal A/B test tracking |
| test_assignments | Internal test assignments |
| customer_personas | Internal persona templates |
| customer_persona_map | Internal persona mapping |
| group_characteristics | Internal group characteristics |
| enterprise_thread_counter | Auto-increment counter for thread IDs |
| vc_thread_counter | Auto-increment counter for thread IDs |
| world_context | Internal world context |
| pending_group_research | Internal async research queue |
| group_parameters | Internal preference drift tracking (agent must infer from behavior) |

---

## 🔴 Global Hidden Columns (stripped from ALL query results)

```
sentiment, reputation_impact, influence_score,
steepness_left, steepness_right, c_max,
usage_demand, expected_quality, quality_sensitivity, price_sensitivity,
willingness_to_pay, usage_scale, patience,
reply_delay_mean, reply_delay_std, negotiation_rate, max_negotiation_turns,
next_reply_day, vc_alpha, turns_this_year, year_start_day,
original_valuation, anti_dilution_triggered, tranche_2_released,
current_offer_price, pre_money_valuation, post_money_valuation,
daily_usage_rate, billing_period_usage,
satisfaction, relationship, open_issue_days,
current_steepness_left, current_steepness_right, current_c_max, current_slope,
last_drift_day, plan_was_acceptable, last_quality, last_satisfaction, shock_event_id,
reputation, awareness, last_updated_day, last_marketing_day,
change_reason, actual_completion_day, initial_offer_factor, persona_communication
```

---

# Part 3 — Refactoring Changelog

## Tool Renames

| Old Name | New Name | Change |
|----------|----------|--------|
| `send_reply` | `send_enterprise_deal` | List-based, `customer_id` only (V2) |
| `propose_vc_terms` | `send_vc_deal` | List-based with `shareholder_id` (V2) |
| `initiate_enterprise_negotiation` | _(merged into `send_enterprise_deal`)_ | Use `customer_id` in deals list |

## API Changes

| Tool | Before | After |
|------|--------|-------|
| All deal tools | Single item OR batch param | Always `deals: [{...}]` — single = list of 1 |
| Enterprise addressing | `message_id` or `thread_id` | `customer_id` only — system auto-resolves thread |
| VC addressing | `message_id` | `shareholder_id` only — system auto-resolves thread |
| `settle_investments` | `deal_ids: [1, 3]` | **No params** — auto-settles all accepted, auto-rejects all open |
| `get_tool_descriptions()` | Hand-written 500-line function | Auto-derived from TOOL_DOCS (single source of truth) |
| `strategy_tips` | Included in tool docs | Removed entirely from all tool documentation |

## Schema Changes

| Table | Before | After |
|-------|--------|-------|
| enterprise_turns | `status TEXT` | `closed INTEGER DEFAULT 0` + `close_reason TEXT` |
| vc_turns | `status TEXT` | `closed INTEGER DEFAULT 0` + `close_reason TEXT` |

## Files Modified (13 total)

`database.py`, `enterprise.py`, `vc_negotiation.py`, `simulation.py`, `tools.py`, `environment.py`, `shocks.py`, `benchmark.py`, `tool_docs.json`, `simulator_instructions.md`, `run_test.py`, `mcp_server.py`, `serve_mcp.py`
