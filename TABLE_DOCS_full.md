# BossBench TABLE_DOCS — Full Reference

Each table shows INTERNAL columns first (hidden from agent),
then EXTERNAL/agent-visible columns in a marked section.

======================================================================

## customers

**Description:** All customers (small and enterprise)

### INTERNAL (hidden from agent)

  - `steepness_left`: REAL — Sigmoid curve steepness for left half (price < c_max/2)
  - `steepness_right`: REAL — Sigmoid curve steepness for right half (price >= c_max/2)
  - `c_max`: REAL — Hard budget constraint (price at which Q_required ≈ 1)
  - `usage_demand`: REAL — Desired usage units per day
  - `reply_delay_mean`: REAL — Mean days to reply in negotiations
  - `reply_delay_std`: REAL — Std dev of reply delay
  - `negotiation_rate`: REAL — Rate of approaching max accepting price (0-1)
  - `initial_offer_factor`: REAL — Factor for initial offer (sampled per customer)
  - `max_negotiation_turns`: INTEGER — Max turns before final decision
  - `expected_quality`: REAL — Baseline quality expectation (0.0-1.0)
  - `quality_sensitivity`: REAL — Sensitivity to quality changes
  - `price_sensitivity`: REAL — Sensitivity to price changes
  - `willingness_to_pay`: REAL — Maximum monthly budget
  - `usage_scale`: REAL — Usage scaling factor
  - `patience`: REAL — Patience parameter
  - `persona_communication`: TEXT — Communication style (used for LLM prompt generation)

### EXTERNAL (agent-visible)

  - `customer_id`: INTEGER PRIMARY KEY — Unique customer identifier
  - `customer_type`: TEXT — 'small' or 'large' (enterprise)
  - `created_day`: INTEGER — Simulation day customer was created
  - `persona_industry`: TEXT — Industry/domain (e.g., creative, legal, manufacturing)
  - `persona_role`: TEXT — Role/position (e.g., freelancer, managing-partner)
  - `persona_experience`: TEXT — Experience level (e.g., early-career, veteran)
  - `persona_work_style`: TEXT — Work style (e.g., scrappy, methodical, strategic)
  - `persona_tech_savvy`: TEXT — Tech savviness (e.g., basic, expert)
  - `company_size_descriptor`: TEXT — Company size descriptor (enterprise only)
  - `company_culture`: TEXT — Company culture (enterprise only)
  - `company_decision_style`: TEXT — Decision style (enterprise only)
  - `company_primary_concern`: TEXT — Primary concern (enterprise only)
  - `persona_description`: TEXT — Human-readable brief description
  - `seat_count`: INTEGER — Number of seats (enterprise only, NULL for small)
  - `email`: TEXT — Email address (enterprise only)
  - `acquisition_source`: TEXT — How acquired: 'word_of_mouth' or ad channel ID
  - `group_id`: TEXT — Customer segment group identifier (e.g., 'S1', 'S2', 'E1')

----------------------------------------------------------------------

## subscriptions

**Description:** Customer subscriptions (current and historical)

### INTERNAL (hidden from agent)

  - `daily_usage_rate`: REAL — Sampled usage rate for billing period (internal)
  - `billing_period_usage`: REAL — Cumulative usage this billing period (internal)
  - `churn_reason`: TEXT — Structured churn reason enum (hidden from agent)

### EXTERNAL (agent-visible)

  - `subscription_id`: INTEGER PRIMARY KEY — Unique subscription ID
  - `customer_id`: INTEGER — Foreign key to customers
  - `plan`: TEXT — Plan tier: 'A', 'B', or 'C'
  - `listed_price`: REAL — List price per seat in $ (before promotions)
  - `promotion`: REAL — Total promotion discount currently applied
  - `effective_price`: REAL — Actual price charged (listed_price - promotion, floored at 0)
  - `start_day`: INTEGER — Day subscription started
  - `end_day`: INTEGER — Day subscription ended (NULL if active)
  - `status`: TEXT — 'lead', 'subscribed', 'cancelled', 'lost'
  - `billing_day_mod30`: INTEGER — Billing cycle day (0-29)
  - `pending_plan`: TEXT — Scheduled plan change (NULL if none)
  - `pending_price`: REAL — Negotiated price for pending plan change
  - `contract_months`: INTEGER — Commitment length in months (1=month-to-month)
  - `contract_end_day`: INTEGER — Day when contract expires (NULL for month-to-month)

----------------------------------------------------------------------

## daily_usage

**Description:** Per-customer daily usage records

### INTERNAL (hidden from agent)

  _(none)_

### EXTERNAL (agent-visible)

  - `day`: INTEGER — Simulation day
  - `customer_id`: INTEGER — Foreign key to customers
  - `usage_units`: INTEGER — Usage units consumed that day

----------------------------------------------------------------------

## ledger

**Description:** Financial ledger — all income and expenses

### INTERNAL (hidden from agent)

  _(none)_

### EXTERNAL (agent-visible)

  - `id`: INTEGER PRIMARY KEY — Unique entry ID
  - `day`: INTEGER — Simulation day
  - `category`: TEXT — Category: 'subscription_payment', 'compute', 'capacity', 'advertising', 'operations', 'development', 'lead_acquisition_cost', 'vc_investment', 'dividend', 'initial_funding', 'market_research', 'group_research', 'research_project'
  - `amount`: REAL — Amount (positive=income, negative=expense)
  - `note`: TEXT — Description of the transaction

----------------------------------------------------------------------

## service_day

**Description:** Daily service metrics (quality, uptime, capacity)

### INTERNAL (hidden from agent)

  _(none)_

### EXTERNAL (agent-visible)

  - `day`: INTEGER PRIMARY KEY — Simulation day
  - `total_usage_units`: INTEGER — Total usage across all customers
  - `p95_ms`: REAL — P95 latency in milliseconds
  - `error_rate`: REAL — Error rate (0.0-1.0)
  - `downtime_minutes`: INTEGER — Minutes of downtime
  - `capacity_tier`: INTEGER — Current capacity tier (0-7)
  - `capacity_units`: INTEGER — Total capacity units available

----------------------------------------------------------------------

## config_history

**Description:** Daily snapshot of all agent-configurable settings

### INTERNAL (hidden from agent)

  _(none)_

### EXTERNAL (agent-visible)

  - `day`: INTEGER PRIMARY KEY — Simulation day
  - `price_A`: REAL — Plan A monthly price
  - `price_B`: REAL — Plan B monthly price
  - `price_C`: REAL — Plan C monthly price
  - `tier_A`: INTEGER — Plan A model tier (1-5)
  - `tier_B`: INTEGER — Plan B model tier (1-5)
  - `tier_C`: INTEGER — Plan C model tier (1-5)
  - `spend_advertising`: REAL — Total advertising spend per day
  - `spend_operations`: REAL — Operations spend per day
  - `spend_development`: REAL — Development spend per day
  - `capacity_tier`: INTEGER — Capacity tier (0-7)
  - `ad_spend_social_media`: REAL — Social media ad spend
  - `ad_spend_search_ads`: REAL — Search ads spend
  - `ad_spend_linkedin`: REAL — LinkedIn ads spend
  - `ad_spend_content_marketing`: REAL — Content marketing spend
  - `ad_spend_referral_program`: REAL — Referral program spend
  - `quota_A`: INTEGER — Plan A usage quota (units/day/customer)
  - `quota_B`: INTEGER — Plan B usage quota (units/day/customer)
  - `quota_C`: INTEGER — Plan C usage quota (units/day/customer)

----------------------------------------------------------------------

## social_media_posts

**Description:** Public customer feedback posts on social media

### INTERNAL (hidden from agent)

  - `sentiment`: REAL — Sentiment score (agent must infer from content)
  - `reputation_impact`: REAL — Impact on company reputation
  - `influence_score`: REAL — Customer influence weight

### EXTERNAL (agent-visible)

  - `post_id`: INTEGER PRIMARY KEY — Unique post ID
  - `day`: INTEGER — Day posted
  - `customer_id`: INTEGER — Foreign key to customers
  - `content`: TEXT — Post content text
  - `likes`: INTEGER — Number of likes
  - `shares`: INTEGER — Number of shares
  - `virality_score`: REAL — Impact multiplier

----------------------------------------------------------------------

## enterprise_turns

**Description:** Enterprise negotiation turns — each row is one turn in a conversation. Use thread_id to group turns into threads.

### INTERNAL (hidden from agent)

  - `next_reply_day`: INTEGER — Day when counterparty will reply (internal scheduling)
  - `current_offer_price`: REAL — Last offer price from customer (internal tracking)

### EXTERNAL (agent-visible)

  - `turn_id`: INTEGER PRIMARY KEY — Unique turn ID
  - `thread_id`: INTEGER — Groups turns into a conversation (same thread_id = same negotiation)
  - `customer_id`: INTEGER — Foreign key to customers
  - `thread_type`: TEXT — 'new_lead', 'plan_change', 'budget_freeze', 'churn_prevention', 'renegotiation', 'renewal', 'general'
  - `turn_number`: INTEGER — 0-indexed turn within thread
  - `sender`: TEXT — 'customer', 'agent', or 'system'
  - `message_text`: TEXT — Message text (NULL for agent structural-only turns)
  - `offer_json`: TEXT — JSON structured offer data
  - `status`: TEXT — 'awaiting_agent_reply', 'replied', 'agent_rejected', 'accepted'
  - `day`: INTEGER — Simulation day of this turn
  - `email`: TEXT — Email of sender (enterprise customers)

----------------------------------------------------------------------

## notifications

**Description:** Agent inbox — all notifications and alerts

### INTERNAL (hidden from agent)

  _(none)_

### EXTERNAL (agent-visible)

  - `notification_id`: INTEGER PRIMARY KEY — Unique notification ID
  - `day`: INTEGER — Day of notification
  - `type`: TEXT — Notification type (e.g., social_media_post, large_customer_message, vc_approach, group_research_complete, ...)
  - `title`: TEXT — Short title
  - `summary`: TEXT — Brief summary
  - `details_json`: TEXT — Additional structured data as JSON
  - `reference_id`: INTEGER — ID of related entity
  - `reference_type`: TEXT — Type of reference (post, thread, event, vc_thread)

----------------------------------------------------------------------

## shareholders

**Description:** Cap table — founder and VC investors

### INTERNAL (hidden from agent)

  - `vc_alpha`: REAL — VC negotiation aggressiveness parameter
  - `turns_this_year`: INTEGER — VC approach turns this year (rate limiting)
  - `year_start_day`: INTEGER — Day when current year started for rate limiting

### EXTERNAL (agent-visible)

  - `shareholder_id`: INTEGER PRIMARY KEY — Unique shareholder ID
  - `name`: TEXT — Shareholder name (e.g., "Founder", "Sequoia Capital")
  - `shareholder_type`: TEXT — 'founder' or 'vc'
  - `shares_held`: REAL — Number of shares held
  - `total_invested`: REAL — Total $ invested
  - `created_day`: INTEGER — Day added to cap table
  - `target_share_pct`: REAL — What % the VC ideally wants (VC only)
  - `investment_amount`: REAL — How much $ the VC wants to invest (VC only)

----------------------------------------------------------------------

## funding_rounds

**Description:** Completed VC investment settlements

### INTERNAL (hidden from agent)

  - `pre_money_valuation`: REAL — Pre-money valuation at settlement
  - `post_money_valuation`: REAL — Post-money valuation at settlement

### EXTERNAL (agent-visible)

  - `round_id`: INTEGER PRIMARY KEY — Unique round ID
  - `day`: INTEGER — Settlement day
  - `investor_shareholder_id`: INTEGER — Foreign key to shareholders
  - `shares_issued`: REAL — New shares issued
  - `price_per_share`: REAL — Price per share
  - `total_amount`: REAL — Total investment amount

----------------------------------------------------------------------

## vc_turns

**Description:** VC negotiation turns — each row is one turn in a VC conversation. Use thread_id to group turns into threads.

### INTERNAL (hidden from agent)

  - `next_reply_day`: INTEGER — Day when VC will reply (internal scheduling)
  - `current_offer_share_pct`: REAL — Latest offered share % (internal tracking)
  - `current_offer_amount`: REAL — Latest offered investment amount (internal)
  - `original_valuation`: REAL — Original valuation at deal creation
  - `anti_dilution_triggered`: INTEGER — Whether anti-dilution has been triggered
  - `tranche_2_released`: INTEGER — Whether second tranche has been released

### EXTERNAL (agent-visible)

  - `turn_id`: INTEGER PRIMARY KEY — Unique turn ID
  - `thread_id`: INTEGER — Groups turns into a conversation (same thread_id = same negotiation)
  - `shareholder_id`: INTEGER — Foreign key to shareholders
  - `turn_number`: INTEGER — 0-indexed turn within thread
  - `sender`: TEXT — 'vc', 'agent', or 'system'
  - `message_text`: TEXT — Message text (NULL for agent structural-only turns)
  - `offer_json`: TEXT — JSON: {share_pct, amount, price_per_share, proposed_terms}
  - `status`: TEXT — 'awaiting_agent_reply', 'replied', 'agent_rejected', 'accepted'
  - `day`: INTEGER — Simulation day of this turn
  - `expiry_day`: INTEGER — Deal expiry day (auto-reject if not settled)
  - `has_anti_dilution`: INTEGER — 1 if deal has anti-dilution protection
  - `has_milestone_tranching`: INTEGER — 1 if deal has milestone-based tranching
  - `has_redemption_rights`: INTEGER — 1 if deal has redemption rights
  - `milestone_revenue_target`: REAL — MRR target for milestone tranche release
  - `milestone_deadline_day`: REAL — Day by which milestone must be hit
  - `tranche_1_amount`: REAL — First tranche amount (released on acceptance)
  - `tranche_2_amount`: REAL — Second tranche amount (released on milestone)
  - `redemption_eligible_day`: INTEGER — Day after which VC can demand buyback
  - `anti_dilution_floor`: REAL — Anti-dilution valuation floor
  - `milestone_tranche_pct`: REAL — Upfront tranche percentage
  - `milestone_revenue_multiplier`: REAL — MRR milestone multiplier
  - `milestone_deadline_days_chosen`: INTEGER — Deadline days for milestone
  - `redemption_days_chosen`: INTEGER — Redemption window days
  - `redemption_buyback_multiplier`: REAL — Buyback multiplier

----------------------------------------------------------------------

## dividends

**Description:** Dividend payment history

### INTERNAL (hidden from agent)

  _(none)_

### EXTERNAL (agent-visible)

  - `dividend_id`: INTEGER PRIMARY KEY — Unique dividend ID
  - `day`: INTEGER — Day declared
  - `total_amount`: REAL — Total dividend declared
  - `per_share_amount`: REAL — Amount per share
  - `total_shares_at_time`: REAL — Total shares when declared
  - `founder_payout`: REAL — Founder's share of this dividend

----------------------------------------------------------------------

## research_projects

**Description:** R&D research projects (available, in-progress, completed)

### INTERNAL (hidden from agent)

  - `actual_completion_day`: INTEGER — Actual completion day (hidden for non-completed projects)

### EXTERNAL (agent-visible)

  - `project_id`: TEXT PRIMARY KEY — Unique project ID (e.g., rp_01)
  - `status`: TEXT — 'available', 'in_progress', 'completed'
  - `started_day`: INTEGER — Day project was started (NULL if available)
  - `expected_completion_day`: INTEGER — Expected completion day
  - `quality_boost_applied`: REAL — Quality boost applied on completion
  - `current_decay_reduction`: REAL — Active decay rate reduction (0 if expired)
  - `decay_reduction_expiry_day`: INTEGER — Day when decay reduction expires

----------------------------------------------------------------------

## ad_channel_leads

**Description:** Advertising channel effectiveness history

### INTERNAL (hidden from agent)

  _(none)_

### EXTERNAL (agent-visible)

  - `id`: INTEGER PRIMARY KEY — Unique record ID
  - `day`: INTEGER — Simulation day
  - `channel_id`: TEXT — Ad channel identifier
  - `group_id`: TEXT — Customer group targeted
  - `leads_generated`: INTEGER — Number of leads generated
  - `spend`: REAL — Amount spent

----------------------------------------------------------------------

## group_info_levels

**Description:** Customer group discovery and research levels

### INTERNAL (hidden from agent)

  _(none)_

### EXTERNAL (agent-visible)

  - `group_id`: TEXT PRIMARY KEY — Customer group identifier
  - `info_level`: INTEGER — Current info level (0=undiscovered, 1-4=researched)
  - `is_discoverable`: INTEGER — 1 if discoverable (not initial), 0 if initial
  - `discovered_day`: INTEGER — Day first discovered (NULL if Level 0)
  - `last_research_day`: INTEGER — Day of last research upgrade

----------------------------------------------------------------------

## segment_discovery

**Description:** History of all market research (segment discovery) attempts and outcomes

### INTERNAL (hidden from agent)

  _(none)_

### EXTERNAL (agent-visible)

  - `id`: INTEGER PRIMARY KEY — Unique attempt ID (auto-incrementing)
  - `day`: INTEGER — Simulation day of the attempt
  - `cost`: REAL — Amount spent on this attempt
  - `success`: INTEGER — 1 if a new segment was discovered, 0 if not
  - `discovered_group_id`: TEXT — Group ID discovered (NULL if unsuccessful)
  - `remaining_undiscovered`: INTEGER — Undiscovered segments remaining after this attempt

----------------------------------------------------------------------

## issues

**Description:** Individual customer support issues with full lifecycle tracking

### INTERNAL (hidden from agent)

  _(none)_

### EXTERNAL (agent-visible)

  - `issue_id`: INTEGER PRIMARY KEY — Unique issue ID (auto-incrementing)
  - `customer_id`: INTEGER — Foreign key to customers
  - `group_id`: TEXT — Customer segment group identifier (e.g., S1, E1)
  - `open_day`: INTEGER — Simulation day when the issue was created
  - `days_open`: INTEGER — How many days the issue has been open (increments daily)
  - `status`: TEXT — 'open' or 'resolved'
  - `resolved_day`: INTEGER — Simulation day when resolved (NULL if still open)
  - `resolution_type`: TEXT — How resolved: 'ops_resolved' (via operations spend)

----------------------------------------------------------------------