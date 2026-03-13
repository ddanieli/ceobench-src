#!/usr/bin/env python3
"""Generate PDF report from a saas-bench run directory."""

import json
import sys
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors


def load_run_data(run_dir: Path):
    """Load data from a run directory."""
    logs_dir = run_dir / "logs"

    # Find files by pattern
    tool_calls_files = list(logs_dir.glob("tool_calls_*.jsonl"))
    rationales_files = list(logs_dir.glob("rationales_*.json"))
    run_files = list(logs_dir.glob("run_*.json"))

    tool_calls = []
    if tool_calls_files:
        with open(tool_calls_files[0], 'r') as f:
            for line in f:
                if line.strip():
                    tool_calls.append(json.loads(line))

    rationales = []
    if rationales_files:
        with open(rationales_files[0], 'r') as f:
            rationales = json.load(f)

    run_meta = {}
    if run_files:
        with open(run_files[0], 'r') as f:
            run_meta = json.load(f)

    return tool_calls, rationales, run_meta


def create_report(run_dir: str, output_path: str):
    """Create PDF report from run directory."""
    run_dir = Path(run_dir)
    tool_calls, rationales, run_meta = load_run_data(run_dir)

    # Create PDF
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

    subheading_style = ParagraphStyle(
        'SubHeading',
        parent=styles['Heading3'],
        fontSize=11,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.darkgreen,
        fontName='Helvetica-Bold',
    )

    # Style for tool call headers
    tool_header_style = ParagraphStyle(
        'ToolHeader',
        parent=styles['Heading3'],
        fontSize=10,
        spaceBefore=5,
        spaceAfter=5,
        textColor=colors.white,
        backColor=colors.Color(0.2, 0.4, 0.6),
        fontName='Helvetica-Bold',
        leftIndent=5,
        rightIndent=5,
        borderPadding=5,
    )

    # Style for rationale headers
    rationale_header_style = ParagraphStyle(
        'RationaleHeader',
        parent=styles['Heading3'],
        fontSize=10,
        spaceBefore=5,
        spaceAfter=5,
        textColor=colors.white,
        backColor=colors.Color(0.4, 0.6, 0.3),
        fontName='Helvetica-Bold',
        leftIndent=5,
        rightIndent=5,
        borderPadding=5,
    )

    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        fontSize=8,
        leading=11,
        fontName='Courier',
        backColor=colors.Color(0.95, 0.95, 0.95),
        leftIndent=10,
        rightIndent=10,
        spaceBefore=5,
        spaceAfter=8,
        borderColor=colors.Color(0.8, 0.8, 0.8),
        borderWidth=0.5,
        borderPadding=5,
    )

    # Style for rationale text
    rationale_text_style = ParagraphStyle(
        'RationaleText',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        leftIndent=10,
        rightIndent=10,
        spaceBefore=5,
        spaceAfter=10,
        backColor=colors.Color(0.98, 1.0, 0.95),
        borderPadding=8,
    )

    normal_style = styles['Normal']

    story = []

    # Title
    config = run_meta.get('metadata', {}).get('config', {})
    model = config.get('model', 'Unknown')
    total_days = config.get('total_days', '?')
    seed = config.get('seed', '?')

    # Find actual latest day
    latest_day = 0
    for tc in tool_calls:
        if tc.get('day', 0) > latest_day:
            latest_day = tc['day']

    story.append(Paragraph(f"SaaS Bench Run Report", title_style))
    story.append(Paragraph(f"Model: {model}", normal_style))
    story.append(Paragraph(f"Days: {latest_day} / {total_days}", normal_style))
    story.append(Paragraph(f"Seed: {seed}", normal_style))
    story.append(Paragraph(f"Run ID: {run_dir.name}", normal_style))
    story.append(Spacer(1, 20))

    # Summary stats
    story.append(Paragraph("Summary Statistics", heading_style))

    # Count tool calls by type
    tool_counts = {}
    for tc in tool_calls:
        tool = tc.get('tool', 'unknown')
        tool_counts[tool] = tool_counts.get(tool, 0) + 1

    summary_data = [['Metric', 'Value']]
    summary_data.append(['Total Tool Calls', str(len(tool_calls))])
    summary_data.append(['Days Simulated', str(latest_day)])
    summary_data.append(['Rationales Logged', str(len(rationales))])

    for tool, count in sorted(tool_counts.items(), key=lambda x: -x[1])[:10]:
        summary_data.append([f'  {tool}', str(count)])

    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    # Daily Dashboard Progression
    story.append(Paragraph("Daily Dashboard Progression", heading_style))

    dashboards = []
    for tc in tool_calls:
        if tc.get('tool') == 'next_day' and tc.get('result'):
            dashboards.append((tc.get('day', 0), tc.get('result', '')))

    # Extract key metrics from dashboards
    metrics_data = [['Day', 'Cash', 'Subscribers', 'New', 'Cancels', 'Usage']]
    for day, dashboard in dashboards[-20:]:  # Last 20 days
        lines = dashboard.split('\n')
        cash = subs = new = cancels = usage = '?'
        for line in lines:
            if 'CASH:' in line:
                cash = line.split('CASH:')[1].strip().split()[0]
            if 'SUBSCRIBERS:' in line:
                subs = line.split('SUBSCRIBERS:')[1].strip().split()[0]
            if 'New subscribers:' in line:
                new = line.split(':')[1].strip()
            if 'Cancellations:' in line:
                cancels = line.split(':')[1].strip()
            if 'Usage:' in line:
                usage = line.split(':')[1].strip().split()[0]
        metrics_data.append([str(day), cash, subs, new, cancels, usage])

    if len(metrics_data) > 1:
        metrics_table = Table(metrics_data, colWidths=[0.6*inch, 1.2*inch, 0.9*inch, 0.6*inch, 0.7*inch, 0.8*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        story.append(metrics_table)

    story.append(PageBreak())

    # Combine tool calls and rationales, sorted by time
    story.append(Paragraph("Full Timeline (Tool Calls + Rationales)", heading_style))
    story.append(Paragraph("All events sorted chronologically with full untruncated output", normal_style))
    story.append(Spacer(1, 10))

    # Build combined timeline
    timeline = []

    for tc in tool_calls:
        timeline.append({
            'type': 'tool_call',
            'day': tc.get('day', 0),
            'timestamp': tc.get('timestamp', ''),
            'data': tc
        })

    for r in rationales:
        timeline.append({
            'type': 'rationale',
            'day': r.get('day', 0),
            'timestamp': r.get('timestamp', ''),
            'data': r
        })

    # Sort by day, then timestamp
    timeline.sort(key=lambda x: (x['day'], x['timestamp']))

    current_day = None
    for event in timeline:
        event_day = event.get('day', 0)

        # Add day separator when day changes
        if current_day is not None and event_day != current_day:
            story.append(Spacer(1, 10))
            story.append(HRFlowable(width="100%", thickness=2, color=colors.darkblue, spaceAfter=10, spaceBefore=10))
            story.append(Paragraph(f"━━━ DAY {event_day} ━━━", ParagraphStyle(
                'DayHeader', parent=normal_style, fontSize=12, alignment=TA_CENTER,
                textColor=colors.darkblue, fontName='Helvetica-Bold', spaceBefore=5, spaceAfter=10
            )))
        current_day = event_day

        if event['type'] == 'rationale':
            r = event['data']
            day = r.get('day', '?')
            rationale = r.get('rationale', '')

            # Rationale header with green background
            story.append(Paragraph(f"  📝 Day {day} - RATIONALE  ", rationale_header_style))

            # Full rationale - no truncation, with proper line breaks
            rationale_clean = rationale.replace('<', '&lt;').replace('>', '&gt;')
            # Convert newlines to <br/> for proper display
            rationale_clean = rationale_clean.replace('\n', '<br/>')
            story.append(Paragraph(rationale_clean, rationale_text_style))

            story.append(Spacer(1, 15))
            story.append(HRFlowable(width="80%", thickness=0.5, color=colors.lightgrey, spaceAfter=10))

        elif event['type'] == 'tool_call':
            tc = event['data']
            day = tc.get('day', '?')
            tool = tc.get('tool', '?')
            args = tc.get('arguments', {})
            result = tc.get('result', '')
            error = tc.get('error')
            timestamp = tc.get('timestamp', '')

            # Tool call header with blue background
            time_short = timestamp.split('T')[1][:8] if 'T' in timestamp else timestamp
            story.append(Paragraph(f"  🔧 Day {day}: {tool}  ({time_short})  ", tool_header_style))

            # Arguments section
            if args:
                story.append(Paragraph("<b>Arguments:</b>", normal_style))
                args_str = json.dumps(args, indent=2)
                args_clean = args_str.replace('<', '&lt;').replace('>', '&gt;')
                # Convert newlines to <br/> for proper display
                args_clean = args_clean.replace('\n', '<br/>')
                story.append(Paragraph(args_clean, code_style))

            # Result/Error section
            if error:
                story.append(Paragraph("<b>Error:</b>", normal_style))
                error_clean = str(error).replace('<', '&lt;').replace('>', '&gt;')
                error_clean = error_clean.replace('\n', '<br/>')
                story.append(Paragraph(error_clean,
                    ParagraphStyle('Error', parent=code_style, textColor=colors.red, backColor=colors.Color(1.0, 0.95, 0.95))))
            elif result:
                story.append(Paragraph("<b>Result:</b>", normal_style))
                # Full result - no truncation
                result_clean = str(result).replace('<', '&lt;').replace('>', '&gt;')
                # Convert newlines to <br/> for proper display
                result_clean = result_clean.replace('\n', '<br/>')
                story.append(Paragraph(result_clean, code_style))

            story.append(Spacer(1, 15))
            story.append(HRFlowable(width="80%", thickness=0.5, color=colors.lightgrey, spaceAfter=10))

    # Build PDF
    doc.build(story)
    print(f"Report generated: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_run_report.py <run_dir> [--output <path>]")
        sys.exit(1)

    run_dir = sys.argv[1]
    output = "/tmp/saas_bench_run_report.pdf"

    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output = sys.argv[idx + 1]

    create_report(run_dir, output)
