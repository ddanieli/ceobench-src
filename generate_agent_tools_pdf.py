#!/usr/bin/env python3
"""Generate comprehensive PDF report of all agent tools and their outputs."""

from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Preformatted, KeepTogether
)
from reportlab.lib.enums import TA_LEFT


def create_tools_pdf(output_path: str):
    """Create comprehensive PDF documenting all agent tools."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=20,
        textColor=colors.HexColor('#1a1a2e')
    )

    section_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#16213e')
    )

    tool_name_style = ParagraphStyle(
        'ToolName',
        parent=styles['Heading3'],
        fontSize=13,
        spaceBefore=15,
        spaceAfter=5,
        textColor=colors.HexColor('#0f3460'),
        fontName='Helvetica-Bold'
    )

    desc_style = ParagraphStyle(
        'Description',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceBefore=5,
        spaceAfter=5,
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        fontName='Courier',
        backColor=colors.HexColor('#f5f5f5'),
        borderPadding=8,
        leftIndent=10,
        rightIndent=10,
    )

    param_style = ParagraphStyle(
        'ParamStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        leftIndent=20,
    )

    output_style = ParagraphStyle(
        'OutputStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        leftIndent=20,
        backColor=colors.HexColor('#e8f5e9'),
        borderPadding=5,
    )

    story = []

    # Title
    story.append(Paragraph("SaaS Bench - Agent Tools Reference", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))

    # Introduction
    story.append(Paragraph("Overview", section_style))
    story.append(Paragraph(
        "This document provides a comprehensive reference for all tools available to the AI agent "
        "in SaaS Bench. Each tool includes its purpose, parameters, output format, and example usage.",
        desc_style
    ))
    story.append(Spacer(1, 10))

    # Tool categories and their tools
    tools = [
        # === COST INFORMATION ===
        {
            "category": "Cost Information",
            "name": "get_cost_info",
            "description": "Get current cost structure for compute and capacity. Returns model tier costs, capacity tier costs, and current compute cost multiplier. Use this to understand costs before setting model tiers or capacity.",
            "parameters": "None",
            "output": """{
  "model_tiers": {
    "1": {"cost_per_usage_unit": 0.01, "base_quality": 0.55},
    "2": {"cost_per_usage_unit": 0.03, "base_quality": 0.65},
    "3": {"cost_per_usage_unit": 0.06, "base_quality": 0.75},
    "4": {"cost_per_usage_unit": 0.12, "base_quality": 0.85},
    "5": {"cost_per_usage_unit": 0.24, "base_quality": 0.95}
  },
  "capacity_tiers": {
    "0": {"capacity_units": 30000, "cost_per_day": 500},
    "1": {"capacity_units": 90000, "cost_per_day": 1200},
    "2": {"capacity_units": 240000, "cost_per_day": 3000},
    "3": {"capacity_units": 600000, "cost_per_day": 7000}
  },
  "compute_cost_multiplier": 1.0,
  "note": "Linear pricing: Each tier adds +0.10 quality..."
}""",
            "impact": "None - read only"
        },

        # === PRICING ACTIONS ===
        {
            "category": "Pricing Actions",
            "name": "set_prices",
            "description": "Set monthly subscription prices for plans A, B, C. New prices apply immediately to new signups. Existing subscribers keep old price until their next billing cycle (every 30 days).",
            "parameters": """- A (number, required): Monthly price in $ for Plan A (entry tier)
- B (number, required): Monthly price in $ for Plan B (mid tier)
- C (number, required): Monthly price in $ for Plan C (premium tier)""",
            "output": """Success:
{
  "success": true,
  "message": "Prices updated: A=$29.00, B=$79.00, C=$199.00"
}

Error:
{
  "success": false,
  "message": "Missing price for plan A"
}""",
            "impact": "New prices apply immediately to new signups. Higher prices = more revenue per customer but fewer signups."
        },

        # === MODEL TIER ACTIONS ===
        {
            "category": "Model Tier Actions",
            "name": "set_model_tiers",
            "description": "Set AI model quality tier (1-5) for each plan. Takes effect immediately for all usage. Each usage unit costs: Tier1=$0.01, Tier2=$0.03, Tier3=$0.06, Tier4=$0.12, Tier5=$0.24 (before multiplier).",
            "parameters": """- A (integer, required): Model tier 1-5 for Plan A
- B (integer, required): Model tier 1-5 for Plan B
- C (integer, required): Model tier 1-5 for Plan C

Tier Quality:
  Tier 1: 0.55 base quality
  Tier 2: 0.65 base quality (+0.10)
  Tier 3: 0.75 base quality (+0.10)
  Tier 4: 0.85 base quality (+0.10)
  Tier 5: 0.95 base quality (+0.10)""",
            "output": """Success:
{
  "success": true,
  "message": "Model tiers updated: A=tier2, B=tier3, C=tier4"
}

Error:
{
  "success": false,
  "message": "Tier for plan A must be 1-5"
}""",
            "impact": "Higher tiers = better AI quality = happier customers but higher compute costs. Compute bill = total_usage_units × tier_cost × multiplier."
        },

        # === SPENDING ACTIONS ===
        {
            "category": "Spending Actions",
            "name": "set_daily_spend",
            "description": "Set daily spending on advertising, operations, and development. Deducted from cash EVERY DAY starting today.",
            "parameters": """- advertising (number, required): Daily $ spent on ads. More = more trial signups.
- operations (number, required): Daily $ spent on ops/support. More = faster issue resolution.
- development (number, required): Daily $ spent on product development. More = gradual improvements.""",
            "output": """Success:
{
  "success": true,
  "message": "Daily spend updated: advertising=$500, operations=$1000, development=$500"
}

Error:
{
  "success": false,
  "message": "Spend for advertising cannot be negative"
}""",
            "impact": "Total daily cost = advertising + operations + development. For fine-grained ad targeting, use set_ad_channel_spend."
        },
        {
            "category": "Spending Actions",
            "name": "set_ad_channel_spend",
            "description": "Set per-channel advertising spend for targeted customer acquisition. Different channels reach different customer groups with varying effectiveness.",
            "parameters": """- social_media (number, optional): Daily $ for social media ads. Best for S1.
- search_ads (number, optional): Daily $ for search engine ads. Good for S2/S3.
- linkedin (number, optional): Daily $ for LinkedIn ads. Best for E1/E2/E3.
- content_marketing (number, optional): Daily $ for content marketing. Good for S2/S3/E2.
- referral_program (number, optional): Daily $ for referral program. Boosts word-of-mouth.""",
            "output": """Success:
{
  "success": true,
  "message": "Ad channel spend updated (total=$500/day):\\n  • Social Media Ads=$150\\n  • Search Engine Ads=$150\\n  • LinkedIn Ads=$100\\n  • Content Marketing=$50\\n  • Referral Program=$50"
}

Error:
{
  "success": false,
  "message": "Invalid channels: {'invalid_channel'}. Valid: {'social_media', 'search_ads', ...}"
}""",
            "impact": "Channels have different effectiveness for different customer groups. Use get_ad_channel_info to see details."
        },
        {
            "category": "Spending Actions",
            "name": "get_ad_channel_info",
            "description": "Get info about advertising channels and their effectiveness for each customer group.",
            "parameters": "None",
            "output": """=== Advertising Channels ===

**Social Media Ads** ($150/day)
  Facebook, Instagram, TikTok - targets S1 freelancers/students
  Cost multiplier: 1.0x
  Best for: S1 (35%)
  Good for: S2 (25%), S3 (20%)

**Search Engine Ads** ($150/day)
  Google Ads, Bing - targets S2/S3 who research tools
  Cost multiplier: 1.3x
  Best for: S2 (40%), S3 (35%)
  Good for: E2 (20%)

**LinkedIn Ads** ($100/day)
  Professional network - targets E1/E2/E3 enterprises
  Cost multiplier: 1.8x
  Best for: E2 (45%), E3 (40%), E1 (35%)
  Good for: S2 (20%)

**Content Marketing** ($50/day)
  Blog posts, SEO, whitepapers - targets quality-focused segments
  Cost multiplier: 0.7x
  Best for: S3 (40%), S2 (35%)
  Good for: E2 (30%), E3 (25%)

**Referral Program** ($50/day)
  Customer referrals - targets all groups via word-of-mouth
  Cost multiplier: 0.4x
  Best for: S3 (35%)
  Good for: S2 (30%), E3 (30%), S1 (25%), E2 (25%)

Data returned includes:
{
  "channels": {
    "social_media": {
      "name": "Social Media Ads",
      "description": "...",
      "cost_multiplier": 1.0,
      "best_for": ["S1 (35%)"],
      "good_for": ["S2 (25%)", "S3 (20%)"]
    },
    ...
  },
  "current_spend": {
    "social_media": 150,
    "search_ads": 150,
    ...
  }
}""",
            "impact": "None - read only. Use to decide how to allocate ad budget across channels."
        },

        # === CAPACITY ACTIONS ===
        {
            "category": "Capacity Actions",
            "name": "set_capacity_tier",
            "description": "Set server capacity tier (0-3). Changes immediately. You pay the daily cost EVERY DAY.",
            "parameters": """- tier (integer, required): Capacity tier 0-3

Capacity Tiers:
  Tier 0: 30,000 units/day at $500/day
  Tier 1: 90,000 units/day at $1,200/day
  Tier 2: 240,000 units/day at $3,000/day
  Tier 3: 600,000 units/day at $7,000/day""",
            "output": """Success:
{
  "success": true,
  "message": "Capacity tier set to 1: 90,000 units/day, $1,200/day"
}

Error:
{
  "success": false,
  "message": "Capacity tier must be 0, 1, 2, or 3"
}""",
            "impact": "If usage exceeds capacity, service degrades (overload). Overload increases outage probability and latency."
        },

        # === CUSTOMER COMMUNICATION ===
        {
            "category": "Customer Communication",
            "name": "read_thread",
            "description": "Read last 5 messages from a large customer thread. Returns messages with sender, text, email, and offers. Also includes thread state, type, customer info.",
            "parameters": """- thread_id (integer, required): Thread ID from inbox notification""",
            "output": """{
  "success": true,
  "message": "Read 5 messages from thread 42",
  "data": {
    "thread_id": 42,
    "state": "negotiating",
    "thread_type": "new_lead",
    "customer_id": 157,
    "customer_email": "procurement@acmecorp.com",
    "group_id": "E2",
    "seat_count": 150,
    "messages": [
      {
        "day": 45,
        "sender": "customer",
        "text": "Hi, we're interested in NovaMind for our team of 150...",
        "email": "procurement@acmecorp.com",
        "offer": null
      },
      {
        "day": 46,
        "sender": "agent",
        "text": "Thank you for your interest! I'd be happy to discuss...",
        "email": null,
        "offer": {"plan": "C", "price_per_seat": 45.00, "seats": 150}
      },
      ...
    ]
  }
}""",
            "impact": "None - read only. For full history, use get_thread_history."
        },
        {
            "category": "Customer Communication",
            "name": "get_thread_history",
            "description": "Get full conversation history for a thread. Returns all messages (up to limit) with full details including email addresses, negotiation turn, current offer price.",
            "parameters": """- thread_id (integer, required): Thread ID to get history for
- limit (integer, optional): Maximum messages to return (default 20)""",
            "output": """=== Thread #42 History ===
Type: new_lead
State: negotiating
Customer: ID=157, Group=E2, Seats=150
Customer Email: procurement@acmecorp.com
Turn: 3

--- Messages (5 total) ---
Day 45 - 👤 CUSTOMER <procurement@acmecorp.com>
  "Hi, we're interested in NovaMind for our team of 150..."
Day 46 - 🤖 AGENT [Offer: $45.00/seat]
  "Thank you for your interest! I'd be happy to discuss..."
Day 47 - 👤 CUSTOMER <procurement@acmecorp.com>
  "That's a bit higher than our budget. Can you do $35/seat?"
...

Data includes:
{
  "thread_id": 42,
  "thread_type": "new_lead",
  "state": "negotiating",
  "customer_id": 157,
  "customer_email": "procurement@acmecorp.com",
  "group_id": "E2",
  "seat_count": 150,
  "negotiation_turn": 3,
  "current_offer_price": 45.00,
  "messages": [...]
}""",
            "impact": "None - read only. Use before responding to review full negotiation context."
        },
        {
            "category": "Customer Communication",
            "name": "send_reply",
            "description": "Send a reply message to a large customer thread. Customer will respond based on your message. Can include structured offer for negotiations.",
            "parameters": """- thread_id (integer, required): Thread ID to reply to
- message_text (string, required): Your reply message text
- offer (object, optional): Structured deal offer for negotiation
    - plan (string): Plan name (A, B, or C)
    - price_per_seat (number): Custom price per seat per month
    - seats (integer): Number of seats
    - term_days (integer): Contract term in days
    - price_lock_days (integer): Days to lock this price""",
            "output": """Success:
{
  "success": true,
  "message": "Reply sent to thread 42"
}

Error:
{
  "success": false,
  "message": "Thread 42 not found"
}""",
            "impact": "Customer will respond based on your message and offer. The negotiation logic evaluates your offer against their acceptable price range."
        },
        {
            "category": "Customer Communication",
            "name": "post_update",
            "description": "Post a public announcement to a channel. Customers see this.",
            "parameters": """- channel (string, required): One of 'status', 'pricing', 'release'
    - status: Service health updates
    - pricing: Price change announcements
    - release: New feature announcements
- text (string, required): The announcement text customers will see""",
            "output": """Success:
{
  "success": true,
  "message": "Update posted to status channel"
}

Error:
{
  "success": false,
  "message": "Channel must be 'status', 'pricing', or 'release'"
}""",
            "impact": "Public announcements visible to customers. Use for transparency during incidents or announcing changes."
        },

        # === ANALYTICS ===
        {
            "category": "Analytics (python_exec)",
            "name": "python_exec",
            "description": "Execute Python code for data analysis. This is the primary analytics tool. Has read-only database access with pandas and numpy pre-loaded.",
            "parameters": """- code (string, required): Python code to execute. Use print() to see output.
- timeout_seconds (number, optional): Maximum execution time (default 5s)

PRE-LOADED:
  - conn: SQLite connection (read-only)
  - pandas as pd, numpy as np
  - rows(sql, params) -> list of tuples
  - row(sql, params) -> single tuple or None

AVAILABLE TABLES:
  - customers: customer_id, group_id, created_day, seat_count, email, ...
  - subscriptions: customer_id, plan, listed_price, promotion, effective_price, status, start_day, end_day
  - customer_state: customer_id, satisfaction
  - ledger: day, category, amount, note
  - service_day: day, total_usage_units, p95_ms, error_rate, downtime_minutes
  - config_history: day, price_A/B/C, tier_A/B/C, spend_*, capacity_tier
  - social_media_posts: day, customer_id, sentiment, content, likes, shares
  - messages: thread_id, day, sender, text, email, offer_json
  - threads: thread_id, customer_id, state, thread_type, negotiation_turn
  - notifications: notification_id, day, type, title, summary""",
            "output": """Example queries and their outputs:

# Subscriber count
>>> row("SELECT COUNT(*) FROM subscriptions WHERE status='subscribed' AND end_day IS NULL")
(247,)

# By plan
>>> rows("SELECT plan, COUNT(*) FROM subscriptions WHERE status='subscribed' GROUP BY plan")
[('A', 89), ('B', 112), ('C', 46)]

# Cash balance
>>> row("SELECT SUM(amount) FROM ledger")
(87543.21,)

# Revenue by day (last 7 days)
>>> df = pd.read_sql("SELECT day, SUM(amount) as revenue FROM ledger WHERE type='subscription_payment' AND day > (SELECT MAX(day)-7 FROM ledger) GROUP BY day", conn)
>>> print(df)
   day   revenue
0  358   4521.00
1  359   4789.00
2  360   4234.00
...

# Satisfaction distribution
>>> rows("SELECT ROUND(satisfaction, 1) as sat_bucket, COUNT(*) FROM customer_state GROUP BY sat_bucket ORDER BY sat_bucket")
[(0.3, 5), (0.4, 12), (0.5, 45), (0.6, 78), (0.7, 89), (0.8, 18)]

# Churn rate
>>> total = row("SELECT COUNT(*) FROM subscriptions WHERE status='subscribed'")[0]
>>> churned = row("SELECT COUNT(*) FROM subscriptions WHERE status='cancelled' AND end_day > (SELECT MAX(day)-30 FROM service_day)")[0]
>>> print(f"Churn rate: {churned}/{total} = {churned/total*100:.1f}%")
Churn rate: 23/247 = 9.3%

# Open threads
>>> rows("SELECT t.thread_id, t.thread_type, c.email, c.seat_count FROM threads t JOIN customers c ON t.customer_id=c.customer_id WHERE t.state NOT IN ('closed','cancelled')")
[(42, 'new_lead', 'procurement@acmecorp.com', 150), (45, 'support', 'admin@techstart.io', 75)]""",
            "impact": "None - read only. Can analyze any business data for decision making."
        },

        # === MEMORY ===
        {
            "category": "Memory Management",
            "name": "memory_insert",
            "description": "Insert text at a line number in the agent's memory. Memory persists across turns within a run and is shown in the system prompt.",
            "parameters": """- line (integer, required): Line number to insert at (1-indexed). Use 1 for top, last_line+1 to append.
- content (string, required): Text to insert. Can contain newlines for multiple lines.""",
            "output": """Success:
{
  "success": true,
  "message": "Inserted 2 line(s) at line 1. Memory now has 5 lines."
}

Error:
{
  "success": false,
  "message": "Invalid line number 10. Valid range: 1-5"
}""",
            "impact": "Memory is shown in system prompt every turn. Use to track important notes, decisions, or context."
        },
        {
            "category": "Memory Management",
            "name": "memory_delete",
            "description": "Delete lines from the agent's memory.",
            "parameters": """- start (integer, required): First line to delete (1-indexed)
- end (integer, required): Last line to delete (1-indexed, inclusive)""",
            "output": """Success:
{
  "success": true,
  "message": "Deleted lines 2-4. Memory now has 3 lines."
}

Error:
{
  "success": false,
  "message": "Invalid range 5-10. Valid range: 1-3"
}""",
            "impact": "Removes outdated notes to keep memory relevant and concise."
        },
        {
            "category": "Memory Management",
            "name": "memory_edit",
            "description": "Replace content of a single line in the agent's memory.",
            "parameters": """- line (integer, required): Line number to edit (1-indexed)
- content (string, required): New content for this line""",
            "output": """Success:
{
  "success": true,
  "message": "Updated line 3."
}

Error:
{
  "success": false,
  "message": "Invalid line number 10. Valid range: 1-5"
}""",
            "impact": "Updates existing notes without changing line numbers of other content."
        },

        # === SOCIAL MEDIA & NOTIFICATIONS ===
        {
            "category": "Social Media & Notifications",
            "name": "get_social_posts",
            "description": "Search social media posts about NovaMind. Use to monitor brand sentiment, find complaints to address, or analyze customer feedback.",
            "parameters": """- sentiment (string, optional): Filter by 'positive', 'neutral', or 'negative'
- days (integer, optional): How many days back to search (default 7)
- limit (integer, optional): Max posts to return (default 50)""",
            "output": """Found 23 posts in last 7 days.
👍 Day 358: "NovaMind has completely transformed how I handle client reports..." (45 likes, 12 shares)
👍 Day 357: "Just upgraded to Plan C and the quality difference is amazing..." (32 likes, 8 shares)
😐 Day 356: "NovaMind is decent for basic tasks but struggles with..." (12 likes, 3 shares)
👎 Day 355: "Disappointed with NovaMind - latency issues during peak hours..." (89 likes, 34 shares)
...

Data includes:
{
  "posts": [
    {
      "post_id": 234,
      "day": 358,
      "customer_id": 145,
      "sentiment": "positive",
      "content": "NovaMind has completely transformed how I handle client reports...",
      "likes": 45,
      "shares": 12,
      "virality_score": 0.67,
      "reputation_impact": 0.012
    },
    ...
  ],
  "total": 23
}""",
            "impact": "None - read only. Useful for understanding customer sentiment and identifying issues to address."
        },
        {
            "category": "Social Media & Notifications",
            "name": "expand_notification",
            "description": "Get full details of a notification. The daily summary shows brief headlines - use this to see complete information.",
            "parameters": """- notification_id (integer, required): The notification ID from the daily summary""",
            "output": """=== Notification #157 ===
Type: enterprise_inquiry
Day: 358

Title: New Enterprise Lead: TechCorp (E2, 200 seats)

Summary:
A new enterprise customer from group E2 (Quality-First Enterprises) has initiated contact.
They are interested in deploying NovaMind for 200 seats.
Thread ID: 42

Details:
{
  "customer_id": 157,
  "group_id": "E2",
  "seat_count": 200,
  "estimated_mrr": 9000,
  "thread_id": 42
}

Reference: thread #42

Data includes full notification record with parsed details JSON.""",
            "impact": "None - read only. Use to investigate important notifications before taking action."
        },
        {
            "category": "Social Media & Notifications",
            "name": "get_company_info",
            "description": "Get NovaMind startup backstory and context.",
            "parameters": "None",
            "output": """Company: NovaMind AI
Product: NovaMind Assistant
Mission: Democratize AI assistance for professionals
Founders: Alex Chen (CEO), Jordan Rivera (CTO)

Full context data includes:
{
  "company_name": "NovaMind AI",
  "product_name": "NovaMind Assistant",
  "mission": "Democratize AI assistance for professionals",
  "founders": "Alex Chen (CEO), Jordan Rivera (CTO)",
  "backstory": "Founded in 2024, NovaMind AI emerged from...",
  "founding_story": "...",
  "company_values": "..."
}""",
            "impact": "None - read only. Useful for understanding company context when communicating with customers."
        },
        {
            "category": "Social Media & Notifications",
            "name": "get_customer_group_info",
            "description": "Get info about a customer segment (S1-S3 individuals, E1-E3 enterprises). Returns characteristics, typical use cases, and common feedback patterns.",
            "parameters": """- group_id (string, required): Customer group ID
    - S1: Price-Sensitive Individuals
    - S2: Quality-Focused Individuals
    - S3: Power Users
    - E1: Cost-Cutting Enterprises
    - E2: Quality-First Enterprises
    - E3: Strategic Partners""",
            "output": """=== E2: Quality-First Enterprises ===
Type: Enterprise

Description:
Large organizations that prioritize reliability and quality over cost. Typically
in regulated industries (finance, healthcare, legal) where AI accuracy is critical.
Willing to pay premium prices for premium service.

Typical Use Cases:
- Contract analysis and risk assessment
- Compliance document review
- Client deliverable generation
- Internal knowledge management

Common Complaints:
- Any accuracy issues are unacceptable
- Need enterprise-grade SLAs
- Require audit trails and compliance features
- Slow response to support tickets

Common Praises:
- Appreciate quality improvements
- Value dedicated support
- Recognize investment in reliability
- Loyalty when expectations are met

Data includes full characteristics from customer research.""",
            "impact": "None - read only. Use to understand customer segments for pricing, marketing, and support decisions."
        },

        # === DAY CONTROL ===
        {
            "category": "Day Control",
            "name": "next_day",
            "description": "End the agent's turn for today and advance to the next day. The simulation will not advance until this is called.",
            "parameters": "None",
            "output": """{
  "success": true,
  "message": "Day 358 complete. Advancing to day 359."
}""",
            "impact": "Simulation advances to next day. All daily events are processed (subscriptions, cancellations, social posts, etc.). Agent receives new daily summary."
        },
    ]

    # Group tools by category
    categories = {}
    for tool in tools:
        cat = tool["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(tool)

    # Table of contents
    story.append(Paragraph("Table of Contents", section_style))
    toc_data = []
    tool_num = 1
    for cat, cat_tools in categories.items():
        toc_data.append([f"{cat}", ""])
        for tool in cat_tools:
            toc_data.append([f"    {tool_num}. {tool['name']}", ""])
            tool_num += 1

    toc_table = Table(toc_data, colWidths=[5*inch, 1*inch])
    toc_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(toc_table)
    story.append(PageBreak())

    # Generate each tool section
    tool_num = 1
    for cat, cat_tools in categories.items():
        story.append(Paragraph(cat, section_style))

        for tool in cat_tools:
            # Tool name with number
            story.append(Paragraph(f"{tool_num}. {tool['name']}", tool_name_style))

            # Description
            story.append(Paragraph("<b>Description:</b>", desc_style))
            story.append(Paragraph(tool['description'], desc_style))

            # Parameters
            story.append(Paragraph("<b>Parameters:</b>", desc_style))
            if tool['parameters'] == "None":
                story.append(Paragraph("None", param_style))
            else:
                # Use preformatted for multi-line params
                param_text = tool['parameters'].replace('<', '&lt;').replace('>', '&gt;')
                story.append(Preformatted(param_text, code_style))

            # Output
            story.append(Paragraph("<b>Output:</b>", desc_style))
            output_text = tool['output'].replace('<', '&lt;').replace('>', '&gt;')
            story.append(Preformatted(output_text, code_style))

            # Impact
            story.append(Paragraph("<b>Impact:</b>", desc_style))
            story.append(Paragraph(tool['impact'], desc_style))

            story.append(Spacer(1, 15))
            tool_num += 1

        story.append(PageBreak())

    # Build PDF
    doc.build(story)
    print(f"PDF saved to: {output_path}")


def main():
    output_path = "agent_tools_reference.pdf"
    print("Generating Agent Tools Reference PDF...")
    create_tools_pdf(output_path)
    print("Done!")


if __name__ == '__main__':
    main()
