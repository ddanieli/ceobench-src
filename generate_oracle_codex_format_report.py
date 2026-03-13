#!/usr/bin/env python3
"""Generate PDF report for Oracle simulation in same format as Codex runs."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import markdown
    from weasyprint import HTML
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


@dataclass
class MergedEvent:
    """A single event in the merged timeline."""
    timestamp: str
    day: int
    source: str  # 'env' or 'agent'
    event_type: str
    summary: str
    details: Optional[Dict[str, Any]] = None


def load_oracle_trajectory(trajectory_path: str) -> List[Dict]:
    """Load oracle trajectory from JSONL file."""
    events = []
    with open(trajectory_path, 'r') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    return events


def convert_to_merged_events(oracle_events: List[Dict]) -> List[MergedEvent]:
    """Convert oracle events to MergedEvent format matching Codex."""
    merged = []

    for event in oracle_events:
        day = event.get('day', 0)
        action = event.get('action', '')
        details = event.get('details', {})
        result = event.get('result', '')
        timestamp = event.get('timestamp', '')

        if action == 'day_result':
            # Daily state - same as Codex 'daily_state'
            cash = details.get('cash', 0)
            subs = details.get('subscribers', 0)
            revenue = details.get('revenue', 0)
            costs = details.get('costs', 0)
            net = details.get('net', 0)

            summary = f"Day {day} End: Cash=${cash:,.0f}, Revenue=${revenue:,.0f}, Costs=${costs:,.0f}, Net=${net:+,.0f}, Subs={subs}"

            merged.append(MergedEvent(
                timestamp=timestamp,
                day=day,
                source='env',
                event_type='daily_state',
                summary=summary,
                details={
                    'cash': cash,
                    'subscribers': subs,
                    'revenue': revenue,
                    'costs': costs,
                    'net': net,
                    'mrr': revenue * 30  # Approximate MRR
                }
            ))
        elif action.startswith('set_'):
            # Tool call - initial setup
            merged.append(MergedEvent(
                timestamp=timestamp,
                day=day,
                source='agent',
                event_type='tool_call',
                summary=f"Tool: {action} -> {details}",
                details={'tool': action, 'args': details, 'result': result}
            ))

            # Add rationale for setup actions
            if result:
                merged.append(MergedEvent(
                    timestamp=timestamp,
                    day=day,
                    source='agent',
                    event_type='rationale',
                    summary=f"Rationale: {result}",
                    details={'full_rationale': result, 'context': action}
                ))
        elif action in ['reduce_ads', 'cut_ads', 'scale_capacity']:
            # Tool call - strategy change
            merged.append(MergedEvent(
                timestamp=timestamp,
                day=day,
                source='agent',
                event_type='tool_call',
                summary=f"Tool: {action} -> {details}",
                details={'tool': action, 'args': details, 'result': result}
            ))

            # Add rationale
            if result:
                merged.append(MergedEvent(
                    timestamp=timestamp,
                    day=day,
                    source='agent',
                    event_type='rationale',
                    summary=f"Rationale: {result}",
                    details={'full_rationale': result, 'context': action}
                ))

    return merged


def generate_markdown_report(oracle_events: List[Dict]) -> str:
    """Generate a Markdown report matching Codex format."""
    merged = convert_to_merged_events(oracle_events)

    # Find final state
    daily_states = [e for e in merged if e.event_type == 'daily_state']
    final_state = daily_states[-1] if daily_states else None

    # Calculate stats
    total_tool_calls = len([e for e in merged if e.event_type == 'tool_call'])
    total_rationales = len([e for e in merged if e.event_type == 'rationale'])

    lines = [
        "# SaaS Bench Oracle Policy Run Report",
        "",
        "## Run Information",
        "",
        f"- **Run ID**: oracle_baseline",
        f"- **Agent**: Oracle (Perfect Information)",
        f"- **Model**: Programmatic Policy",
        f"- **Scenario**: default",
        f"- **Seed**: 42",
        f"- **Report Generated**: {datetime.now().isoformat()}",
        "",
    ]

    # Summary
    lines.extend([
        "## Summary",
        "",
    ])

    if final_state and final_state.details:
        d = final_state.details
        initial_cash = 500000
        final_cash = d.get('cash', 0)
        return_mult = final_cash / initial_cash

        lines.extend([
            f"- **Final Day**: {final_state.day}",
            f"- **Initial Cash**: ${initial_cash:,.2f}",
            f"- **Final Cash**: ${final_cash:,.2f}",
            f"- **Return Multiple**: {return_mult:.2f}x ({(return_mult - 1) * 100:+.1f}%)",
            f"- **Final Subscribers**: {d.get('subscribers', 0)}",
            "",
        ])

    # Statistics
    lines.extend([
        "## Statistics",
        "",
        f"- Tool calls: {total_tool_calls}",
        f"- Rationales logged: {total_rationales}",
        f"- Days simulated: 365",
        "",
    ])

    # Oracle Strategy Section
    lines.extend([
        "## Oracle Strategy",
        "",
        "The Oracle policy uses perfect information about customer C_max distributions:",
        "",
        "### Pricing",
        "- Plan A: $25/month (targets customers with low C_max)",
        "- Plan B: $69/month (targets mid-range customers)",
        "- Plan C: $129/month (targets high-value customers)",
        "",
        "### Quality Tiers",
        "- Plan A: Model tier 4",
        "- Plan B: Model tier 5",
        "- Plan C: Model tier 5",
        "",
        "### Advertising Strategy",
        "- Days 0-13: $2,000/day (heavy initial spend for growth)",
        "- Days 14-29: $500/day (reduced as subscriber base established)",
        "- Days 30-59: $100/day (minimal spend, rely on organic)",
        "- Days 60+: $0/day (word-of-mouth only)",
        "",
        "### Channel Mix",
        "- Social Media: 35%",
        "- Search Ads: 15%",
        "- Content Marketing: 10%",
        "- Referral Program: 40%",
        "",
    ])

    # Day-by-day breakdown (sampled for readability)
    lines.extend([
        "## Day-by-Day Timeline",
        "",
    ])

    current_day = -1
    sample_days = set([0, 1, 7, 14, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 365])

    # Also include days with strategy changes
    for event in merged:
        if event.event_type == 'tool_call' and event.day > 0:
            sample_days.add(event.day)

    for event in merged:
        if event.day not in sample_days:
            continue

        if event.day != current_day:
            current_day = event.day
            lines.append(f"### Day {current_day}")
            lines.append("")

        # Format event
        source_icon = "🤖" if event.source == 'agent' else "🌍"
        lines.append(f"- {source_icon} **{event.event_type}**: {event.summary}")

    lines.append("")

    # Agent Rationales Section
    rationales = [e for e in merged if e.event_type == 'rationale']
    if rationales:
        lines.extend([
            "## Agent Rationales",
            "",
        ])

        for rat in rationales:
            context = rat.details.get('context', 'General') if rat.details else 'General'
            full_rationale = rat.details.get('full_rationale', rat.summary) if rat.details else rat.summary
            lines.extend([
                f"### Day {rat.day} - {context}",
                "",
                full_rationale,
                "",
            ])

    # Full trajectory table
    lines.extend([
        "## Full Daily Trajectory",
        "",
        "| Day | Cash | Subscribers | Revenue | Costs | Net |",
        "|-----|------|-------------|---------|-------|-----|",
    ])

    for event in merged:
        if event.event_type == 'daily_state' and event.details:
            d = event.details
            lines.append(f"| {event.day} | ${d.get('cash', 0):,.0f} | {d.get('subscribers', 0)} | ${d.get('revenue', 0):,.0f} | ${d.get('costs', 0):,.0f} | ${d.get('net', 0):+,.0f} |")

    return "\n".join(lines)


def generate_pdf_with_reportlab(oracle_events: List[Dict], output_path: str):
    """Generate PDF using reportlab."""
    merged = convert_to_merged_events(oracle_events)
    daily_states = [e for e in merged if e.event_type == 'daily_state']
    final_state = daily_states[-1] if daily_states else None

    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           topMargin=0.5*inch, bottomMargin=0.5*inch,
                           leftMargin=0.5*inch, rightMargin=0.5*inch)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=15, alignment=1)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=12, spaceBefore=12, spaceAfter=8)
    body_style = ParagraphStyle('CustomBody', parent=styles['Normal'], fontSize=9, spaceAfter=4)
    small_style = ParagraphStyle('Small', parent=styles['Normal'], fontSize=8, spaceAfter=2)

    story = []

    # Title
    story.append(Paragraph("SaaS Bench Oracle Policy Run Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style))
    story.append(Spacer(1, 15))

    # Run Information
    story.append(Paragraph("Run Information", heading_style))
    info_data = [
        ['Run ID', 'oracle_baseline'],
        ['Agent', 'Oracle (Perfect Information)'],
        ['Model', 'Programmatic Policy'],
        ['Scenario', 'default'],
        ['Seed', '42'],
    ]
    info_table = Table(info_data, colWidths=[1.5*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))

    # Summary
    story.append(Paragraph("Summary", heading_style))
    if final_state and final_state.details:
        d = final_state.details
        initial_cash = 500000
        final_cash = d.get('cash', 0)
        return_mult = final_cash / initial_cash

        summary_data = [
            ['Metric', 'Value'],
            ['Final Day', '365'],
            ['Initial Cash', '$500,000'],
            ['Final Cash', f"${final_cash:,.0f}"],
            ['Return Multiple', f"{return_mult:.2f}x ({(return_mult - 1) * 100:+.1f}%)"],
            ['Final Subscribers', f"{d.get('subscribers', 0):,}"],
        ]
        summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#D9E2F3')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        story.append(summary_table)
    story.append(Spacer(1, 15))

    # Oracle Strategy
    story.append(Paragraph("Oracle Strategy", heading_style))
    story.append(Paragraph("The Oracle policy uses perfect information about customer C_max distributions:", body_style))
    story.append(Spacer(1, 5))

    strategy_data = [
        ['Component', 'Configuration', 'Rationale'],
        ['Prices', 'A=$25, B=$69, C=$129', 'Based on customer C_max distributions'],
        ['Quality', 'A=Tier 4, B=Tier 5, C=Tier 5', 'High quality for retention'],
        ['Ads D0-13', '$2,000/day', 'Front-loaded for quick growth'],
        ['Ads D14-29', '$500/day', 'Reduced as base established'],
        ['Ads D30-59', '$100/day', 'Minimal, rely on organic'],
        ['Ads D60+', '$0/day', 'Word-of-mouth only'],
    ]
    strategy_table = Table(strategy_data, colWidths=[1.2*inch, 1.8*inch, 2.5*inch])
    strategy_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#70AD47')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E2EFDA')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    story.append(strategy_table)
    story.append(Spacer(1, 15))

    # Key Milestones
    story.append(Paragraph("Key Milestones", heading_style))
    milestones = []
    for ds in daily_states:
        d = ds.details
        if d:
            if d.get('net', 0) > 0 and not any('profitable' in m for m in milestones):
                milestones.append(f"Day {ds.day}: First profitable day (net ${d.get('net', 0):,.0f})")
            if d.get('cash', 0) >= 500000 and not any('recovered' in m.lower() for m in milestones):
                milestones.append(f"Day {ds.day}: Recovered initial investment (cash ${d.get('cash', 0):,.0f})")
            if d.get('subscribers', 0) >= 100 and not any('100 sub' in m for m in milestones):
                milestones.append(f"Day {ds.day}: Reached 100 subscribers")
            if d.get('subscribers', 0) >= 500 and not any('500 sub' in m for m in milestones):
                milestones.append(f"Day {ds.day}: Reached 500 subscribers")
            if d.get('subscribers', 0) >= 1000 and not any('1000 sub' in m for m in milestones):
                milestones.append(f"Day {ds.day}: Reached 1000 subscribers")

    for m in milestones[:6]:  # Limit to 6 milestones
        story.append(Paragraph(f"• {m}", body_style))
    story.append(Spacer(1, 15))

    # Day-by-Day Timeline (sampled)
    story.append(Paragraph("Day-by-Day Timeline (Sampled)", heading_style))

    sample_days = [1, 7, 14, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 365]
    traj_data = [['Day', 'Cash', 'Subs', 'Revenue', 'Costs', 'Net']]

    for ds in daily_states:
        if ds.day in sample_days and ds.details:
            d = ds.details
            traj_data.append([
                ds.day,
                f"${d.get('cash', 0):,.0f}",
                d.get('subscribers', 0),
                f"${d.get('revenue', 0):,.0f}",
                f"${d.get('costs', 0):,.0f}",
                f"${d.get('net', 0):+,.0f}"
            ])

    traj_table = Table(traj_data, colWidths=[0.5*inch, 1.1*inch, 0.6*inch, 0.8*inch, 0.7*inch, 0.8*inch])
    traj_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#D9E2F3')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(traj_table)

    # Page break for full trajectory
    story.append(PageBreak())

    # Full Daily Trajectory
    story.append(Paragraph("Full Daily Trajectory", heading_style))

    # Split into chunks of 50 days per table for readability
    full_traj_data = [['Day', 'Cash', 'Subs', 'Rev', 'Costs', 'Net']]
    for ds in daily_states:
        if ds.details:
            d = ds.details
            full_traj_data.append([
                ds.day,
                f"${d.get('cash', 0)/1000:.0f}k",
                d.get('subscribers', 0),
                f"${d.get('revenue', 0):,.0f}",
                f"${d.get('costs', 0):,.0f}",
                f"${d.get('net', 0):+,.0f}"
            ])

    # Create table in chunks
    chunk_size = 60
    for i in range(0, len(full_traj_data), chunk_size):
        chunk = [full_traj_data[0]] + full_traj_data[max(1, i):i+chunk_size]
        if len(chunk) > 1:
            chunk_table = Table(chunk, colWidths=[0.4*inch, 0.7*inch, 0.5*inch, 0.6*inch, 0.6*inch, 0.6*inch])
            chunk_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(chunk_table)
            story.append(Spacer(1, 10))

    # Build PDF
    doc.build(story)
    print(f"PDF report generated: {output_path}")
    return output_path


def main():
    trajectory_path = '/tmp/saas_bench_oracle_trajectory/logs/oracle_trajectory.jsonl'
    output_path = '/tmp/oracle_codex_format_report.pdf'

    # Load oracle events
    oracle_events = load_oracle_trajectory(trajectory_path)

    if HAS_REPORTLAB:
        generate_pdf_with_reportlab(oracle_events, output_path)
    elif HAS_WEASYPRINT:
        md_content = generate_markdown_report(oracle_events)
        html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.4; font-size: 10pt; }}
                h1 {{ color: #333; border-bottom: 2px solid #333; padding-bottom: 10px; }}
                h2 {{ color: #555; border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-top: 20px; }}
                h3 {{ color: #666; margin-top: 15px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9pt; }}
                th, td {{ border: 1px solid #ddd; padding: 4px 8px; text-align: left; }}
                th {{ background: #4472C4; color: white; }}
                tr:nth-child(even) {{ background: #f9f9f9; }}
            </style>
        </head>
        <body>{html_content}</body>
        </html>
        """
        HTML(string=styled_html).write_pdf(output_path)
        print(f"PDF report generated: {output_path}")
    else:
        # Fallback to markdown
        md_content = generate_markdown_report(oracle_events)
        md_path = output_path.replace('.pdf', '.md')
        with open(md_path, 'w') as f:
            f.write(md_content)
        print(f"Markdown report generated: {md_path}")


if __name__ == '__main__':
    main()
