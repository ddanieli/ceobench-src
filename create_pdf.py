#!/usr/bin/env python3
"""Convert agent log to PDF."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
import re

def create_pdf(log_path: str, output_path: str):
    """Create PDF from log file."""

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

    # Custom style for code/log content
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7,
        leading=9,
        alignment=TA_LEFT,
        wordWrap='CJK',  # Better word wrapping
    )

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=20,
    )

    day_style = ParagraphStyle(
        'DayHeader',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=15,
        spaceAfter=10,
        textColor='blue',
    )

    # Build story
    story = []

    # Title
    story.append(Paragraph("SaaS Bench Agent Log - Full Detail", title_style))
    story.append(Spacer(1, 0.2*inch))

    # Process content by day
    lines = content.split('\n')
    current_section = []

    for line in lines:
        # Escape HTML special characters
        line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # Check for day markers
        if line.startswith('=' * 20) and 'DAY' in lines[lines.index(line.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')) + 1] if line.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>') in lines else False:
            pass  # Skip separator lines
        elif 'DAY ' in line and line.strip().startswith('DAY'):
            # Flush current section
            if current_section:
                text = '<br/>'.join(current_section)
                story.append(Paragraph(text, code_style))
                current_section = []
            # Add day header
            story.append(Paragraph(line.strip(), day_style))
        elif '--- MODEL RESPONSE' in line:
            # Flush and add turn header
            if current_section:
                text = '<br/>'.join(current_section)
                story.append(Paragraph(text, code_style))
                current_section = []
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(f"<b>{line.strip()}</b>", code_style))
        elif '--- END TURN' in line:
            current_section.append(f"<b>{line}</b>")
        elif line.startswith('  💭 REASONING:'):
            current_section.append(f"<i>{line}</i>")
        elif line.startswith('  📞'):
            current_section.append(f"<b>{line}</b>")
        elif line.startswith('  📊'):
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
    create_pdf("agent_log.txt", "agent_log.pdf")
