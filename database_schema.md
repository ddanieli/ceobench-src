# SaaS Bench — Complete Database Schema

All tables defined in `src/saas_bench/database.py`. SQLite with WAL mode.

---

## Tables Overview (34 tables)

| # | Table Name | Description |
|---|-----------|-------------|
| 1 | `customers` | Customer profiles with persona, preferences, and economic parameters |
| 2 | `subscriptions` | Active/cancelled subscriptions with pricing and billing info |
| 3 | `daily_usage` | Per-customer daily usage records |
| 4 | `service_day` | Daily service metrics (latency, errors, capacity) |
| 5 | `ledger` | Financial transactions (income & expenses) |
| 6 | `config_history` | Daily snapshot of pricing, tiers, spending, and quotas |
| 7 | `ad_channel_leads` | Leads generated per ad channel per day |
| 8 | `enterprise_turns` | Enterprise conversation threads (negotiation, churn prevention, etc.) |
| 9 | `enterprise_thread_counter` | Auto-increment counter for enterprise thread IDs |
| 10 | `feature_tests` | A/B test definitions |
| 11 | `test_assignments` | Customer assignments to A/B tests |
| 12 | `events` | World events (demand surges, etc.) |
| 13 | `customer_state` | Dynamic customer state (satisfaction, drift, relationship) |
| 14 | `group_reputation` | Per-segment reputation scores |
| 15 | `group_awareness` | Per-segment marketing awareness |
| 16 | `group_info_levels` | Per-segment research/discovery levels |
| 17 | `pending_group_research` | In-progress group research tasks |
| 18 | `segment_discovery` | Market research attempts to discover new segments |
| 19 | `reputation_history` | Audit log of reputation changes |
| 20 | `global_state` | Key-value store for global simulation state |
| 21 | `api_costs` | LLM API cost tracking |
| 22 | `social_media_posts` | Customer social media activity |
| 23 | `notifications` | System notifications to the agent |
| 24 | `research_projects` | R&D project tracking (tiered) |
| 25 | `competitor_events` | Competitor actions affecting churn |
| 26 | `macroeconomic_conditions` | Daily PMI and economic cycle data |
| 27 | `world_context` | Key-value store for world narrative context |
| 28 | `customer_personas` | Persona templates per segment |
| 29 | `customer_persona_map` | Mapping customers → personas |
| 30 | `group_characteristics` | Qualitative segment descriptions |
| 31 | `group_parameters` | Per-segment economic parameter drift |
| 32 | `issues` | Customer support issues |
| 33 | `ads_revenue` | Per-customer ad revenue records |
| 34 | `config_overrides` | Tool/setting overrides per day |

---

## Detailed Column Definitions

### 1. `customers`
| Column | Type | Notes |
|--------|------|-------|
| `customer_id` | INTEGER PK AUTOINCREMENT | |
| `customer_type` | TEXT NOT NULL | CHECK: 'small' \| 'large' |
| `group_id` | TEXT NOT NULL | Segment: S1, S2, S3, E1, E2, E3 |
| `created_day` | INTEGER NOT NULL | |
| `steepness_left` | REAL NOT NULL | Sigmoid curve left half |
| `steepness_right` | REAL NOT NULL | Sigmoid curve right half |
| `c_max` | REAL NOT NULL | Hard budget constraint |
| `q_max` | REAL NOT NULL DEFAULT 0.75 | Quality ceiling |
| `q_min` | REAL NOT NULL DEFAULT 0.25 | Quality floor |
| `usage_demand` | REAL NOT NULL | |
| `reply_delay_mean` | REAL | Enterprise only |
| `reply_delay_std` | REAL | Enterprise only |
| `negotiation_rate` | REAL | Enterprise only |
| `initial_offer_factor` | REAL | Enterprise only |
| `max_negotiation_turns` | INTEGER | Enterprise only |
| `contract_lockin_penalty` | REAL NOT NULL DEFAULT 0.005 | |
| `persona_industry` | TEXT | |
| `persona_role` | TEXT | |
| `persona_experience` | TEXT | |
| `persona_work_style` | TEXT | |
| `persona_tech_savvy` | TEXT | |
| `persona_communication` | TEXT | |
| `company_size_descriptor` | TEXT | Enterprise only |
| `company_culture` | TEXT | Enterprise only |
| `company_decision_style` | TEXT | Enterprise only |
| `company_primary_concern` | TEXT | Enterprise only |
| `persona_description` | TEXT | |
| `quality_sensitivity` | REAL NOT NULL | |
| `price_sensitivity` | REAL NOT NULL | |
| `willingness_to_pay` | REAL NOT NULL | |
| `usage_scale` | REAL NOT NULL | |
| `patience` | REAL NOT NULL | |
| `seat_count` | REAL | Float for drift accumulation |
| `email` | TEXT | Enterprise only |
| `contract_start_day` | INTEGER | Enterprise only |
| `acquisition_source` | TEXT | 'word_of_mouth' or ad channel ID |
| `ads_quality_sensitivity` | REAL NOT NULL DEFAULT 0.1 | |
| `ads_return_sensitivity` | REAL NOT NULL DEFAULT 0.15 | |

### 2. `subscriptions`
| Column | Type | Notes |
|--------|------|-------|
| `subscription_id` | INTEGER PK AUTOINCREMENT | |
| `customer_id` | INTEGER NOT NULL | FK → customers |
| `plan` | TEXT NOT NULL | CHECK: 'A', 'B', 'C', 'pending' |
| `listed_price` | REAL NOT NULL | |
| `promotion` | REAL NOT NULL DEFAULT 0.0 | |
| `effective_price` | REAL NOT NULL | listed_price - promotion |
| `effective_c_max` | REAL | Customer's drifted c_max snapshot |
| `start_day` | INTEGER NOT NULL | |
| `end_day` | INTEGER | NULL if active |
| `status` | TEXT NOT NULL | CHECK: 'lead', 'subscribed', 'cancelled', 'lost' |
| `billing_day_mod30` | INTEGER NOT NULL | CHECK: 0 ≤ value < 30 |
| `pending_plan` | TEXT | CHECK: NULL or 'A', 'B', 'C' |
| `pending_price` | REAL | |
| `daily_usage_rate` | REAL NOT NULL DEFAULT 0 | |
| `billing_period_usage` | REAL NOT NULL DEFAULT 0 | |
| `seat_count` | INTEGER NOT NULL DEFAULT 1 | |
| `contract_months` | INTEGER NOT NULL DEFAULT 1 | |
| `contract_end_day` | INTEGER | NULL for month-to-month |
| `churn_reason` | TEXT | HIDDEN from agent |
| `first_billing_done` | INTEGER NOT NULL DEFAULT 0 | |

### 3. `daily_usage`
| Column | Type | Notes |
|--------|------|-------|
| `day` | INTEGER NOT NULL | Composite PK |
| `customer_id` | INTEGER NOT NULL | Composite PK, FK → customers |
| `usage_units` | INTEGER NOT NULL | |

### 4. `service_day`
| Column | Type | Notes |
|--------|------|-------|
| `day` | INTEGER PK | |
| `total_usage_units` | INTEGER NOT NULL | |
| `p95_ms` | REAL NOT NULL | |
| `error_rate` | REAL NOT NULL | |
| `downtime_minutes` | INTEGER NOT NULL | |
| `capacity_tier` | INTEGER NOT NULL | |
| `capacity_units` | INTEGER NOT NULL | |

### 5. `ledger`
| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `day` | INTEGER NOT NULL | |
| `category` | TEXT NOT NULL | CHECK: 'subscription_payment', 'compute', 'capacity', 'advertising', 'operations', 'development', 'lead_acquisition_cost', 'initial_funding', 'market_research', 'group_research', 'research_project', 'ad_revenue' |
| `amount` | REAL NOT NULL | Positive = income, Negative = expense |
| `note` | TEXT | |

### 6. `config_history`
| Column | Type | Notes |
|--------|------|-------|
| `day` | INTEGER PK | |
| `price_A` | REAL NOT NULL | |
| `price_B` | REAL NOT NULL | |
| `price_C` | REAL NOT NULL | |
| `tier_A` | INTEGER NOT NULL | |
| `tier_B` | INTEGER NOT NULL | |
| `tier_C` | INTEGER NOT NULL | |
| `spend_advertising` | REAL NOT NULL | |
| `spend_operations` | REAL NOT NULL | |
| `spend_development` | REAL NOT NULL | |
| `capacity_tier` | INTEGER NOT NULL | |
| `ad_spend_social_media` | REAL NOT NULL DEFAULT 0 | |
| `ad_spend_search_ads` | REAL NOT NULL DEFAULT 0 | |
| `ad_spend_linkedin` | REAL NOT NULL DEFAULT 0 | |
| `ad_spend_content_marketing` | REAL NOT NULL DEFAULT 0 | |
| `ad_spend_referral_program` | REAL NOT NULL DEFAULT 0 | |
| `quota_A` | INTEGER NOT NULL DEFAULT 0 | |
| `quota_B` | INTEGER NOT NULL DEFAULT 0 | |
| `quota_C` | INTEGER NOT NULL DEFAULT 0 | |

### 7. `ad_channel_leads`
| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `day` | INTEGER NOT NULL | |
| `channel_id` | TEXT NOT NULL | |
| `group_id` | TEXT NOT NULL | |
| `leads_generated` | INTEGER NOT NULL | |
| `spend` | REAL NOT NULL | |

### 8. `enterprise_turns`
| Column | Type | Notes |
|--------|------|-------|
| `message_id` | INTEGER PK AUTOINCREMENT | |
| `thread_id` | INTEGER NOT NULL | Groups turns into conversation |
| `customer_id` | INTEGER NOT NULL | FK → customers |
| `thread_type` | TEXT NOT NULL DEFAULT 'general' | CHECK: 'new_lead', 'plan_change', 'churn_prevention', 'renegotiation', 'renewal', 'general' |
| `turn_number` | INTEGER NOT NULL DEFAULT 0 | |
| `sender` | TEXT NOT NULL | CHECK: 'customer', 'agent', 'system' |
| `message_text` | TEXT NOT NULL DEFAULT '' | |
| `offer_json` | TEXT NOT NULL DEFAULT '{}' | |
| `day` | INTEGER NOT NULL | |
| `next_reply_day` | INTEGER | HIDDEN — internal scheduling |
| `current_offer_price` | REAL | HIDDEN — internal tracking |
| `email` | TEXT NOT NULL DEFAULT '' | |
| `seat_count` | INTEGER NOT NULL DEFAULT 1 | |
| `closed` | INTEGER NOT NULL DEFAULT 0 | 0=open, 1=closed |
| `close_reason` | TEXT NOT NULL DEFAULT '' | 'accepted' or 'agent_rejected' |
| `_internal_status` | TEXT | HIDDEN (NULL=active, 'timeout'=dead) |

### 9. `enterprise_thread_counter`
| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | CHECK: id = 1 |
| `next_thread_id` | INTEGER NOT NULL DEFAULT 1 | |

### 10. `feature_tests`
| Column | Type | Notes |
|--------|------|-------|
| `test_id` | INTEGER PK AUTOINCREMENT | |
| `name` | TEXT NOT NULL | |
| `description_text` | TEXT NOT NULL | |
| `start_day` | INTEGER NOT NULL | |
| `end_day` | INTEGER NOT NULL | |
| `rollout_fraction` | REAL NOT NULL | |
| `extra_budget` | REAL NOT NULL | |
| `target_json` | TEXT | Target customer segment |

### 11. `test_assignments`
| Column | Type | Notes |
|--------|------|-------|
| `test_id` | INTEGER NOT NULL | Composite PK, FK → feature_tests |
| `customer_id` | INTEGER NOT NULL | Composite PK, FK → customers |
| `treated` | INTEGER NOT NULL | CHECK: 0 or 1 |

### 12. `events`
| Column | Type | Notes |
|--------|------|-------|
| `event_id` | INTEGER PK AUTOINCREMENT | |
| `day` | INTEGER NOT NULL | |
| `type` | TEXT NOT NULL | CHECK: 'demand_surge' |
| `details_json` | TEXT | |

### 13. `customer_state`
| Column | Type | Notes |
|--------|------|-------|
| `customer_id` | INTEGER PK | FK → customers |
| `satisfaction` | REAL NOT NULL DEFAULT 0.0 | |
| `open_issue_days` | INTEGER NOT NULL DEFAULT 0 | |
| `relationship` | REAL NOT NULL DEFAULT 0.5 | Range 0.0–1.0 |
| `current_steepness_left` | REAL | |
| `current_steepness_right` | REAL | |
| `current_c_max` | REAL | |
| `current_q_max` | REAL | |
| `current_q_min` | REAL | |
| `current_slope` | REAL | |
| `last_drift_day` | INTEGER | |
| `plan_was_acceptable` | INTEGER DEFAULT 1 | |
| `last_quality` | REAL | |
| `last_satisfaction` | REAL | |
| `shock_event_id` | INTEGER | FK → events |

### 14. `group_reputation`
| Column | Type | Notes |
|--------|------|-------|
| `group_id` | TEXT PK | |
| `reputation` | REAL NOT NULL DEFAULT 0.5 | |
| `last_updated_day` | INTEGER NOT NULL DEFAULT 0 | |

### 15. `group_awareness`
| Column | Type | Notes |
|--------|------|-------|
| `group_id` | TEXT PK | |
| `awareness` | REAL NOT NULL DEFAULT 0.0 | Range 0.0–1.0 |
| `last_marketing_day` | INTEGER NOT NULL DEFAULT 0 | |

### 16. `group_info_levels`
| Column | Type | Notes |
|--------|------|-------|
| `group_id` | TEXT PK | |
| `info_level` | INTEGER NOT NULL DEFAULT 0 | CHECK: 0–5 |
| `is_discoverable` | INTEGER NOT NULL DEFAULT 0 | |
| `discovered_day` | INTEGER | NULL if Level 0 |
| `last_research_day` | INTEGER | |

### 17. `pending_group_research`
| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `group_id` | TEXT NOT NULL | |
| `from_level` | INTEGER NOT NULL | |
| `to_level` | INTEGER NOT NULL | |
| `cost` | REAL NOT NULL | |
| `started_day` | INTEGER NOT NULL | |
| `expected_completion_day` | INTEGER NOT NULL | |
| `status` | TEXT NOT NULL DEFAULT 'in_progress' | CHECK: 'in_progress', 'completed' |

### 18. `segment_discovery`
| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `day` | INTEGER NOT NULL | |
| `cost` | REAL NOT NULL | |
| `success` | INTEGER NOT NULL DEFAULT 0 | |
| `discovered_group_id` | TEXT | NULL if unsuccessful |
| `remaining_undiscovered` | INTEGER NOT NULL | HIDDEN from agent |

### 19. `reputation_history`
| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `day` | INTEGER NOT NULL | |
| `group_id` | TEXT NOT NULL | |
| `reputation` | REAL NOT NULL | |
| `change_reason` | TEXT | 'quality_churn', 'satisfaction_boost', 'cross_influence', 'decay' |

### 20. `global_state`
| Column | Type | Notes |
|--------|------|-------|
| `key` | TEXT PK | |
| `value` | REAL NOT NULL | |

### 21. `api_costs`
| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK AUTOINCREMENT | |
| `day` | INTEGER NOT NULL | |
| `model` | TEXT NOT NULL | |
| `purpose` | TEXT NOT NULL | 'env_llm' or 'agent' |
| `input_tokens` | INTEGER NOT NULL | |
| `output_tokens` | INTEGER NOT NULL | |
| `cost_usd` | REAL NOT NULL | |

### 22. `social_media_posts`
| Column | Type | Notes |
|--------|------|-------|
| `post_id` | INTEGER PK AUTOINCREMENT | |
| `day` | INTEGER NOT NULL | |
| `customer_id` | INTEGER NOT NULL | FK → customers |
| `sentiment` | TEXT NOT NULL | CHECK: 'positive', 'neutral', 'negative' |
| `content` | TEXT NOT NULL | |
| `likes` | INTEGER NOT NULL DEFAULT 0 | |
| `shares` | INTEGER NOT NULL DEFAULT 0 | |
| `virality_score` | REAL NOT NULL DEFAULT 0.0 | |
| `reputation_impact` | REAL NOT NULL DEFAULT 0.0 | |
| `influence_score` | REAL NOT NULL DEFAULT 0.0 | HIDDEN |

### 23. `notifications`
| Column | Type | Notes |
|--------|------|-------|
| `notification_id` | INTEGER PK AUTOINCREMENT | |
| `day` | INTEGER NOT NULL | |
| `type` | TEXT NOT NULL | CHECK: 'large_customer_message', 'service_alert', 'financial_alert', 'event_alert', 'cancellation', 'lead_lost', 'deal_won', 'customer_churned', 'broken_promise', 'market_discovery', 'research_complete', 'group_research_complete', 'contract_renewal', 'macro_economic_update' |
| `message` | TEXT NOT NULL | |

### 24. `research_projects`
| Column | Type | Notes |
|--------|------|-------|
| `project_id` | TEXT PK | e.g., "t1_1", "t3_2" (20 tiers, repeatable) |
| `tier` | INTEGER NOT NULL | |
| `status` | TEXT DEFAULT 'in_progress' | CHECK: 'in_progress', 'completed' |
| `started_day` | INTEGER | |
| `expected_completion_day` | INTEGER | |
| `actual_completion_day` | INTEGER | |
| `expected_quality_boost` | REAL DEFAULT 0 | |
| `quality_boost_applied` | REAL DEFAULT 0 | |
| `current_decay_reduction` | REAL DEFAULT 0 | DEPRECATED |
| `decay_reduction_expiry_day` | INTEGER | DEPRECATED |

### 25. `competitor_events`
| Column | Type | Notes |
|--------|------|-------|
| `event_id` | INTEGER PK AUTOINCREMENT | |
| `start_day` | INTEGER NOT NULL | |
| `boost_amount` | REAL NOT NULL | |
| `post_end_day` | INTEGER NOT NULL | |
| `description` | TEXT | |
| `applied` | INTEGER DEFAULT 0 | |

### 26. `macroeconomic_conditions`
| Column | Type | Notes |
|--------|------|-------|
| `day` | INTEGER PK | |
| `pmi_value` | REAL NOT NULL | 30–70 scale; >50 = expansion |
| `pmi_trend` | TEXT NOT NULL | CHECK: 'strong_expansion', 'expansion', 'neutral', 'contraction', 'severe_contraction' |
| `pmi_change` | REAL NOT NULL DEFAULT 0.0 | |
| `cycle_phase` | TEXT NOT NULL | CHECK: 'peak', 'declining', 'trough', 'recovering' |
| `description` | TEXT NOT NULL | |

### 27. `world_context`
| Column | Type | Notes |
|--------|------|-------|
| `key` | TEXT PK | |
| `value` | TEXT | |

### 28. `customer_personas`
| Column | Type | Notes |
|--------|------|-------|
| `persona_id` | INTEGER PK | |
| `group_id` | TEXT | |
| `name` | TEXT | |
| `job_title` | TEXT | |
| `company_name` | TEXT | |
| `industry` | TEXT | |
| `personality_traits` | TEXT | |
| `communication_style` | TEXT | |
| `pain_points` | TEXT | |
| `goals` | TEXT | |
| `writing_style` | TEXT | |
| `backstory` | TEXT | |

### 29. `customer_persona_map`
| Column | Type | Notes |
|--------|------|-------|
| `customer_id` | INTEGER PK | |
| `persona_id` | INTEGER | |
| `custom_name` | TEXT | |
| `custom_details_json` | TEXT | |

### 30. `group_characteristics`
| Column | Type | Notes |
|--------|------|-------|
| `group_id` | TEXT PK | |
| `description` | TEXT | |
| `typical_use_cases` | TEXT | |
| `common_complaints` | TEXT | |
| `common_praises` | TEXT | |
| `social_media_tone` | TEXT | |
| `enterprise_negotiation_style` | TEXT | |
| `price_discussion_phrases` | TEXT | |
| `quality_discussion_phrases` | TEXT | |

### 31. `group_parameters`
| Column | Type | Notes |
|--------|------|-------|
| `group_id` | TEXT PK | |
| `current_c_max_mean` | REAL | |
| `current_q_min_mean` | REAL | |
| `current_q_max_mean` | REAL | |
| `current_steepness_left_factor` | REAL | |
| `last_drift_day` | INTEGER | |

### 32. `issues`
| Column | Type | Notes |
|--------|------|-------|
| `issue_id` | INTEGER PK | |
| `customer_id` | INTEGER | |
| `group_id` | TEXT | |
| `open_day` | INTEGER | |
| `days_open` | INTEGER | |
| `status` | TEXT | |
| `resolved_day` | INTEGER | |
| `resolution_type` | TEXT | |

### 33. `ads_revenue`
| Column | Type | Notes |
|--------|------|-------|
| `day` | INTEGER | Composite PK |
| `customer_id` | INTEGER | Composite PK |
| `group_id` | TEXT | |
| `ads_strength` | REAL | |
| `sensitivity` | REAL | |
| `seat_count` | INTEGER | |
| `revenue` | REAL | |

### 34. `config_overrides`
| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | |
| `day` | INTEGER | |
| `tool_name` | TEXT | |
| `setting_type` | TEXT | |
| `settings_json` | TEXT | |

---

## Dividends (Virtual Table)

Not a standalone table — dividends are tracked via the `ledger` table with category `'subscription_payment'` and related entries, plus a separate `dividends` table for founder payouts:

- **Founder dividends** = `SUM(founder_payout) FROM dividends`

---

## Key Indexes

- **subscriptions:** `idx_subscriptions_customer`, `idx_subscriptions_status`, `idx_subs_active_billing`, `idx_subs_active_customer`
- **enterprise_turns:** `idx_enterprise_turns_thread`, `idx_enterprise_turns_customer`, `idx_enterprise_turns_closed`, `idx_et_thread_msgid`, `idx_et_active_customer`, `idx_et_active_thread_msgid`
- **issues:** `idx_issues_customer`, `idx_issues_status`, `idx_issues_group`, `idx_issues_open_day`, `idx_issues_customer_open`
- **Others:** ledger (day, category), social posts, notifications, research projects, ads revenue, config overrides, customer type, customer state
