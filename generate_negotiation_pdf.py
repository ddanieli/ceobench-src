#!/usr/bin/env python3
"""Generate PDF report from negotiation test output with improved formatting."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, HRFlowable
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
from pathlib import Path
import re


def generate_pdf():
    """Generate a nicely formatted PDF from negotiation output."""
    # Read the output file
    output_file = Path(__file__).parent / "negotiation_llm_output.txt"
    with open(output_file, 'r') as f:
        content = f.read()

    # Create PDF
    pdf_path = Path(__file__).parent / "negotiation_llm_report.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    styles = getSampleStyleSheet()

    # Custom styles - larger fonts for readability
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        spaceAfter=12,
        textColor=HexColor('#1a1a2e'),
        alignment=TA_CENTER,
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=20,
        textColor=HexColor('#4a4a6a'),
        alignment=TA_CENTER,
    )

    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=10,
        textColor=HexColor('#2d3436'),
        borderWidth=1,
        borderColor=HexColor('#dfe6e9'),
        borderPadding=5,
    )

    scenario_style = ParagraphStyle(
        'Scenario',
        parent=styles['Normal'],
        fontSize=11,
        spaceBefore=8,
        spaceAfter=8,
        textColor=HexColor('#2d3436'),
        leftIndent=10,
    )

    # Message styles
    agent_style = ParagraphStyle(
        'AgentMessage',
        parent=styles['Normal'],
        fontSize=11,
        spaceBefore=8,
        spaceAfter=8,
        leftIndent=20,
        rightIndent=60,
        backColor=HexColor('#e8f4f8'),
        borderWidth=1,
        borderColor=HexColor('#74b9ff'),
        borderPadding=8,
        borderRadius=4,
    )

    customer_style = ParagraphStyle(
        'CustomerMessage',
        parent=styles['Normal'],
        fontSize=11,
        spaceBefore=8,
        spaceAfter=8,
        leftIndent=60,
        rightIndent=20,
        backColor=HexColor('#ffeaa7'),
        borderWidth=1,
        borderColor=HexColor('#fdcb6e'),
        borderPadding=8,
        borderRadius=4,
    )

    info_style = ParagraphStyle(
        'Info',
        parent=styles['Normal'],
        fontSize=10,
        spaceBefore=4,
        spaceAfter=4,
        textColor=HexColor('#636e72'),
        leftIndent=15,
    )

    outcome_style = ParagraphStyle(
        'Outcome',
        parent=styles['Normal'],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=12,
        textColor=HexColor('#00b894'),
        leftIndent=10,
    )

    story = []

    # Add title
    story.append(Paragraph("SaaS Bench", title_style))
    story.append(Paragraph("LLM Negotiation Testing Report", subtitle_style))
    story.append(Spacer(1, 0.3*inch))

    # Parse content and format nicely
    lines = content.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Escape special characters
        escaped = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # Section headers (=== ... ===)
        if line.startswith('===') and line.endswith('==='):
            # Extract title from between === markers
            title_match = re.search(r'===+\s*(.+?)\s*===+', line)
            if title_match:
                title_text = title_match.group(1)
            else:
                title_text = line.strip('= ')
            story.append(Spacer(1, 0.2*inch))
            story.append(HRFlowable(width="100%", thickness=2, color=HexColor('#74b9ff')))
            story.append(Paragraph(title_text, section_style))
            i += 1
            continue

        # Test headers (TEST 1:, TEST 2:, etc.)
        if 'TEST' in line and ':' in line and ('NEGOTIATION' in line or 'GPT' in line):
            story.append(Spacer(1, 0.3*inch))
            story.append(HRFlowable(width="100%", thickness=2, color=HexColor('#6c5ce7')))
            story.append(Paragraph(escaped, section_style))
            i += 1
            continue

        # Scenario info
        if line.startswith('📋 Scenario:'):
            story.append(Paragraph(f"<b>{escaped}</b>", scenario_style))
            i += 1
            continue

        # Customer email
        if line.startswith('Customer:') and '@' in line:
            story.append(Paragraph(f"<b>Customer:</b> {escaped[9:]}", info_style))
            i += 1
            continue

        # Curve parameters
        if line.startswith('Curve:'):
            story.append(Paragraph(f"<b>Curve:</b> {escaped[6:]}", info_style))
            i += 1
            continue

        # Budget shock info
        if '⚡' in line or 'BUDGET SHOCK' in line:
            story.append(Paragraph(f"<font color='#e17055'><b>{escaped}</b></font>", scenario_style))
            i += 1
            continue

        # Warning/churn risk
        if '⚠️' in line or 'CHURN RISK' in line or 'URGENT' in line:
            story.append(Paragraph(f"<font color='#d63031'><b>{escaped}</b></font>", scenario_style))
            i += 1
            continue

        # Negotiation parameters section
        if '📊 Negotiation Parameters:' in line:
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph("<b>Negotiation Parameters</b>", info_style))
            i += 1
            continue

        # Parameter values (indented with spaces)
        if line.startswith('Quality for Plan') or line.startswith("Customer's max") or line.startswith("Customer's target"):
            story.append(Paragraph(f"• {escaped}", info_style))
            i += 1
            continue

        # Agent turn header
        if line.startswith('🤖 Agent turn'):
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(f"<b>{escaped}</b>", info_style))
            i += 1
            continue

        # Customer turn header
        if line.startswith('👤 Customer turn'):
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(f"<b>{escaped}</b>", info_style))
            i += 1
            continue

        # Agent message in conversation
        if line.startswith('Agent: "') or (line.startswith('   Agent: "') and '"' in line):
            # Extract the message content
            msg_match = re.search(r'Agent:\s*"(.+)"', line)
            if msg_match:
                msg_text = msg_match.group(1).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(f"<b>Agent:</b> {msg_text}", agent_style))
            else:
                story.append(Paragraph(escaped, agent_style))
            i += 1
            continue

        # Customer message in conversation
        if line.startswith('Customer: "') or (line.startswith('   Customer: "') and '"' in line):
            msg_match = re.search(r'Customer:\s*"(.+)"', line)
            if msg_match:
                msg_text = msg_match.group(1).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                story.append(Paragraph(f"<b>Customer:</b> {msg_text}", customer_style))
            else:
                story.append(Paragraph(escaped, customer_style))
            i += 1
            continue

        # Offer lines
        if line.startswith('Offer:') or line.startswith('   Offer:'):
            story.append(Paragraph(f"<font color='#0984e3'><b>{escaped.strip()}</b></font>", info_style))
            i += 1
            continue

        # Counter offer lines
        if line.startswith('Counter:') or line.startswith('   Counter:'):
            story.append(Paragraph(f"<font color='#e17055'><b>{escaped.strip()}</b></font>", info_style))
            i += 1
            continue

        # Deal accepted
        if '✅ DEAL ACCEPTED' in line or 'DEAL ACCEPTED' in line:
            story.append(Paragraph(f"<font color='#00b894'><b>{escaped}</b></font>", outcome_style))
            i += 1
            continue

        # Thread info section
        if line.startswith('--- Thread #'):
            story.append(Spacer(1, 0.15*inch))
            story.append(HRFlowable(width="80%", thickness=1, color=HexColor('#b2bec3')))
            story.append(Paragraph(f"<b>{escaped}</b>", scenario_style))
            i += 1
            continue

        # Conversation header
        if '📨 Conversation' in line:
            story.append(Paragraph(f"<b>{escaped}</b>", scenario_style))
            i += 1
            continue

        # Day + sender line in conversation history
        if line.startswith('Day ') and (' - 👤 ' in line or ' - 🤖 ' in line):
            story.append(Spacer(1, 0.05*inch))
            story.append(Paragraph(f"<b>{escaped}</b>", info_style))
            i += 1
            continue

        # Quoted message text (indented with quotes)
        if line.startswith('"') and line.endswith('"'):
            msg_text = line[1:-1].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # Determine if previous line was agent or customer
            if i > 0 and '🤖 AGENT' in lines[i-1].upper():
                story.append(Paragraph(msg_text, agent_style))
            elif i > 0 and '👤 CUSTOMER' in lines[i-1].upper():
                story.append(Paragraph(msg_text, customer_style))
            else:
                story.append(Paragraph(msg_text, scenario_style))
            i += 1
            continue

        # Outcome lines
        if line.startswith('✅ Outcome:') or line.startswith('❌ Outcome:'):
            color = '#00b894' if '✅' in line else '#d63031'
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(f"<font color='{color}'><b>{escaped}</b></font>", outcome_style))
            i += 1
            continue

        # Summary section
        if 'SUMMARY' in line:
            story.append(Spacer(1, 0.3*inch))
            story.append(HRFlowable(width="100%", thickness=3, color=HexColor('#6c5ce7')))
            story.append(Paragraph("SUMMARY", section_style))
            i += 1
            continue

        # Model config info
        if 'Environment LLM:' in line or 'Agent LLM:' in line:
            story.append(Paragraph(f"<b>{escaped}</b>", info_style))
            i += 1
            continue

        # Skip separator lines
        if line.startswith('---') or line.startswith('===') or line == '🔬 ' * 20:
            i += 1
            continue

        # Thread metadata (Type:, State:, etc.)
        if line.startswith('Type:') or line.startswith('State:') or line.startswith('Turn:') or line.startswith('Current Offer:'):
            story.append(Paragraph(f"• {escaped}", info_style))
            i += 1
            continue

        if line.startswith('Customer ID:') or line.startswith('Customer Email:'):
            story.append(Paragraph(f"• {escaped}", info_style))
            i += 1
            continue

        # Default - just add as regular paragraph
        if escaped.strip():
            story.append(Paragraph(escaped, scenario_style))

        i += 1

    # Build PDF
    doc.build(story)
    print(f"PDF generated: {pdf_path}")
    return str(pdf_path)


if __name__ == '__main__':
    generate_pdf()
