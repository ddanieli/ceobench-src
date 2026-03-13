#!/usr/bin/env python3
"""Generate PDF of python_exec documentation."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors

def create_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
    )

    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10,
        textColor=colors.darkblue,
    )

    subheading_style = ParagraphStyle(
        'SubHeading',
        parent=styles['Heading3'],
        fontSize=11,
        spaceBefore=10,
        spaceAfter=5,
        textColor=colors.darkgreen,
    )

    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=8,
        leading=10,
        fontName='Courier',
        backColor=colors.Color(0.95, 0.95, 0.95),
        leftIndent=10,
        rightIndent=10,
        spaceBefore=5,
        spaceAfter=10,
    )

    normal = styles['Normal']

    story = []

    # Title
    story.append(Paragraph("python_exec Tool Documentation", title_style))
    story.append(Paragraph("Execute Python code for data analysis in SaaS Bench", normal))
    story.append(Spacer(1, 20))

    # Overview
    story.append(Paragraph("Overview", heading_style))
    story.append(Paragraph(
        "This is your primary analytics tool. The database contains all business data. "
        "Use this for any analysis that isn't covered by other tools.",
        normal
    ))
    story.append(Spacer(1, 10))

    # Important Note
    story.append(Paragraph("IMPORTANT - USE PRE-LOADED VARIABLES", heading_style))
    story.append(Paragraph(
        "A database connection <b>conn</b> is ALREADY connected to the world database. "
        "DO NOT create your own sqlite3 connection - just use conn directly!",
        normal
    ))
    story.append(Spacer(1, 5))

    story.append(Paragraph("WRONG:", subheading_style))
    story.append(Preformatted("conn = sqlite3.connect('some/path/database.db')  # DON'T DO THIS!", code_style))

    story.append(Paragraph("CORRECT:", subheading_style))
    story.append(Preformatted(
        'print(rows("SELECT * FROM customers LIMIT 5"))\n'
        'df = pd.read_sql("SELECT * FROM ledger", conn)',
        code_style
    ))
    story.append(Spacer(1, 15))

    # Available Tables - with detailed column descriptions
    story.append(Paragraph("Available Tables", heading_style))

    # Define column style for indented bullet points
    column_style = ParagraphStyle(
        'Column',
        parent=normal,
        fontSize=9,
        leftIndent=20,
        spaceBefore=1,
        spaceAfter=1,
    )

    # customers table
    story.append(Paragraph("<b>customers</b> - All customer records", subheading_style))
    story.append(Paragraph("• <b>customer_id</b>: Unique identifier for the customer", column_style))
    story.append(Paragraph("• <b>created_day</b>: Simulation day when customer was created", column_style))
    story.append(Paragraph("• <b>seat_count</b>: Number of user seats the customer has (determines usage scale)", column_style))
    story.append(Paragraph("• <b>email</b>: Customer email address for communication", column_style))
    story.append(Paragraph("• <b>customer_type</b>: Category like 'startup', 'smb', 'enterprise'", column_style))
    story.append(Paragraph("• <b>persona_description</b>: Text describing customer's behavior and preferences", column_style))
    story.append(Spacer(1, 8))

    # subscriptions table
    story.append(Paragraph("<b>subscriptions</b> - Subscription records linking customers to plans", subheading_style))
    story.append(Paragraph("• <b>subscription_id</b>: Unique identifier for the subscription", column_style))
    story.append(Paragraph("• <b>customer_id</b>: Foreign key to customers table", column_style))
    story.append(Paragraph("• <b>plan</b>: Plan tier - 'A' (basic), 'B' (standard), 'C' (premium)", column_style))
    story.append(Paragraph("• <b>listed_price</b>: List price in dollars (before promotions)", column_style))
    story.append(Paragraph("• <b>promotion</b>: Total promotion discount currently applied", column_style))
    story.append(Paragraph("• <b>effective_price</b>: Actual price charged (listed_price - promotion)", column_style))
    story.append(Paragraph("• <b>status</b>: Current state - 'lead', 'trial', 'subscribed', 'cancelled', 'lost', 'free_trial'", column_style))
    story.append(Paragraph("• <b>start_day</b>: Day subscription started", column_style))
    story.append(Paragraph("• <b>end_day</b>: Day subscription ended (NULL if active)", column_style))
    story.append(Paragraph("• <b>billing_day_mod30</b>: Day of month for billing (0-29)", column_style))
    story.append(Spacer(1, 8))

    # daily_usage table
    story.append(Paragraph("<b>daily_usage</b> - Per-customer daily usage metrics", subheading_style))
    story.append(Paragraph("• <b>day</b>: Simulation day", column_style))
    story.append(Paragraph("• <b>customer_id</b>: Foreign key to customers table", column_style))
    story.append(Paragraph("• <b>usage_units</b>: Number of compute units consumed that day", column_style))
    story.append(Spacer(1, 8))

    # ledger table
    story.append(Paragraph("<b>ledger</b> - All financial transactions (revenue and expenses)", subheading_style))
    story.append(Paragraph("• <b>id</b>: Transaction ID", column_style))
    story.append(Paragraph("• <b>day</b>: Simulation day of transaction", column_style))
    story.append(Paragraph("• <b>category</b>: Type of transaction:", column_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- 'subscription_payment': Revenue from customer payments (positive)", column_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- 'compute': Variable compute costs (negative)", column_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- 'capacity': Fixed capacity/infrastructure costs (negative)", column_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- 'advertising': Marketing spend (negative)", column_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- 'operations': Operational costs (negative)", column_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;- 'development': R&amp;D/development costs (negative)", column_style))
    story.append(Paragraph("• <b>amount</b>: Dollar amount (positive=revenue, negative=expense)", column_style))
    story.append(Paragraph("• <b>note</b>: Description of the transaction", column_style))
    story.append(Spacer(1, 8))

    # service_day table
    story.append(Paragraph("<b>service_day</b> - Daily service quality metrics", subheading_style))
    story.append(Paragraph("• <b>day</b>: Simulation day", column_style))
    story.append(Paragraph("• <b>total_usage_units</b>: Total compute units used across all customers", column_style))
    story.append(Paragraph("• <b>p95_ms</b>: 95th percentile response latency in milliseconds", column_style))
    story.append(Paragraph("• <b>error_rate</b>: Fraction of requests that failed (0.0-1.0)", column_style))
    story.append(Paragraph("• <b>downtime_minutes</b>: Minutes of service unavailability", column_style))
    story.append(Paragraph("• <b>capacity_tier</b>: Current infrastructure tier (1=small, 2=medium, 3=large)", column_style))
    story.append(Paragraph("• <b>capacity_units</b>: Maximum compute units the infrastructure can handle", column_style))
    story.append(Spacer(1, 8))

    # config_history table
    story.append(Paragraph("<b>config_history</b> - Historical record of configuration changes", subheading_style))
    story.append(Paragraph("• <b>day</b>: Simulation day", column_style))
    story.append(Paragraph("• <b>price_A, price_B, price_C</b>: Prices for each plan tier", column_style))
    story.append(Paragraph("• <b>tier_A, tier_B, tier_C</b>: Feature tiers for each plan", column_style))
    story.append(Paragraph("• <b>spend_advertising, spend_development, spend_operations</b>: Daily spending amounts", column_style))
    story.append(Paragraph("• <b>capacity_tier</b>: Infrastructure tier setting", column_style))
    story.append(Paragraph("• <b>quota_A, quota_B, quota_C</b>: Usage quotas for each plan", column_style))
    story.append(Spacer(1, 8))

    # social_media_posts table
    story.append(Paragraph("<b>social_media_posts</b> - Customer posts on social media about the service", subheading_style))
    story.append(Paragraph("• <b>post_id</b>: Unique identifier", column_style))
    story.append(Paragraph("• <b>day</b>: Simulation day posted", column_style))
    story.append(Paragraph("• <b>customer_id</b>: Foreign key to customers table", column_style))
    story.append(Paragraph("• <b>content</b>: Text content of the post", column_style))
    story.append(Paragraph("• <b>likes</b>: Number of likes received", column_style))
    story.append(Paragraph("• <b>shares</b>: Number of shares/retweets", column_style))
    story.append(Paragraph("• <b>virality_score</b>: Computed virality metric (higher = more viral)", column_style))
    story.append(Spacer(1, 8))

    # messages table
    story.append(Paragraph("<b>messages</b> - Individual messages within conversation threads", subheading_style))
    story.append(Paragraph("• <b>message_id</b>: Unique identifier", column_style))
    story.append(Paragraph("• <b>thread_id</b>: Foreign key to threads table", column_style))
    story.append(Paragraph("• <b>day</b>: Simulation day sent", column_style))
    story.append(Paragraph("• <b>sender</b>: Who sent it - 'customer', 'agent' (you), or 'system'", column_style))
    story.append(Paragraph("• <b>text</b>: Message content", column_style))
    story.append(Paragraph("• <b>email</b>: Email address if sent via email", column_style))
    story.append(Paragraph("• <b>offer_json</b>: JSON with offer details if this message contains an offer", column_style))
    story.append(Spacer(1, 8))

    # threads table
    story.append(Paragraph("<b>threads</b> - Conversation threads with customers", subheading_style))
    story.append(Paragraph("• <b>thread_id</b>: Unique identifier", column_style))
    story.append(Paragraph("• <b>customer_id</b>: Foreign key to customers table", column_style))
    story.append(Paragraph("• <b>state</b>: Thread state - 'lead', 'evaluation', 'offer', 'active', 'churn_risk', 'cancelled', 'closed'", column_style))
    story.append(Paragraph("• <b>thread_type</b>: Why thread was created - 'new_lead', 'plan_change', 'budget_freeze', 'churn_prevention', 'general'", column_style))
    story.append(Paragraph("• <b>negotiation_turn</b>: Number of back-and-forth exchanges", column_style))
    story.append(Paragraph("• <b>current_offer_price</b>: Most recent price offered (if any)", column_style))
    story.append(Paragraph("• <b>next_reply_day</b>: Day when customer will next respond", column_style))
    story.append(Paragraph("• <b>created_day</b>: Day thread was created", column_style))
    story.append(Paragraph("• <b>replied</b>: Whether agent has replied (0=not replied, 1=replied)", column_style))
    story.append(Spacer(1, 8))

    # notifications table
    story.append(Paragraph("<b>notifications</b> - System notifications for the agent", subheading_style))
    story.append(Paragraph("• <b>notification_id</b>: Unique identifier", column_style))
    story.append(Paragraph("• <b>day</b>: Simulation day created", column_style))
    story.append(Paragraph("• <b>type</b>: Category - 'social_media_post', 'large_customer_message', 'service_alert', 'financial_alert', 'cancellation'", column_style))
    story.append(Paragraph("• <b>title</b>: Short title/headline", column_style))
    story.append(Paragraph("• <b>summary</b>: Brief description", column_style))
    story.append(Paragraph("• <b>details_json</b>: JSON with additional details", column_style))
    story.append(Paragraph("• <b>reference_id</b>: ID of related entity (thread, post, etc.)", column_style))
    story.append(Paragraph("• <b>reference_type</b>: Type of reference - 'post', 'thread', 'event', etc.", column_style))

    story.append(Spacer(1, 15))

    # Pre-loaded Variables
    story.append(Paragraph("Pre-loaded Variables", heading_style))
    story.append(Paragraph("<b>conn</b> - SQLite connection to the world database (read-only)", normal))
    story.append(Paragraph("<b>pandas as pd</b>, <b>numpy as np</b> - Data analysis libraries", normal))
    story.append(Paragraph("<b>rows(sql, params)</b> - Returns list of tuples for query results", normal))
    story.append(Paragraph("<b>row(sql, params)</b> - Returns single tuple or None", normal))
    story.append(Spacer(1, 15))

    # Example Queries
    story.append(Paragraph("Example Queries", heading_style))

    examples = [
        ("Get current subscriber count",
         'row("SELECT COUNT(*) FROM subscriptions WHERE status=\'subscribed\' AND end_day IS NULL")'),
        ("Get total monthly revenue",
         'row("SELECT SUM(effective_price) FROM subscriptions WHERE status=\'subscribed\' AND end_day IS NULL")'),
        ("Get subscriber count by plan",
         'rows("SELECT plan, COUNT(*) FROM subscriptions WHERE status=\'subscribed\' AND end_day IS NULL GROUP BY plan")'),
        ("Get recent cancellations",
         'rows("SELECT customer_id, plan, end_day FROM subscriptions WHERE status=\'cancelled\' ORDER BY end_day DESC LIMIT 10")'),
        ("Get daily revenue trend (last 7 days)",
         'pd.read_sql("SELECT day, SUM(amount) as revenue FROM ledger WHERE category=\'subscription_payment\' AND day > (SELECT MAX(day)-7 FROM ledger) GROUP BY day", conn)'),
        ("Get recent social media posts",
         'rows("SELECT day, content, likes, shares FROM social_media_posts WHERE day > (SELECT MAX(day)-7 FROM social_media_posts) ORDER BY likes DESC LIMIT 10")'),
        ("Get cash balance",
         'row("SELECT SUM(amount) FROM ledger")'),
        ("Get churn rate (last 30 days)",
         'total = row("SELECT COUNT(*) FROM subscriptions WHERE status=\'subscribed\'")[0]\n'
         'churned = row("SELECT COUNT(*) FROM subscriptions WHERE status=\'cancelled\' AND end_day > (SELECT MAX(day)-30 FROM service_day)")[0]\n'
         'print(f"Churn rate: {churned}/{total} = {churned/total*100:.1f}%")'),
    ]

    for title, code in examples:
        story.append(Paragraph(f"<b>{title}</b>", subheading_style))
        story.append(Preformatted(code, code_style))

    story.append(Spacer(1, 15))

    # Message History Queries
    story.append(Paragraph("Message History Queries", heading_style))

    msg_examples = [
        ("Get all messages for a specific thread",
         '''rows(\'\'\'
    SELECT m.day, m.sender, m.email, m.text, m.offer_json
    FROM messages m
    WHERE m.thread_id = ?
    ORDER BY m.message_id ASC
\'\'\', (thread_id,))'''),
        ("Get thread info with customer details",
         '''row(\'\'\'
    SELECT t.thread_id, t.thread_type, t.state, t.negotiation_turn,
           c.customer_id, c.email, c.seat_count
    FROM threads t
    JOIN customers c ON t.customer_id = c.customer_id
    WHERE t.thread_id = ?
\'\'\', (thread_id,))'''),
        ("Get all open negotiation threads",
         '''rows(\'\'\'
    SELECT t.thread_id, t.thread_type, t.state, c.email, c.seat_count
    FROM threads t
    JOIN customers c ON t.customer_id = c.customer_id
    WHERE t.state NOT IN (\'closed\', \'cancelled\')
\'\'\')'''),
    ]

    for title, code in msg_examples:
        story.append(Paragraph(f"<b>{title}</b>", subheading_style))
        story.append(Preformatted(code, code_style))

    doc.build(story)
    print(f"PDF generated: {output_path}")

if __name__ == "__main__":
    create_pdf("/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench/python_exec_documentation.pdf")
