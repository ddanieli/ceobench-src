# SaaS Bench: World Dynamics Documentation v3.0

## Executive Summary

SaaS Bench is a benchmark where an AI agent runs a subscription-based AI service (NovaMind AI) for 365 simulated days. This document describes the world model organized strictly around the **Three-Layer Architecture**:

![Three-Layer Architecture](fig4_architecture.png)

**Key Features**:
- **Linear cost-quality model**: Each tier adds +0.10 quality, cost doubles (see Figure 1)
- **Participation constraint customer model**: Microeconomic decision theory (see Figure 3)
- **Realistic agent observability**: Agent only sees what a real startup founder could see
- **6 customer groups**: Different preferences and behaviors (see Figure 2)

---

# LAYER 1: AGENT

The agent is the AI system being evaluated. It operates like a real startup founder - making decisions based on observable business metrics and customer feedback, without access to hidden world variables.

---

## 1.1 Design Philosophy: Realistic Observability

**Key Principle**: The agent can only see what a real startup founder could see.

**Observable (via tools)**:
- Financial data (cash, revenue, costs) via `python_exec`
- Customer behavior (signups, churn, upgrades) via `python_exec`
- Social media posts (content, likes, shares) via `get_social_posts`
- Customer messages and threads via `read_thread`
- Service metrics (usage, downtime) via `python_exec`
- Qualitative customer research via `get_customer_group_info`

**Hidden (NOT accessible to agent)**:
- Individual customer satisfaction scores
- Reputation scores (internal world variable)
- Customer satisfaction calculations
- Participation curve parameters
- Churn/conversion probabilities

---

## 1.2 Agent Properties

| Property | Description |
|----------|-------------|
| Memory | Persistent notes (line-numbered text, 0-∞ lines) |
| Turn Budget | Unlimited actions per day until `next_day()` called |

---

## 1.3 System Prompt (Minimal)

Each turn, the agent's system prompt contains only essential context:

```
=== Day {day} ===
Cash: ${cash:,.2f}

=== Today's Notifications ===
{notification_summary}

=== Your Memory ===
{memory_lines}
```

**That's it.** All other information must be queried via tools.

The daily notification summary shows brief headlines:
```
🚨 [42] Service Alert: 30-minute outage detected at 2:15 AM
⚠️ [43] Enterprise Message: TechCorp requesting pricing discussion
📌 [44] Social Media: Negative post about response times (152 likes)
📋 [45] Cancellation: 3 customers churned today
```

Agent uses `expand_notification(id)` to see full details.

---

## 1.4 Agent Observations

### 1.4.1 Via System Prompt (Automatic)

| Field | Description |
|-------|-------------|
| day | Current simulation day (1-365) |
| cash | Current cash balance |
| notification_summary | Brief headlines of today's notifications |
| memory | Agent's persistent notes |

### 1.4.2 Via python_exec (On Demand)

All business metrics require explicit queries:

```python
# Subscriber count
row("SELECT COUNT(*) FROM subscriptions WHERE status='subscribed' AND end_day IS NULL")

# Monthly revenue from subscriptions
row("SELECT SUM(effective_price) FROM subscriptions WHERE status='subscribed' AND end_day IS NULL")

# By plan
rows("SELECT plan, COUNT(*) FROM subscriptions WHERE status='subscribed' AND end_day IS NULL GROUP BY plan")

# Churn analysis
rows("SELECT customer_id, plan, end_day FROM subscriptions WHERE status='cancelled' ORDER BY end_day DESC LIMIT 10")

# Service metrics
rows("SELECT day, total_usage_units, p95_ms, error_rate FROM service_day ORDER BY day DESC LIMIT 7")

# Cost breakdown
rows("SELECT type, SUM(amount) FROM ledger WHERE day > (SELECT MAX(day)-30 FROM ledger) GROUP BY type")
```

### 1.4.3 Via Notification Tools

Use `expand_notification(id)` to get full details of any notification headline.

---

## 1.5 Agent Actions

### 1.5.1 Configuration Actions

| Action | Parameters | Effect |
|--------|------------|--------|
| `set_prices` | A, B, C (float) | Set monthly prices for plans |
| `set_model_tiers` | A, B, C (1-5) | Set AI quality tier per plan |
| `set_daily_spend` | advertising, operations, development (float) | Set daily budgets |
| `set_capacity_tier` | tier (0-3) | Set infrastructure capacity |

### 1.5.2 Communication Actions

| Action | Parameters | Effect |
|--------|------------|--------|
| `read_thread` | thread_id | Read enterprise customer conversation |
| `send_reply` | thread_id, message, offer? | Reply to enterprise customer |
| `post_update` | channel, text | Public announcement (status/pricing/release) |

### 1.5.3 Intelligence Actions

| Action | Parameters | Effect |
|--------|------------|--------|
| `get_social_posts` | sentiment?, days?, limit? | Search social media posts |
| `expand_notification` | notification_id | View full notification details |
| `get_customer_group_info` | group_id | Qualitative segment information |
| `get_company_info` | - | Startup backstory and context |
| `get_cost_info` | - | Current cost structure |

### 1.5.4 Analytics Actions (Primary Data Source)

| Action | Parameters | Effect |
|--------|------------|--------|
| `python_exec` | code | Query database via Python sandbox |

**Available Tables**:
- `customers` - All customers (customer_id, group_id, created_day, seat_count)
- `subscriptions` - Subscription records (customer_id, plan, listed_price, promotion, effective_price, status, start_day, end_day)
- `ledger` - All financial transactions (day, category, amount, note)
- `service_day` - Daily service metrics (day, total_usage_units, p95_ms, error_rate, downtime_minutes)
- `config_history` - Configuration over time (day, price_A/B/C, tier_A/B/C, spend_*, capacity_tier)
- `social_media_posts` - Customer posts (day, customer_id, sentiment, content, likes, shares)
- `messages` - Thread messages (thread_id, day, sender, text)
- `threads` - Customer threads (thread_id, customer_id, state)

**NOT accessible via python_exec**:
- `customer_state` (contains hidden satisfaction)
- `global_state` (contains hidden reputation)
- `group_reputation` (hidden world variable)

### 1.5.5 Memory Actions

| Action | Parameters | Effect |
|--------|------------|--------|
| `memory_insert` | line, content | Insert text at line number |
| `memory_delete` | start, end | Delete line range |
| `memory_edit` | line, content | Replace line content |

### 1.5.6 Control Actions

| Action | Parameters | Effect |
|--------|------------|--------|
| `next_day` | - | End turn, advance simulation |

---

## 1.6 Agent → Company Interactions

How agent actions affect company state:

| Agent Action | Company Effect |
|--------------|----------------|
| `set_prices(A, B, C)` | Updates `config.price_*`, affects new signups and retention |
| `set_model_tiers(A, B, C)` | Updates `config.tier_*`, affects quality and compute costs |
| `set_daily_spend(...)` | Updates `config.spend_*`, deducted from cash daily |
| `set_capacity_tier(tier)` | Updates `config.capacity_tier`, affects overload threshold |
| `send_reply(...)` | Affects enterprise deal progress and relationship |
| `post_update(...)` | May affect customer perception (future feature) |

---

# LAYER 2: COMPANY

The company (NovaMind AI) is the middle layer - the business being managed by the agent, serving customers.

---

## 2.1 Company Properties

### 2.1.1 Financial State

| Property | Type | Description |
|----------|------|-------------|
| cash | float | Current cash balance (game over if < 0, **goal is to maximize final cash**) |

### 2.1.2 Configuration State

| Property | Type | Description |
|----------|------|-------------|
| price_A, price_B, price_C | float | Monthly subscription prices |
| tier_A, tier_B, tier_C | int (1-5) | AI model quality tiers |
| spend_advertising | float | Daily advertising budget |
| spend_operations | float | Daily operations budget |
| spend_development | float | Daily development budget |
| capacity_tier | int (0-3) | Infrastructure capacity tier |

### 2.1.3 Hidden State (Not Directly Observable)

| Property | Initial | Range | Description |
|----------|---------|-------|-------------|
| ease | 0.1 | 0-1 | Product usability |
| q_shared | 0.0 | -0.15-0.15 | Shared quality adjustment (dev spending) |

### 2.1.4 Per-Group Reputation

| Property | Initial | Range | Description |
|----------|---------|-------|-------------|
| reputation_S1 | 0.5 | 0-1 | Reputation among Price-Sensitive individuals |
| reputation_S2 | 0.5 | 0-1 | Reputation among Quality-Focused individuals |
| reputation_S3 | 0.5 | 0-1 | Reputation among Power Users |
| reputation_E1 | 0.5 | 0-1 | Reputation among Cost-Cutting enterprises |
| reputation_E2 | 0.5 | 0-1 | Reputation among Quality-First enterprises |
| reputation_E3 | 0.5 | 0-1 | Reputation among Strategic Partners |

---

## 2.2 Company Internal Dynamics

### 2.2.1 Daily Financial Flow

```
INCOME (on each customer's billing day):
+ effective_price per active subscriber (listed_price - promotion)

COSTS (daily):
- capacity_cost = CAPACITY_TIERS[tier].cost_per_day
- compute_cost = Σ(usage × MODEL_TIERS[tier].unit_cost × multiplier)
- advertising = config.spend_advertising
- operations = config.spend_operations
- development = config.spend_development

cash_new = cash + income - costs
```

### 2.2.2 Model Tiers (AI Quality) - Linear Pricing

Quality scales linearly with tier: each tier adds +0.10 quality.

![Linear Cost-Quality Model](fig1_scurve_quality.png)

| Tier | Base Quality | Unit Cost | Δ Quality |
|------|-------------|-----------|-----------|
| 1 | 0.55 | $0.01 | baseline |
| 2 | 0.65 | $0.03 | +0.10 |
| 3 | 0.75 | $0.06 | +0.10 |
| 4 | 0.85 | $0.12 | +0.10 |
| 5 | 0.95 | $0.24 | +0.10 |

**Strategic implications**:
- Cost doubles each tier, quality increases by constant +0.10
- Higher tiers = better quality but exponentially more expensive
- Agent must balance quality gains against cost increases

### 2.2.3 Capacity Tiers (Infrastructure)

| Tier | Units/Day | Cost/Day | Description |
|------|-----------|----------|-------------|
| 0 | 30,000 | $500 | Starter |
| 1 | 90,000 | $1,200 | Standard |
| 2 | 240,000 | $3,000 | Growth |
| 3 | 600,000 | $7,000 | Enterprise |

### 2.2.4 Service Quality Calculation

**Overload**:
```
overload = max(0, total_usage / capacity_units - 1)
```

**Outage Probability**:
```
p_outage = 0.006 × (1 + 4×overload)
```

**Downtime** (if outage occurs):
- 10 minutes (50% probability)
- 30 minutes (35% probability)
- 90 minutes (15% probability)

### 2.2.5 Hidden State Updates

**Shared Quality** (grows with dev spending, decays without):
```
q_shared_new = q_shared + improvement - decay + noise
q_shared_new = clamp(q_shared_new, -0.15, 0.15)
```

### 2.2.6 Reputation Dynamics

**Per-Group Reputation Changes**:
- Quality-related cancellations: -0.02 per cancel
- Negative social posts: -0.01 to -0.03 (× virality)
- Positive social posts: +0.005 to +0.015 (× virality)
- Daily recovery: +0.005 toward baseline (0.5)

**Cross-Group Influence Matrix**:
```
When group X reputation changes by Δ, group Y changes by influence[X][Y] × Δ × 0.3

         S1    S2    S3    E1    E2    E3
S1     1.00  0.15  0.10  0.02  0.02  0.02
S2     0.20  1.00  0.25  0.05  0.08  0.05
S3     0.15  0.20  1.00  0.05  0.10  0.05
E1     0.02  0.05  0.05  1.00  0.15  0.12
E2     0.02  0.08  0.10  0.12  1.00  0.20
E3     0.02  0.05  0.05  0.15  0.18  1.00
```

---

## 2.3 Company → Customer Interactions

How company state affects customers:

| Company State | Customer Effect |
|---------------|-----------------|
| price_* | Affects affordability (C ≤ C_max constraint) |
| tier_* | Affects quality (Q in satisfaction function) |
| capacity_tier | Affects fulfillment and reliability |
| overload | Degrades quality, increases outage risk |
| outage | Major satisfaction drop |
| reputation_* | Affects new customer acquisition rate per group |

---

## 2.4 Company Backstory

### NovaMind AI

**Founded**: 2023 in San Francisco

**Founders**:
- Dr. Sarah Chen (CEO) - Former Google Brain researcher
- Marcus Rodriguez (CTO) - Former Google Brain researcher
- Dr. Aisha Patel (Chief Scientist) - Former Google Brain researcher

**Product**: NovaMind Assistant
- AI-powered productivity platform
- Document analysis, email drafting, code review, data analysis

**Market Position**:
- Plan A ($29): Individual users, small teams
- Plan B ($79): Growing businesses
- Plan C ($199): Large organizations

**Competitors**: Notion AI, Jasper, ChatGPT, various startups

**Day 1 Situation**:
- $500,000 runway
- Just launched publicly
- Small early user base
- Growing word-of-mouth

**Agent's Role**: COO managing day-to-day operations

---

# LAYER 3: CUSTOMER

Customers are the bottom layer - they make decisions based on company offerings and their own preferences.

---

## 3.1 Customer Properties

### 3.1.1 Customer Groups Overview

![Customer Groups: Market Share and Segmentation](fig2_customer_groups.png)

| Group | Type | Name | Market Share |
|-------|------|------|--------------|
| S1 | Individual | Price-Sensitive | 35% |
| S2 | Individual | Quality-Focused | 25% |
| S3 | Individual | Power Users | 15% |
| E1 | Enterprise | Cost-Cutting | 10% |
| E2 | Enterprise | Quality-First | 8% |
| E3 | Enterprise | Strategic Partners | 7% |

### 3.1.2 Participation Curve Parameters

| Group | Q_min | C_max | Slope | Usage/day |
|-------|-------|-------|-------|-----------|
| S1 | 0.40 | $50 | 0.008 | 30 |
| S2 | 0.65 | $150 | 0.004 | 60 |
| S3 | 0.55 | $120 | 0.005 | 100 |
| E1 | 0.50 | $35/seat | 0.007 | 25/seat |
| E2 | 0.72 | $80/seat | 0.003 | 40/seat |
| E3 | 0.58 | $55/seat | 0.004 | 35/seat |

**Parameter meanings**:
- Q_min: Minimum acceptable quality (reservation satisfaction)
- C_max: Maximum affordable monthly cost
- Slope: Price sensitivity (higher = more price sensitive)
- Usage: Expected daily API usage

### 3.1.3 Per-Customer State

| Property | Type | Description |
|----------|------|-------------|
| satisfaction | float (0-1) | Current satisfaction level |
| q_min | float | Quality threshold (can drift) |
| c_max | float | Budget constraint (can drift) |
| slope | float | Price sensitivity (can drift) |
| group_id | string | Customer group (S1-E3) |
| persona_id | int | Assigned persona template |

---

## 3.2 Customer Decision Model

### 3.2.1 Theoretical Foundation: Participation Constraint

![Participation Constraint Model](fig3_participation_constraint.png)

From microeconomic contract theory. Each customer has:

**Satisfaction Function**:
```
U(Q, C) = Q - slope × C
```
Where:
- Q = Comprehensive quality (0-1)
- C = Monthly cost
- slope = Price sensitivity

**Participation Constraint**:
```
Customer subscribes iff U(Q, C) ≥ Q_min
Equivalently: Q ≥ Q_min + slope × C
```

**Budget Constraint**:
```
C ≤ C_max
```

### 3.2.2 Comprehensive Quality Calculation

Quality is multi-dimensional:
```
Q = 0.50 × (model_quality + q_shared + q_test)
  + 0.30 × fulfillment
  + 0.20 × reliability

Where:
- model_quality = MODEL_TIERS[tier].base_quality (0.55-0.92)
- q_shared = shared quality adjustment (-0.15 to 0.15, from dev spending)
- q_test = A/B test bonus (if in treatment)
- fulfillment = 1/(1 + overload) if overloaded, else 1.0
- reliability = 1.0 - 0.15×overload - 0.25×(outage ? 1 : 0)
```

### 3.2.3 Customer Decisions

**Subscribe Decision**:
```
For each plan P in {A, B, C}:
  quality_P = compute_comprehensive_quality(tier_P)
  satisfaction_P = quality_P - slope × price_P
  acceptable_P = (satisfaction_P ≥ Q_min) AND (price_P ≤ C_max)

Customer subscribes to plan with highest satisfaction among acceptable plans.
If no plan is acceptable, customer does not subscribe.
```

**Churn Decision**:
```
For current plan:
  If no plan is acceptable: churn
  Additional churn probability based on satisfaction and issues
```

**Switch Decision**:
```
On billing day, re-evaluate all plans.
Switch to plan with highest satisfaction if different from current.
```

---

## 3.3 Customer Internal Dynamics

### 3.3.1 Satisfaction Update

Daily exponential moving average:
```
satisfaction_new = 0.9 × satisfaction_old + 0.1 × (quality - penalties)

Where penalties:
- perf_penalty = 0.08 × overload + 0.15 × outage
- issue_penalty = 0.05 × open_issue_days
```

### 3.3.2 Characteristic Drift

Customer parameters evolve over time:

**Drift Probability (per day)**:
| Group | Probability | Reasoning |
|-------|-------------|-----------|
| S1 | 3% | Volatile, comparing alternatives |
| S2 | 2% | Stable professionals |
| S3 | 4% | Tech-savvy, always evaluating |
| E1 | 2% | Budget cycles |
| E2 | 1.5% | Stable quality requirements |
| E3 | 1% | Long-term partnerships |

**Drift Amounts**:
| Parameter | Standard Deviation |
|-----------|-------------------|
| Q_min | ±0.02 |
| C_max | ±$5 |
| slope | ±0.0005 |

### 3.3.3 Issue Generation and Resolution

**New Issue Probability**:
```
p_issue = 0.003 + 0.08×(1 - satisfaction) + 0.05×outage
```

**Issue Resolution Probability**:
```
p_resolve = 0.2 + 0.75×(1 - exp(-spend_ops / 3000))
```

---

## 3.4 Customer Behaviors

### 3.4.1 Social Media Posting

![Social Media → Reputation Flow](fig5_reputation_flow.png)

**Posting Probability**:
| Satisfaction | Daily Probability |
|-------------|-------------------|
| ≥ 0.8 or ≤ 0.2 | 2% |
| 0.7-0.8 or 0.2-0.3 | 1% |
| 0.3-0.7 | 0.3% |

New customers (first 30 days): 2× probability

**Sentiment Determination**:
| Satisfaction | Positive | Neutral | Negative |
|-------------|----------|---------|----------|
| ≥ 0.8 | 70% | 25% | 5% |
| 0.6-0.8 | 40% | 50% | 10% |
| 0.4-0.6 | 15% | 55% | 30% |
| 0.2-0.4 | 5% | 35% | 60% |
| < 0.2 | 2% | 18% | 80% |

**Virality**:
- Base likes: 1-100 (individual), 5-50 (enterprise)
- Negative posts: 1.5-2.5× multiplier
- 1% chance of viral spike (3-5× additional)

**Reputation Impact**:
```
impact = base × (1 + 2×virality) × group_weight
Where:
- base_positive = +0.005 to +0.015
- base_negative = -0.01 to -0.03
- group_weight = 1.5 for enterprise, 1.0 for individual
```

### 3.4.2 Customer Personas

Each customer is assigned a pre-generated persona:

**Persona Properties**:
- Name, job title, company (enterprise)
- Personality traits
- Communication style
- Pain points, goals
- Writing style (for social posts)
- Backstory

**Example Personas**:

*S1 - Alex Chen* (Freelance Graphic Designer)
- Budget-conscious, practical, comparison-shopper
- Casual communication, uses emojis
- Pain points: tight budgets, unpredictable income

*S2 - Dr. Michael Foster* (Management Consultant)
- Quality-focused, professional, detail-oriented
- Formal, structured feedback
- Pain points: client deliverable quality, deadlines

*E2 - Victoria Sterling* (Law Firm Partner)
- Quality-demanding, reputation-conscious
- Formal, expects excellence
- Pain points: accuracy requirements, liability

---

## 3.5 Customer → Company Interactions

How customers affect company state:

| Customer Behavior | Company Effect |
|-------------------|----------------|
| Subscribe | +revenue, +usage |
| Churn | -revenue, reputation damage if quality-related |
| Social post (positive) | +reputation for group |
| Social post (negative) | -reputation for group |
| Enterprise message | Creates thread requiring response |
| High usage | Contributes to overload |

---

## 3.6 Customer Group Details

### S1 - Price-Sensitive Individuals (35%)
- Freelancers, students, hobbyists
- Low quality threshold, tight budgets, high price sensitivity
- Quick to churn on price increases
- Social media: Casual, price-focused, compares to free alternatives

### S2 - Quality-Focused Individuals (25%)
- Professionals, consultants, technical writers
- High quality threshold, generous budgets, low price sensitivity
- Tolerant of price if quality is excellent
- Social media: Professional, detailed reviews

### S3 - Power Users (15%)
- Developers, content agencies, automation enthusiasts
- Moderate threshold, high usage (100 units/day)
- Concerned about rate limits and API reliability
- Social media: Technical posts with benchmarks

### E1 - Cost-Cutting Enterprises (10%)
- 20-200 seats, strict per-seat budgets
- Negotiate aggressively, want volume discounts
- Accept "good enough" quality
- Negotiation: References competitor pricing

### E2 - Quality-First Enterprises (8%)
- 30-300 seats, legal/finance/consulting
- High quality threshold, willing to pay premium
- Require SLAs, compliance features
- Negotiation: Focused on guarantees

### E3 - Strategic Partners (7%)
- 50-500 seats, long-term partnerships
- Interested in co-development, roadmap influence
- Most stable (lowest drift)
- Negotiation: Partnership terms

---

## 3.7 Enterprise Negotiations (Direct Agent ↔ Enterprise Communication)

Enterprise customers (E1, E2, E3) can communicate directly with the agent through negotiation threads. This is the "triangular" part of the architecture - bypassing the standard participation constraint churn mechanism.

### 3.7.1 Negotiation Triggers

| Trigger | Condition | Thread Type |
|---------|-----------|-------------|
| Budget Freeze | Random shock event | `budget_freeze` |
| Churn Prevention | Satisfaction drops < 0 | `churn_prevention` |
| Renewal | Subscription > 300 days | `renewal` |
| Plan Change | Curve drift violates constraints | `churn_prevention` |
| New Lead | Enterprise arrives (future) | `new_lead` |
| Upgrade | Enterprise wants more seats (future) | `upgrade` |

### 3.7.2 Negotiation Chassis (Programmatic Pricing)

The negotiation follows a programmatic chassis that determines acceptable prices:

**Max Accepting Price**:
```
max_price = min(c_max, (Q - q_min) / slope)
```
Where Q is the perceived quality of the plan being discussed.

**Customer Offer Evolution** (asymptotic approach):
```
offer(turn) = max_price - (max_price - initial_offer) × exp(-rate × turn)

Where:
- initial_offer = max_price × 0.75 (starts at 75% of max)
- rate = negotiation_rate (per-customer, typically 0.2-0.4)
```

Over multiple turns, customer offers asymptotically approach their true maximum.

### 3.7.3 Enterprise Customer Parameters

Each enterprise customer has unique negotiation characteristics:

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| reply_delay_mean | Mean days to reply | 1-4 days |
| reply_delay_std | Reply delay variance | 0.5-2 days |
| negotiation_rate | Speed of approaching max price | 0.2-0.5 per turn |

### 3.7.4 Thread States

```
lead → evaluation → offer → active
                         ↘ cancelled
renewal → offer → active
                ↘ cancelled
churn_risk → offer → active
                   ↘ cancelled
```

### 3.7.5 Agent Negotiation Actions

| Action | Effect |
|--------|--------|
| `read_thread(thread_id)` | View conversation history and customer info |
| `send_reply(thread_id, message, offer?)` | Respond with optional structured offer |

**Offer Structure**:
```json
{
  "plan": "B",
  "price_per_seat": 65.00,
  "seats": 50,
  "term_days": 365,
  "price_lock_days": 180
}
```

### 3.7.6 Relationship Score

Customer relationship affects perceived quality:

| Relationship | Effect |
|--------------|--------|
| 1.0 (excellent) | +15% quality perception bonus |
| 0.5 (neutral) | No effect |
| 0.0 (poor) | -15% quality perception bonus |

**Relationship Changes**:
- Timely responses: +relationship
- Delayed responses: -relationship
- Fair offers: +relationship
- Lowball offers: -relationship
- Daily decay toward neutral (0.5)

Formula:
```
perceived_quality = base_quality + relationship_bonus + perception_bias

Where:
- relationship_bonus = 0.15 × (relationship - 0.5) × 2
- perception_bias = customer-specific bias (-0.2 to +0.2)
```

### 3.7.7 Customer Response Generation

Customer responses are generated using GPT-5.2 with medium thinking effort:

1. **Chassis computes** acceptable price range and decision (accept/counter/reject)
2. **LLM generates** natural language response matching customer persona
3. **Response includes** offer price and negotiation position

The model is configurable via `config.customer_simulation_model`.

### 3.7.8 Curve Drift Impact on Enterprise

Enterprise customers' participation curves drift over time (like individuals). When drift causes:

- **Budget constraint violation** (price > c_max): Triggers churn prevention thread
- **Satisfaction constraint violation** (U < 0): Triggers churn prevention thread

This gives the agent opportunity to renegotiate rather than automatic churn.

---

# APPENDICES

## Appendix A: Daily Simulation Loop

```
1. Generate shock events (if any)
2. Agent turn (multiple actions until next_day())
3. Compute usage from all subscribers
4. Compute service metrics (overload, outage)
5. Update hidden state (q_shared)
6. Update customer satisfaction
7. Process customer issues
8. Process trials (convert or expire)
9. Process cancellations (individuals only)
10. Process social media posts (LLM-generated if enabled)
11. Update reputation (direct + cross-group)
12. Process enterprise negotiations:
    a. Process scheduled customer replies
    b. Check for new negotiation triggers (churn risk, renewals)
    c. Decay relationships toward neutral
13. Process curve drift (can trigger enterprise plan change threads)
14. Process plan switches
15. Generate new trials (advertising + word-of-mouth)
16. Process billing (payments on billing days)
17. Process costs (capacity + compute + spending)
18. Check game over (cash < 0)
```

## Appendix B: Key Formulas

**Satisfaction**: `U(Q, C) = Q - slope × C`

**Participation**: `Customer subscribes iff U ≥ Q_min AND C ≤ C_max`

**Quality**: `Q = 0.5×model + 0.3×fulfillment + 0.2×reliability`

**Satisfaction**: `S_new = 0.9×S_old + 0.1×(Q - penalties)`

**Reputation Impact**: `impact = base × (1 + 2×virality) × group_weight`

## Appendix C: Default Configuration

| Parameter | Default |
|-----------|---------|
| Initial Cash | $500,000 |
| Total Days | 365 |
| Trial Duration | 7 days |
| Prices (A/B/C) | $29/$79/$199 |
| Model Tiers (A/B/C) | 2/3/4 |
| Advertising | $500/day |
| Operations | $1,000/day |
| Development | $500/day |
| Capacity | Tier 1 |

## Appendix D: Scoring

**Goal: Maximize final cash**

```
Score = Final Cash on day 365
```

Game over if cash < 0 at any point.

---

*Document Version 3.0 - Enterprise negotiation system, GPT-5.2 customer simulation, relationship tracking, curve drift triggers*

**v3.0 Changes**:
- Added enterprise negotiation system (Section 3.7)
- Multi-turn negotiations with programmatic pricing chassis
- GPT-5.2 customer simulation for social posts and negotiations
- Customer relationship tracking affecting perceived quality
- Curve drift triggers plan change negotiations for enterprise
- Customer-specific perceived quality bias
