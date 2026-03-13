#!/usr/bin/env python3
"""Generate PDF report for Oracle simulation trajectory."""

import json
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from datetime import datetime

def load_trajectory(path: str) -> list[dict]:
    """Load trajectory from JSONL file."""
    events = []
    with open(path, 'r') as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    return events

def generate_pdf_report(trajectory_path: str, output_path: str):
    """Generate PDF report from trajectory."""
    events = load_trajectory(trajectory_path)

    # Extract data
    initial_settings = []
    ad_changes = []
    daily_results = []

    for event in events:
        action = event.get('action', '')
        day = event.get('day', 0)
        details = event.get('details', {})
        result = event.get('result', '')

        if action == 'day_result':
            daily_results.append({
                'day': day,
                'cash': details.get('cash', 0),
                'subscribers': details.get('subscribers', 0),
                'revenue': details.get('revenue', 0),
                'costs': details.get('costs', 0),
                'net': details.get('net', 0)
            })
        elif action == 'set_prices':
            initial_settings.append(f"Prices: A=${details.get('A')}, B=${details.get('B')}, C=${details.get('C')}")
        elif action == 'set_model_tiers':
            initial_settings.append(f"Quality Tiers: A={details.get('A')}, B={details.get('B')}, C={details.get('C')}")
        elif action == 'set_daily_spend':
            initial_settings.append(f"Initial Daily Spend: Ads=${details.get('advertising')}")
        elif action in ['reduce_ads', 'cut_ads']:
            ad_changes.append({
                'day': day,
                'action': action,
                'ads': details.get('advertising', 0),
                'result': result
            })

    # Calculate final metrics
    final = daily_results[-1] if daily_results else {}
    initial_cash = 500000
    final_cash = final.get('cash', 0)
    final_subs = final.get('subscribers', 0)
    return_multiple = final_cash / initial_cash

    # Create PDF
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=20,
        alignment=1  # Center
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6
    )

    story = []

    # Title
    story.append(Paragraph("Oracle Policy Simulation Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", body_style))
    story.append(Spacer(1, 20))

    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    summary_data = [
        ['Metric', 'Value'],
        ['Initial Investment', '$500,000'],
        ['Final Cash', f'${final_cash:,.0f}'],
        ['Return Multiple', f'{return_multiple:.2f}x'],
        ['Final Subscribers', f'{final_subs:,}'],
        ['Days Simulated', '365'],
    ]
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#D9E2F3')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    # Oracle Strategy
    story.append(Paragraph("Oracle Strategy", heading_style))
    story.append(Paragraph("The oracle policy uses perfect information about customer C_max distributions:", body_style))
    for setting in initial_settings:
        story.append(Paragraph(f"• {setting}", body_style))
    story.append(Spacer(1, 10))

    # Ad Strategy Changes
    story.append(Paragraph("Advertising Strategy Timeline", heading_style))
    ad_data = [['Day', 'Action', 'Ads/Day', 'Rationale']]
    ad_data.append([0, 'Initial', '$2,000', 'Front-loaded for quick growth'])
    for change in ad_changes:
        ad_data.append([
            change['day'],
            change['action'].replace('_', ' ').title(),
            f"${change['ads']:,}",
            change['result']
        ])

    ad_table = Table(ad_data, colWidths=[0.6*inch, 1.2*inch, 0.8*inch, 3.5*inch])
    ad_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#70AD47')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (0, 0), (2, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E2EFDA')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(ad_table)
    story.append(Spacer(1, 20))

    # Key Milestones
    story.append(Paragraph("Key Milestones", heading_style))
    milestones = []

    # Find when we first turned profitable (positive net)
    for r in daily_results:
        if r['net'] > 0:
            milestones.append(f"Day {r['day']}: First profitable day (net ${r['net']:.0f})")
            break

    # Find when we crossed back to initial investment
    for r in daily_results:
        if r['cash'] >= 500000:
            milestones.append(f"Day {r['day']}: Recovered initial investment (cash ${r['cash']:,.0f})")
            break

    # Find subscriber milestones
    sub_milestones = [100, 250, 500, 750, 1000]
    for m in sub_milestones:
        for r in daily_results:
            if r['subscribers'] >= m:
                milestones.append(f"Day {r['day']}: Reached {m} subscribers")
                break

    for ms in sorted(milestones, key=lambda x: int(x.split(':')[0].replace('Day ', ''))):
        story.append(Paragraph(f"• {ms}", body_style))

    story.append(Spacer(1, 20))

    # Daily Trajectory (sampled)
    story.append(Paragraph("Daily Trajectory (Sampled)", heading_style))

    # Sample days: 1, 7, 14, 30, 60, 90, 120, 180, 270, 365
    sample_days = [1, 7, 14, 30, 60, 90, 120, 180, 270, 365]
    traj_data = [['Day', 'Cash', 'Subscribers', 'Revenue', 'Costs', 'Net']]

    for r in daily_results:
        if r['day'] in sample_days:
            traj_data.append([
                r['day'],
                f"${r['cash']:,.0f}",
                r['subscribers'],
                f"${r['revenue']:,.0f}",
                f"${r['costs']:,.0f}",
                f"${r['net']:,.0f}"
            ])

    traj_table = Table(traj_data, colWidths=[0.5*inch, 1.2*inch, 0.9*inch, 0.9*inch, 0.9*inch, 0.9*inch])
    traj_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#D9E2F3')),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(traj_table)
    story.append(Spacer(1, 20))

    # Final Analysis
    story.append(Paragraph("Final Analysis", heading_style))

    total_revenue = sum(r['revenue'] for r in daily_results)
    total_costs = sum(r['costs'] for r in daily_results)
    total_ads = 2000 * 14 + 500 * 16 + 100 * 30  # Approximate ad spend

    story.append(Paragraph(f"• Total Revenue: ${total_revenue:,.0f}", body_style))
    story.append(Paragraph(f"• Total Costs: ${total_costs:,.0f}", body_style))
    story.append(Paragraph(f"• Net Profit: ${final_cash - initial_cash:,.0f} ({(return_multiple - 1) * 100:.1f}%)", body_style))
    story.append(Paragraph(f"• Final Monthly Run Rate: ~${daily_results[-1]['revenue'] * 30:,.0f}/month", body_style))

    # Build PDF
    doc.build(story)
    print(f"PDF report generated: {output_path}")
    return output_path

if __name__ == '__main__':
    trajectory_path = '/tmp/saas_bench_oracle_trajectory/logs/oracle_trajectory.jsonl'
    output_path = '/tmp/oracle_simulation_report.pdf'
    generate_pdf_report(trajectory_path, output_path)
