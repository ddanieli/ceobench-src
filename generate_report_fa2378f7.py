#!/usr/bin/env python3
"""Generate PDF report for run fa2378f7"""

import json
import sqlite3
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER

RUN_DIR = "opencode_runs/run_fa2378f7"

def load_config():
    with open(f"{RUN_DIR}/config.json") as f:
        return json.load(f)

def load_rationales():
    with open(f"{RUN_DIR}/logs/rationales_fa2378f7.json") as f:
        return json.load(f)

def load_tool_calls():
    calls = []
    with open(f"{RUN_DIR}/logs/tool_calls_fa2378f7.jsonl") as f:
        for line in f:
            if line.strip():
                calls.append(json.loads(line))
    return calls

def load_file_diffs():
    """Load file diffs if available."""
    diffs_file = f"{RUN_DIR}/logs/file_diffs_fa2378f7.jsonl"
    diffs = []
    try:
        with open(diffs_file) as f:
            for line in f:
                if line.strip():
                    diffs.append(json.loads(line))
    except FileNotFoundError:
        pass  # File diffs not available for this run
    return diffs

def get_db_stats():
    conn = sqlite3.connect(f"{RUN_DIR}/world.db")
    cur = conn.cursor()

    # Current day
    cur.execute("SELECT day FROM service_day ORDER BY day DESC LIMIT 1")
    current_day = cur.fetchone()[0]

    # Cash (ledger already includes initial $1M as "Initial funding")
    cur.execute("SELECT COALESCE(SUM(amount), 0) FROM ledger")
    cash = cur.fetchone()[0]

    # Subscribers
    cur.execute("SELECT COUNT(*) FROM subscriptions WHERE status='subscribed'")
    subscribers = cur.fetchone()[0]

    # Free trials
    cur.execute("SELECT COUNT(*) FROM subscriptions WHERE status='free_trial'")
    trials = cur.fetchone()[0]

    # MRR (sum of effective prices for subscribed)
    cur.execute("SELECT COALESCE(SUM(effective_price), 0) FROM subscriptions WHERE status='subscribed'")
    mrr = cur.fetchone()[0]

    conn.close()
    return {
        'current_day': current_day,
        'cash': cash,
        'subscribers': subscribers,
        'trials': trials,
        'mrr': mrr
    }

def create_report():
    config = load_config()
    rationales = load_rationales()
    tool_calls = load_tool_calls()
    file_diffs = load_file_diffs()
    stats = get_db_stats()

    # Create PDF
    pdf_path = f"report_opus45_bedrock_seed42_day{stats['current_day']}.pdf"
    doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                           leftMargin=0.75*inch, rightMargin=0.75*inch,
                           topMargin=0.75*inch, bottomMargin=0.75*inch)

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10,
        textColor=colors.darkblue
    )

    day_heading_style = ParagraphStyle(
        'DayHeading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.darkgreen,
        borderWidth=1,
        borderColor=colors.lightgrey,
        borderPadding=5,
        backColor=colors.Color(0.95, 0.98, 0.95)
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        spaceAfter=6
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Code'],
        fontSize=7,
        leading=9,
        leftIndent=10,
        backColor=colors.Color(0.95, 0.95, 0.95)
    )

    elements = []

    # Title
    elements.append(Paragraph("SaaS Bench Run Report", title_style))
    elements.append(Paragraph(f"Run ID: {config['run_id']}", styles['Normal']))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    # Configuration
    elements.append(Paragraph("Run Configuration", heading_style))
    config_data = [
        ["Model", config['model']],
        ["Reasoning Effort", config['reasoning_effort']],
        ["Seed", str(config['seed'])],
        ["Total Days", str(config['total_days'])],
        ["Initial Cash", f"${config['initial_cash']:,.0f}"],
        ["Compaction Threshold", str(config.get('opencode_settings', {}).get('compaction', {}).get('threshold', 'N/A'))],
    ]
    config_table = Table(config_data, colWidths=[2*inch, 4*inch])
    config_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.9)),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(config_table)
    elements.append(Spacer(1, 20))

    # Current Status
    elements.append(Paragraph("Current Status", heading_style))
    status_data = [
        ["Current Day", f"{stats['current_day']} / {config['total_days']}"],
        ["Cash", f"${stats['cash']:,.2f}"],
        ["Paid Subscribers", str(stats['subscribers'])],
        ["Free Trials", f"{stats['trials']:,}"],
        ["MRR", f"${stats['mrr']:,.2f}"],
    ]
    status_table = Table(status_data, colWidths=[2*inch, 4*inch])
    status_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.9)),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(status_table)
    elements.append(Spacer(1, 20))

    # Issue Note
    elements.append(Paragraph("⚠️ Note: Rationale Logging Issue", heading_style))
    elements.append(Paragraph(
        "Due to OpenCode's context compaction (threshold 0.85), the agent's rationale content became stuck on "
        "Day 5 data after approximately Day 5. Rationales from Day 6 onwards contain stale analysis text "
        "that does not reflect the actual simulation state. The simulation itself ran correctly - only the "
        "agent's analysis text was affected.",
        body_style
    ))
    elements.append(Spacer(1, 20))

    # Organize tool calls by day
    calls_by_day = {}
    for call in tool_calls:
        day = call.get('day', 0)
        if day not in calls_by_day:
            calls_by_day[day] = []
        calls_by_day[day].append(call)

    # Organize rationales by day
    rationales_by_day = {}
    for r in rationales:
        day = r.get('day', 0)
        rationales_by_day[day] = r

    # Organize file diffs by day
    diffs_by_day = {}
    for entry in file_diffs:
        day = entry.get('day', 0)
        if day not in diffs_by_day:
            diffs_by_day[day] = []
        diffs_by_day[day].extend(entry.get('diffs', []))

    elements.append(PageBreak())
    elements.append(Paragraph("Daily Activity Log", title_style))

    # Process each day
    all_days = sorted(set(list(calls_by_day.keys()) + list(rationales_by_day.keys()) + list(diffs_by_day.keys())))

    for day in all_days:
        # Day separator
        elements.append(Paragraph(f"═══════════════ DAY {day} ═══════════════", day_heading_style))

        # Rationale for this day
        if day in rationales_by_day:
            r = rationales_by_day[day]
            elements.append(Paragraph("<b>Rationale:</b>", body_style))
            # Clean and format rationale text - escape all special chars
            rationale_text = r.get('rationale', '')
            rationale_text = rationale_text.replace('&', '&amp;')
            rationale_text = rationale_text.replace('<', '&lt;')
            rationale_text = rationale_text.replace('>', '&gt;')
            rationale_text = rationale_text.replace('\n', '<br/>')
            elements.append(Paragraph(rationale_text, body_style))
            elements.append(Spacer(1, 10))

        # Tool calls for this day
        if day in calls_by_day:
            elements.append(Paragraph("<b>Tool Calls:</b>", body_style))
            for call in calls_by_day[day]:
                tool_name = call.get('tool', 'unknown')
                args = call.get('arguments', {})
                result = call.get('result', '')
                error = call.get('error')

                # Format tool call header
                elements.append(Paragraph(f"<b>→ {tool_name}</b>", body_style))

                # Full arguments (untruncated)
                if args:
                    args_str = json.dumps(args, indent=2)
                    # Escape special characters for XML
                    args_str = args_str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    elements.append(Paragraph(f"<font size=7>Arguments: {args_str}</font>", code_style))

                # Full result (untruncated)
                if result:
                    result_str = str(result)
                    # Escape special characters
                    result_str = result_str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    # Handle long results - show full content
                    if len(result_str) > 2000:
                        # Still show full but note it's long
                        elements.append(Paragraph(f"<font size=7>Result ({len(result_str)} chars):</font>", code_style))
                    elements.append(Paragraph(f"<font size=6>{result_str}</font>", code_style))

                if error:
                    error_str = str(error).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    elements.append(Paragraph(f"<font size=7 color='red'>Error: {error_str}</font>", code_style))

                elements.append(Spacer(1, 5))

        # File diffs for this day
        if day in diffs_by_day:
            elements.append(Paragraph("<b>📁 File Changes:</b>", body_style))
            for diff in diffs_by_day[day]:
                diff_type = diff.get('type', 'unknown')
                path = diff.get('path', 'unknown')

                # Color code by type
                if diff_type == 'added':
                    type_color = 'green'
                    type_symbol = '+'
                elif diff_type == 'deleted':
                    type_color = 'red'
                    type_symbol = '-'
                else:  # modified
                    type_color = 'blue'
                    type_symbol = '~'

                elements.append(Paragraph(
                    f"<font color='{type_color}'><b>{type_symbol} {path}</b></font> ({diff_type})",
                    body_style
                ))

                # Show content based on type
                if diff_type == 'added':
                    content = diff.get('content', '')
                    content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    elements.append(Paragraph(f"<font size=6 color='green'>{content}</font>", code_style))
                elif diff_type == 'deleted':
                    content = diff.get('previous_content', '')
                    content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    elements.append(Paragraph(f"<font size=6 color='red'>{content}</font>", code_style))
                elif diff_type == 'modified':
                    prev = diff.get('previous_content', '')
                    new = diff.get('new_content', '')
                    prev = prev.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    new = new.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    elements.append(Paragraph("<font size=6>Previous:</font>", code_style))
                    elements.append(Paragraph(f"<font size=6 color='red'>{prev}</font>", code_style))
                    elements.append(Paragraph("<font size=6>New:</font>", code_style))
                    elements.append(Paragraph(f"<font size=6 color='green'>{new}</font>", code_style))

                elements.append(Spacer(1, 5))

        elements.append(Spacer(1, 15))

    # Build PDF
    doc.build(elements)
    print(f"Report generated: {pdf_path}")
    return pdf_path

if __name__ == "__main__":
    pdf_path = create_report()
