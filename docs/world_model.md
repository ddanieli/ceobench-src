# SaaS Bench: Structured World Model

This document describes the simulation as a formal model with explicit properties, their domains, update rules, and interactions.

---

# Part I: Company Properties

The company has global state that persists across the simulation.

## 1.1 Financial Properties

| Property | Symbol | Domain | Initial Value | Persistence |
|----------|--------|--------|---------------|-------------|
| Cash | `C` | R (can go negative) | $100,000 | Across days |
| Monthly Recurring Revenue | `MRR` | R >= 0 | $0 | Computed daily |

### Cash Update Rule
```
C(t+1) = C(t) + Revenue(t) - Costs(t)

Revenue(t) = sum of subscription payments on day t
Costs(t) = CapacityCost + ComputeCost + AdvertisingSpend + OperationsSpend + DevelopmentSpend
```

### MRR Computation
```
MRR = sum(effective_price) for all subscriptions where status = 'subscribed'
```

---

## 1.2 Configuration Properties (Agent-Controlled)

| Property | Symbol | Domain | Initial Value | When Applied |
|----------|--------|--------|---------------|--------------|
| Price Plan A | `P_A` | R > 0 | $29 | New signups immediate |
| Price Plan B | `P_B` | R > 0 | $79 | New signups immediate |
| Price Plan C | `P_C` | R > 0 | $199 | New signups immediate |
| Model Tier A | `T_A` | {1,2,3,4,5} | 2 | Immediate |
| Model Tier B | `T_B` | {1,2,3,4,5} | 3 | Immediate |
| Model Tier C | `T_C` | {1,2,3,4,5} | 4 | Immediate |
| Capacity Tier | `K` | {0,1,2,3} | 1 | Immediate |
| Advertising Spend | `S_ad` | R >= 0 | $500/day | Daily deduction |
| Operations Spend | `S_ops` | R >= 0 | $1000/day | Daily deduction |
| Development Spend | `S_dev` | R >= 0 | $500/day | Daily deduction |

---

## 1.3 Infrastructure Properties

| Property | Symbol | Domain | Initial Value | Update Trigger |
|----------|--------|--------|---------------|----------------|
| Capacity Units | `CAP` | {30k, 90k, 240k, 600k} | 90,000 | When K changes |
| Capacity Cost/Day | `COST_cap` | {100, 250, 600, 1500} | $250 | When K changes |

### Capacity Tier Mapping

Reality-matched to 2025 cloud infrastructure costs:
- Tier 0: Serverless/auto-scale startup (~$3K/mo) [CloudZero 2025: serverless saves 70%]
- Tier 1: Small dedicated cluster (~$7.5K/mo) [AWS EC2 benchmarks]
- Tier 2: Medium infrastructure (~$18K/mo) [CloudZero 2025]
- Tier 3: Large-scale dedicated (~$45K/mo) [Enterprise cloud benchmarks]

```
K=0: CAP=30,000,  COST_cap=$100/day  ($3K/mo)
K=1: CAP=90,000,  COST_cap=$250/day  ($7.5K/mo)
K=2: CAP=240,000, COST_cap=$600/day  ($18K/mo)
K=3: CAP=600,000, COST_cap=$1,500/day ($45K/mo)
```

---

## 1.4 Quality Properties (Hidden from Agent)

| Property | Symbol | Domain | Initial Value | Update |
|----------|--------|--------|---------------|--------|
| Robustness | `R` | [0, 1] | 0.1 | Daily (ops spending) |
| Ease | `E` | [0, 1] | 0.1 | Daily (dev spending) |
| Dev Quality Bonus | `q_shared` | [0, 0.1] | 0.0 | Daily (dev spending) |
| Reputation | `REP` | [0, 1] | 0.5 | On quality cancels, daily recovery |

### Robustness Update Rule
```
R(t+1) = clamp(1 - (1-R(t)) * exp(-k_r * S_ops) + noise, 0, 1)

k_r = 0.0002
noise ~ N(0, 0.01)
```

### Ease Update Rule

**Reality-matched to software engineering productivity research:**
- McKinsey 2024: Companies investing 15%+ of revenue in R&D see 20% quality gains over 2 years
- Stripe 2023: Engineering velocity correlates with product quality at r=0.7
- DORA 2024: Elite performers invest 2-3x more in developer experience

```
E(t+1) = clamp(1 - (1-E(t)) * exp(-k_e * S_dev) + noise, 0, 1)

k_e = 0.0005  # 3x faster than baseline - reflects compounding dev investment returns
noise ~ N(0, 0.01)
```

### Dev Quality Bonus Update Rule

**Reality-matched to AI product quality research:**
- Gartner 2025: Sustained AI R&D investment yields 0.5-1% monthly quality improvements
- Google AI 2024: Model fine-tuning shows 10-15% quality gains with focused investment

```
q_shared(t+1) = clamp(q_shared(t) + 0.001 * log(1 + S_dev/1000) + noise, 0, 0.1)

noise ~ N(0, 0.001)  # Tighter variance for more predictable quality improvements
```

### Reputation Update Rule
```
On quality-related cancellation:
  damage = 0.02 * U(0.5, 1.5)
  REP = clamp(REP - damage, 0, 1)

Daily recovery (if REP < 0.5):
  recovery = 0.005 * U(0.8, 1.2)
  REP = clamp(REP + recovery, 0, 0.5)
```

---

## 1.5 Cost Properties

| Property | Symbol | Domain | Initial Value | Update Trigger |
|----------|--------|--------|---------------|----------------|
| Compute Cost Multiplier | `M_compute` | R >= 1 | 1.0 | Compute price shock (permanent) |

### Model Tier Cost Table
```
Tier 1: $0.01/unit * M_compute
Tier 2: $0.03/unit * M_compute
Tier 3: $0.06/unit * M_compute
Tier 4: $0.12/unit * M_compute
Tier 5: $0.24/unit * M_compute
```

### Model Tier Quality Table
```
Tier 1: base_quality = 0.55
Tier 2: base_quality = 0.65
Tier 3: base_quality = 0.75
Tier 4: base_quality = 0.85
Tier 5: base_quality = 0.92
```

---

## 1.6 Service Properties (Computed Daily)

| Property | Symbol | Domain | Computation |
|----------|--------|--------|-------------|
| Total Usage | `U_total` | Z >= 0 | Sum of all customer usage |
| Overload | `OVL` | R >= 0 | max(0, U_total/CAP - 1) |
| Outage | `OUT` | {0, 1} | Bernoulli(p_outage) |
| Downtime | `DT` | {0, 10, 30, 90} min | Conditional on OUT |
| P95 Latency | `LAT` | R > 0 | 600 + 1500*OVL + noise |
| Error Rate | `ERR` | [0, 1] | 0.004 + 0.03*OVL + noise |

### Outage Probability
```
p_outage = 0.008 * (1 + 4*OVL) * (1 - 0.6*R)
```

### Downtime Distribution (given outage)
```
DT = 10 min  with p=0.50
DT = 30 min  with p=0.35
DT = 90 min  with p=0.15
```

---

# Part II: Customer Properties

Each customer `i` has individual properties.

## 2.1 Customer Type

| Property | Symbol | Domain | When Set |
|----------|--------|--------|----------|
| Customer Type | `type_i` | {small, large} | Creation |

---

## 2.2 Customer Trait Properties (Fixed at Creation)

| Property | Symbol | Domain | Small Distribution | Large Distribution |
|----------|--------|--------|-------------------|-------------------|
| Quality Sensitivity | `a_i` | [0.1, 1] | N(0.6, 0.15) | N(0.7, 0.1) |
| Price Sensitivity | `b_i` | [0.1, 1] | N(0.5, 0.2) | N(0.4, 0.15) |
| Willingness to Pay | `W_i` | R > 0 | N(100, 50) | N(500, 200)/seat |
| Usage Scale | `u_i` | R > 0 | N(50, 30) | N(30, 15)/seat |
| Patience | `pat_i` | [0.1, 1] | N(0.5, 0.15) | N(0.6, 0.1) |
| Seat Count | `seats_i` | Z > 0 | 1 | U(20, 500) |
| Counterparty Risk | `cr_i` | [0, 0.5] | 0 | N(0.1, 0.08) |

---

## 2.3 Customer State Properties (Dynamic)

| Property | Symbol | Domain | Initial Value | Update |
|----------|--------|--------|---------------|--------|
| Satisfaction | `S_i` | [0, 1] | 0.5 | Daily EMA |
| Open Issue Days | `I_i` | Z >= 0 | 0 | Daily |

### Satisfaction Update Rule
```
S_i(t+1) = clamp(0.9 * S_i(t) + 0.1 * (q_shared - penalties), 0, 1)

penalties = 0.08*OVL + 0.15*OUT + 0.05*I_i
```

---

## 2.4 Subscription Properties

| Property | Symbol | Domain | When Set |
|----------|--------|--------|----------|
| Plan | `plan_i` | {A, B, C} | Signup/switch |
| Monthly Price | `price_i` | R > 0 | Signup/switch |
| Status | `status_i` | {trial, subscribed, cancelled} | State changes |
| Start Day | `start_i` | Z >= 0 | Creation |
| Billing Day | `bill_i` | {0..29} | start_i mod 30 |
| End Day | `end_i` | Z or NULL | Cancellation |

---

## 2.5 Derived Customer Properties

| Property | Symbol | Computation |
|----------|--------|-------------|
| Delivered Quality | `Q_i` | base_quality(T_plan) + q_shared + Q_test - 0.08*OVL - 0.2*OUT |
| Value Gap | `V_i` | a_i * S_i - b_i * (price_i / W_i) |
| Daily Usage | `usage_i` | Poisson(plan_weight * u_i * seats_i) |
| Tenure | `tenure_i` | current_day - start_i |

### Plan Usage Weights
```
Plan A: weight = 1
Plan B: weight = 2
Plan C: weight = 4
```

---

# Part III: Company Property Interactions

How company properties affect other company properties.

## 3.1 Spending → Quality Properties

**Reality-matched to SaaS support and engineering research:**

### Operations Spending Impact

Operations spending affects support capacity and customer relationship quality.

**Issue Generation Rate (customer support tickets):**
- Notion 2024: <2% MAU ticket rate with excellent in-app help
- Superhuman 2024: <1% ticket rate with hyper-polished product
- Pendo 2024: Products with in-app guides see 60-70% fewer support requests

```
base_issue_rate = 0.002  # 0.2% daily - hyper-polished UX with proactive help
issue_quality_factor = 0.06  # Exceptional docs and self-service
issue_outage_factor = 0.10  # Outages cause 10% ticket surge
```

**Issue Resolution:**
- Totango 2024: Fast support response (<24h) correlates with 30% higher NPS
- Gainsight 2024: Companies with exceptional CS teams see 30-40% lower churn
- Zendesk 2024: Same-day resolution increases CSAT by 35%, retention by 30%
- HubSpot 2024: Customers with great support are 3x more likely to renew

```
S_ops ──────► Mean issues resolved/day (scales: 2 + 0.053 × spend)
             └─► Relationship boost for quick resolution (≤2 days): +0.30 to +0.40
             └─► Relationship DECAY for unresolved issues: -0.01 per day
             └─► relationship_quality_bonus_max = 0.45 (exceptional support drives strong loyalty)
```

**Relationship Dynamics:** Unresolved issues decay relationship by 0.01/day (loyal customers of excellent products are patient). After 5 days: -0.05, after 10 days: -0.10. Quick resolution provides large boost (+0.30-0.40), making ops investment highly profitable!

### Development Spending Impact

- a16z 2024: Top quartile engineering teams ship 2x faster with same quality
- McKinsey 2024: Companies investing 15%+ of revenue in R&D see 20-30% quality gains

```
S_dev ──────► E (ease) - asymptotic growth, k=0.0015 (high-velocity team)
             └─► q_shared (quality bonus) - logarithmic growth, max 0.10
```

| Source | Target | Relationship | Lag |
|--------|--------|--------------|-----|
| S_ops | mean_issues_resolved | Linear: 1 + 0.01 × spend (count, not rate) | Same day |
| S_ops | relationship | +0.05-0.10 for quick resolution | Same day |
| S_dev | E | Asymptotic growth (k=0.0005) | Same day |
| S_dev | q_shared | Logarithmic growth | Same day |

---

## 3.2 Configuration → Service Properties

```
K (capacity) ──────► CAP ──────► OVL (overload)
                                    │
T_plan (model tier) ────────────────┼──► q_shared
                                    │
                                    └──► p_outage ──► OUT
```

| Source | Target | Relationship |
|--------|--------|--------------|
| K | CAP | Direct mapping |
| CAP | OVL | OVL = max(0, U_total/CAP - 1) |
| OVL | p_outage | Linear increase |
| R | p_outage | Linear decrease |
| T_plan | Q_base | Direct mapping |

---

## 3.3 Configuration → Cost Properties

```
K ──────► COST_cap (daily)

T_plan ──► unit_cost ──┐
                       ├──► COST_compute = sum(usage_i * unit_cost * M_compute)
usage_i ───────────────┘

S_ad + S_ops + S_dev ──► COST_spend
```

---

## 3.4 Reputation Feedback Loop

```
Quality cancellations ──(-)-► REP ──(+)-► Advertising effectiveness
                                          │
                              ▲           ▼
                              └───────── New trials
```

---

# Part IV: Customer Property Interactions

How customer properties affect other customer properties.

## 4.1 Trait → Behavior Interactions

```
a_i (quality sensitivity) ──────► Weight of S_i in V_i
                                  └─► Cancel sensitivity to quality drops

b_i (price sensitivity) ────────► Weight of price in V_i
                                  └─► Cancel sensitivity to price increases

W_i (willingness to pay) ──────► Price normalization in V_i

u_i (usage scale) ─────────────► Daily usage generation

pat_i (patience) ───────────────► Issue tolerance (future use)
```

---

## 4.2 State → Behavior Interactions

```
S_i (satisfaction) ──────► V_i (value gap) ──────► p_cancel
                                                   p_convert
                                                   p_switch

I_i (open issues) ───────► Satisfaction penalty
                           └─► Cancel probability boost
```

---

## 4.3 Subscription → State Interactions

```
plan_i ──────► T_plan lookup ──────► Q_base ──────► q_shared ──────► S_i update

price_i ─────► V_i calculation

tenure_i ────► Stickiness multiplier on p_cancel
```

### Tenure-Based Stickiness
```
tenure < 30 days:  multiplier = 1.0
tenure 30-90:      multiplier = 0.8
tenure 90-180:     multiplier = 0.6
tenure >= 180:     multiplier = 0.4
```

---

# Part V: Company ↔ Customer Interactions

Cross-domain interactions between company and customer properties.

## 5.1 Company → Customer Effects

### Configuration → Customer State

| Company Property | Customer Property | Effect |
|-----------------|-------------------|--------|
| T_plan | q_shared_i | Higher tier → higher quality |
| P_plan | V_i | Higher price → lower value gap |
| OVL | S_i | Overload → satisfaction penalty |
| OUT | S_i | Outage → large satisfaction penalty |
| S_ops | I_i | More ops → faster issue resolution |

### Configuration → Customer Acquisition

| Company Property | Effect on Acquisition |
|-----------------|----------------------|
| S_ad | More advertising → more trials (log relationship) |
| REP | Higher reputation → more effective advertising |
| MRR (via active subs) | More subscribers → more word-of-mouth |
| avg(S_i) | Higher avg satisfaction → more word-of-mouth |

---

## 5.2 Customer → Company Effects

### Customer State → Company Financials

| Customer Property | Company Property | Effect |
|-------------------|------------------|--------|
| status_i = subscribed | C | +price_i on billing day |
| status_i → cancelled | MRR | -price_i |
| usage_i | C | -unit_cost * usage_i * M_compute |

### Customer State → Company Quality

| Customer Property | Company Property | Effect |
|-------------------|------------------|--------|
| S_i < 0.4 on cancel | REP | Reputation damage |
| sum(usage_i) | OVL | Higher total usage → overload |

---

## 5.3 Interaction Flow Diagram

```
                    COMPANY                                    CUSTOMER
    ┌─────────────────────────────────────┐      ┌─────────────────────────────────┐
    │                                     │      │                                 │
    │  Configuration                      │      │  Traits (fixed)                 │
    │  ├─ Prices (P_A, P_B, P_C)         │      │  ├─ a_i (quality sensitivity)   │
    │  ├─ Tiers (T_A, T_B, T_C)     ─────┼──────┼──► q_shared_i                │
    │  ├─ Capacity (K)              ─────┼──────┼──► OVL → S_i penalty            │
    │  └─ Spending (S_ad, S_ops, S_dev)  │      │  ├─ b_i (price sensitivity)     │
    │                                     │      │  └─ W_i, u_i, pat_i            │
    │  Quality State                      │      │                                 │
    │  ├─ E (ease)                        │      │                                 │
    │  ├─ q_shared                   ─────┼──────┼──► q_shared per plan            │
    │  └─ REP (reputation)          ─────┼──────┼──► Trial generation rate        │
    │                                     │      │                                 │
    │  Service State                      │      │  Dynamic State                  │
    │  ├─ U_total                   ◄────┼──────┼── sum(usage_i)                  │
    │  ├─ OVL, OUT                        │      │  ├─ S_i (satisfaction)          │
    │  └─ LAT, ERR                        │      │  ├─ I_i (open issues)           │
    │                                     │      │  └─ V_i (value gap)             │
    │  Financial State                    │      │                                 │
    │  ├─ C (cash)                  ◄────┼──────┼── Subscription payments         │
    │  └─ MRR                       ◄────┼──────┼── Active subscriptions          │
    │                                     │      │                                 │
    │  REP                          ◄────┼──────┼── Quality-related cancels       │
    │                                     │      │                                 │
    └─────────────────────────────────────┘      └─────────────────────────────────┘
```

---

# Part VI: Agent Loop

## 6.1 Daily Loop Structure

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ DAY t                                                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  1. SHOCK GENERATION                                                            │
│     └─ Random events may modify company properties                              │
│                                                                                 │
│  2. AGENT OBSERVATION                                                           │
│     └─ Agent receives: day, cash, MRR, config, service metrics, inbox          │
│                                                                                 │
│  3. AGENT ACTION LOOP (multi-turn)                                              │
│     ├─ Agent takes actions (modify config, communicate, analyze)                │
│     ├─ Agent receives tool results                                              │
│     └─ Loop until agent calls next_day()                                        │
│                                                                                 │
│  4. SIMULATION STEP (after next_day)                                            │
│     ├─ Compute usage: U_total = sum(usage_i)                                    │
│     ├─ Compute service: OVL, OUT, DT, LAT, ERR                                 │
│     ├─ Update global state: R, E, q_shared                                         │
│     ├─ Update customer satisfaction: S_i for all                                │
│     ├─ Process issues: generate new, resolve existing                           │
│     ├─ Process trials: convert or expire                                        │
│     ├─ Process cancellations: churn subscribers                                 │
│     ├─ Update reputation: damage + recovery                                     │
│     ├─ Process plan switches: upgrades/downgrades                               │
│     ├─ Generate new trials: from ads + word-of-mouth                            │
│     ├─ Process billing: collect payments                                        │
│     └─ Process costs: deduct all costs                                          │
│                                                                                 │
│  5. CHECK TERMINAL CONDITIONS                                                   │
│     ├─ If C < 0: GAME OVER                                                      │
│     └─ If day = 365: END, compute score                                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 6.2 Agent Observation Structure

```python
observation = {
    # Time
    "day": int,                    # Current day [1, 365]

    # Financial (Company)
    "cash": float,                 # C
    "mrr": float,                  # MRR

    # Service (Company, computed)
    "active_subscribers": int,     # Count of status='subscribed'
    "total_usage": int,            # U_total
    "overload": float,             # OVL
    "outage": bool,                # OUT
    "downtime_minutes": int,       # DT

    # Flow metrics (today)
    "new_trials": int,
    "conversions": int,
    "cancellations": int,
    "upgrades": int,
    "downgrades": int,

    # Current config
    "config": {
        "price_A": float, "price_B": float, "price_C": float,
        "tier_A": int, "tier_B": int, "tier_C": int,
        "spend_advertising": float,
        "spend_operations": float,
        "spend_development": float,
        "capacity_tier": int
    },

    # Notifications
    "inbox": [
        {"type": str, "message": str, ...}
    ]
}
```

---

## 6.3 Agent Memory

Agent has persistent memory displayed in system prompt:

```
=== YOUR MEMORY (edit with memory_insert/delete/edit) ===
  1| [line 1 content]
  2| [line 2 content]
  ...
```

Memory persists across days within a run. Agent must use memory tools to update.

---

# Part VII: Agent Actions

## 7.1 Action Categories

| Category | Actions | Purpose |
|----------|---------|---------|
| Pricing | set_prices | Control revenue per customer |
| Quality | set_model_tiers | Control delivered quality |
| Capacity | set_capacity_tier | Control max usage before overload |
| Investment | set_daily_spend | Control growth, reliability, quality |
| Communication | read_thread, send_reply, post_update | Manage large customers |
| Analysis | python_exec, get_cost_info | Query state |
| Memory | memory_insert, memory_delete, memory_edit | Persist learnings |
| Control | next_day | End turn |

---

## 7.2 Action Definitions

### set_prices(A, B, C)
```
Input: P_A, P_B, P_C in R > 0
Effect: Updates config.price_A/B/C
Timing: Immediate for new signups; existing subscribers keep old price until billing
```

### set_model_tiers(A, B, C)
```
Input: T_A, T_B, T_C in {1, 2, 3, 4, 5}
Effect: Updates config.tier_A/B/C
Timing: Immediate for all usage
```

### set_capacity_tier(tier)
```
Input: K in {0, 1, 2, 3}
Effect: Updates capacity tier
Timing: Immediate
```

### set_daily_spend(advertising, operations, development)
```
Input: S_ad, S_ops, S_dev in R >= 0
Effect: Updates daily spend config
Timing: Deducted daily starting today
```

### read_thread(thread_id)
```
Input: thread_id
Output: Last 5 messages, thread state, customer info
Effect: None (read-only)
```

### send_reply(thread_id, message_text, offer)
```
Input: thread_id, message text, optional structured offer
Effect: Adds message to thread; environment LLM generates customer response
```

### post_update(channel, text)
```
Input: channel in {status, pricing, release}, text
Effect: Posts public announcement (affects customer perception)
```

### python_exec(code)
```
Input: Python code string
Output: stdout from execution
Effect: None (read-only database access)
Available: conn (SQLite), pandas, numpy, sklearn
```

### get_cost_info()
```
Output: Current cost structure including M_compute
Effect: None (read-only)
```

### memory_insert(line, content)
```
Input: line number, content string
Effect: Inserts content at line, shifts others down
```

### memory_delete(start, end)
```
Input: start line, end line (inclusive)
Effect: Removes lines in range
```

### memory_edit(line, content)
```
Input: line number, new content
Effect: Replaces content at line
```

### next_day()
```
Input: None
Effect: Ends agent turn, triggers simulation step
```

---

# Part VIII: Action → Property Impact Matrix

## 8.1 Direct Impacts

| Action | Property Modified | Timing | Notes |
|--------|-------------------|--------|-------|
| set_prices | P_A, P_B, P_C | Immediate | Affects V_i for new signups |
| set_model_tiers | T_A, T_B, T_C | Immediate | Affects q_shared, compute cost |
| set_capacity_tier | K, CAP, COST_cap | Immediate | Affects OVL calculation |
| set_daily_spend | S_ad, S_ops, S_dev | Immediate | Deducted daily |
| send_reply | Thread state | Immediate | May affect large customer retention |
| memory_* | Agent memory | Immediate | No simulation effect |

---

## 8.2 Indirect Impacts (via Simulation)

### set_prices Impact Chain
```
P_plan ──► V_i ──┬─► p_convert (trials)
                 ├─► p_cancel (subscribers)
                 └─► p_switch (plan changes)
```

### set_model_tiers Impact Chain
```
T_plan ──► Q_base ──► q_shared ──► S_i ──► V_i ──► p_cancel, p_convert

T_plan ──► unit_cost ──► COST_compute ──► C
```

### set_capacity_tier Impact Chain
```
K ──► CAP ──► OVL ──┬─► S_i penalty
                    ├─► p_outage
                    └─► LAT, ERR
```

### set_daily_spend Impact Chains

**Advertising:**
```
S_ad ──► trial_rate ──► new customers ──► potential MRR growth
```

**Operations:**
```
S_ops ──► R ──► p_outage (reduced)
S_ops ──► p_resolve ──► I_i resolution ──► S_i improvement
```

**Development:**
```
S_dev ──► E (ease)
S_dev ──► q_shared ──► q_shared ──► S_i ──► retention
```

---

## 8.3 Full Impact Matrix

| Action | Cash | MRR | Satisfaction | Churn | Growth | Quality |
|--------|------|-----|--------------|-------|--------|---------|
| set_prices ↑ | +revenue | ±MRR | neutral | ↑churn | ↓signups | neutral |
| set_prices ↓ | -revenue | ±MRR | neutral | ↓churn | ↑signups | neutral |
| set_model_tiers ↑ | -cost | neutral | ↑ | ↓ | neutral | ↑ |
| set_model_tiers ↓ | +cost | neutral | ↓ | ↑ | neutral | ↓ |
| set_capacity ↑ | -cost | neutral | ↑ (if was overloaded) | ↓ | neutral | ↑ |
| set_capacity ↓ | +cost | neutral | ↓ (if becomes overloaded) | ↑ | neutral | ↓ |
| spend_advertising ↑ | -cost | neutral | neutral | neutral | ↑ | neutral |
| spend_operations ↑ | -cost | neutral | ↑ (fewer issues) | ↓ | neutral | ↑ reliability |
| spend_development ↑ | -cost | neutral | ↑ (gradual) | ↓ | neutral | ↑ (gradual) |

---

## 8.4 Time Delays

| Action | Effect Timing |
|--------|--------------|
| set_prices | New signups: immediate. Existing: next billing cycle |
| set_model_tiers | Quality: immediate. Satisfaction: EMA lag |
| set_capacity_tier | Immediate |
| spend_advertising | Trial generation: same day |
| spend_operations | R update: same day. Issue resolution: probabilistic daily |
| spend_development | q_shared: accumulates daily, very slow |

---

# Part IX: Stochastic Elements

## 9.1 Random Processes

| Process | Distribution | Parameters |
|---------|--------------|------------|
| Customer trait generation | Truncated Normal | See Part II |
| Daily usage per customer | Poisson | λ = weight × u_i × seats_i |
| Outage occurrence | Bernoulli | p = f(OVL, R) |
| Downtime duration | Categorical | [10, 30, 90] with [0.5, 0.35, 0.15] |
| Issue generation | Bernoulli | p = f(S_i, OUT) |
| Issue resolution | Bernoulli | p = f(S_ops) |
| Trial conversion | Bernoulli | p = sigmoid(f(V_i, usage, quality)) |
| Cancellation | Bernoulli | p = sigmoid(f(V_i, OUT, I_i)) × stickiness |
| Plan switch | Bernoulli | p = sigmoid(f(V_best - V_current)) |
| Trial generation (ads) | Poisson | λ = f(S_ad, REP) |
| Trial generation (WoM) | Poisson | λ = f(n_active, avg_S) |
| Global state noise | Normal | μ=0, σ varies |

---

## 9.2 Shock Events

| Event | Daily Probability | Effect Duration | Impact |
|-------|-------------------|-----------------|--------|
| Demand surge | 0.5% | 3-10 days | Trial rate × 2-8 |
| Compute price change | 0.2% | Permanent | M_compute × 1.2-1.6 |
| Public scare | 0.3% | 7-21 days | Trials -30-70%, cancels +2-7% |
| Budget freeze (large) | 0.4% | 14-60 days | Renegotiation required |
| Service outage | 0.3% | 1-3 days | Forced downtime |

---

# Part X: Summary Equations

## 10.1 Key Formulas

**Value Gap:**
```
V_i = a_i × S_i - b_i × (price_i / W_i)
```

**Delivered Quality:**
```
Q_i = Q_base(T_plan) + q_shared - 0.08×OVL - 0.20×OUT
```

**Satisfaction Update:**
```
S_i(t+1) = 0.9 × S_i(t) + 0.1 × (Q_i - 0.08×OVL - 0.15×OUT - 0.05×I_i)
```

**Conversion Probability:**
```
p_convert = σ(-0.5 + 2.0×V_i + usage_bonus + quality_bonus)
```

**Cancellation Probability:**
```
p_cancel = σ(-3.5 - 3.0×V_i + 0.8×OUT + 0.15×I_i) × stickiness
```

**Trial Generation:**

AI tools have stronger viral growth than traditional SaaS [GrowthUnhinged 2025: AI-native startups grow 3x faster].
Viral coefficient benchmarks: consumer products 0.15-0.7, B2B SaaS ~0.20 [Saxifrage 2025].

```
n_trials = Poisson(α × log(1 + S_ad/500) × rep_mult) + Poisson(β × WoM_rate)

where:
  α = 12.0 (advertising_alpha, boosted for AI tools)
  β = 0.8  (word_of_mouth_beta, reflects AI tool virality)
```

**Daily Profit:**
```
Profit = Σ(payments) - COST_cap - Σ(usage_i × tier_cost × M) - S_ad - S_ops - S_dev
```

---

---

# Part XI: Reality-Matched Parameter Sources

## 11.1 Customer Budget Parameters

Customer willingness-to-pay (c_max) values are calibrated to 2025 market research:

| Group | c_max Mean | Justification | Source |
|-------|------------|---------------|--------|
| S1 (Price-Sensitive) | $45/mo | Freelancers spend $10-50/mo per key tool | Research.com 2025, Freelancers Union 2025 |
| S2 (Quality-Focused) | $120/mo | Professionals pay premium for quality AI tools | BCG 2025: 68% vendors charge premium for AI |
| S3 (Power Users) | $150/mo | Tech power users invest heavily in productivity | MarketerHire 2025 |
| E1 (Cost-Cutting Enterprise) | $45/seat/mo | Enterprise software per-seat pricing | KeyBanc 2024 |
| E2 (Quality-First Enterprise) | $95/seat/mo | Premium enterprise tier | KeyBanc 2024 |
| E3 (Strategic Partners) | $85/seat/mo | Strategic partnership pricing | KeyBanc 2024 |

## 11.2 Infrastructure Cost Parameters

Capacity tier costs are calibrated to 2025 cloud infrastructure benchmarks:

| Tier | Cost/Day | Monthly | Capacity | Justification | Source |
|------|----------|---------|----------|---------------|--------|
| 0 | $80 | $2,400 | 35K units | Efficient serverless | CloudZero 2025 (70%+ savings) |
| 1 | $200 | $6,000 | 100K units | Small dedicated with Graviton | AWS Graviton savings |
| 2 | $500 | $15,000 | 280K units | Medium with reserved instances | CloudZero 2025 |
| 3 | $1,200 | $36,000 | 700K units | Enterprise committed use | Enterprise discounts |

**Cloud cost context:** Cloud costs continue to decline - GPT-4 costs dropped 90% in 18 months [OpenAI 2024]. Modern infrastructure with Graviton/ARM, reserved instances, and committed use discounts significantly reduces costs.

## 11.3 Growth Parameters

| Parameter | Value | Justification | Source |
|-----------|-------|---------------|--------|
| advertising_alpha | 18.0 | Exceptional conversion for AI tools | Cursor 2024: 5x conversion on developer ads |
| word_of_mouth_beta | 1.3 | Strong product-led growth | ChatGPT 2023: >1.2 viral coefficient |

**Growth context:** AI tools in 2024-2025 see unprecedented growth rates. ChatGPT reached 100M users in 2 months [OpenAI 2024]. AI coding tools like Cursor show viral coefficients of 1.3+ [Cursor 2024].

## 11.4 Operations & Support Parameters

Operations spending determines support capacity and customer relationship quality.

| Parameter | Value | Justification | Source |
|-----------|-------|---------------|--------|
| base_issue_rate | 0.002 | 0.2% daily - hyper-polished UX | Superhuman 2024: <1% ticket rate |
| issue_quality_factor | 0.06 | Exceptional docs and self-service | Pendo 2024: In-app guides reduce requests 70% |
| issue_outage_factor | 0.10 | Outages cause 10% ticket surge | PagerDuty 2024: Incident-driven support spikes |
| relationship_quality_bonus_max | 0.45 | Exceptional support drives strong loyalty | Gainsight 2024: Top CS teams reduce churn 40% |
| relationship_decay_rate | 0.01 | Loyal customers are patient | Gainsight 2024: High-NPS customers 3x more patient |
| relationship_boost_quick | +0.30-0.40 | Fast resolution creates loyalty | Zendesk 2024: Same-day resolution +35% retention |

**Real-world context:** Best-in-class SaaS products like Notion, Linear, and Superhuman achieve <2% MAU monthly ticket rates through hyper-polished UX, excellent in-app guidance, and proactive support. Quick issue resolution significantly boosts customer loyalty.

## 11.5 Development & Quality Parameters

Development spending improves product quality and ease-of-use over time.

| Parameter | Value | Justification | Source |
|-----------|-------|---------------|--------|
| ease_k | 0.0015 | High-velocity team with good practices | a16z 2024: Top quartile ships 2x faster |
| quality_dev_sigma | 0.001 | Predictable quality improvements | Stripe 2023: Engineering velocity ↔ quality r=0.7 |
| base_outage_prob | 0.005 | 0.5% daily - world-class infrastructure | Stripe 2024: 99.99% API uptime |
| outage_overload_factor | 6.0 | Heavy penalty for overload | PagerDuty 2024: Overload causes cascading failures |

## 11.6 Customer Quality Expectations

Customers in 2025 expect high-quality AI tools. Expectations raised to reflect market maturity.

| Group | Expected Quality | Justification | Source |
|-------|-----------------|---------------|--------|
| S1 (Price-Sensitive) | 0.55 | Even budget users expect decent AI | Gartner 2025: 78% expect AI ≥ human quality |
| S2 (Quality-Focused) | 0.75 | Professionals demand excellence | Forrester 2025: AI adoption hinges on quality |
| S3 (Power Users) | 0.65 | Tech users have high standards | StackOverflow 2025: Developer tool expectations |
| E1 (Cost-Cutting) | 0.60 | Enterprises need reliability | Deloitte 2025: 85% require SOC2/ISO compliance |
| E2 (Quality-First) | 0.80 | Premium tier demands premium quality | IDC 2025: Enterprise AI quality benchmarks |
| E3 (Strategic Partners) | 0.65 | Partners need consistent performance | McKinsey 2025: Partnership quality requirements |

---

*Document generated for SaaS Bench v1.1 - Structured World Model with Ops/Dev Reality-Matching*
