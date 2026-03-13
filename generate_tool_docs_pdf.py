"""Generate PDF documentation for SaaS Bench tools."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime

# =============================================================================
# DATABASE TABLE DOCUMENTATION (visible columns only)
# =============================================================================

DATABASE_TABLES = [
    {
        "name": "customers",
        "description": "All customers in the system. Contains customer identifiers, type, creation date, and persona information. Latent preference parameters are hidden.",
        "columns": [
            {"name": "customer_id", "type": "INTEGER", "description": "Primary key, auto-increment"},
            {"name": "customer_type", "type": "TEXT", "description": "'small' or 'large' (enterprise)"},
            {"name": "created_day", "type": "INTEGER", "description": "Day the customer was created"},
            {"name": "persona_industry", "type": "TEXT", "description": "Industry (e.g., 'creative', 'legal', 'manufacturing')"},
            {"name": "persona_role", "type": "TEXT", "description": "Role (e.g., 'freelancer', 'managing-partner')"},
            {"name": "persona_experience", "type": "TEXT", "description": "Experience level (e.g., 'early-career', 'veteran')"},
            {"name": "persona_work_style", "type": "TEXT", "description": "Work style (e.g., 'scrappy', 'methodical')"},
            {"name": "persona_tech_savvy", "type": "TEXT", "description": "Tech savviness (e.g., 'basic', 'expert')"},
            {"name": "persona_communication", "type": "TEXT", "description": "Communication style (e.g., 'casual', 'formal')"},
            {"name": "company_size_descriptor", "type": "TEXT", "description": "Enterprise only: company size descriptor"},
            {"name": "company_culture", "type": "TEXT", "description": "Enterprise only: culture (e.g., 'cost-conscious')"},
            {"name": "company_decision_style", "type": "TEXT", "description": "Enterprise only: decision style"},
            {"name": "company_primary_concern", "type": "TEXT", "description": "Enterprise only: primary concern"},
            {"name": "persona_description", "type": "TEXT", "description": "Human-readable brief description of persona"},
            {"name": "seat_count", "type": "INTEGER", "description": "Number of seats (enterprise only, NULL for small)"},
            {"name": "email", "type": "TEXT", "description": "Email address (enterprise only, NULL for small)"},
            {"name": "acquisition_source", "type": "TEXT", "description": "How customer was acquired: ad channel IDs, 'word_of_mouth', 'organic_marketing', or 'organic'"},
        ],
        "notes": "HIDDEN: group_id, steepness_left, steepness_right, c_max, usage_demand, expected_quality, quality_sensitivity, price_sensitivity, willingness_to_pay, usage_scale, patience, reply_delay_mean, reply_delay_std, negotiation_rate, max_negotiation_turns"
    },
    {
        "name": "subscriptions",
        "description": "Subscription records linking customers to plans. Tracks status, pricing, billing cycle, and pending plan changes.",
        "columns": [
            {"name": "subscription_id", "type": "INTEGER", "description": "Primary key, auto-increment"},
            {"name": "customer_id", "type": "INTEGER", "description": "Foreign key to customers"},
            {"name": "plan", "type": "TEXT", "description": "Plan name: 'A', 'B', or 'C'"},
            {"name": "listed_price", "type": "REAL", "description": "List price per seat (before promotions)"},
            {"name": "promotion", "type": "REAL", "description": "Total promotion discount currently applied"},
            {"name": "effective_price", "type": "REAL", "description": "Actual price charged (listed_price - promotion)"},
            {"name": "start_day", "type": "INTEGER", "description": "Day subscription started"},
            {"name": "end_day", "type": "INTEGER", "description": "Day subscription ended (NULL if active)"},
            {"name": "status", "type": "TEXT", "description": "'lead', 'trial', 'subscribed', 'cancelled', 'lost', 'free_trial'"},
            {"name": "billing_day_mod30", "type": "INTEGER", "description": "Day of month for billing (0-29)"},
            {"name": "pending_plan", "type": "TEXT", "description": "Scheduled plan change (NULL if none)"},
            {"name": "pending_price", "type": "REAL", "description": "Price for pending plan change"},
        ],
        "notes": "HIDDEN: daily_usage_rate, billing_period_usage"
    },
    {
        "name": "daily_usage",
        "description": "Daily usage records per customer. Shows actual usage units consumed each day (quota-capped).",
        "columns": [
            {"name": "day", "type": "INTEGER", "description": "Simulation day"},
            {"name": "customer_id", "type": "INTEGER", "description": "Foreign key to customers"},
            {"name": "usage_units", "type": "INTEGER", "description": "Usage units consumed that day"},
        ],
        "notes": "Primary key: (day, customer_id). This is the visible usage data - internal usage rate is hidden."
    },
    {
        "name": "service_day",
        "description": "Daily service metrics. Shows overall system performance and capacity utilization.",
        "columns": [
            {"name": "day", "type": "INTEGER", "description": "Primary key - simulation day"},
            {"name": "total_usage_units", "type": "INTEGER", "description": "Total usage units across all customers"},
            {"name": "p95_ms", "type": "REAL", "description": "95th percentile response time in ms"},
            {"name": "error_rate", "type": "REAL", "description": "Fraction of requests that errored (0.0-1.0)"},
            {"name": "downtime_minutes", "type": "INTEGER", "description": "Minutes of downtime that day"},
            {"name": "capacity_tier", "type": "INTEGER", "description": "Capacity tier in use (0-3)"},
            {"name": "capacity_units", "type": "INTEGER", "description": "Total capacity units available"},
        ],
        "notes": "Use this to monitor system health and capacity planning."
    },
    {
        "name": "ledger",
        "description": "Financial ledger tracking all income and expenses. Positive amounts are income, negative are costs.",
        "columns": [
            {"name": "id", "type": "INTEGER", "description": "Primary key, auto-increment"},
            {"name": "day", "type": "INTEGER", "description": "Simulation day"},
            {"name": "category", "type": "TEXT", "description": "'subscription_payment', 'compute', 'capacity', 'advertising', 'operations', 'development', 'feature_test', 'emergency', 'lead_acquisition_cost'"},
            {"name": "amount", "type": "REAL", "description": "Amount (positive=income, negative=cost)"},
            {"name": "note", "type": "TEXT", "description": "Optional description"},
        ],
        "notes": "Cash balance = SUM(amount). Query: SELECT SUM(amount) FROM ledger"
    },
    {
        "name": "config_history",
        "description": "Configuration over time. Tracks prices, model tiers, spending, capacity, and quotas.",
        "columns": [
            {"name": "day", "type": "INTEGER", "description": "Primary key - day config was set"},
            {"name": "price_A", "type": "REAL", "description": "Price for Plan A"},
            {"name": "price_B", "type": "REAL", "description": "Price for Plan B"},
            {"name": "price_C", "type": "REAL", "description": "Price for Plan C"},
            {"name": "tier_A", "type": "INTEGER", "description": "Model tier for Plan A (1-5)"},
            {"name": "tier_B", "type": "INTEGER", "description": "Model tier for Plan B (1-5)"},
            {"name": "tier_C", "type": "INTEGER", "description": "Model tier for Plan C (1-5)"},
            {"name": "spend_advertising", "type": "REAL", "description": "Total daily advertising spend"},
            {"name": "spend_operations", "type": "REAL", "description": "Daily operations spend"},
            {"name": "spend_development", "type": "REAL", "description": "Daily development spend"},
            {"name": "capacity_tier", "type": "INTEGER", "description": "Capacity tier (0-3)"},
            {"name": "ad_spend_social_media", "type": "REAL", "description": "Per-channel: social media"},
            {"name": "ad_spend_search_ads", "type": "REAL", "description": "Per-channel: search ads"},
            {"name": "ad_spend_linkedin", "type": "REAL", "description": "Per-channel: LinkedIn"},
            {"name": "ad_spend_content_marketing", "type": "REAL", "description": "Per-channel: content marketing"},
            {"name": "ad_spend_referral_program", "type": "REAL", "description": "Per-channel: referral program"},
            {"name": "quota_A", "type": "INTEGER", "description": "Usage quota for Plan A (units/day)"},
            {"name": "quota_B", "type": "INTEGER", "description": "Usage quota for Plan B (units/day)"},
            {"name": "quota_C", "type": "INTEGER", "description": "Usage quota for Plan C (units/day)"},
        ],
        "notes": "Get current config: SELECT * FROM config_history ORDER BY day DESC LIMIT 1"
    },
    {
        "name": "threads",
        "description": "Customer communication threads. Used for enterprise negotiations and support.",
        "columns": [
            {"name": "thread_id", "type": "INTEGER", "description": "Primary key, auto-increment"},
            {"name": "customer_id", "type": "INTEGER", "description": "Foreign key to customers"},
            {"name": "state", "type": "TEXT", "description": "'lead', 'evaluation', 'offer', 'active', 'churn_risk', 'cancelled', 'closed'"},
            {"name": "thread_type", "type": "TEXT", "description": "'new_lead', 'plan_change', 'budget_freeze', 'churn_prevention', 'general'"},
            {"name": "negotiation_turn", "type": "INTEGER", "description": "Current turn in negotiation (0 = initial)"},
            {"name": "current_offer_price", "type": "REAL", "description": "Last offer price from customer"},
            {"name": "created_day", "type": "INTEGER", "description": "Day thread was created"},
            {"name": "replied", "type": "INTEGER", "description": "0=not replied, 1=replied by agent"},
        ],
        "notes": "Thread types: new_lead (enterprise inquiry), plan_change (upgrade/downgrade request), budget_freeze (budget shock), churn_prevention (at-risk customer)"
    },
    {
        "name": "messages",
        "description": "Messages within threads. Contains the full conversation history.",
        "columns": [
            {"name": "message_id", "type": "INTEGER", "description": "Primary key, auto-increment"},
            {"name": "day", "type": "INTEGER", "description": "Day message was sent"},
            {"name": "thread_id", "type": "INTEGER", "description": "Foreign key to threads"},
            {"name": "sender", "type": "TEXT", "description": "'customer', 'agent', or 'system'"},
            {"name": "text", "type": "TEXT", "description": "Message content"},
            {"name": "offer_json", "type": "TEXT", "description": "JSON for structured offers (plan, price, seats, term)"},
            {"name": "email", "type": "TEXT", "description": "Email address of sender (for enterprise)"},
        ],
        "notes": "HIDDEN: llm_commitments_json. Query messages: SELECT * FROM messages WHERE thread_id=? ORDER BY message_id"
    },
    {
        "name": "social_media_posts",
        "description": "Customer posts on social media about NovaMind. Contains post content and engagement metrics.",
        "columns": [
            {"name": "post_id", "type": "INTEGER", "description": "Primary key, auto-increment"},
            {"name": "day", "type": "INTEGER", "description": "Day post was made"},
            {"name": "customer_id", "type": "INTEGER", "description": "Foreign key to customers"},
            {"name": "content", "type": "TEXT", "description": "Post content (LLM-generated)"},
            {"name": "likes", "type": "INTEGER", "description": "Number of likes"},
            {"name": "shares", "type": "INTEGER", "description": "Number of shares"},
            {"name": "virality_score", "type": "REAL", "description": "Impact multiplier (0.0-1.0+)"},
        ],
        "notes": "HIDDEN: sentiment, reputation_impact. You must infer sentiment from content."
    },
    {
        "name": "notifications",
        "description": "Agent inbox notifications. Alerts about events, customer actions, and system status.",
        "columns": [
            {"name": "notification_id", "type": "INTEGER", "description": "Primary key, auto-increment"},
            {"name": "day", "type": "INTEGER", "description": "Day notification was created"},
            {"name": "type", "type": "TEXT", "description": "'social_media_post', 'large_customer_message', 'service_alert', 'financial_alert', 'event_alert', 'trial_conversion', 'cancellation', 'lead_lost'"},
            {"name": "title", "type": "TEXT", "description": "Brief title"},
            {"name": "summary", "type": "TEXT", "description": "Summary text"},
            {"name": "details_json", "type": "TEXT", "description": "Additional structured data as JSON"},
            {"name": "reference_id", "type": "INTEGER", "description": "ID of related entity"},
            {"name": "reference_type", "type": "TEXT", "description": "'post', 'thread', 'event', etc."},
        ],
        "notes": "Use expand_notification(id) to get full details"
    },
    {
        "name": "ad_channel_trials",
        "description": "Advertising channel effectiveness tracking. Shows trials generated per channel per day.",
        "columns": [
            {"name": "id", "type": "INTEGER", "description": "Primary key, auto-increment"},
            {"name": "day", "type": "INTEGER", "description": "Simulation day"},
            {"name": "channel_id", "type": "TEXT", "description": "Channel: social_media, search_ads, linkedin, content_marketing, referral_program"},
            {"name": "group_id", "type": "TEXT", "description": "Customer group targeted"},
            {"name": "trials_generated", "type": "INTEGER", "description": "Number of trials from this channel"},
            {"name": "spend", "type": "REAL", "description": "Amount spent on this channel"},
        ],
        "notes": "Use to analyze advertising ROI by channel."
    },
]

# Tool documentation extracted from tools.py
TOOLS = [
    # === COST INFORMATION ===
    {
        "name": "get_cost_info",
        "category": "Cost Information",
        "description": "Get current cost structure for compute and capacity.",
        "output": "JSON with model_tiers (cost_per_usage_unit for tiers 1-5) and capacity_tiers (cost_per_day for tiers 0-3).",
        "impact": "None - read only.",
        "parameters": [],
        "notes": "Use this to understand costs before setting model tiers or capacity. Model tier costs: Tier1=$0.01, Tier2=$0.03, Tier3=$0.06, Tier4=$0.12, Tier5=$0.24 per usage unit. Each tier adds +0.10 quality."
    },

    # === PRICING ACTIONS ===
    {
        "name": "set_prices",
        "category": "Pricing Actions",
        "description": "Set monthly subscription prices for plans A, B, C.",
        "output": "Confirmation message with new prices.",
        "impact": "New prices apply immediately to new signups. Existing subscribers keep old price until their next billing cycle (every 30 days). Higher prices = more revenue per customer but fewer signups. Lower prices = more signups but less revenue per customer.",
        "parameters": [
            {"name": "A", "type": "number", "required": True, "description": "Monthly price in $ for Plan A (entry tier)"},
            {"name": "B", "type": "number", "required": True, "description": "Monthly price in $ for Plan B (mid tier)"},
            {"name": "C", "type": "number", "required": True, "description": "Monthly price in $ for Plan C (premium tier)"},
        ],
        "example": '{"A": 19.99, "B": 49.99, "C": 99.99}'
    },

    # === MODEL TIER ACTIONS ===
    {
        "name": "set_model_tiers",
        "category": "Model Tier Actions",
        "description": "Set AI model quality tier (1-5) for each plan.",
        "output": "Confirmation with new tiers.",
        "impact": "Takes effect immediately for all usage. Each usage unit costs: Tier1=$0.01, Tier2=$0.03, Tier3=$0.06, Tier4=$0.12, Tier5=$0.24 (before multiplier). Higher tiers = better AI quality = happier customers but higher compute costs. Your compute bill = total_usage_units x tier_cost x multiplier.",
        "parameters": [
            {"name": "A", "type": "integer", "required": True, "description": "Model tier 1-5 for Plan A. Tier 1 cheapest ($0.01/unit), Tier 5 best quality ($0.24/unit)"},
            {"name": "B", "type": "integer", "required": True, "description": "Model tier 1-5 for Plan B"},
            {"name": "C", "type": "integer", "required": True, "description": "Model tier 1-5 for Plan C"},
        ],
        "example": '{"A": 2, "B": 3, "C": 5}'
    },

    # === SPENDING ACTIONS ===
    {
        "name": "set_daily_spend",
        "category": "Spending Actions",
        "description": "Set daily spending on advertising, operations, and development.",
        "output": "Confirmation with new spend amounts.",
        "impact": "Deducted from cash EVERY DAY starting today. Advertising: drives new trial signups (more spend = more trials). Operations: affects issue resolution speed and service reliability. Development: improves product over time (q_dev bonus, capped at 0.10).",
        "parameters": [
            {"name": "advertising", "type": "number", "required": True, "description": "Daily $ spent on ads. More = more trial signups. Set to 0 to stop all advertising."},
            {"name": "operations", "type": "number", "required": True, "description": "Daily $ spent on ops/support. More = faster issue resolution, better reliability."},
            {"name": "development", "type": "number", "required": True, "description": "Daily $ spent on product development. More = gradual product improvements (q_dev)."},
        ],
        "example": '{"advertising": 500, "operations": 300, "development": 200}',
        "notes": "For fine-grained ad targeting, use set_ad_channel_spend instead. Total daily cost = advertising + operations + development."
    },
    {
        "name": "set_ad_channel_spend",
        "category": "Spending Actions",
        "description": "Set advertising budget allocation across channels as percentages. Values are normalized to sum to 1.0.",
        "output": "Confirmation with percentage and dollar amount per channel.",
        "impact": "Reallocates the total advertising budget (from set_daily_spend) across channels. Different channels have different effectiveness for different customer segments.",
        "parameters": [
            {"name": "social_media", "type": "number", "required": False, "description": "Percentage (0.0-1.0) for social media ads (Facebook, Instagram, TikTok). Best for S1 (casual users)."},
            {"name": "search_ads", "type": "number", "required": False, "description": "Percentage (0.0-1.0) for search engine ads (Google, Bing). Good for S2 (professionals)."},
            {"name": "linkedin", "type": "number", "required": False, "description": "Percentage (0.0-1.0) for LinkedIn ads. Best for enterprise (E1, E2, E3)."},
            {"name": "content_marketing", "type": "number", "required": False, "description": "Percentage (0.0-1.0) for content marketing (blogs, SEO, whitepapers). Good for S3 (power users)."},
            {"name": "referral_program", "type": "number", "required": False, "description": "Percentage (0.0-1.0) for referral program incentives. Broad reach."},
        ],
        "example": '{"social_media": 0.3, "linkedin": 0.4, "content_marketing": 0.3}'
    },

    # === CAPACITY ACTIONS ===
    {
        "name": "set_capacity_tier",
        "category": "Capacity Actions",
        "description": "Set server capacity tier (0-3).",
        "output": "Confirmation with capacity units and daily cost.",
        "impact": "Changes immediately. You pay the daily cost EVERY DAY. If usage exceeds capacity, service degrades (overload penalty to Q_perceived).",
        "parameters": [
            {"name": "tier", "type": "integer", "required": True, "description": "Capacity tier: 0 ($500/day, 30k units), 1 ($1200/day, 90k units), 2 ($3000/day, 240k units), or 3 ($7000/day, 600k units)"},
        ],
        "example": '{"tier": 1}',
        "notes": "Tier 0: 30,000 units/day at $500/day. Tier 1: 90,000 units/day at $1,200/day. Tier 2: 240,000 units/day at $3,000/day. Tier 3: 600,000 units/day at $7,000/day."
    },

    # === USAGE QUOTAS ===
    {
        "name": "set_usage_quotas",
        "category": "Usage Quotas",
        "description": "Set daily usage quotas (rate limits) for each plan.",
        "output": "Confirmation with new quotas.",
        "impact": "Customers exceeding their quota experience degraded service (quota_penalty in Q_perceived). Higher quotas = better customer experience but more compute costs. Lower quotas = cost control but may cause customer dissatisfaction.",
        "parameters": [
            {"name": "A", "type": "integer", "required": True, "description": "Daily usage quota for Plan A (units/day per customer)"},
            {"name": "B", "type": "integer", "required": True, "description": "Daily usage quota for Plan B (units/day per customer)"},
            {"name": "C", "type": "integer", "required": True, "description": "Daily usage quota for Plan C (units/day per customer)"},
        ],
        "example": '{"A": 100, "B": 500, "C": 2000}'
    },

    # === CUSTOMER COMMUNICATION ===
    {
        "name": "read_thread",
        "category": "Customer Communication",
        "description": "Read last 5 messages from a large customer thread.",
        "output": "Messages with sender, text, email, and offers. Also includes thread state, type, customer info (email, seat count).",
        "impact": "None - read only.",
        "parameters": [
            {"name": "thread_id", "type": "integer", "required": True, "description": "Thread ID from inbox notification"},
        ],
        "example": '{"thread_id": 42}',
        "notes": "For full history, use get_thread_history."
    },
    {
        "name": "get_thread_history",
        "category": "Customer Communication",
        "description": "Get full conversation history for a thread.",
        "output": "All messages (up to limit) with full details including email addresses, negotiation turn, current offer price.",
        "impact": "None - read only.",
        "parameters": [
            {"name": "thread_id", "type": "integer", "required": True, "description": "Thread ID to get history for"},
            {"name": "limit", "type": "integer", "required": False, "description": "Maximum messages to return (default 20)"},
        ],
        "example": '{"thread_id": 42, "limit": 50}',
        "notes": "Use this to review the complete negotiation/conversation history before responding."
    },
    {
        "name": "send_reply",
        "category": "Customer Communication",
        "description": "Send a reply message to a large customer thread.",
        "output": "Confirmation that reply was sent.",
        "impact": "Customer will respond based on your message (scheduled for future day). Can include structured offer for negotiations.",
        "parameters": [
            {"name": "thread_id", "type": "integer", "required": True, "description": "Thread ID to reply to"},
            {"name": "message_text", "type": "string", "required": True, "description": "Your reply message text"},
            {"name": "offer", "type": "object", "required": False, "description": "Optional: structured deal offer for negotiation"},
        ],
        "example": '{"thread_id": 42, "message_text": "Thank you for your interest...", "offer": {"plan": "B", "price_per_seat": 45.00, "seats": 50, "term_days": 365}}',
        "notes": "Offer fields: plan (A/B/C), price_per_seat, seats, term_days, price_lock_days"
    },

    # === ANALYTICS ===
    {
        "name": "python_exec",
        "category": "Analytics",
        "description": "Execute Python for data analysis. This is your primary analytics tool.",
        "output": "Output from print() statements (max 5000 chars).",
        "impact": "None - read-only database access.",
        "parameters": [
            {"name": "code", "type": "string", "required": True, "description": "Python code. 'conn' is ready. Use print() to see results."},
        ],
        "example": '''{"code": "# Get subscriber count by plan\\nprint(rows(\\"SELECT plan, COUNT(*) FROM subscriptions WHERE status='subscribed' AND end_day IS NULL GROUP BY plan\\"))"}''',
        "notes": """PRE-LOADED: conn (SQLite), pandas as pd, numpy as np, rows(sql)->list, row(sql)->tuple

TABLES: customers, subscriptions, daily_usage, ledger, service_day, config_history, social_media_posts, messages, threads, notifications, ad_channel_trials

COMMON QUERIES:
- Subscribers: row("SELECT COUNT(*) FROM subscriptions WHERE status='subscribed' AND end_day IS NULL")
- By plan: rows("SELECT plan, COUNT(*) FROM subscriptions WHERE status='subscribed' GROUP BY plan")
- Cash: row("SELECT SUM(amount) FROM ledger")
- Revenue by day: rows("SELECT day, SUM(amount) FROM ledger WHERE category='subscription_payment' GROUP BY day")
- Daily usage: rows("SELECT day, SUM(usage_units) FROM daily_usage GROUP BY day")

NOTE: Hidden columns are automatically filtered out."""
    },

    # === MEMORY ===
    {
        "name": "memory_insert",
        "category": "Memory Management",
        "description": "Insert text at a line number in your memory. Lines below shift down.",
        "output": "Confirmation with new line count.",
        "impact": "Persistent notes shown in system prompt.",
        "parameters": [
            {"name": "line", "type": "integer", "required": True, "description": "Line number to insert at (1-indexed). Use line 1 to insert at top, or last_line+1 to append."},
            {"name": "content", "type": "string", "required": True, "description": "Text to insert. Can contain newlines to insert multiple lines."},
        ],
        "example": '{"line": 1, "content": "TODO: Review churn rate weekly"}'
    },
    {
        "name": "memory_delete",
        "category": "Memory Management",
        "description": "Delete lines from your memory.",
        "output": "Confirmation with new line count.",
        "impact": "Removes notes from persistent memory.",
        "parameters": [
            {"name": "start", "type": "integer", "required": True, "description": "First line to delete (1-indexed)"},
            {"name": "end", "type": "integer", "required": True, "description": "Last line to delete (1-indexed, inclusive)"},
        ],
        "example": '{"start": 3, "end": 5}'
    },
    {
        "name": "memory_edit",
        "category": "Memory Management",
        "description": "Replace content of a single line in your memory.",
        "output": "Confirmation.",
        "impact": "Updates existing note.",
        "parameters": [
            {"name": "line", "type": "integer", "required": True, "description": "Line number to edit (1-indexed)"},
            {"name": "content", "type": "string", "required": True, "description": "New content for this line"},
        ],
        "example": '{"line": 2, "content": "DONE: Fixed pricing issue"}'
    },

    # === DAILY CALCULATIONS ===
    {
        "name": "register_daily_calculation",
        "category": "Daily Calculations",
        "description": "Register a named Python calculation to run automatically at the start of each day.",
        "output": "Confirmation.",
        "impact": "The output (via print()) will be shown in the daily dashboard.",
        "parameters": [
            {"name": "name", "type": "string", "required": True, "description": "Unique name for this calculation (e.g., 'revenue_trend', 'churn_rate')"},
            {"name": "code", "type": "string", "required": True, "description": "Python code to execute. Has access to: conn (DB), rows(query), row(query), numpy, pandas, math, statistics. Use print() to output results."},
        ],
        "example": '{"name": "churn_rate", "code": "total = row(\\"SELECT COUNT(*) FROM subscriptions WHERE status=\'subscribed\'\\")[0]\\nchurned = row(\\"SELECT COUNT(*) FROM subscriptions WHERE status=\'cancelled\' AND end_day > (SELECT MAX(day)-30 FROM service_day)\\")[0]\\nprint(f\\"30-day churn: {churned}/{total} = {churned/total*100:.1f}%\\")"}',
        "notes": "Use this to track custom metrics like revenue trends, churn rates, or any analysis you want to see daily."
    },
    {
        "name": "remove_daily_calculation",
        "category": "Daily Calculations",
        "description": "Remove a registered daily calculation.",
        "output": "Confirmation or error if not found.",
        "impact": "Calculation stops running daily.",
        "parameters": [
            {"name": "name", "type": "string", "required": True, "description": "Name of the calculation to remove"},
        ],
        "example": '{"name": "churn_rate"}'
    },
    {
        "name": "list_daily_calculations",
        "category": "Daily Calculations",
        "description": "List all registered daily calculations with previews of their code.",
        "output": "List of registered calculations.",
        "impact": "None - read only.",
        "parameters": []
    },

    # === SOCIAL MEDIA & NOTIFICATIONS ===
    {
        "name": "get_social_posts",
        "category": "Social Media & Notifications",
        "description": "Search social media posts about NovaMind.",
        "output": "Posts with content, likes, shares (sentiment NOT provided - must infer from content).",
        "impact": "None - read only.",
        "parameters": [
            {"name": "days", "type": "integer", "required": False, "description": "How many days back to search (default 7)"},
            {"name": "limit", "type": "integer", "required": False, "description": "Max posts to return (default 50)"},
        ],
        "example": '{"days": 14, "limit": 100}',
        "notes": "Use to monitor brand sentiment, find complaints to address, or analyze customer feedback. Sentiment must be inferred from post content."
    },
    {
        "name": "expand_notification",
        "category": "Social Media & Notifications",
        "description": "Get full details of a notification.",
        "output": "Complete notification with type, priority, title, summary, and details JSON.",
        "impact": "None - read only.",
        "parameters": [
            {"name": "notification_id", "type": "integer", "required": True, "description": "The notification ID from the daily summary"},
        ],
        "example": '{"notification_id": 15}',
        "notes": "The daily summary shows brief headlines - use this to see complete information for any notification you want to investigate."
    },

    # === DAY CONTROL ===
    {
        "name": "next_day",
        "category": "Day Control",
        "description": "End your turn for today and advance to the next day.",
        "output": "Daily dashboard showing: cash, subscribers, yesterday's metrics (usage, trials, conversions, cancellations, upgrades, downgrades, overload, outage, open issues), current config (prices, model tiers, daily spend, capacity tier), and inbox summary.",
        "impact": "Simulation advances to next day. All overnight processing occurs (billing, churn, new signups, etc.).",
        "parameters": [],
        "notes": "You MUST call this to proceed - the day will not advance until you do. Call this when you have finished all actions for today."
    },
]


def generate_pdf(output_path: str):
    """Generate the tool documentation PDF."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.6*inch,
        leftMargin=0.6*inch,
        topMargin=0.6*inch,
        bottomMargin=0.6*inch
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=20,
        alignment=TA_CENTER
    )

    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading1'],
        fontSize=18,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#1e3a5f')
    )

    category_style = ParagraphStyle(
        'Category',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.HexColor('#2563eb')
    )

    tool_name_style = ParagraphStyle(
        'ToolName',
        parent=styles['Heading3'],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=4,
        textColor=colors.HexColor('#1e40af'),
        fontName='Helvetica-Bold'
    )

    table_name_style = ParagraphStyle(
        'TableName',
        parent=styles['Heading3'],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=4,
        textColor=colors.HexColor('#166534'),
        fontName='Helvetica-Bold'
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=9,
        spaceAfter=4,
        leading=12
    )

    small_style = ParagraphStyle(
        'Small',
        parent=styles['Normal'],
        fontSize=8,
        spaceAfter=3,
        leading=10,
        textColor=colors.HexColor('#4b5563')
    )

    code_style = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Courier',
        backColor=colors.HexColor('#f3f4f6'),
        leftIndent=5,
        spaceAfter=4,
        leading=9
    )

    story = []

    # Title
    story.append(Paragraph("SaaS Bench Documentation", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 15))

    # Table of Contents
    story.append(Paragraph("Contents", styles['Heading2']))
    story.append(Paragraph("<b>Part 1: Database Tables</b> - Schema reference for all accessible tables", body_style))
    story.append(Paragraph("<b>Part 2: Agent Tools</b> - Actions available to the agent", body_style))
    story.append(Spacer(1, 10))

    # ==========================================================================
    # PART 1: DATABASE TABLES
    # ==========================================================================
    story.append(PageBreak())
    story.append(Paragraph("Part 1: Database Tables", section_style))
    story.append(Paragraph("Reference for all database tables accessible via python_exec. Hidden columns (latent customer parameters, internal simulation state) are automatically filtered.", body_style))
    story.append(Spacer(1, 10))

    for table in DATABASE_TABLES:
        # Table name
        story.append(Paragraph(f"{table['name']}", table_name_style))
        story.append(Paragraph(table['description'], body_style))

        # Columns table
        col_data = [['Column', 'Type', 'Description']]
        for col in table['columns']:
            col_data.append([
                col['name'],
                col['type'],
                col['description'][:55] + '...' if len(col['description']) > 55 else col['description']
            ])

        col_table = Table(col_data, colWidths=[1.5*inch, 0.8*inch, 4.5*inch])
        col_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dcfce7')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(col_table)

        # Notes
        if table.get('notes'):
            story.append(Paragraph(f"<i>{table['notes']}</i>", small_style))

        story.append(Spacer(1, 8))

    # ==========================================================================
    # PART 2: AGENT TOOLS
    # ==========================================================================
    story.append(PageBreak())
    story.append(Paragraph("Part 2: Agent Tools", section_style))
    story.append(Paragraph("Actions available to the agent. Each tool has parameters, output format, and impact description.", body_style))
    story.append(Spacer(1, 10))

    # Tools by category
    current_category = None

    for tool in TOOLS:
        # Category header
        if tool['category'] != current_category:
            current_category = tool['category']
            story.append(Paragraph(current_category, category_style))

        # Tool name
        story.append(Paragraph(f"{tool['name']}()", tool_name_style))

        # Description
        story.append(Paragraph(f"<b>Description:</b> {tool['description']}", body_style))

        # Output
        if 'output' in tool:
            story.append(Paragraph(f"<b>Output:</b> {tool['output']}", body_style))

        # Impact
        if 'impact' in tool:
            story.append(Paragraph(f"<b>Impact:</b> {tool['impact']}", body_style))

        # Parameters
        if tool.get('parameters'):
            story.append(Paragraph("<b>Parameters:</b>", body_style))

            param_data = [['Name', 'Type', 'Req', 'Description']]
            for p in tool['parameters']:
                param_data.append([
                    p['name'],
                    p['type'],
                    'Y' if p['required'] else 'N',
                    p['description'][:50] + '...' if len(p['description']) > 50 else p['description']
                ])

            param_table = Table(param_data, colWidths=[1.2*inch, 0.7*inch, 0.4*inch, 4.5*inch])
            param_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e5e7eb')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            story.append(param_table)
        else:
            story.append(Paragraph("<b>Parameters:</b> None", body_style))

        # Example
        if tool.get('example'):
            example_text = tool['example'].replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(f"<b>Example:</b> <font face='Courier' size='7'>{example_text[:100]}{'...' if len(example_text) > 100 else ''}</font>", body_style))

        # Notes
        if tool.get('notes'):
            notes_text = tool['notes'].replace('\n', '<br/>').replace('<', '&lt;').replace('>', '&gt;')
            # Truncate long notes
            if len(notes_text) > 400:
                notes_text = notes_text[:400] + '...'
            story.append(Paragraph(f"<b>Notes:</b> {notes_text}", small_style))

        story.append(Spacer(1, 6))

    # Build PDF
    doc.build(story)
    print(f"PDF generated: {output_path}")


if __name__ == "__main__":
    output_path = "/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench/tool_documentation.pdf"
    generate_pdf(output_path)
