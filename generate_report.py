"""Generate PDF report for SaaS Bench architecture."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle, Polygon
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import textwrap

# Set up style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 10


def create_title_page(pdf):
    """Create title page."""
    fig = plt.figure(figsize=(11, 8.5))
    ax = fig.add_subplot(111)
    ax.axis('off')

    ax.text(0.5, 0.7, 'SaaS Bench', fontsize=36, fontweight='bold',
            ha='center', va='center', transform=ax.transAxes)
    ax.text(0.5, 0.55, 'Architecture & Design Document', fontsize=24,
            ha='center', va='center', transform=ax.transAxes, color='#555')
    ax.text(0.5, 0.35, 'An OpenAI Gym-Style Environment for\nAI Agent SaaS Business Management',
            fontsize=14, ha='center', va='center', transform=ax.transAxes, color='#777')
    ax.text(0.5, 0.15, 'Version 1.0 | January 2026', fontsize=12,
            ha='center', va='center', transform=ax.transAxes, color='#999')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_triangle_overview(pdf):
    """Create the triangle structure overview diagram."""
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.set_xlim(-1, 11)
    ax.set_ylim(-1, 9)
    ax.axis('off')
    ax.set_aspect('equal')

    # Title
    ax.text(5, 8.5, '1. Triangle Structure Overview', fontsize=18, fontweight='bold',
            ha='center', va='top')
    ax.text(5, 8.0, 'The three-way interaction between Agent, Environment, and Customers',
            fontsize=11, ha='center', va='top', color='#555')

    # Draw the three main components as boxes
    # Agent (top)
    agent_box = FancyBboxPatch((3, 5.5), 4, 1.5, boxstyle="round,pad=0.1",
                                facecolor='#3498db', edgecolor='#2980b9', linewidth=2)
    ax.add_patch(agent_box)
    ax.text(5, 6.25, 'AI AGENT', fontsize=14, fontweight='bold', ha='center', va='center', color='white')

    # Environment (bottom left)
    env_box = FancyBboxPatch((0.5, 1.5), 4, 1.5, boxstyle="round,pad=0.1",
                              facecolor='#2ecc71', edgecolor='#27ae60', linewidth=2)
    ax.add_patch(env_box)
    ax.text(2.5, 2.25, 'ENVIRONMENT', fontsize=14, fontweight='bold', ha='center', va='center', color='white')
    ax.text(2.5, 1.85, '(SaaSBenchEnv)', fontsize=10, ha='center', va='center', color='white')

    # Customers (bottom right)
    cust_box = FancyBboxPatch((5.5, 1.5), 4, 1.5, boxstyle="round,pad=0.1",
                               facecolor='#e74c3c', edgecolor='#c0392b', linewidth=2)
    ax.add_patch(cust_box)
    ax.text(7.5, 2.25, 'CUSTOMERS', fontsize=14, fontweight='bold', ha='center', va='center', color='white')
    ax.text(7.5, 1.85, '(Simulated)', fontsize=10, ha='center', va='center', color='white')

    # Draw arrows with labels
    # Agent -> Environment (Actions)
    ax.annotate('', xy=(2.5, 3.1), xytext=(4, 5.4),
                arrowprops=dict(arrowstyle='->', color='#2980b9', lw=2))
    ax.text(2.5, 4.5, 'Actions\n(Tool Calls)', fontsize=9, ha='center', va='center',
            bbox=dict(boxstyle='round', facecolor='#ebf5fb', edgecolor='#2980b9'))

    # Environment -> Agent (Observations)
    ax.annotate('', xy=(6, 5.4), xytext=(4.5, 3.1),
                arrowprops=dict(arrowstyle='->', color='#27ae60', lw=2))
    ax.text(6.2, 4.5, 'Observations\n(Dashboard)', fontsize=9, ha='center', va='center',
            bbox=dict(boxstyle='round', facecolor='#eafaf1', edgecolor='#27ae60'))

    # Environment <-> Customers (bidirectional)
    ax.annotate('', xy=(5.5, 2.25), xytext=(4.5, 2.25),
                arrowprops=dict(arrowstyle='<->', color='#8e44ad', lw=2))
    ax.text(5, 2.7, 'Simulation', fontsize=9, ha='center', va='center',
            bbox=dict(boxstyle='round', facecolor='#f5eef8', edgecolor='#8e44ad'))

    # Company (in the middle, part of environment)
    company_box = FancyBboxPatch((3.5, 3.3), 3, 1.2, boxstyle="round,pad=0.1",
                                  facecolor='#f39c12', edgecolor='#d68910', linewidth=2)
    ax.add_patch(company_box)
    ax.text(5, 3.9, 'COMPANY STATE', fontsize=11, fontweight='bold', ha='center', va='center', color='white')
    ax.text(5, 3.55, '(Cash, MRR, Config)', fontsize=9, ha='center', va='center', color='white')

    # Add explanatory text at bottom
    explanation = """The Triangle Structure:
• AGENT: AI that makes decisions (prices, capacity, marketing, customer negotiations)
• ENVIRONMENT: Gym-style interface (step, reset) + Company state (cash, subscriptions, config)
• CUSTOMERS: Simulated customer population with realistic behavior models

Each day, the agent receives a dashboard (observation), takes actions (tool calls),
and the environment advances simulation, updating company and customer state."""

    ax.text(5, 0.5, explanation, fontsize=9, ha='center', va='top',
            bbox=dict(boxstyle='round', facecolor='#f8f9fa', edgecolor='#dee2e6', pad=0.5),
            family='monospace')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_agent_interaction_diagram(pdf):
    """Create detailed agent interaction diagram."""
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # Title
    ax.text(5, 8.7, '2. Agent Environment Interaction', fontsize=18, fontweight='bold', ha='center')
    ax.text(5, 8.3, 'How the agent interacts with the environment through tool calls', fontsize=11, ha='center', color='#555')

    # Tools organized by category
    categories = {
        'Business Configuration': ['set_prices', 'set_model_tiers', 'set_capacity_tier', 'set_usage_quotas'],
        'Marketing & Spend': ['set_daily_spend', 'set_ad_channel_spend'],
        'Customer Communication': ['read_thread', 'get_thread_history', 'send_reply'],
        'Analytics & Monitoring': ['python_exec', 'get_social_posts', 'expand_notification', 'get_cost_info'],
        'Automation': ['register_daily_calculation', 'remove_daily_calculation', 'list_daily_calculations'],
        'Simulation Control': ['next_day']
    }

    colors = ['#3498db', '#2ecc71', '#e74c3c', '#9b59b6', '#f39c12', '#1abc9c']

    y_start = 7.5
    y_step = 1.1

    for i, (category, tools) in enumerate(categories.items()):
        y = y_start - i * y_step

        # Category box
        cat_box = FancyBboxPatch((0.3, y - 0.3), 2.5, 0.6, boxstyle="round,pad=0.05",
                                  facecolor=colors[i], edgecolor='none', alpha=0.9)
        ax.add_patch(cat_box)
        ax.text(1.55, y, category, fontsize=9, fontweight='bold', ha='center', va='center', color='white')

        # Tools
        x_tool = 3.2
        for tool in tools:
            tool_width = len(tool) * 0.08 + 0.3
            tool_box = FancyBboxPatch((x_tool, y - 0.2), tool_width, 0.4, boxstyle="round,pad=0.02",
                                       facecolor='#f8f9fa', edgecolor=colors[i], linewidth=1.5)
            ax.add_patch(tool_box)
            ax.text(x_tool + tool_width/2, y, tool, fontsize=7, ha='center', va='center',
                    family='monospace', color='#2c3e50')
            x_tool += tool_width + 0.15

    # Action-Observation loop diagram
    ax.text(5, 0.9, 'Gym-Style Loop:', fontsize=11, fontweight='bold', ha='center')

    loop_text = """
env.reset() → initial_observation, info
while not done:
    action = agent.act(observation)     # Agent chooses tool
    result = env.step(action)           # Environment executes
    observation = result.observation    # Tool output / Dashboard
    reward = result.reward              # (revenue - costs) for next_day
    done = result.done                  # Bankruptcy or max days
"""
    ax.text(5, 0.5, loop_text, fontsize=8, ha='center', va='top',
            family='monospace', bbox=dict(boxstyle='round', facecolor='#2c3e50', edgecolor='none'),
            color='#ecf0f1')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_dashboard_example(pdf):
    """Create example daily dashboard page."""
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis('off')

    # Title
    ax.text(0.5, 0.97, '3. Daily Dashboard (Agent Observation)', fontsize=18, fontweight='bold',
            ha='center', transform=ax.transAxes)
    ax.text(0.5, 0.93, 'What the agent sees after calling next_day', fontsize=11,
            ha='center', transform=ax.transAxes, color='#555')

    # Dashboard content
    dashboard = """
=== Day 45 Dashboard ===

Cash: $87,234
Subscribers: 142
MRR: $8,450

--- Yesterday's Metrics ---
Usage: 45,230 units
New Subscribers: 8
Cancellations: 2
Upgrades: 3 | Downgrades: 1
Overload: 15.2%
Outage: No
P95 Latency: 450ms | Error Rate: 0.8%
Revenue: $2,840 | Costs: $3,120

--- Current Config ---
Prices: A=$29, B=$79, C=$199
Model Tiers: A=2, B=3, C=4
Quotas: A=100, B=500, C=2000 units/day
Capacity: Tier 1
Daily Spend: Ads=$500, Ops=$1000, Dev=$500

--- Inbox ---
  * [CRITICAL] [N-123] Server overload detected
  * [HIGH] [N-124] Customer complaint trending on social
  * [THREAD] #45: negotiation (200 seats)
  * [THREAD] #46: negotiation (150 seats)
"""

    ax.text(0.05, 0.88, dashboard, fontsize=9, family='monospace',
            va='top', ha='left', transform=ax.transAxes,
            bbox=dict(boxstyle='round', facecolor='#1e1e1e', edgecolor='#3c3c3c', pad=0.5),
            color='#d4d4d4')

    # Annotations explaining sections
    annotations = [
        (0.72, 0.82, 'Financial Summary', 'Current cash position,\nsubscriber count, and\nmonthly recurring revenue'),
        (0.72, 0.68, 'Operational Metrics', 'System performance,\nchurn, growth, and\nservice quality indicators'),
        (0.72, 0.52, 'Configuration State', 'Current pricing,\nservice tiers, quotas,\nand spending levels'),
        (0.72, 0.35, 'Inbox / Notifications', 'Urgent items requiring\nattention: alerts,\nenterprise negotiations')
    ]

    for x, y, title, desc in annotations:
        ax.text(x, y, title, fontsize=10, fontweight='bold', transform=ax.transAxes)
        ax.text(x, y - 0.03, desc, fontsize=8, color='#666', transform=ax.transAxes, va='top')
        # Arrow pointing left
        ax.annotate('', xy=(0.58, y - 0.02), xytext=(x - 0.02, y - 0.02),
                    arrowprops=dict(arrowstyle='->', color='#3498db', lw=1.5),
                    transform=ax.transAxes)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_customer_lifecycle(pdf):
    """Create customer lifecycle diagram."""
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # Title
    ax.text(5, 8.7, '4. Customer Lifecycle', fontsize=18, fontweight='bold', ha='center')
    ax.text(5, 8.3, 'From potential customer to subscriber (or free trial)', fontsize=11, ha='center', color='#555')

    # States
    states = [
        (1, 6, 'Potential\nCustomer', '#95a5a6'),
        (3.5, 6, 'Spawned\n(Curve Check)', '#f39c12'),
        (6, 7, 'Subscribed', '#2ecc71'),
        (6, 5, 'Free Trial\n(No Convert)', '#e74c3c'),
        (8.5, 7, 'Enterprise\nLead', '#9b59b6'),
        (8.5, 5, 'Cancelled', '#7f8c8d'),
    ]

    for x, y, label, color in states:
        circle = Circle((x, y), 0.6, facecolor=color, edgecolor='white', linewidth=2)
        ax.add_patch(circle)
        ax.text(x, y, label, fontsize=8, ha='center', va='center', color='white', fontweight='bold')

    # Arrows
    arrows = [
        ((1.6, 6), (2.9, 6), 'Marketing\n+ Ad Spend'),
        ((4.1, 6.3), (5.4, 6.8), 'Plan\nAcceptable'),
        ((4.1, 5.7), (5.4, 5.2), 'No Plan\nAcceptable'),
        ((4.1, 6.5), (7.9, 7), 'Enterprise\nCustomer'),
        ((6.6, 7), (7.9, 5.3), 'Cancel'),
        ((6.6, 5), (7.9, 5), 'N/A'),
    ]

    for start, end, label in arrows:
        ax.annotate('', xy=end, xytext=start,
                    arrowprops=dict(arrowstyle='->', color='#34495e', lw=1.5))
        mid_x = (start[0] + end[0]) / 2
        mid_y = (start[1] + end[1]) / 2
        ax.text(mid_x, mid_y + 0.3, label, fontsize=7, ha='center', va='bottom', color='#34495e')

    # Process explanation
    process_text = """
Customer Generation Process:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. SPAWNING: Marketing spend generates potential customers via Poisson process
   • Rate = base_rate × reputation × marketing × awareness × network_effect
   • Each customer belongs to a group (S1, S2, S3, E1, E2, E3)

2. SUBSCRIPTION CHECK: For each spawned customer:
   • Sample sigmoid participation curve parameters (q_floor, q_ceiling, steepness, c_max)
   • Find best plan where: Q_delivered ≥ Q_required(Cost) AND Cost ≤ c_max
   • If acceptable plan exists → SUBSCRIBE (individual) or LEAD (enterprise)
   • If no acceptable plan → FREE_TRIAL record (costs company $5)

3. ONGOING: Subscribed customers re-evaluate monthly at billing day
   • Curve parameters can drift over time
   • If no plan acceptable anymore → CANCEL
   • If better plan exists → SWITCH (upgrade/downgrade)
"""

    ax.text(5, 3.5, process_text, fontsize=8, ha='center', va='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='#f8f9fa', edgecolor='#dee2e6', pad=0.5))

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_sigmoid_curve_plot(pdf):
    """Create sigmoid participation curve visualization."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))

    # Left plot: Single sigmoid curve explanation
    ax1 = axes[0]

    # Parameters for example curve
    q_floor = 0.4
    q_ceiling = 0.85
    steepness = 0.08
    midpoint = 50
    c_max = 120

    costs = np.linspace(0, c_max, 100)
    q_required = q_floor + (q_ceiling - q_floor) / (1 + np.exp(-steepness * (costs - midpoint)))

    ax1.plot(costs, q_required, 'b-', linewidth=2.5, label='Q_required(C)')
    ax1.fill_between(costs, q_required, 1, alpha=0.3, color='green', label='Acceptable Region')
    ax1.fill_between(costs, 0, q_required, alpha=0.3, color='red', label='Unacceptable Region')

    # Mark example plans
    plans = [
        ('A', 29, 0.65, '#3498db'),   # (name, price, quality, color)
        ('B', 79, 0.75, '#2ecc71'),
        ('C', 199, 0.85, '#e74c3c'),  # This one is beyond c_max
    ]

    for name, price, quality, color in plans:
        if price <= c_max:
            q_req = q_floor + (q_ceiling - q_floor) / (1 + np.exp(-steepness * (price - midpoint)))
            marker = 'o' if quality >= q_req else 'x'
            ax1.scatter([price], [quality], s=150, c=color, marker=marker, zorder=5, edgecolor='white', linewidth=2)
            ax1.annotate(f'Plan {name}', (price, quality), xytext=(5, 5), textcoords='offset points', fontsize=9)

    ax1.axvline(x=c_max, color='purple', linestyle='--', linewidth=1.5, label=f'c_max = ${c_max}')
    ax1.axhline(y=q_floor, color='gray', linestyle=':', alpha=0.5)
    ax1.axhline(y=q_ceiling, color='gray', linestyle=':', alpha=0.5)

    ax1.set_xlabel('Cost ($/month)', fontsize=10)
    ax1.set_ylabel('Quality Required / Delivered', fontsize=10)
    ax1.set_title('Sigmoid Participation Curve\n(Single Customer)', fontsize=12, fontweight='bold')
    ax1.legend(loc='lower right', fontsize=8)
    ax1.set_xlim(0, 150)
    ax1.set_ylim(0.3, 1.0)
    ax1.grid(True, alpha=0.3)

    # Right plot: Multiple customer groups
    ax2 = axes[1]

    groups = {
        'S1 (Price-Sensitive)': {'q_floor': 0.40, 'q_ceiling': 0.70, 'steepness': 0.10, 'midpoint': 30, 'c_max': 50, 'color': '#e74c3c'},
        'S2 (Quality-Focused)': {'q_floor': 0.65, 'q_ceiling': 0.90, 'steepness': 0.06, 'midpoint': 80, 'c_max': 150, 'color': '#3498db'},
        'S3 (Power Users)': {'q_floor': 0.55, 'q_ceiling': 0.85, 'steepness': 0.07, 'midpoint': 60, 'c_max': 120, 'color': '#2ecc71'},
    }

    costs = np.linspace(0, 200, 200)

    for name, params in groups.items():
        q_req = params['q_floor'] + (params['q_ceiling'] - params['q_floor']) / (1 + np.exp(-params['steepness'] * (costs - params['midpoint'])))
        # Mask beyond c_max
        q_req[costs > params['c_max']] = np.nan
        ax2.plot(costs, q_req, linewidth=2, color=params['color'], label=name)
        ax2.axvline(x=params['c_max'], color=params['color'], linestyle=':', alpha=0.5)

    ax2.set_xlabel('Cost ($/month)', fontsize=10)
    ax2.set_ylabel('Quality Required', fontsize=10)
    ax2.set_title('Participation Curves by Customer Group\n(Small Customers)', fontsize=12, fontweight='bold')
    ax2.legend(loc='lower right', fontsize=8)
    ax2.set_xlim(0, 200)
    ax2.set_ylim(0.3, 1.0)
    ax2.grid(True, alpha=0.3)

    plt.suptitle('5. Customer Modeling: Sigmoid Participation Curves', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_customer_groups_plot(pdf):
    """Create customer groups overview."""
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis('off')

    # Title
    ax.text(0.5, 0.97, '6. Customer Groups', fontsize=18, fontweight='bold',
            ha='center', transform=ax.transAxes)
    ax.text(0.5, 0.93, 'Six customer segments with different characteristics', fontsize=11,
            ha='center', transform=ax.transAxes, color='#555')

    # Table data
    groups_data = [
        ('Group', 'Name', 'Q_min', 'C_max', 'Usage', 'Market Share'),
        ('S1', 'Price-Sensitive Individuals', '0.40', '$50', '30/day', '35%'),
        ('S2', 'Quality-Focused Individuals', '0.65', '$150', '60/day', '25%'),
        ('S3', 'Power Users', '0.55', '$120', '100/day', '15%'),
        ('E1', 'Cost-Cutting Enterprises', '0.50', '$35/seat', '25/seat', '4%'),
        ('E2', 'Quality-First Enterprises', '0.72', '$80/seat', '40/seat', '3%'),
        ('E3', 'Strategic Partners', '0.58', '$55/seat', '35/seat', '2%'),
    ]

    # Draw table
    y_start = 0.85
    y_step = 0.08
    colors_row = ['#ecf0f1', '#ffffff']
    header_color = '#34495e'

    for i, row in enumerate(groups_data):
        y = y_start - i * y_step
        bg_color = header_color if i == 0 else colors_row[i % 2]
        text_color = 'white' if i == 0 else '#2c3e50'
        fontweight = 'bold' if i == 0 else 'normal'

        # Background rectangle
        rect = plt.Rectangle((0.05, y - 0.03), 0.9, 0.065,
                             facecolor=bg_color, edgecolor='#bdc3c7',
                             transform=ax.transAxes, linewidth=0.5)
        ax.add_patch(rect)

        # Column positions
        cols_x = [0.08, 0.20, 0.45, 0.55, 0.68, 0.82]
        for j, (text, x) in enumerate(zip(row, cols_x)):
            ax.text(x, y, text, fontsize=9, fontweight=fontweight,
                   color=text_color, transform=ax.transAxes, va='center')

    # Enterprise info
    enterprise_text = """
Enterprise Customers (E1, E2, E3):
• Have multiple seats (50-2000)
• Require negotiation via message threads
• Agent must respond to negotiation threads
• Higher revenue but need relationship management

Small Customers (S1, S2, S3):
• Subscribe directly if plan acceptable
• Automatic churn/switch at billing day
• Generate social media posts affecting reputation
"""

    ax.text(0.5, 0.25, enterprise_text, fontsize=10, ha='center', va='top',
            transform=ax.transAxes, family='monospace',
            bbox=dict(boxstyle='round', facecolor='#f8f9fa', edgecolor='#dee2e6', pad=0.5))

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_impact_flow_diagram(pdf):
    """Create diagram showing how agent actions impact company and customers."""
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # Title
    ax.text(5, 8.7, '7. Impact Flows', fontsize=18, fontweight='bold', ha='center')
    ax.text(5, 8.3, 'How agent actions cascade through the system', fontsize=11, ha='center', color='#555')

    # Agent actions on left
    actions = [
        ('set_prices', 'Pricing'),
        ('set_model_tiers', 'Quality'),
        ('set_daily_spend', 'Marketing'),
        ('set_capacity_tier', 'Capacity'),
        ('send_reply', 'Negotiations'),
    ]

    y_actions = 7
    for i, (action, label) in enumerate(actions):
        y = y_actions - i * 0.9
        box = FancyBboxPatch((0.3, y - 0.25), 1.8, 0.5, boxstyle="round,pad=0.02",
                              facecolor='#3498db', edgecolor='#2980b9')
        ax.add_patch(box)
        ax.text(1.2, y, label, fontsize=9, ha='center', va='center', color='white', fontweight='bold')

    # Company state in middle
    company_items = ['Cash', 'MRR', 'Reputation', 'Awareness', 'Capacity']
    y_company = 7
    for i, item in enumerate(company_items):
        y = y_company - i * 0.9
        box = FancyBboxPatch((4, y - 0.25), 1.5, 0.5, boxstyle="round,pad=0.02",
                              facecolor='#f39c12', edgecolor='#d68910')
        ax.add_patch(box)
        ax.text(4.75, y, item, fontsize=9, ha='center', va='center', color='white', fontweight='bold')

    # Customer effects on right
    customer_effects = ['Acquisition', 'Satisfaction', 'Churn Rate', 'Plan Choice', 'Social Posts']
    y_cust = 7
    for i, effect in enumerate(customer_effects):
        y = y_cust - i * 0.9
        box = FancyBboxPatch((7.5, y - 0.25), 1.8, 0.5, boxstyle="round,pad=0.02",
                              facecolor='#e74c3c', edgecolor='#c0392b')
        ax.add_patch(box)
        ax.text(8.4, y, effect, fontsize=9, ha='center', va='center', color='white', fontweight='bold')

    # Draw flow arrows
    for i in range(5):
        y = y_actions - i * 0.9
        # Action -> Company
        ax.annotate('', xy=(3.9, y), xytext=(2.2, y),
                    arrowprops=dict(arrowstyle='->', color='#7f8c8d', lw=1.5))
        # Company -> Customer
        ax.annotate('', xy=(7.4, y), xytext=(5.6, y),
                    arrowprops=dict(arrowstyle='->', color='#7f8c8d', lw=1.5))

    # Feedback loop arrow (Customer -> Company)
    ax.annotate('', xy=(5.5, 2.5), xytext=(7.5, 2.5),
                arrowprops=dict(arrowstyle='->', color='#9b59b6', lw=2,
                               connectionstyle='arc3,rad=-0.3'))
    ax.text(6.5, 2.0, 'Feedback\n(Revenue, Rep)', fontsize=8, ha='center', color='#9b59b6')

    # Labels
    ax.text(1.2, 7.7, 'AGENT ACTIONS', fontsize=11, fontweight='bold', ha='center', color='#2980b9')
    ax.text(4.75, 7.7, 'COMPANY', fontsize=11, fontweight='bold', ha='center', color='#d68910')
    ax.text(8.4, 7.7, 'CUSTOMERS', fontsize=11, fontweight='bold', ha='center', color='#c0392b')

    # Impact explanation box
    impact_text = """
Impact Chain Examples:
━━━━━━━━━━━━━━━━━━━━━━
• set_prices ↓ → MRR changes → Subscription decisions → Revenue/Churn
• set_model_tiers ↑ → Quality ↑ → Satisfaction ↑ → Churn ↓, Reputation ↑
• set_daily_spend (ads) ↑ → Awareness ↑ → Acquisition ↑ → Cash ↓ then MRR ↑
• set_capacity_tier ↑ → Overload ↓ → P95 latency ↓ → Satisfaction ↑
• send_reply (good offer) → Enterprise signs → Large revenue boost

Feedback Loops:
• Happy customers → positive social posts → reputation ↑ → acquisition ↑
• Outages → complaints → reputation ↓ → acquisition ↓, churn ↑
"""

    ax.text(5, 1.3, impact_text, fontsize=8, ha='center', va='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='#f8f9fa', edgecolor='#dee2e6', pad=0.5))

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_billing_cycle_diagram(pdf):
    """Create billing cycle and decision flow diagram."""
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 9)
    ax.axis('off')

    # Title
    ax.text(5, 8.7, '8. Customer Billing Cycle & Decision Flow', fontsize=18, fontweight='bold', ha='center')
    ax.text(5, 8.3, 'Monthly re-evaluation at each customer\'s billing day', fontsize=11, ha='center', color='#555')

    # Flow chart nodes
    nodes = [
        (2, 6.5, 'Billing Day\nArrives', '#3498db'),
        (5, 6.5, 'Compute\nQuality(plan)', '#9b59b6'),
        (8, 6.5, 'Apply Drift\nto Curve', '#f39c12'),
        (5, 4.5, 'Find Best\nAcceptable\nPlan', '#2ecc71'),
        (2, 2.5, 'CANCEL', '#e74c3c'),
        (5, 2.5, 'SWITCH\nPlan', '#3498db'),
        (8, 2.5, 'STAY\n(Same Plan)', '#27ae60'),
    ]

    for x, y, label, color in nodes:
        box = FancyBboxPatch((x - 0.8, y - 0.5), 1.6, 1, boxstyle="round,pad=0.05",
                              facecolor=color, edgecolor='white', linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, label, fontsize=9, ha='center', va='center', color='white', fontweight='bold')

    # Arrows
    arrows_data = [
        ((2.8, 6.5), (4.2, 6.5)),   # Billing -> Compute
        ((5.8, 6.5), (7.2, 6.5)),   # Compute -> Drift
        ((8, 5.9), (5.6, 5.1)),     # Drift -> Best Plan (curved)
        ((4.4, 4.2), (2.6, 3.1)),   # Best Plan -> Cancel
        ((5, 3.9), (5, 3.1)),       # Best Plan -> Switch
        ((5.6, 4.2), (7.4, 3.1)),   # Best Plan -> Stay
    ]

    for start, end in arrows_data:
        ax.annotate('', xy=end, xytext=start,
                    arrowprops=dict(arrowstyle='->', color='#34495e', lw=2))

    # Decision labels
    ax.text(3.3, 3.8, 'No acceptable\nplan', fontsize=8, ha='center', color='#e74c3c')
    ax.text(5, 3.6, 'Better plan\nexists', fontsize=8, ha='center', color='#3498db')
    ax.text(6.7, 3.8, 'Current plan\nis best', fontsize=8, ha='center', color='#27ae60')

    # Quality computation detail
    quality_text = """
Quality Computation:
━━━━━━━━━━━━━━━━━━
Q = base_quality(tier)
    × (1 - overload_penalty)
    × (1 - outage_penalty)
    × (1 - issue_penalty)
    × (1 + relationship_bonus)

Curve Drift (daily, probabilistic):
q_floor, q_ceiling, c_max can drift
up or down based on market conditions
"""
    ax.text(2, 1.5, quality_text, fontsize=8, ha='left', va='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='#ecf0f1', edgecolor='#bdc3c7', pad=0.3))

    # Plan acceptance rule
    accept_text = """
Plan Acceptance Rule:
━━━━━━━━━━━━━━━━━━━━
Plan is acceptable iff:
  • Cost ≤ c_max (budget)
  • Q_delivered ≥ Q_required(Cost)

Q_required = sigmoid curve:
  q_floor + (q_ceiling - q_floor) /
  (1 + exp(-steepness × (cost - midpoint)))
"""
    ax.text(6, 1.5, accept_text, fontsize=8, ha='left', va='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='#ecf0f1', edgecolor='#bdc3c7', pad=0.3))

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_final_summary(pdf):
    """Create final summary page."""
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis('off')

    ax.text(0.5, 0.95, '9. Summary: Running the SaaS Business', fontsize=18, fontweight='bold',
            ha='center', transform=ax.transAxes)

    summary = """
    ┌────────────────────────────────────────────────────────────────────────────┐
    │                           AGENT'S DAILY LOOP                               │
    ├────────────────────────────────────────────────────────────────────────────┤
    │                                                                            │
    │   1. OBSERVE: Receive daily dashboard                                      │
    │      • Cash position, MRR, subscriber count                                │
    │      • Yesterday's metrics (usage, churn, revenue, costs)                  │
    │      • System health (latency, errors, outages)                            │
    │      • Inbox (notifications, enterprise threads)                           │
    │                                                                            │
    │   2. ANALYZE: Use python_exec for custom analytics                         │
    │      • Query database for trends, cohorts, segments                        │
    │      • Calculate LTV, CAC, churn rates, conversion rates                   │
    │      • Identify at-risk customers, growth opportunities                    │
    │                                                                            │
    │   3. ACT: Configure business via tools                                     │
    │      • Pricing: set_prices (affect acquisition + churn)                    │
    │      • Quality: set_model_tiers (affect satisfaction + costs)              │
    │      • Marketing: set_ad_channel_spend (target customer groups)            │
    │      • Capacity: set_capacity_tier (prevent overload)                      │
    │      • Quotas: set_usage_quotas (rate limiting per plan)                   │
    │      • Negotiations: read_thread + send_reply (enterprise deals)           │
    │                                                                            │
    │   4. ADVANCE: Call next_day to simulate                                    │
    │      • New customers spawned (based on marketing + reputation)             │
    │      • Existing customers re-evaluate plans (may churn/switch)             │
    │      • Revenue collected, costs incurred                                   │
    │      • Service metrics updated (usage, latency, errors)                    │
    │      • Social posts generated (affect reputation)                          │
    │                                                                            │
    │   5. REPEAT: Loop until bankruptcy (cash < 0) or day 365                   │
    │                                                                            │
    ├────────────────────────────────────────────────────────────────────────────┤
    │                              SUCCESS METRICS                               │
    ├────────────────────────────────────────────────────────────────────────────┤
    │   • Final Cash: Higher is better                                           │
    │   • Final MRR: Sustainable recurring revenue                               │
    │   • Subscriber Count: Active paying customers                              │
    │   • Survival: Did not go bankrupt                                          │
    │   • Scoring Window: Performance in days 336-365 (final month)              │
    └────────────────────────────────────────────────────────────────────────────┘
    """

    ax.text(0.5, 0.85, summary, fontsize=9, ha='center', va='top',
            transform=ax.transAxes, family='monospace',
            bbox=dict(boxstyle='round', facecolor='#2c3e50', edgecolor='none', pad=0.5),
            color='#ecf0f1')

    ax.text(0.5, 0.08, 'SaaS Bench - An OpenAI Gym Environment for AI Business Agents',
            fontsize=10, ha='center', transform=ax.transAxes, color='#7f8c8d', style='italic')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def main():
    """Generate the complete PDF report."""
    output_path = 'saas_bench_architecture.pdf'

    print("Generating SaaS Bench Architecture Report...")

    with PdfPages(output_path) as pdf:
        print("  Creating title page...")
        create_title_page(pdf)

        print("  Creating triangle overview...")
        create_triangle_overview(pdf)

        print("  Creating agent interaction diagram...")
        create_agent_interaction_diagram(pdf)

        print("  Creating dashboard example...")
        create_dashboard_example(pdf)

        print("  Creating customer lifecycle...")
        create_customer_lifecycle(pdf)

        print("  Creating sigmoid curve plots...")
        create_sigmoid_curve_plot(pdf)

        print("  Creating customer groups overview...")
        create_customer_groups_plot(pdf)

        print("  Creating impact flow diagram...")
        create_impact_flow_diagram(pdf)

        print("  Creating billing cycle diagram...")
        create_billing_cycle_diagram(pdf)

        print("  Creating final summary...")
        create_final_summary(pdf)

    print(f"\nReport generated: {output_path}")
    return output_path


if __name__ == '__main__':
    main()
