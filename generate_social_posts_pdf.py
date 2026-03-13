#!/usr/bin/env python3
"""Generate social media posts with LLM and create PDF report."""

import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime
from openai import OpenAI
from numpy.random import Generator, PCG64
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

from saas_bench.config import BenchmarkConfig
from saas_bench.database import (
    init_database, get_customer_persona,
    add_social_media_post, get_world_context
)
from saas_bench.personas import (
    initialize_all_personas, determine_post_sentiment,
    calculate_virality, calculate_reputation_impact
)
from saas_bench.customer_llm import CustomerSimulator


def setup_test_customers(conn: sqlite3.Connection, rng: Generator):
    """Create test customers with varied satisfaction levels."""
    # Set world context
    conn.execute("INSERT OR REPLACE INTO world_context (key, value) VALUES ('product_name', 'NovaMind')")
    conn.execute("INSERT OR REPLACE INTO world_context (key, value) VALUES ('company_name', 'NovaMind AI')")

    # More diverse test customers
    test_customers = [
        # Small customers - varied satisfaction
        (1, 'S1', 'small', 0.95, 'Ecstatic freelancer - loves the tool'),
        (2, 'S1', 'small', 0.75, 'Satisfied budget user'),
        (3, 'S1', 'small', 0.25, 'Frustrated price-conscious user'),
        (4, 'S2', 'small', 0.85, 'Happy quality-focused professional'),
        (5, 'S2', 'small', 0.50, 'Neutral professional - mixed feelings'),
        (6, 'S2', 'small', 0.20, 'Disappointed professional - quality issues'),
        (7, 'S3', 'small', 0.90, 'Power user - impressed with capabilities'),
        (8, 'S3', 'small', 0.40, 'Power user - performance concerns'),

        # Enterprise customers
        (9, 'E1', 'large', 0.70, 'Cost-cutting enterprise - decent value'),
        (10, 'E1', 'large', 0.30, 'Cost-cutting enterprise - not worth the price'),
        (11, 'E2', 'large', 0.80, 'Quality-first enterprise - meeting expectations'),
        (12, 'E2', 'large', 0.15, 'Quality-first enterprise - COMPANY CAUSED DROP'),
        (13, 'E3', 'large', 0.65, 'Strategic partner - solid relationship'),
        (14, 'E3', 'large', 0.18, 'Strategic partner - COMPANY CAUSED DROP'),
    ]

    for cust_id, group_id, cust_type, satisfaction, scenario in test_customers:
        # Insert customer with all required fields
        conn.execute("""
            INSERT OR REPLACE INTO customers
            (customer_id, group_id, customer_type, created_day, seat_count, usage_demand,
             q_min, c_max, quality_sensitivity, price_sensitivity,
             willingness_to_pay, usage_scale, patience, expected_quality)
            VALUES (?, ?, ?, 0, ?, ?, ?, ?, 0.5, 0.5, 100, 1.0, 0.5, 0.5)
        """, (cust_id, group_id, cust_type, 50 if cust_type == 'large' else 1, 50, 0.4, 100))

        # Insert customer state
        conn.execute("""
            INSERT OR REPLACE INTO customer_state
            (customer_id, satisfaction, open_issue_days, relationship)
            VALUES (?, ?, ?, ?)
        """, (cust_id, satisfaction, 0, 0.5))

        # Insert subscription (needed for simulation)
        conn.execute("""
            INSERT OR REPLACE INTO subscriptions
            (subscription_id, customer_id, plan, listed_price, promotion, effective_price, start_day, status, billing_day_mod30)
            VALUES (?, ?, 'B', 50, 0.0, 50.0, 0, 'subscribed', 1)
        """, (cust_id, cust_id))

    conn.commit()

    # Initialize personas
    initialize_all_personas(conn)

    return test_customers


def generate_posts(config: BenchmarkConfig, test_customers: list, conn: sqlite3.Connection,
                   simulator: CustomerSimulator, rng: Generator) -> list:
    """Generate social media posts for all test customers."""
    all_posts = []

    for cust_id, group_id, cust_type, satisfaction, scenario in test_customers:
        print(f"  Generating post for Customer #{cust_id}: {scenario[:40]}...")

        # Get persona info
        persona = get_customer_persona(conn, cust_id)

        # Determine sentiment
        if satisfaction <= 0.2:
            sentiment = 'negative'
        elif satisfaction >= 0.85:
            sentiment = 'positive'
        else:
            sentiment = determine_post_sentiment(satisfaction, rng)

        # Build quality_change context for company-caused drops
        quality_change = None
        if 'COMPANY CAUSED DROP' in scenario:
            # Simulate quality degradation journey
            quality_change = {
                'previous_quality': 0.78,  # Was good before
                'current_quality': 0.45,   # Now degraded
                'change_reason': 'model_downgrade',
                'days_since_change': 14,
            }
        elif satisfaction <= 0.3 and satisfaction > 0.2:
            # Moderate dissatisfaction - gradual decline
            quality_change = {
                'previous_quality': 0.65,
                'current_quality': 0.50,
                'change_reason': 'quality_regression',
                'days_since_change': 30,
            }

        # Generate post with LLM
        response = simulator.generate_social_post(
            day=1,
            customer_id=cust_id,
            satisfaction=satisfaction,
            group_id=group_id,
            sentiment=sentiment,
            quality_change=quality_change
        )

        # Calculate engagement metrics
        likes, shares, virality = calculate_virality(sentiment, group_id, rng)
        rep_impact = calculate_reputation_impact(sentiment, virality, group_id, rng)

        # Store post
        add_social_media_post(
            conn, day=1, customer_id=cust_id, sentiment=sentiment,
            content=response.text, likes=likes, shares=shares,
            virality_score=virality, reputation_impact=rep_impact
        )

        all_posts.append({
            'customer_id': cust_id,
            'group_id': group_id,
            'customer_type': cust_type,
            'scenario': scenario,
            'satisfaction': satisfaction,
            'sentiment': sentiment,
            'text': response.text,
            'likes': likes,
            'shares': shares,
            'virality': virality,
            'rep_impact': rep_impact,
            'persona': persona,
            'input_tokens': response.input_tokens,
            'output_tokens': response.output_tokens,
        })

    return all_posts


def create_pdf_report(posts: list, config: BenchmarkConfig, output_path: str):
    """Create a PDF report with all generated posts."""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=72)

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#1a1a2e')
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
        textColor=colors.HexColor('#16213e')
    )

    subheading_style = ParagraphStyle(
        'SubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceBefore=15,
        spaceAfter=5,
        textColor=colors.HexColor('#0f3460')
    )

    post_style = ParagraphStyle(
        'PostStyle',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        spaceBefore=10,
        spaceAfter=10,
        leftIndent=20,
        rightIndent=20,
        backColor=colors.HexColor('#f8f9fa'),
        borderPadding=10,
    )

    meta_style = ParagraphStyle(
        'MetaStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#6c757d'),
        spaceBefore=5,
    )

    story = []

    # Title
    story.append(Paragraph("SaaS Bench - Social Media Posts Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", meta_style))
    story.append(Spacer(1, 20))

    # Configuration info
    story.append(Paragraph("Model Configuration", heading_style))
    config_data = [
        ["Social Post Model", config.social_post_llm_model],
        ["Reasoning Effort", config.social_post_llm_reasoning_effort],
        ["Agent Model", config.agent_llm_model],
    ]
    config_table = Table(config_data, colWidths=[2*inch, 3*inch])
    config_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e9ecef')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#212529')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
    ]))
    story.append(config_table)
    story.append(Spacer(1, 20))

    # Summary statistics
    story.append(Paragraph("Summary Statistics", heading_style))
    positive = sum(1 for p in posts if p['sentiment'] == 'positive')
    neutral = sum(1 for p in posts if p['sentiment'] == 'neutral')
    negative = sum(1 for p in posts if p['sentiment'] == 'negative')
    total_rep = sum(p['rep_impact'] for p in posts)
    total_likes = sum(p['likes'] for p in posts)
    total_shares = sum(p['shares'] for p in posts)

    summary_data = [
        ["Total Posts", str(len(posts))],
        ["Positive", f"{positive} ({positive/len(posts)*100:.0f}%)"],
        ["Neutral", f"{neutral} ({neutral/len(posts)*100:.0f}%)"],
        ["Negative", f"{negative} ({negative/len(posts)*100:.0f}%)"],
        ["Total Reputation Impact", f"{total_rep:+.4f}"],
        ["Total Engagement", f"{total_likes} likes, {total_shares} shares"],
    ]
    summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e9ecef')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#212529')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
    ]))
    story.append(summary_table)

    story.append(PageBreak())

    # Group posts by sentiment
    for sentiment_type, sentiment_label, sentiment_color in [
        ('positive', 'Positive Posts', '#28a745'),
        ('neutral', 'Neutral Posts', '#6c757d'),
        ('negative', 'Negative Posts', '#dc3545'),
    ]:
        sentiment_posts = [p for p in posts if p['sentiment'] == sentiment_type]
        if not sentiment_posts:
            continue

        story.append(Paragraph(f"{sentiment_label} ({len(sentiment_posts)})",
                              ParagraphStyle('SentimentHeading',
                                           parent=heading_style,
                                           textColor=colors.HexColor(sentiment_color))))
        story.append(Spacer(1, 10))

        for post in sentiment_posts:
            # Customer info
            persona = post.get('persona') or {}
            name = persona.get('name', f"Customer #{post['customer_id']}")
            job = persona.get('job_title', 'Unknown')

            story.append(Paragraph(
                f"<b>{name}</b> ({post['group_id']}) - {job}",
                subheading_style
            ))

            # Scenario and satisfaction
            story.append(Paragraph(
                f"Scenario: {post['scenario']}<br/>"
                f"Satisfaction: {post['satisfaction']:.0%} | "
                f"Virality: {post['virality']:.2f} | "
                f"Rep Impact: {post['rep_impact']:+.3f}",
                meta_style
            ))

            # The post content
            post_text = post['text'] if post['text'] else "(Empty post generated)"
            story.append(Paragraph(f'"{post_text}"', post_style))

            # Engagement
            story.append(Paragraph(
                f"👍 {post['likes']} likes  |  🔄 {post['shares']} shares  |  "
                f"Tokens: {post['input_tokens']}→{post['output_tokens']}",
                meta_style
            ))

            story.append(Spacer(1, 15))

        story.append(Spacer(1, 20))

    # Company-caused drops section
    story.append(PageBreak())
    story.append(Paragraph("Company-Caused Plan Drops",
                          ParagraphStyle('DropHeading',
                                       parent=heading_style,
                                       textColor=colors.HexColor('#dc3545'))))

    story.append(Paragraph(
        "These posts were triggered when company-side changes (model tier reduction, "
        "quality degradation, outages) caused a customer's plan to fall below their "
        "participation curve. This results in forced negative sentiment with high "
        "reputation damage probability.",
        styles['Normal']
    ))
    story.append(Spacer(1, 15))

    drop_posts = [p for p in posts if 'COMPANY CAUSED DROP' in p['scenario']]
    for post in drop_posts:
        persona = post.get('persona') or {}
        name = persona.get('name', f"Customer #{post['customer_id']}")

        story.append(Paragraph(f"<b>{name}</b> ({post['group_id']})", subheading_style))
        story.append(Paragraph(f"Scenario: {post['scenario']}", meta_style))
        story.append(Paragraph(
            f"Satisfaction: {post['satisfaction']:.0%} | Rep Impact: {post['rep_impact']:+.4f}",
            meta_style
        ))

        post_text = post['text'] if post['text'] else "(Empty post generated)"
        story.append(Paragraph(f'"{post_text}"', post_style))
        story.append(Spacer(1, 15))

    # Build PDF
    doc.build(story)
    print(f"\nPDF saved to: {output_path}")


def main():
    print("=" * 70)
    print("SOCIAL MEDIA POSTS PDF GENERATION")
    print("=" * 70)

    # Initialize
    config = BenchmarkConfig()
    rng = Generator(PCG64(42))

    print(f"\nModel Configuration:")
    print(f"  Social Post Model: {config.social_post_llm_model}")
    print(f"  Social Post Reasoning: {config.social_post_llm_reasoning_effort}")
    print()

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        conn = init_database(db_path)

        # Setup test customers
        print("Setting up test customers...")
        test_customers = setup_test_customers(conn, rng)
        print(f"  Created {len(test_customers)} test customers\n")

        # Initialize OpenAI client
        client = OpenAI()

        # Create customer simulator
        simulator = CustomerSimulator(client, conn, config)

        # Generate posts
        print("Generating social media posts with LLM...")
        posts = generate_posts(config, test_customers, conn, simulator, rng)
        print(f"\nGenerated {len(posts)} posts\n")

        conn.close()

    # Create PDF report
    output_path = "social_media_posts_report.pdf"
    print("Creating PDF report...")
    create_pdf_report(posts, config, output_path)

    print("\nDone!")


if __name__ == '__main__':
    main()
