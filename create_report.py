#!/usr/bin/env python3
"""Create PDF report from 10-day benchmark run."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
import re

def create_report(log_path: str, output_path: str):
    """Create PDF report from log file."""

    # Read log content
    with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    # Create PDF
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )

    # Styles
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER,
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10,
        textColor=colors.darkblue,
    )

    code_style = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7,
        leading=9,
        alignment=TA_LEFT,
        wordWrap='CJK',
    )

    normal_style = styles['Normal']

    # Build story
    story = []

    # Title
    story.append(Paragraph("SaaS Bench - 10 Day Benchmark Report", title_style))
    story.append(Spacer(1, 0.2*inch))

    # Summary section
    story.append(Paragraph("Executive Summary", heading_style))

    # Extract final results
    final_match = re.search(r'Final Cash: \$([0-9,]+)', content)
    mrr_match = re.search(r'Final MRR: \$([0-9,]+)', content)
    cost_match = re.search(r'Total API Cost: \$([0-9.]+)', content)

    final_cash = final_match.group(1) if final_match else "N/A"
    final_mrr = mrr_match.group(1) if mrr_match else "N/A"
    api_cost = cost_match.group(1) if cost_match else "N/A"

    summary_data = [
        ['Metric', 'Value'],
        ['Days Simulated', '10'],
        ['Starting Cash', '$100,000'],
        ['Final Cash', f'${final_cash}'],
        ['Final MRR', f'${final_mrr}'],
        ['API Cost', f'${api_cost}'],
    ]

    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))

    # Daily Progress
    story.append(Paragraph("Daily Progress", heading_style))

    # Extract daily cash/MRR
    daily_pattern = r'📊 End of day: Cash=\$([0-9,]+), MRR=\$([0-9,]+)'
    daily_matches = re.findall(daily_pattern, content)

    daily_data = [['Day', 'Cash', 'MRR', 'Cash Change']]
    prev_cash = 100000
    for i, (cash, mrr) in enumerate(daily_matches, 1):
        cash_val = int(cash.replace(',', ''))
        change = cash_val - prev_cash
        daily_data.append([str(i), f'${cash}', f'${mrr}', f'{change:+,}'])
        prev_cash = cash_val

    daily_table = Table(daily_data, colWidths=[0.8*inch, 1.5*inch, 1*inch, 1.2*inch])
    daily_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(daily_table)
    story.append(Spacer(1, 0.3*inch))

    # Agent Actions Summary
    story.append(Paragraph("Agent Strategy &amp; Actions", heading_style))

    # Count tool calls
    tool_calls = re.findall(r'📞 (\w+)\(', content)
    tool_counts = {}
    for tool in tool_calls:
        tool_counts[tool] = tool_counts.get(tool, 0) + 1

    tool_data = [['Tool', 'Times Called']]
    for tool, count in sorted(tool_counts.items(), key=lambda x: -x[1]):
        tool_data.append([tool, str(count)])

    tool_table = Table(tool_data, colWidths=[2.5*inch, 1.5*inch])
    tool_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    story.append(tool_table)
    story.append(Spacer(1, 0.3*inch))

    # Reasoning Highlights
    story.append(Paragraph("Agent Reasoning Highlights", heading_style))

    reasoning_matches = re.findall(r'💭 REASONING: (.+?)(?=\n  [📞💭]|\n  ---)', content, re.DOTALL)
    for i, reasoning in enumerate(reasoning_matches[:8], 1):  # First 8 reasoning blocks
        clean = reasoning.strip().replace('\n', ' ')[:300]
        clean = clean.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        story.append(Paragraph(f"<b>{i}.</b> {clean}...", code_style))
        story.append(Spacer(1, 0.1*inch))

    # Full Log Section
    story.append(Paragraph("Full Agent Log", heading_style))
    story.append(Paragraph("<i>Complete log of all agent interactions</i>", normal_style))
    story.append(Spacer(1, 0.1*inch))

    # Process log content
    lines = content.split('\n')
    current_section = []

    for line in lines:
        # Escape HTML
        line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        if 'DAY ' in line and '===' in line:
            if current_section:
                text = '<br/>'.join(current_section)
                story.append(Paragraph(text, code_style))
                current_section = []
            story.append(Spacer(1, 0.15*inch))
            story.append(Paragraph(f"<b>{line.strip()}</b>", heading_style))
        elif '--- MODEL RESPONSE' in line:
            if current_section:
                text = '<br/>'.join(current_section)
                story.append(Paragraph(text, code_style))
                current_section = []
            story.append(Spacer(1, 0.05*inch))
            current_section.append(f"<b>{line}</b>")
        elif '--- END TURN' in line:
            current_section.append(f"<b>{line}</b>")
        elif '💭 REASONING:' in line:
            current_section.append(f"<i>{line}</i>")
        elif '📞' in line:
            current_section.append(f"<b>{line}</b>")
        elif '📊' in line:
            current_section.append(f"<b><font color='green'>{line}</font></b>")
        else:
            current_section.append(line)

    # Flush remaining
    if current_section:
        text = '<br/>'.join(current_section)
        story.append(Paragraph(text, code_style))

    # Build PDF
    doc.build(story)
    print(f"PDF created: {output_path}")

if __name__ == "__main__":
    create_report("agent_10days_log.txt", "benchmark_10day_report.pdf")
