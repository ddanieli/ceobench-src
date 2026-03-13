"""Generate comprehensive database schema PDF for python_exec."""

import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# Load tool documentation
with open('src/saas_bench/tool_docs.json', 'r') as f:
    tools = json.load(f)

python_exec = tools['python_exec']

def create_title_page(pdf):
    """Create title page."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')

    ax.text(0.5, 0.7, 'SaaS Bench', fontsize=32, fontweight='bold',
            ha='center', transform=ax.transAxes)
    ax.text(0.5, 0.6, 'python_exec Tool', fontsize=24,
            ha='center', transform=ax.transAxes, color='#555')
    ax.text(0.5, 0.5, 'Database Schema & Query Reference', fontsize=18,
            ha='center', transform=ax.transAxes, color='#777')

    # Available libraries
    libs_text = """Available in python_exec:

    conn          - SQLite connection (read-only)
    rows(q, p)    - Execute query, return list of tuples
    row(q, p)     - Execute query, return single tuple
    pd            - pandas
    np            - numpy
    LinearRegression, StandardScaler - sklearn
    json, math, statistics, Counter, defaultdict
    """
    ax.text(0.5, 0.3, libs_text, fontsize=10, ha='center', va='top',
            transform=ax.transAxes, family='monospace',
            bbox=dict(boxstyle='round', facecolor='#ecf0f1', edgecolor='#bdc3c7', pad=0.5))

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)

def create_schema_page(pdf, table_name, table_info):
    """Create a page for a single table schema."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')

    y = 0.95

    # Table name
    ax.text(0.05, y, f"TABLE: {table_name}", fontsize=16, fontweight='bold',
            transform=ax.transAxes, color='#2c3e50')
    y -= 0.03

    # Description
    if isinstance(table_info, dict) and 'description' in table_info:
        ax.text(0.05, y, table_info['description'], fontsize=10,
                transform=ax.transAxes, color='#7f8c8d', style='italic')
        y -= 0.04

    # Columns
    if isinstance(table_info, dict) and 'columns' in table_info:
        columns = table_info['columns']

        # Header
        ax.text(0.05, y, "Columns:", fontsize=12, fontweight='bold',
                transform=ax.transAxes, color='#34495e')
        y -= 0.025

        for col_name, col_type in columns.items():
            if y < 0.05:
                break
            ax.text(0.07, y, f"{col_name}", fontsize=9, fontweight='bold',
                    transform=ax.transAxes, family='monospace', color='#2980b9')
            ax.text(0.35, y, f"{col_type}", fontsize=8,
                    transform=ax.transAxes, family='monospace', color='#555')
            y -= 0.022

        # Primary key if specified
        if 'primary_key' in table_info:
            y -= 0.01
            ax.text(0.07, y, f"PRIMARY KEY: {table_info['primary_key']}", fontsize=8,
                    transform=ax.transAxes, family='monospace', color='#e67e22')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)

def create_examples_page(pdf, category, examples):
    """Create a page for example queries."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')

    y = 0.95

    ax.text(0.05, y, f"Example Queries: {category}", fontsize=14, fontweight='bold',
            transform=ax.transAxes, color='#2c3e50')
    y -= 0.05

    if isinstance(examples, list):
        for line in examples:
            if y < 0.05:
                break
            if line.startswith('#'):
                # Comment
                ax.text(0.05, y, line, fontsize=9, transform=ax.transAxes,
                        family='monospace', color='#27ae60')
            elif line == '':
                pass  # Skip empty lines
            else:
                # Code
                ax.text(0.05, y, line[:95], fontsize=8, transform=ax.transAxes,
                        family='monospace', color='#2c3e50')
            y -= 0.025

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)

def create_tips_page(pdf):
    """Create tips page."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')

    tips = python_exec.get('tips', [])

    y = 0.95
    ax.text(0.05, y, "Tips for python_exec", fontsize=16, fontweight='bold',
            transform=ax.transAxes, color='#2c3e50')
    y -= 0.05

    for tip in tips:
        if y < 0.1:
            break
        ax.text(0.07, y, f"* {tip}", fontsize=10, transform=ax.transAxes,
                color='#34495e', wrap=True)
        y -= 0.04

    # Full example
    y -= 0.03
    ax.text(0.05, y, "Complete Example:", fontsize=12, fontweight='bold',
            transform=ax.transAxes, color='#2c3e50')
    y -= 0.03

    example = python_exec.get('example_call', {}).get('arguments', {}).get('code', '')
    lines = example.split('\n')
    for line in lines[:20]:
        if y < 0.05:
            break
        ax.text(0.05, y, line[:90], fontsize=8, transform=ax.transAxes,
                family='monospace', color='#2c3e50',
                bbox=dict(boxstyle='round,pad=0.01', facecolor='#f8f9fa', edgecolor='none'))
        y -= 0.022

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)

def main():
    output_path = 'python_exec_reference.pdf'

    print("Generating python_exec Reference PDF...")

    schema = python_exec.get('database_schema', {})
    examples = python_exec.get('example_queries', {})

    with PdfPages(output_path) as pdf:
        print("  Creating title page...")
        create_title_page(pdf)

        print("  Creating schema pages...")
        for table_name, table_info in schema.items():
            print(f"    - {table_name}")
            create_schema_page(pdf, table_name, table_info)

        print("  Creating example pages...")
        for category, queries in examples.items():
            print(f"    - {category}")
            create_examples_page(pdf, category, queries)

        print("  Creating tips page...")
        create_tips_page(pdf)

    print(f"\nPDF generated: {output_path}")
    return output_path

if __name__ == '__main__':
    main()
