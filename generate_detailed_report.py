"""Generate comprehensive detailed PDF documentation for SaaS Bench.

This creates a detailed technical document covering:
- System architecture and triangle structure
- Individual customer lifecycle (S1-S3)
- Enterprise customer lifecycle (E1-E3) with negotiation
- Social media and reputation system
- All tools with sample inputs/outputs
- Relationship management effects
"""

import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
import textwrap
import numpy as np

# Load tool documentation
with open('src/saas_bench/tool_docs.json', 'r') as f:
    tools = json.load(f)


def wrap_text(text, width=80):
    """Wrap text to specified width."""
    if isinstance(text, dict):
        return json.dumps(text, indent=2)
    return '\n'.join(textwrap.wrap(str(text), width))


# =============================================================================
# TITLE AND TOC
# =============================================================================

def create_title_page(pdf):
    """Create title page with table of contents."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')

    # Title
    ax.text(0.5, 0.85, 'SaaS Bench', fontsize=36, fontweight='bold',
            ha='center', transform=ax.transAxes, color='#2c3e50')
    ax.text(0.5, 0.78, 'Comprehensive Technical Documentation', fontsize=18,
            ha='center', transform=ax.transAxes, color='#7f8c8d')
    ax.text(0.5, 0.73, 'AI Agent Benchmark for SaaS Operations', fontsize=14,
            ha='center', transform=ax.transAxes, color='#95a5a6')

    # Table of contents
    toc = """
Table of Contents

Part 1: System Architecture
  1.1 The Triangle Structure
  1.2 Agent-Environment Interaction
  1.3 Daily Dashboard Flow
  1.4 Tools Overview

Part 2: Customer Groups
  2.1 Individual Customers (S1, S2, S3)
  2.2 Enterprise Customers (E1, E2, E3)

Part 3: Customer Lifecycle
  3.1 Individual Customer Lifecycle
  3.2 Enterprise Customer Lifecycle
  3.3 Participation Constraint Curves

Part 4: Social & Reputation System
  4.1 Social Media Posts
  4.2 Reputation Mechanics
  4.3 Cross-Group Influence

Part 5: Negotiation System
  5.1 Enterprise Negotiation Flow
  5.2 Thread States and Transitions
  5.3 Relationship Management

Part 6: Tool Reference
  6.1 Business Configuration Tools
  6.2 Marketing & Spend Tools
  6.3 Customer Communication Tools
  6.4 Analytics & Monitoring Tools
  6.5 Automation Tools
"""
    ax.text(0.5, 0.5, toc, fontsize=9, ha='center', va='top',
            transform=ax.transAxes, family='monospace',
            bbox=dict(boxstyle='round', facecolor='#f8f9fa', edgecolor='#dee2e6', pad=0.5))

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# =============================================================================
# PART 1: SYSTEM ARCHITECTURE
# =============================================================================

def create_triangle_diagram(pdf):
    """Create the core triangle structure diagram."""
    fig = plt.figure(figsize=(11, 8.5))
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis('off')
    ax.set_title('Part 1.1: The Triangle Structure', fontsize=16, fontweight='bold', pad=20)

    # Agent box (top)
    agent = FancyBboxPatch((3.5, 6), 3, 1.2, boxstyle="round,pad=0.1",
                           facecolor='#3498db', edgecolor='#2980b9', linewidth=2)
    ax.add_patch(agent)
    ax.text(5, 6.6, 'AI AGENT', ha='center', va='center', fontsize=14,
            fontweight='bold', color='white')

    # Company box (bottom left)
    company = FancyBboxPatch((0.5, 1), 3, 2, boxstyle="round,pad=0.1",
                             facecolor='#27ae60', edgecolor='#1e8449', linewidth=2)
    ax.add_patch(company)
    ax.text(2, 2.3, 'COMPANY', ha='center', va='center', fontsize=14,
            fontweight='bold', color='white')
    ax.text(2, 1.7, '(NovaMind AI)', ha='center', va='center', fontsize=10, color='white')

    # Customer box (bottom right)
    customer = FancyBboxPatch((6.5, 1), 3, 2, boxstyle="round,pad=0.1",
                              facecolor='#e74c3c', edgecolor='#c0392b', linewidth=2)
    ax.add_patch(customer)
    ax.text(8, 2.3, 'CUSTOMERS', ha='center', va='center', fontsize=14,
            fontweight='bold', color='white')
    ax.text(8, 1.7, '(6 Groups)', ha='center', va='center', fontsize=10, color='white')

    # Arrows with labels
    # Agent -> Company (tools)
    ax.annotate('', xy=(2, 3), xytext=(4, 6),
                arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=2))
    ax.text(2.5, 4.5, 'Tools:\nset_prices\nset_capacity\nset_spend', fontsize=8,
            ha='center', va='center', color='#2c3e50')

    # Company -> Agent (dashboard)
    ax.annotate('', xy=(4.5, 6), xytext=(2.5, 3),
                arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=2))
    ax.text(3.8, 4.5, 'Dashboard:\ncash, MRR\nmetrics', fontsize=8,
            ha='center', va='center', color='#2c3e50')

    # Agent -> Customer (communication)
    ax.annotate('', xy=(8, 3), xytext=(6, 6),
                arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=2))
    ax.text(7.5, 4.5, 'Tools:\nsend_reply\nread_thread', fontsize=8,
            ha='center', va='center', color='#2c3e50')

    # Customer -> Agent (threads/posts)
    ax.annotate('', xy=(5.5, 6), xytext=(7.5, 3),
                arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=2))
    ax.text(6.2, 4.5, 'Inbox:\nthreads\nsocial posts', fontsize=8,
            ha='center', va='center', color='#2c3e50')

    # Company <-> Customer
    ax.annotate('', xy=(6.5, 2), xytext=(3.5, 2),
                arrowprops=dict(arrowstyle='<->', color='#2c3e50', lw=2))
    ax.text(5, 2.5, 'Service: quality, pricing, capacity', fontsize=8,
            ha='center', va='center', color='#2c3e50')
    ax.text(5, 1.5, 'Response: subscribe, churn, upgrade, social posts', fontsize=8,
            ha='center', va='center', color='#2c3e50')

    # Legend box
    legend_text = """Key Relationships:
- Agent controls Company via business tools
- Company serves Customers via service quality
- Customers respond via subscriptions & social media
- Agent handles Customer communication
- Daily cycle: Agent acts -> next_day -> Results"""
    ax.text(5, 0.3, legend_text, fontsize=8, ha='center', va='bottom',
            bbox=dict(boxstyle='round', facecolor='#ecf0f1', edgecolor='#bdc3c7'))

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_agent_interaction_diagram(pdf):
    """Create detailed agent-environment interaction diagram."""
    fig = plt.figure(figsize=(11, 8.5))
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_title('Part 1.2: Agent-Environment Interaction (Gym API)', fontsize=16, fontweight='bold', pad=20)

    # API box at top right (moved away from agent)
    api_text = """Gym-style API:
obs, info = env.reset()
while not done:
    action = agent.select_action(obs)
    obs, reward, done, truncated, info = env.step(action)"""
    ax.text(11.5, 9.5, api_text, fontsize=8, ha='right', va='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='#fff3cd', edgecolor='#ffc107'))

    # Agent box (top center)
    agent = FancyBboxPatch((3.5, 7), 4, 1.5, boxstyle="round,pad=0.1",
                           facecolor='#e74c3c', edgecolor='#c0392b', linewidth=2)
    ax.add_patch(agent)
    ax.text(5.5, 8.1, 'AI AGENT', fontsize=14, fontweight='bold', ha='center', color='white')
    ax.text(5.5, 7.5, 'Observes dashboard, takes actions', fontsize=9, ha='center', color='white')

    # Environment box (below agent)
    env = FancyBboxPatch((0.5, 0.5), 10, 5.5, boxstyle="round,pad=0.1",
                         facecolor='#f8f9fa', edgecolor='#bdc3c7', linewidth=2)
    ax.add_patch(env)
    ax.text(5.5, 5.7, 'SaaSBenchEnv (Environment)', fontsize=12, fontweight='bold',
            ha='center', va='center', color='#2c3e50')

    # Simulator inside env
    sim = FancyBboxPatch((1, 1), 3.5, 4, boxstyle="round,pad=0.05",
                         facecolor='#27ae60', edgecolor='#1e8449', linewidth=1)
    ax.add_patch(sim)
    ax.text(2.75, 4.6, 'Simulator', fontsize=10, fontweight='bold', ha='center', color='white')
    ax.text(2.75, 3.8, 'step_day()', fontsize=9, ha='center', color='white')
    ax.text(2.75, 3.2, 'generate_customers()', fontsize=9, ha='center', color='white')
    ax.text(2.75, 2.6, 'process_billing()', fontsize=9, ha='center', color='white')
    ax.text(2.75, 2.0, 'compute_usage()', fontsize=9, ha='center', color='white')
    ax.text(2.75, 1.4, 'apply_costs()', fontsize=9, ha='center', color='white')

    # Tools inside env
    tools_box = FancyBboxPatch((5, 1), 3.5, 4, boxstyle="round,pad=0.05",
                               facecolor='#3498db', edgecolor='#2980b9', linewidth=1)
    ax.add_patch(tools_box)
    ax.text(6.75, 4.6, 'AgentTools', fontsize=10, fontweight='bold', ha='center', color='white')
    ax.text(6.75, 3.8, '18 Environment Tools', fontsize=9, ha='center', color='white')
    ax.text(6.75, 3.0, 'Business config', fontsize=8, ha='center', color='white')
    ax.text(6.75, 2.4, 'Marketing spend', fontsize=8, ha='center', color='white')
    ax.text(6.75, 1.8, 'Communication', fontsize=8, ha='center', color='white')
    ax.text(6.75, 1.2, 'Analytics', fontsize=8, ha='center', color='white')

    # Database inside env
    db = FancyBboxPatch((9, 1.5), 1.2, 3, boxstyle="round,pad=0.05",
                        facecolor='#9b59b6', edgecolor='#8e44ad', linewidth=1)
    ax.add_patch(db)
    ax.text(9.6, 4.1, 'SQLite', fontsize=8, fontweight='bold', ha='center', color='white')
    ax.text(9.6, 3.2, '17', fontsize=12, ha='center', color='white')
    ax.text(9.6, 2.6, 'tables', fontsize=8, ha='center', color='white')

    # Arrows between agent and environment
    ax.annotate('', xy=(4.5, 6), xytext=(4.5, 7),
                arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=2))
    ax.text(4.2, 6.5, 'action', fontsize=9, ha='right', va='center')

    ax.annotate('', xy=(6.5, 7), xytext=(6.5, 6),
                arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=2))
    ax.text(6.8, 6.5, 'observation', fontsize=9, ha='left', va='center')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_dashboard_flow_diagram(pdf):
    """Create daily dashboard flow diagram."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_title('Part 1.3: Daily Dashboard Flow', fontsize=16, fontweight='bold', pad=20)

    # Sample dashboard (compact version)
    dashboard = """=== Day 45 Dashboard ===

Cash: $87,432  |  Subscribers: 234  |  MRR: $12,580

--- Yesterday's Metrics ---
Usage: 45,230 units  |  New: 8  |  Churned: 2  |  Upgrades: 3
Overload: 12.5%  |  Outage: No  |  P95: 245ms  |  Errors: 1.2%
Revenue: $2,850  |  Costs: $1,920

--- Current Config ---
Prices: A=$29, B=$79, C=$199  |  Tiers: A=1, B=2, C=3
Quotas: A=100, B=500, C=2000 units/day  |  Capacity: Tier 2
Daily Spend: Ads=$150, Ops=$50, Dev=$100

--- Inbox ---
  [CRITICAL] New negative social media post going viral
  [HIGH] Thread #12: Enterprise negotiation (50 seats)
  [MEDIUM] Thread #18: Support request from Plan B user"""

    ax.text(0.5, 0.92, dashboard, fontsize=8, ha='center', va='top',
            transform=ax.transAxes, family='monospace',
            bbox=dict(boxstyle='round', facecolor='#1a1a2e', edgecolor='#16213e', pad=0.4),
            color='#00ff00')

    # Flow explanation (positioned lower)
    flow_text = """Dashboard Flow:

1. Agent calls next_day tool
2. Simulator runs daily cycle:
   - Process billing decisions (30-day cycle)
   - Generate new customers based on marketing
   - Compute usage and capacity load
   - Check for outages (stochastic based on overload)
   - Process social media posts
   - Apply costs (compute, capacity, marketing, ops, dev)
   - Record metrics to database
3. Dashboard returned with:
   - Financial summary (cash, MRR)
   - Service metrics (usage, latency, errors)
   - Customer changes (new, churned, upgraded)
   - Current configuration
   - Inbox items requiring attention

Agent uses this to decide next actions:
- Adjust prices if churn is high
- Increase capacity if overloaded
- Respond to critical threads
- Adjust marketing spend"""

    ax.text(0.5, 0.52, flow_text, fontsize=9, ha='center', va='top',
            transform=ax.transAxes,
            bbox=dict(boxstyle='round', facecolor='#ecf0f1', edgecolor='#bdc3c7', pad=0.4))

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_tools_overview_page(pdf):
    """Create brief tools overview page (Part 1.4)."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_title('Part 1.4: Tools Overview', fontsize=16, fontweight='bold', pad=20)

    content = """
The agent interacts with the environment through 18 tools across 5 categories:


BUSINESS CONFIGURATION (4 tools)
================================
set_prices          Set monthly prices for Plans A, B, C
set_model_tiers     Set AI model quality tiers (1-5) for each plan
set_capacity_tier   Set infrastructure capacity (1-5)
set_usage_quotas    Set daily usage limits per plan


MARKETING & SPEND (2 tools)
===========================
set_daily_spend     Allocate daily budget: ads, operations, development
set_ad_channel_spend Distribute ad budget across channels (social, search, LinkedIn, etc.)


CUSTOMER COMMUNICATION (3 tools)
================================
read_thread         Read a customer conversation thread
get_thread_history  Get full message history for a thread
send_reply          Send a reply to a customer thread


ANALYTICS & MONITORING (4 tools)
================================
python_exec         Execute Python code for SQL analytics (most powerful tool)
expand_notification Get full details of a notification
get_cost_info       Get current cost structure breakdown
get_social_posts    Search social media posts (sentiment hidden - infer from content)


SIMULATION CONTROL (3 tools)
============================
next_day            Advance simulation by one day, get dashboard
get_tool_documentation  Get detailed documentation for any tool
register/remove/list_daily_calculations  Automate daily Python calculations


AUTOMATION (2 tools)
====================
register_daily_calculation  Register Python code to run automatically each day
remove_daily_calculation    Remove a registered calculation


Key Points:
-----------
• python_exec is the primary analytics tool - can run arbitrary SQL queries
• Communication tools are essential for enterprise negotiations
• next_day is required to advance time (no automatic passage of time)
• Sentiment is NOT provided in social media data - must infer from content
"""

    ax.text(0.5, 0.95, content, fontsize=9, ha='center', va='top',
            transform=ax.transAxes, family='monospace',
            bbox=dict(boxstyle='round', facecolor='#f8f9fa', edgecolor='#dee2e6', pad=0.5))

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# =============================================================================
# PART 2: CUSTOMER GROUPS
# =============================================================================

def create_individual_groups_page(pdf):
    """Create individual customer groups page (S1, S2, S3)."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_title('Part 2.1: Individual Customer Groups (S1, S2, S3)', fontsize=14, fontweight='bold', pad=20)

    groups_text = """
S1: Price-Sensitive Individuals
--------------------------------
Profile: Freelancers, students, hobbyists
Budget: $15-60/month max (c_max)
Quality Need: Low-medium (expected_quality: 0.4 to 0.5)
Behavior:
  - Quick to churn if prices increase
  - Very responsive to discounts
  - Active on social media (Instagram, TikTok, Twitter)
  - Discovers tools via influencer recommendations
Market Share: 25% of individual segment
Personas: Alex Chen (designer), Jordan Taylor (student), Sam Rivera (side hustler)
Negotiation: None (direct subscription)

S2: Quality-Focused Professionals
---------------------------------
Profile: Consultants, writers, attorneys
Budget: $50-150/month max (c_max)
Quality Need: High (expected_quality: 0.6 to 0.7)
Behavior:
  - Willing to pay premium for quality
  - Low tolerance for outages/errors
  - Researches via Google, reads reviews
  - Active on LinkedIn, professional forums
Market Share: 35% of individual segment
Personas: Dr. Michael Foster (consultant), Rachel Kim (tech writer), David Okonkwo (attorney)
Negotiation: None (direct subscription)

S3: Power Users
---------------
Profile: Developers, content agencies, data scientists
Budget: $100-300/month max
Quality Need: Medium-high, performance-focused
Behavior:
  - Heavy API usage, pushes rate limits
  - Cares about throughput and reliability
  - Active in tech communities (HN, Reddit, dev Twitter)
  - Discovers via technical content, SEO
Market Share: 40% of individual segment
Personas: Nina Petrov (developer), Marcus Zhang (agency owner), Sophie Anderson (data scientist)
Negotiation: None (direct subscription)

Common Characteristics:
- Subscribe immediately if any plan acceptable
- Evaluate plans via sigmoid participation curve
- Post on social media based on satisfaction
- 30-day billing cycle for plan re-evaluation
"""

    ax.text(0.05, 0.95, groups_text, fontsize=8.5, ha='left', va='top',
            transform=ax.transAxes, family='monospace')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_enterprise_groups_page(pdf):
    """Create enterprise customer groups page (E1, E2, E3)."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_title('Part 2.2: Enterprise Customer Groups (E1, E2, E3)', fontsize=14, fontweight='bold', pad=20)

    groups_text = """
E1: Cost-Cutting Enterprises
-----------------------------
Profile: Manufacturing, healthcare IT
Seats: 10-50 employees
Budget: $800-4000/month total
Quality Need: Medium (accepts "good enough")
Behavior:
  - Aggressive on price negotiation
  - References competitor pricing
  - Focuses on ROI and cost savings
  - Active on LinkedIn, attends vendor webinars
Negotiation Style: "Our budget is firm", "Competitor offered 20% less"
Negotiation Rate: Fast (wants quick decisions)
Market Share: 30% of enterprise segment
Personas: Jennifer Walsh (VP Ops), Robert Chen (IT Director)

E2: Quality-First Enterprises
-----------------------------
Profile: Law firms, biotech, consulting
Seats: 20-100 employees
Budget: $2000-15000/month total (c_max)
Quality Need: Very high (expected_quality: 0.65 to 0.8)
Behavior:
  - Willing to pay premium for quality guarantees
  - Wants SLAs with financial penalties
  - Concerns about compliance and audit trails
  - Evaluates via thought leadership content
Negotiation Style: "Quality over price", "Need compliance certification"
Negotiation Rate: Medium (thorough evaluation)
Market Share: 40% of enterprise segment
Personas: Victoria Sterling (law partner), Dr. James Nakamura (CMO)

E3: Strategic Partners
----------------------
Profile: Conglomerates, digital services companies
Seats: 50-200+ employees
Budget: $5000-50000+/month total
Quality Need: Custom requirements
Behavior:
  - Wants deep partnership, co-development
  - Long sales cycles
  - C-level engagement
  - Discovers via executive referrals, conferences
Negotiation Style: "Let's discuss partnership", "Interested in equity/revenue sharing"
Negotiation Rate: Slow (strategic decisions)
Market Share: 30% of enterprise segment
Personas: Catherine Dubois (CSO), Thomas Brennan (CEO)

Enterprise-Specific Features:
- Require negotiation thread before subscribing
- Have per-customer reply delays (N-day)
- Multiple negotiation turns with counter-offers
- Relationship score affects perceived quality
- Can have support threads and escalations
"""

    ax.text(0.05, 0.95, groups_text, fontsize=8.5, ha='left', va='top',
            transform=ax.transAxes, family='monospace')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_customer_model_static_page(pdf):
    """Create page documenting static customer variables."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_title('Part 2.3: Customer Model - Static Variables', fontsize=14, fontweight='bold', pad=20)

    content = """
CUSTOMER CHARACTERIZATION: STATIC VARIABLES
============================================

Each customer has STATIC variables that are set at creation and NEVER change.
These define the customer's fundamental preferences and constraints.


STATIC VARIABLES (set at creation, never change):
-------------------------------------------------

1. steepness_left (REAL, range 0.3-2.5)
   - Steepness of participation curve for price < c_max/2
   - Lower = gentler slope for cheap plans (forgiving at low prices)
   - Initialized: exponential(0.8) + 0.3, clamped to [0.3, 2.5]

2. steepness_right (REAL, range 1.0-5.0)
   - Steepness of participation curve for price >= c_max/2
   - Higher = steeper slope for expensive plans (demanding at premium prices)
   - Initialized: exponential(1.5) + 1.0, clamped to [1.0, 5.0]

3. c_max (REAL, > 15.0)
   - Hard budget constraint (maximum price customer will ever pay)
   - Initialized: normal(group.c_max_mean, group.c_max_std * 1.2)
   - Per-seat for enterprise customers

4. expected_quality (REAL, range 0.0-1.0)
   - Customer's quality expectation baseline
   - Higher = harder to satisfy (expects premium quality)
   - Initialized: normal(group.expected_quality_mean, group.expected_quality_std)
   - Used in: Q_perceived = Q_delivered - expected_quality + bonuses - penalties

5. usage_demand (REAL, > 5.0)
   - Desired usage units per day
   - Initialized: normal(group.usage_demand_mean, group.usage_demand_std)
   - Per-seat for enterprise customers

6. group_id (TEXT: S1, S2, S3, E1, E2, E3)
   - Customer group assignment
   - Determines group-specific behavior patterns
   - Set at creation based on marketing channel effectiveness


ENTERPRISE-ONLY STATIC VARIABLES:
---------------------------------

7. seat_count (INTEGER)
   - Number of employee seats
   - Initialized: uniform(group.seat_count_min, group.seat_count_max)

8. reply_delay_mean / reply_delay_std (REAL)
   - Mean and std dev of days to reply in negotiations
   - Initialized: normal from group parameters

9. negotiation_rate (REAL, range 0.05-0.8)
   - Rate of approaching max accepting price per negotiation turn
   - Initialized: normal(group.negotiation_rate_mean, group.negotiation_rate_std)

10. max_negotiation_turns (INTEGER, >= 2)
    - Maximum turns before final accept/reject decision
    - Initialized: normal(group.max_negotiation_turns_mean, group.max_negotiation_turns_std)

11. email (TEXT)
    - Generated email address for enterprise contact
    - Format: persona-based realistic email


PARTICIPATION CURVE MODEL:
--------------------------

The curve Q_required(price) determines minimum acceptable quality:

  Q_required(price) = sigmoid(steepness × (price/c_max - 0.5) × 10)

Where steepness = steepness_left if price < c_max/2 else steepness_right

This creates an asymmetric S-curve:
  - At price=0: Q_required ≈ 0 (any quality acceptable)
  - At price=c_max: Q_required ≈ 1 (premium quality required)
  - Left half (cheap): gentler slope (forgiving)
  - Right half (expensive): steeper slope (demanding)
"""

    ax.text(0.05, 0.95, content, fontsize=7.5, ha='left', va='top',
            transform=ax.transAxes, family='monospace')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_customer_model_dynamic_page(pdf):
    """Create page documenting dynamic customer states."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_title('Part 2.4: Customer Model - Dynamic States', fontsize=14, fontweight='bold', pad=20)

    content = """
CUSTOMER CHARACTERIZATION: DYNAMIC STATES
==========================================

Each customer has DYNAMIC states that change over the course of the simulation.
These are stored in the customer_state table and updated daily.


DYNAMIC STATES (updated daily, stored in customer_state):
---------------------------------------------------------

1. satisfaction (REAL, range 0.0-1.0, default 0.5)
   - How happy the customer is with the service
   - Updated: EMA of (perceived_quality - required_quality at current price)
   - Formula: new_sat = 0.9 * old_sat + 0.1 * instant_satisfaction
   - Affects: churn probability, social media sentiment, reputation

2. relationship (REAL, range 0.0-1.0, default 0.5)
   - Quality of relationship with the company
   - 0.5 = neutral, >0.5 = good relationship, <0.5 = poor relationship
   - Increases: +0.10 when issue resolved in 1 day, +0.05 if resolved in 2 days
   - Decreases: when response times are slow (enterprise)
   - Affects: perceived quality via relationship_bonus

3. open_issue_days (INTEGER, default 0)
   - Days with an unresolved support issue
   - Increases: +1 each day with unresolved issue
   - Resets to 0: when issue is resolved
   - Affects: perceived quality via issue_penalty = min(0.03 * days, 0.15)


DRIFTING CURVE PARAMETERS (can drift, stored in customer_state):
----------------------------------------------------------------

4. current_steepness_left (REAL, nullable)
   - Current left steepness after drift (NULL if never drifted)
   - Drift occurs with probability group.drift_probability per day
   - Drift amount: normal(0, steepness_left * 0.05-0.10)
   - Clamped to [0.3, 2.5]

5. current_steepness_right (REAL, nullable)
   - Current right steepness after drift
   - Drift amount: normal(0, steepness_right * 0.05-0.10)
   - Clamped to [1.0, 5.0]

6. current_c_max (REAL, nullable)
   - Current budget constraint after drift
   - Tendency: slight downward drift (budget pressure)
   - Drift: normal(-c_max * 0.02, c_max * 0.05-0.10)
   - Minimum: 10.0


DERIVED VALUES (computed on demand):
------------------------------------

7. Q_required (computed)
   - Required quality at current price from participation curve
   - Uses current_steepness_left/right or initial values
   - Q_required = sigmoid(steepness × (price/c_max - 0.5) × 10)

8. Q_delivered (computed)
   - Objective quality from plan tier, reliability, fulfillment
   - Q_delivered = 0.5 * model_quality + 0.3 * fulfillment + 0.2 * reliability

9. Q_perceived (computed)
   - Customer's perception of quality
   - Q_perceived = (Q_delivered - expected_quality)
                 + relationship_bonus    (from relationship)
                 + stickiness_bonus      (from subscription duration)
                 - issue_penalty         (from open_issue_days)
                 - quota_penalty         (if usage > quota)


STATE TRACKING (for analytics):
-------------------------------

10. plan_was_acceptable (INTEGER, 0 or 1)
    - Was the plan acceptable yesterday? Used to detect company-caused drops

11. last_quality (REAL)
    - Last computed quality for tracking changes

12. last_satisfaction (REAL)
    - Previous day's satisfaction for detecting decreases

13. last_drift_day (INTEGER)
    - Day of last characteristic drift

14. shock_event_id (INTEGER, nullable)
    - Event ID if curve was shifted by external shock
"""

    ax.text(0.05, 0.95, content, fontsize=7.5, ha='left', va='top',
            transform=ax.transAxes, family='monospace')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_customer_initialization_page(pdf):
    """Create page documenting how customers are initialized."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_title('Part 2.5: Customer Initialization & Group Parameters', fontsize=14, fontweight='bold', pad=20)

    content = """
CUSTOMER INITIALIZATION PROCESS
================================

Customers are generated from CustomerGroupConfig distributions.


INITIALIZATION FLOW:
-------------------

1. GROUP SELECTION
   - Marketing generates trials from specific channels
   - Each channel has different effectiveness per group
   - Customer assigned to group based on marketing channel that generated them

2. STATIC PARAMETER SAMPLING (from group distributions)

   steepness_left  = exponential(0.8) + 0.3        → [0.3, 2.5]
   steepness_right = exponential(1.5) + 1.0        → [1.0, 5.0]
   c_max           = normal(group.c_max_mean, group.c_max_std * 1.2)  → > 15.0
   usage_demand    = normal(group.usage_demand_mean, group.usage_demand_std) → > 5.0
   expected_quality = normal(group.expected_quality_mean, group.expected_quality_std) → [0, 1]

3. CUSTOMER STATE INITIALIZATION
   - satisfaction = 0.5 (neutral)
   - relationship = 0.5 (neutral)
   - open_issue_days = 0
   - current_steepness_left/right/c_max = NULL (not yet drifted)


GROUP PARAMETERS BY TYPE:
-------------------------

SMALL CUSTOMERS (S1, S2, S3):
┌──────┬────────────────────────┬─────────────┬───────────────────┐
│ Group│ c_max (mean±std)       │ exp_quality │ usage_demand      │
├──────┼────────────────────────┼─────────────┼───────────────────┤
│ S1   │ $50 ± $15              │ 0.45 ± 0.12 │ 30 ± 15 units/day │
│ S2   │ $150 ± $40             │ 0.65 ± 0.08 │ 60 ± 25 units/day │
│ S3   │ $120 ± $35             │ 0.55 ± 0.10 │ 100 ± 40 units/day│
└──────┴────────────────────────┴─────────────┴───────────────────┘

ENTERPRISE CUSTOMERS (E1, E2, E3):
┌──────┬────────────────────────┬─────────────┬───────────────────┐
│ Group│ c_max/seat (mean±std)  │ exp_quality │ seats             │
├──────┼────────────────────────┼─────────────┼───────────────────┤
│ E1   │ $35 ± $10              │ 0.50 ± 0.10 │ 50-500 seats      │
│ E2   │ $80 ± $20              │ 0.70 ± 0.08 │ 100-1000 seats    │
│ E3   │ $55 ± $15              │ 0.55 ± 0.10 │ 200-2000 seats    │
└──────┴────────────────────────┴─────────────┴───────────────────┘

ENTERPRISE NEGOTIATION PARAMETERS:
┌──────┬────────────────────────┬───────────────────┬──────────────┐
│ Group│ reply_delay (days)     │ negotiation_rate  │ max_turns    │
├──────┼────────────────────────┼───────────────────┼──────────────┤
│ E1   │ 1.5 ± 0.5              │ 0.40 ± 0.10       │ 4 ± 1.5      │
│ E2   │ 3.0 ± 1.5              │ 0.25 ± 0.08       │ 6 ± 2.0      │
│ E3   │ 4.0 ± 2.0              │ 0.15 ± 0.05       │ 8 ± 3.0      │
└──────┴────────────────────────┴───────────────────┴──────────────┘

DRIFT PARAMETERS:
┌──────┬────────────────────────┬───────────────────────────────────┐
│ Group│ drift_probability      │ Notes                             │
├──────┼────────────────────────┼───────────────────────────────────┤
│ S1   │ 3% per day             │ Volatile, price-conscious         │
│ S2   │ 2% per day             │ Stable, quality-focused           │
│ S3   │ 4% per day             │ Moderately volatile, tech-savvy   │
│ E1   │ 2% per day             │ Budget-driven, predictable        │
│ E2   │ 1.5% per day           │ Very stable, careful evaluators   │
│ E3   │ 1% per day             │ Most stable, relationship-focused │
└──────┴────────────────────────┴───────────────────────────────────┘


EXPECTED_QUALITY INTERPRETATION:
--------------------------------
- 0.45 (S1): Low expectations - prioritizes price over quality
- 0.65-0.70 (S2, E2): High expectations - demands premium quality
- 0.55 (S3, E3): Medium-high - balanced expectations
- 0.50 (E1): Medium - pragmatic about quality
"""

    ax.text(0.05, 0.95, content, fontsize=7.5, ha='left', va='top',
            transform=ax.transAxes, family='monospace')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# =============================================================================
# PART 3: CUSTOMER LIFECYCLE
# =============================================================================

def create_individual_lifecycle_diagram(pdf):
    """Create individual customer lifecycle diagram with social media and reputation."""
    fig = plt.figure(figsize=(11, 8.5))
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 11)
    ax.axis('off')
    ax.set_title('Part 3.1: Individual Customer Lifecycle (S1, S2, S3)', fontsize=14, fontweight='bold', pad=20)

    # Main lifecycle states (top row)
    main_states = [
        (2, 9, 'POTENTIAL', '#95a5a6'),
        (5.5, 9, 'FREE\nTRIAL', '#f39c12'),
        (9, 9, 'SUBSCRIBED', '#27ae60'),
        (13, 9, 'CHURNED', '#e74c3c'),
    ]

    # Secondary states
    secondary_states = [
        (9, 6.5, 'PLAN\nCHANGE', '#3498db'),         # Customer-initiated plan change
        (12, 6.5, 'COMPANY\nCHANGE', '#c0392b'),     # Company-forced plan change (red - negative)
        (5.5, 6.5, 'SOCIAL\nMEDIA', '#e91e63'),      # Social media action
        (2, 6.5, 'REPUTATION', '#9c27b0'),           # Reputation system
    ]

    for x, y, label, color in main_states:
        circle = Circle((x, y), 0.65, facecolor=color, edgecolor='white', linewidth=2)
        ax.add_patch(circle)
        ax.text(x, y, label, ha='center', va='center', fontsize=6, fontweight='bold', color='white')

    for x, y, label, color in secondary_states:
        rect = FancyBboxPatch((x-0.6, y-0.4), 1.2, 0.8, boxstyle='round,pad=0.05',
                              facecolor=color, edgecolor='white', linewidth=2)
        ax.add_patch(rect)
        ax.text(x, y, label, ha='center', va='center', fontsize=5, fontweight='bold', color='white')

    # Main flow arrows
    main_arrows = [
        ((2.65, 9), (4.85, 9), 'Marketing\n+WoM'),
        ((6.15, 9), (8.35, 9), 'Plan OK'),
        ((6.15, 8.5), (12.35, 8.7), 'No plan'),
        ((9.65, 9), (12.35, 9), 'Churn'),
    ]

    for start, end, label in main_arrows:
        ax.annotate('', xy=end, xytext=start,
                    arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=1.5))
        mid = ((start[0] + end[0])/2, (start[1] + end[1])/2)
        ax.text(mid[0], mid[1] + 0.3, label, fontsize=5, ha='center', va='bottom', color='#2c3e50')

    # Plan change arrows
    ax.annotate('', xy=(9, 7.15), xytext=(9, 8.35),
                arrowprops=dict(arrowstyle='->', color='#3498db', lw=1.5))
    ax.text(9.3, 7.7, 'Switch', fontsize=5, ha='left', color='#3498db')
    ax.annotate('', xy=(9.5, 8.35), xytext=(9.5, 7.15),
                arrowprops=dict(arrowstyle='->', color='#3498db', lw=1.5))
    ax.text(9.7, 7.7, 'Done', fontsize=5, ha='left', color='#3498db')

    # Self-loop for billing re-evaluation
    ax.annotate('', xy=(9.3, 9.65), xytext=(8.7, 9.65),
                arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=1.5,
                               connectionstyle='arc3,rad=0.5'))
    ax.text(9, 10.1, '30-day billing', fontsize=5, ha='center', color='#2c3e50')

    # Social media arrows (from SUBSCRIBED and CHURNED)
    ax.annotate('', xy=(6.1, 6.5), xytext=(8.35, 8.5),
                arrowprops=dict(arrowstyle='->', color='#e91e63', lw=1.5, linestyle='--'))
    ax.text(7, 7.7, 'Post\n(prob~sat)', fontsize=4, ha='center', color='#e91e63')

    ax.annotate('', xy=(6.1, 6.8), xytext=(12.5, 8.5),
                arrowprops=dict(arrowstyle='->', color='#e91e63', lw=1.5, linestyle='--'))
    ax.text(10, 7.3, 'Neg post', fontsize=4, ha='center', color='#e91e63')

    # Reputation impact arrows
    ax.annotate('', xy=(2.6, 6.5), xytext=(4.9, 6.5),
                arrowprops=dict(arrowstyle='->', color='#9c27b0', lw=1.5))
    ax.text(3.75, 6.8, 'Sentiment\n→ Impact', fontsize=4, ha='center', color='#9c27b0')

    # Reputation to Potential (word of mouth feedback)
    ax.annotate('', xy=(2, 8.35), xytext=(2, 7.1),
                arrowprops=dict(arrowstyle='->', color='#9c27b0', lw=1.5))
    ax.text(1.5, 7.7, 'WoM\nboost', fontsize=4, ha='center', color='#9c27b0')

    # Company-initiated plan change arrows
    # SUBSCRIBED -> COMPANY CHANGE
    ax.annotate('', xy=(12, 7.1), xytext=(9.5, 8.5),
                arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.5))
    ax.text(10.9, 8, 'Company\nforces', fontsize=4, ha='center', color='#c0392b')

    # COMPANY CHANGE -> SOCIAL MEDIA (negative post) - CONDITIONAL on lower satisfaction
    ax.annotate('', xy=(6.1, 6.7), xytext=(11.4, 6.7),
                arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.5, linestyle='--'))
    ax.text(8.7, 7.0, 'Neg post\n(if sat ↓)', fontsize=4, ha='center', color='#c0392b')

    # COMPANY CHANGE -> REPUTATION (direct damage) - CONDITIONAL on lower satisfaction
    ax.annotate('', xy=(2.6, 6.3), xytext=(11.4, 6.3),
                arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.2, linestyle=':'))
    ax.text(7, 6.0, 'Rep damage (if sat ↓)', fontsize=4, ha='center', color='#c0392b')

    # Random issues note (moved)
    ax.text(14.5, 8, 'Random issues\naffect perceived\nquality', fontsize=4, ha='center',
            style='italic', color='#7f8c8d')

    # Stickiness note (moved)
    ax.text(14.5, 7, 'Stickiness:\nlonger sub\n= higher\nperceived Q', fontsize=4, ha='center',
            style='italic', color='#27ae60')

    # Explanation box
    explanation = """Individual Customer Lifecycle:

1. ATTRACTION: Marketing + Word of Mouth (WoM). Reputation affects WoM bonus.

2. FREE TRIAL: Evaluate via Q_required(C) = sigmoid(steepness*(C/c_max-0.5)*10). Trial cost: $5.

3. SUBSCRIBED: Daily usage, satisfaction = EMA(Q_perceived - Q_required).
   Stickiness bonus: longer subscription → higher perceived quality.

4. PLAN CHANGE (Customer): Customer-initiated upgrade/downgrade based on satisfaction comparison.

5. COMPANY CHANGE (Forced): Company-initiated plan changes (price increase, plan discontinuation).
   → IF results in LOWER satisfaction: negative posts + reputation damage (customers feel betrayed).

6. SOCIAL MEDIA: Post probability based on satisfaction OR forced changes. Sentiment → reputation.

7. CHURN (TERMINAL): Churned customers do NOT return. Often post negative reviews."""

    ax.text(8, 0.2, explanation, fontsize=5.5, ha='center', va='bottom',
            bbox=dict(boxstyle='round', facecolor='#ecf0f1', edgecolor='#bdc3c7', pad=0.3))

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_enterprise_lifecycle_diagram(pdf):
    """Create enterprise customer lifecycle diagram with all negotiation types and reputation."""
    fig = plt.figure(figsize=(11, 8.5))
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 17)
    ax.set_ylim(0, 11)
    ax.axis('off')
    ax.set_title('Part 3.2: Enterprise Customer Lifecycle (E1, E2, E3)', fontsize=14, fontweight='bold', pad=20)

    # Main lifecycle states (top row)
    main_states = [
        (1.5, 9.5, 'POTENTIAL', '#95a5a6'),
        (4.5, 9.5, 'LEAD', '#f39c12'),
        (8, 9.5, 'NEGOTIATING', '#9b59b6'),
        (12, 9.5, 'SUBSCRIBED', '#27ae60'),
        (15.5, 9.5, 'CHURNED', '#e74c3c'),
    ]

    # Negotiation types (middle section)
    neg_types = [
        (5.5, 7, 'new_lead', '#9b59b6'),
        (8, 7, 'plan_change', '#3498db'),
        (10.5, 7, 'churn_prev', '#e67e22'),
        (13, 7, 'budget_freeze', '#c0392b'),
    ]

    # Bottom row: Social media, reputation, and company change
    bottom_states = [
        (7, 5.5, 'COMPANY\nCHANGE', '#8e44ad'),    # Company-forced plan change (darker purple)
        (4, 4.5, 'SOCIAL\nMEDIA', '#e91e63'),
        (1.5, 4.5, 'REPUTATION', '#9c27b0'),
    ]

    # Draw main states
    for x, y, label, color in main_states:
        circle = Circle((x, y), 0.55, facecolor=color, edgecolor='white', linewidth=2)
        ax.add_patch(circle)
        ax.text(x, y, label, ha='center', va='center', fontsize=5, fontweight='bold', color='white')

    # Draw negotiation type boxes
    for x, y, label, color in neg_types:
        rect = FancyBboxPatch((x-0.7, y-0.35), 1.4, 0.7, boxstyle='round,pad=0.03',
                              facecolor=color, edgecolor='white', linewidth=1.5, alpha=0.9)
        ax.add_patch(rect)
        ax.text(x, y, label, ha='center', va='center', fontsize=5, fontweight='bold', color='white')

    # Draw bottom states
    for x, y, label, color in bottom_states:
        rect = FancyBboxPatch((x-0.55, y-0.35), 1.1, 0.7, boxstyle='round,pad=0.03',
                              facecolor=color, edgecolor='white', linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x, y, label, ha='center', va='center', fontsize=5, fontweight='bold', color='white')

    # Main flow arrows
    ax.annotate('', xy=(3.95, 9.5), xytext=(2.05, 9.5),
                arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=1.5))
    ax.text(3, 9.8, 'Marketing', fontsize=5, ha='center', color='#2c3e50')

    ax.annotate('', xy=(7.45, 9.5), xytext=(5.05, 9.5),
                arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=1.5))
    ax.text(6.25, 9.8, 'Outreach', fontsize=5, ha='center', color='#2c3e50')

    ax.annotate('', xy=(11.45, 9.5), xytext=(8.55, 9.5),
                arrowprops=dict(arrowstyle='->', color='#27ae60', lw=1.5))
    ax.text(10, 9.8, 'Deal', fontsize=5, ha='center', color='#27ae60')

    ax.annotate('', xy=(14.95, 9.5), xytext=(12.55, 9.5),
                arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=1.5))
    ax.text(13.75, 9.8, 'Churn', fontsize=5, ha='center', color='#e74c3c')

    # Negotiation failure back to LEAD (lost)
    ax.annotate('', xy=(4.5, 8.95), xytext=(7.5, 8.95),
                arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=1.2, linestyle='--'))
    ax.text(6, 8.7, 'Reject/Timeout', fontsize=4, ha='center', color='#e74c3c')

    # Arrows from LEAD to new_lead negotiation
    ax.annotate('', xy=(5.5, 7.35), xytext=(4.5, 8.95),
                arrowprops=dict(arrowstyle='->', color='#9b59b6', lw=1.2))

    # Arrows from SUBSCRIBED to re-negotiation types
    ax.annotate('', xy=(8, 7.35), xytext=(11.5, 8.95),
                arrowprops=dict(arrowstyle='->', color='#3498db', lw=1.2))
    ax.text(9.5, 8.3, 'plan_change', fontsize=4, ha='center', color='#3498db')

    ax.annotate('', xy=(10.5, 7.35), xytext=(11.8, 8.95),
                arrowprops=dict(arrowstyle='->', color='#e67e22', lw=1.2))
    ax.text(11.5, 8.1, 'churn_prev', fontsize=4, ha='center', color='#e67e22')

    ax.annotate('', xy=(13, 7.35), xytext=(12.2, 8.95),
                arrowprops=dict(arrowstyle='->', color='#c0392b', lw=1.2))
    ax.text(13, 8.1, 'budget', fontsize=4, ha='center', color='#c0392b')

    # All negotiations go back to main NEGOTIATING state
    ax.annotate('', xy=(8, 8.95), xytext=(6.5, 7.35),
                arrowprops=dict(arrowstyle='->', color='#9b59b6', lw=1, linestyle=':'))

    # Self-loop for billing
    ax.annotate('', xy=(12.3, 10.05), xytext=(11.7, 10.05),
                arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=1.2,
                               connectionstyle='arc3,rad=0.5'))
    ax.text(12, 10.5, '30d billing', fontsize=4, ha='center', color='#2c3e50')

    # Social media arrows
    ax.annotate('', xy=(4.55, 4.5), xytext=(11.5, 8.95),
                arrowprops=dict(arrowstyle='->', color='#e91e63', lw=1.2, linestyle='--'))
    ax.text(8, 6, 'Post (based\non satisfaction)', fontsize=4, ha='center', color='#e91e63')

    ax.annotate('', xy=(4.55, 4.7), xytext=(15, 8.95),
                arrowprops=dict(arrowstyle='->', color='#e91e63', lw=1.2, linestyle='--'))
    ax.text(10.5, 5.5, 'Neg post on churn', fontsize=4, ha='center', color='#e91e63')

    # Social media to reputation
    ax.annotate('', xy=(2.05, 4.5), xytext=(3.45, 4.5),
                arrowprops=dict(arrowstyle='->', color='#9c27b0', lw=1.2))
    ax.text(2.75, 4.8, 'Impact', fontsize=4, ha='center', color='#9c27b0')

    # Reputation to potential (WoM)
    ax.annotate('', xy=(1.5, 8.95), xytext=(1.5, 5.15),
                arrowprops=dict(arrowstyle='->', color='#9c27b0', lw=1.2))
    ax.text(1.1, 7, 'WoM\nboost', fontsize=4, ha='center', color='#9c27b0')

    # Company-initiated plan change arrows
    # SUBSCRIBED -> COMPANY CHANGE
    ax.annotate('', xy=(7, 5.85), xytext=(11.5, 8.95),
                arrowprops=dict(arrowstyle='->', color='#8e44ad', lw=1.2))
    ax.text(9, 7.5, 'Company\nforces', fontsize=4, ha='center', color='#8e44ad')

    # COMPANY CHANGE -> SOCIAL MEDIA (negative post) - CONDITIONAL on lower satisfaction
    ax.annotate('', xy=(4.55, 4.8), xytext=(6.45, 5.5),
                arrowprops=dict(arrowstyle='->', color='#8e44ad', lw=1.2, linestyle='--'))
    ax.text(5.3, 5.4, 'Neg post\n(if sat ↓)', fontsize=3, ha='center', color='#8e44ad')

    # COMPANY CHANGE -> REPUTATION (direct damage) - CONDITIONAL on lower satisfaction
    ax.annotate('', xy=(2.05, 4.7), xytext=(6.45, 5.3),
                arrowprops=dict(arrowstyle='->', color='#8e44ad', lw=1, linestyle=':'))
    ax.text(4.2, 5.3, 'Rep dmg\n(if sat ↓)', fontsize=3, ha='center', color='#8e44ad')

    # Notes
    ax.text(15.5, 6.5, 'Random issues\naffect perceived\nquality', fontsize=4, ha='center',
            style='italic', color='#7f8c8d')
    ax.text(15.5, 5.5, 'Stickiness:\nlonger sub =\nhigher Q', fontsize=4, ha='center',
            style='italic', color='#27ae60')

    # Explanation box
    explanation = """Enterprise Lifecycle with Negotiation Types:

NEGOTIATION TYPES (customer-initiated):
• new_lead: Initial contact. Delays: E1=1.5d, E2=2.5d, E3=4d
• plan_change: Customer wants upgrade/downgrade.
• churn_prevention: At-risk customer (satisfaction<0).
• budget_freeze: Budget constraints (E1 common).

COMPANY CHANGE (company-initiated):
• Company forces plan change (price increase, plan discontinuation)
• IF results in LOWER satisfaction:
  → Negative social media posts + direct reputation damage

SOCIAL MEDIA & REPUTATION:
• Posts based on satisfaction OR forced changes → affect reputation
• Reputation → Word of Mouth → arrivals (feedback loop)"""

    ax.text(8.5, 0.1, explanation, fontsize=5.5, ha='center', va='bottom',
            bbox=dict(boxstyle='round', facecolor='#ecf0f1', edgecolor='#bdc3c7', pad=0.3))

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_participation_curves_page(pdf):
    """Create page with 3 separate plots for different customer types."""
    fig = plt.figure(figsize=(8.5, 11))
    fig.suptitle('Part 3.3: Participation Constraint Curves', fontsize=14, fontweight='bold', y=0.98)

    # Asymmetric sigmoid: steeper on right (near c_max, customers demand more quality)
    def asymmetric_required_quality(x_normalized, steepness_left, steepness_right):
        """Asymmetric sigmoid: different steepness for left and right halves.

        Left half (x < 0.5): gentler slope - even cheap plans need some quality
        Right half (x >= 0.5): steeper slope - near c_max, quality demands spike
        """
        result = np.zeros_like(x_normalized)
        left_mask = x_normalized < 0.5
        right_mask = ~left_mask

        # Left half: gentler rise
        result[left_mask] = 0.5 / (1 + np.exp(-steepness_left * (x_normalized[left_mask] - 0.25) * 10))

        # Right half: steeper rise to 1
        result[right_mask] = 0.5 + 0.5 / (1 + np.exp(-steepness_right * (x_normalized[right_mask] - 0.75) * 10))

        return result

    x_norm = np.linspace(0, 1, 200)

    # Plan Q_delivered values (these are fixed by the company, not on the curve)
    plans = {
        'A': {'price': 29, 'q_delivered': 0.5, 'color': '#3498db'},
        'B': {'price': 79, 'q_delivered': 0.7, 'color': '#27ae60'},
        'C': {'price': 199, 'q_delivered': 0.9, 'color': '#e74c3c'},
    }

    # Three customer types with different c_max and curve parameters
    customers = [
        {'name': 'S1: Price-Sensitive', 'c_max': 60, 'steep_l': 1.0, 'steep_r': 2.5, 'color': '#3498db'},
        {'name': 'S2: Quality-Focused', 'c_max': 150, 'steep_l': 0.8, 'steep_r': 2.0, 'color': '#27ae60'},
        {'name': 'E2: Enterprise', 'c_max': 300, 'steep_l': 0.6, 'steep_r': 1.5, 'color': '#9b59b6'},
    ]

    for i, cust in enumerate(customers):
        ax = fig.add_subplot(3, 1, i + 1)

        # Plot the Q_required curve (asymmetric)
        q_req = asymmetric_required_quality(x_norm, cust['steep_l'], cust['steep_r'])
        ax.plot(x_norm, q_req, color=cust['color'], linewidth=2.5, label='Q_required curve')
        ax.fill_between(x_norm, 0, q_req, alpha=0.1, color=cust['color'])

        # Plot each plan as a point (Q_delivered at normalized price position)
        for plan_name, plan in plans.items():
            if plan['price'] <= cust['c_max']:
                x_pos = plan['price'] / cust['c_max']
                q_delivered = plan['q_delivered']
                q_required_at_price = asymmetric_required_quality(np.array([x_pos]), cust['steep_l'], cust['steep_r'])[0]

                # Plot Q_delivered point (NOT on curve)
                ax.scatter([x_pos], [q_delivered], s=120, marker='*', color=plan['color'],
                          edgecolor='black', linewidth=0.5, zorder=10)

                # Draw vertical line from Q_required to Q_delivered to show gap
                ax.plot([x_pos, x_pos], [q_required_at_price, q_delivered],
                       color=plan['color'], linestyle='--', linewidth=1, alpha=0.7)

                # Label
                status = '✓' if q_delivered >= q_required_at_price else '✗'
                ax.annotate(f'{plan_name} ${plan["price"]}\nQ={q_delivered} {status}',
                           (x_pos, q_delivered), textcoords='offset points',
                           xytext=(8, 0), fontsize=7, color=plan['color'])
            else:
                # Plan too expensive - mark on right edge
                ax.annotate(f'{plan_name} ${plan["price"]}\n(> c_max)',
                           (1.02, plan['q_delivered']), fontsize=6, color='gray',
                           ha='left', va='center')

        ax.set_title(f'{cust["name"]} (c_max=${cust["c_max"]})', fontsize=10, fontweight='bold')
        ax.set_xlabel('Normalized Price (C / c_max)')
        ax.set_ylabel('Quality')
        ax.set_xlim(0, 1.15)
        ax.set_ylim(0, 1.1)
        ax.axhline(y=0.5, color='gray', linestyle=':', alpha=0.5, linewidth=0.5)
        ax.grid(True, alpha=0.3)

        # Add legend only to first plot
        if i == 0:
            ax.plot([], [], 'k*', markersize=10, label='Plan Q_delivered')
            ax.plot([], [], 'k--', linewidth=1, label='Gap to Q_required')
            ax.legend(loc='upper left', fontsize=7)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    pdf.savefig(fig)
    plt.close(fig)


def create_participation_curves_explanation_page(pdf):
    """Create explanation page for participation curves."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_title('Part 3.3: Participation Curve Model (Continued)', fontsize=14, fontweight='bold', pad=20)

    explanation = """
Asymmetric Participation Constraint Model
=========================================

Each customer has an ASYMMETRIC curve - steeper on the right (near c_max):

    Left half (price < c_max/2):   Gentler slope - even cheap plans need decent quality
    Right half (price >= c_max/2): Steeper slope - near c_max, quality demands spike sharply

This reflects reality: customers paying near their max budget expect premium quality.


IMPORTANT: Plans Have FIXED Q_delivered
=======================================

Plans (A, B, C) deliver a FIXED quality level set by the company:
    • Plan A: Q_delivered = 0.5 (basic)
    • Plan B: Q_delivered = 0.7 (standard)
    • Plan C: Q_delivered = 0.9 (premium)

These are NOT on the curve! The curve shows Q_required at each price point.

Decision: Customer accepts plan iff:
    1. Q_delivered >= Q_required(price/c_max)  [quality sufficient]
    2. price <= c_max                          [can afford it]


Reading the Plots
=================

• Solid curve: Q_required - minimum quality customer demands at that price
• Stars (*): Plan Q_delivered - actual quality the plan provides
• Dashed lines: Gap between Q_required and Q_delivered
• ✓: Plan acceptable (Q_delivered >= Q_required)
• ✗: Plan rejected (Q_delivered < Q_required)
• (> c_max): Plan unaffordable for this customer


Example Reading (S1 customer, c_max=$60):
-----------------------------------------
• Plan A ($29): x = 29/60 = 0.48, Q_required ≈ 0.35, Q_delivered = 0.5 → ✓ Accept
• Plan B ($79): 79 > 60 → Cannot afford, rejected regardless of quality
• Plan C ($199): 199 > 60 → Cannot afford


Agent Implications:
==================
• Different customers accept different plans at the same price
• Must offer multiple price points to capture different segments
• High-budget customers (E2) can accept expensive plans; low-budget (S1) need cheap options
• Quality improvements benefit customers near the acceptance threshold
"""

    ax.text(0.5, 0.95, explanation, fontsize=8.5, ha='center', va='top',
            transform=ax.transAxes, family='monospace',
            bbox=dict(boxstyle='round', facecolor='#f8f9fa', edgecolor='#dee2e6', pad=0.5))

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# =============================================================================
# PART 4: SOCIAL & REPUTATION SYSTEM
# =============================================================================

def create_social_media_page(pdf):
    """Create social media system page."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_title('Part 4.1: Social Media System', fontsize=14, fontweight='bold', pad=20)

    content = """
Social Media Post Generation
============================

When Posts Happen:
- Daily probability based on satisfaction:
  * Satisfaction >= 0.8 or <= 0.2: 2% daily chance (extreme feelings = more posts)
  * Satisfaction 0.7-0.8 or 0.2-0.3: 1% daily chance
  * Neutral satisfaction (0.3-0.7): 0.3% daily chance
- New customers (first 30 days): 2x probability
- Each post generates notification for agent

Sentiment Determination:
Based on satisfaction level:
- Satisfaction >= 0.8: 70% positive, 25% neutral, 5% negative
- Satisfaction 0.6-0.8: 40% positive, 50% neutral, 10% negative
- Satisfaction 0.4-0.6: 15% positive, 55% neutral, 30% negative
- Satisfaction 0.2-0.4: 5% positive, 35% neutral, 60% negative
- Satisfaction < 0.2: 2% positive, 18% neutral, 80% negative

Sample Posts by Group:

S1 (Price-Sensitive):
  Positive: "Just discovered NovaMind! Finally an AI tool that doesn't break the bank."
  Negative: "Had to cancel NovaMind subscription. Just too expensive for what I use."

S2 (Quality-Focused):
  Positive: "NovaMind has elevated my client deliverables. The quality is outstanding."
  Negative: "Missed a client deadline because NovaMind was down. Unacceptable."

S3 (Power Users):
  Positive: "Benchmark results: NovaMind API handling 10k requests/day flawlessly."
  Negative: "Hit rate limits again. Automation completely broke. Need higher quotas."

E1 (Cost-Cutting Enterprise):
  Positive: "Team productivity increased 40% with NovaMind. ROI speaks for itself."
  Negative: "ROI projections not meeting expectations. Reviewing our contract."

E2 (Quality-First Enterprise):
  Positive: "NovaMind meets our strict quality standards. Impressive accuracy."
  Negative: "Accuracy issues caused a compliance incident. Escalating to leadership."

E3 (Strategic Partners):
  Positive: "Excited to announce strategic partnership with NovaMind for AI transformation."
  Negative: "Strategic concerns about NovaMind long-term viability. Evaluating alternatives."

Engagement Metrics:
- Likes: 1-100 for individuals, 5-50 for enterprise (varies by group)
- Shares: 0-30 for individuals, 0-10 for enterprise
- Negative posts get 1.5-2.5x virality multiplier
- 1% chance of viral spike (5-10x engagement)
"""

    ax.text(0.5, 0.95, content, fontsize=8, ha='center', va='top',
            transform=ax.transAxes, family='monospace')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_reputation_mechanics_page(pdf):
    """Create reputation mechanics page."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_title('Part 4.2: Reputation Mechanics', fontsize=14, fontweight='bold', pad=20)

    content = """
Per-Group Reputation System
===========================

Each customer group (S1, S2, S3, E1, E2, E3) has its own reputation score (0.0 to 1.0).

Reputation Impacts Customer Acquisition:
- reputation_factor = 0.6 + 0.8 * reputation
- Low reputation (0.2): factor = 0.76 (24% fewer arrivals)
- Neutral (0.5): factor = 1.0 (baseline)
- High reputation (0.8): factor = 1.24 (24% more arrivals)

How Reputation Changes:

1. SOCIAL MEDIA POSTS:
   - Positive posts: +0.005 to +0.015 base impact
   - Negative posts: -0.01 to -0.03 base impact
   - Neutral posts: -0.002 to +0.002 (slight random)
   - Impact amplified by virality: impact * (1 + 2 * virality_score)
   - Enterprise posts have 1.5x weight

2. QUALITY-RELATED CHURN:
   - Cancellation with low satisfaction damages reputation
   - Damage = reputation_quality_cancel_damage * (0.5 + random)
   - Only applies to group of churned customer

3. SERVICE OUTAGES:
   - Major outages can trigger reputation damage
   - Communicated through notifications

Database Tables:
- group_reputations: current reputation per group
- reputation_history: tracks changes with source
  (social_media, quality_cancel, cross_influence)

Sample reputation_history entries:
| day | group_id | reputation | change_source          |
|-----|----------|------------|------------------------|
| 15  | S1       | 0.52       | social_media           |
| 15  | S2       | 0.48       | cross_influence_from_S1|
| 23  | E2       | 0.45       | quality_cancel         |
"""

    ax.text(0.5, 0.95, content, fontsize=9, ha='center', va='top',
            transform=ax.transAxes, family='monospace')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_cross_influence_page(pdf):
    """Create cross-group influence page."""
    fig = plt.figure(figsize=(8.5, 11))

    # Top: Influence matrix visualization
    ax1 = fig.add_subplot(211)
    ax1.set_title('Part 4.3: Cross-Group Reputation Influence', fontsize=14, fontweight='bold')

    # Influence matrix data
    groups = ['S1', 'S2', 'S3', 'E1', 'E2', 'E3']
    matrix = np.array([
        [1.0, 0.4, 0.3, 0.1, 0.1, 0.0],  # S1 influences
        [0.4, 1.0, 0.5, 0.2, 0.3, 0.1],  # S2 influences
        [0.3, 0.5, 1.0, 0.2, 0.3, 0.2],  # S3 influences
        [0.1, 0.2, 0.2, 1.0, 0.6, 0.4],  # E1 influences
        [0.1, 0.3, 0.3, 0.6, 1.0, 0.5],  # E2 influences
        [0.0, 0.1, 0.2, 0.4, 0.5, 1.0],  # E3 influences
    ])

    im = ax1.imshow(matrix, cmap='YlOrRd', aspect='auto')
    ax1.set_xticks(range(6))
    ax1.set_yticks(range(6))
    ax1.set_xticklabels(groups)
    ax1.set_yticklabels(groups)
    ax1.set_xlabel('Influenced Group')
    ax1.set_ylabel('Influencing Group')

    for i in range(6):
        for j in range(6):
            ax1.text(j, i, f'{matrix[i,j]:.1f}', ha='center', va='center', fontsize=8)

    plt.colorbar(im, ax=ax1, label='Influence Strength')

    # Bottom: Explanation
    ax2 = fig.add_subplot(212)
    ax2.axis('off')

    explanation = """
Cross-Group Influence Mechanics:

When reputation changes in one group, it spreads to related groups:

cross_impact = direct_impact * influence_weight * 0.3  (30% damping)

Influence Patterns:

Individual Groups (S1, S2, S3):
- S1 <-> S2: 0.4 (similar individual users)
- S2 <-> S3: 0.5 (professional overlap)
- S1 -> E*: 0.1 (minimal enterprise influence)

Enterprise Groups (E1, E2, E3):
- E1 <-> E2: 0.6 (enterprise B2B network)
- E2 <-> E3: 0.5 (quality-focused overlap)
- E3 -> S*: 0.0-0.2 (strategic partners don't influence individuals much)

Cross-Segment:
- S3 -> E*: 0.2-0.3 (power users overlap with enterprise)
- E2 -> S2: 0.3 (quality professionals follow enterprise signals)

Example Scenario:
- Viral negative post from E2 customer (virality=0.8)
- E2 direct impact: -0.04
- E1 cross-impact: -0.04 * 0.6 * 0.3 = -0.007
- E3 cross-impact: -0.04 * 0.5 * 0.3 = -0.006
- S2 cross-impact: -0.04 * 0.3 * 0.3 = -0.004
- S3 cross-impact: -0.04 * 0.3 * 0.3 = -0.004

This creates:
1. Cluster effects: Enterprise issues affect all enterprise groups
2. Quality signals: S2/E2 quality issues spread to similar groups
3. Isolation: S1 issues mostly stay within S1
4. Asymmetry: Enterprise influences individuals more than reverse
"""

    ax2.text(0.5, 0.95, explanation, fontsize=9, ha='center', va='top',
            transform=ax2.transAxes, family='monospace',
            bbox=dict(boxstyle='round', facecolor='#f8f9fa', edgecolor='#dee2e6', pad=0.5))

    plt.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)


# =============================================================================
# PART 5: NEGOTIATION SYSTEM
# =============================================================================

def create_negotiation_flow_page(pdf):
    """Create enterprise negotiation flow page."""
    fig = plt.figure(figsize=(11, 8.5))
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 11)
    ax.axis('off')
    ax.set_title('Part 5.1: Enterprise Negotiation Flow', fontsize=14, fontweight='bold', pad=20)

    # Flow steps - at top
    steps = [
        (1.5, 10, '1. Lead', '#95a5a6'),
        (4, 10, '2. Outreach', '#f39c12'),
        (6.5, 10, '3. Agent', '#3498db'),
        (9, 10, '4. Evaluate', '#9b59b6'),
        (11.5, 10, '5. Outcome', '#27ae60'),
    ]

    for x, y, label, color in steps:
        box = FancyBboxPatch((x-0.7, y-0.35), 1.4, 0.7, boxstyle="round,pad=0.05",
                             facecolor=color, edgecolor='white', linewidth=2)
        ax.add_patch(box)
        ax.text(x, y, label, ha='center', va='center', fontsize=7, fontweight='bold', color='white')

    # Arrows
    for i in range(len(steps)-1):
        ax.annotate('', xy=(steps[i+1][0]-0.7, steps[i+1][1]),
                    xytext=(steps[i][0]+0.7, steps[i][1]),
                    arrowprops=dict(arrowstyle='->', color='#2c3e50', lw=2))

    # Loop back from step 4 to step 3
    ax.annotate('', xy=(7.2, 9.65), xytext=(9, 9.65),
                arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=2,
                               connectionstyle='arc3,rad=-0.3'))
    ax.text(8.1, 9.2, 'Counter', fontsize=6, ha='center', color='#e74c3c')

    # Sample conversation - LEFT SIDE
    conversation = """Sample Negotiation (E1):

Day 1 - Customer:
  "Evaluating for 35 people.
   Interested in Plan C pricing."

Day 1 - Agent:
  "For 35 seats: 199/seat = 6,965/mo.
   With 15% discount: 5,920/mo."

Day 3 - Customer (2-day delay):
  "Budget firm at 4,500/mo.
   Competitor offered 25% less."

Day 3 - Agent:
  "Plan B at 79/seat with 20%
   discount = 2,212/mo."

Day 5 - Customer Accepts:
  "Proceed with Plan B, 35 seats."

[Deal: 2,212/mo, Plan B]"""

    ax.text(3.5, 8.5, conversation, fontsize=6.5, ha='center', va='top',
            family='monospace',
            bbox=dict(boxstyle='round', facecolor='#f8f9fa', edgecolor='#dee2e6', pad=0.3))

    # Price dynamics - RIGHT SIDE
    price_text = """Price Negotiation Dynamics:

Formula:
  offer = max - (max - init) * exp(-rate * turn)

Where:
  max_price = min(c_max, (Q - q_min) / slope)
  initial = max * 0.6 (default)
  rate = per-customer (by group)

Typical progression:
  Turn 0: ~60% of max
  Turn 3: ~85% of max
  Turn 5+: ~95% of max (final)

Reply delays:
  E1: 1.5 days (fast)
  E2: 2.5 days (thorough)
  E3: 4.0 days (strategic)"""

    ax.text(10.5, 8.5, price_text, fontsize=6.5, ha='center', va='top',
            family='monospace',
            bbox=dict(boxstyle='round', facecolor='#fff3cd', edgecolor='#ffc107', pad=0.3))

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_thread_states_page(pdf):
    """Create thread states and transitions page."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_title('Part 5.2: Thread States and Transitions', fontsize=14, fontweight='bold', pad=20)

    content = """
Thread Types and States
=======================

Thread Types:
- new_lead: Initial enterprise sales conversation
- plan_change: Existing customer requesting plan change
- budget_freeze: Customer facing budget cuts
- churn_prevention: At-risk customer retention
- support: Technical or service issue
- feature_request: Product feedback

Thread States:
- lead: Initial contact, not yet engaged
- evaluation: Customer is evaluating offer
- negotiating: Active price negotiation
- waiting: Waiting for customer reply
- active: Subscribed and active
- closed: Successfully resolved
- cancelled: Lost/churned

State Transitions:

  lead --> evaluation --> negotiating --> active --> closed
   |           |              |            |
   v           v              v            v
 cancelled  cancelled     cancelled    support
                                          |
                                          v
                                    churn_prevention
                                          |
                                    ------+------
                                    |           |
                                    v           v
                                  active    cancelled

Key Timeouts:
- Agent response timeout: 3 days
- If agent doesn't respond in 3 days:
  * Relationship damage
  * Customer may abandon thread
  * Lead may be lost

Reply Delays (per customer):
- E1: Mean 1.5 days, Std 0.5 days (fast, decisive)
- E2: Mean 2.5 days, Std 1.0 days (thorough evaluation)
- E3: Mean 4.0 days, Std 2.0 days (strategic, slow)

Max Negotiation Turns:
- E1: 3-5 turns (wants quick resolution)
- E2: 4-7 turns (quality evaluation)
- E3: 6-10 turns (relationship building)


Database Tables:
================

threads:
| thread_id | customer_id | state       | thread_type | negotiation_turn | current_offer_price | created_day |
|-----------|-------------|-------------|-------------|------------------|---------------------|-------------|
| 1         | 45          | negotiating | new_lead    | 2                | 4500.00             | 10          |
| 2         | 67          | waiting     | support     | 0                | NULL                | 12          |

messages:
| message_id | day | thread_id | sender   | text                                    | offer_json       | email                        |
|------------|-----|-----------|----------|-----------------------------------------|------------------|------------------------------|
| 1          | 12  | 1         | customer | "Hi, evaluating for 35 people..."       | NULL             | jennifer.walsh@midwestmfg.com|
| 2          | 12  | 1         | agent    | "Thank you! Our rate would be..."       | {"price": 5920}  | NULL                         |
| 3          | 14  | 1         | customer | "Our budget is firm at $4,500..."       | {"price": 4500}  | jennifer.walsh@midwestmfg.com|
"""

    ax.text(0.5, 0.97, content, fontsize=7.5, ha='center', va='top',
            transform=ax.transAxes, family='monospace')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_relationship_management_page(pdf):
    """Create relationship management page."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_title('Part 5.3: Relationship Management', fontsize=14, fontweight='bold', pad=20)

    content = """
Relationship Score System
=========================

Every customer has a relationship score (0.0 to 1.0):
- Starts at 0.5 (neutral)
- Affects perceived quality
- Updated based on interactions

Relationship Effects on Perceived Quality:
  relationship_bonus = relationship_quality_bonus_max * (relationship - 0.5) * 2

  Example (bonus_max = 0.1):
  - relationship = 0.2: bonus = 0.1 * (0.2 - 0.5) * 2 = -0.06
  - relationship = 0.5: bonus = 0.1 * (0.5 - 0.5) * 2 = 0.00
  - relationship = 0.8: bonus = 0.1 * (0.8 - 0.5) * 2 = +0.06

This means:
- Good relationship: Customer perceives higher quality -> more likely to stay
- Bad relationship: Customer perceives lower quality -> more likely to churn

How Relationship Changes:

Positive Actions:
- Successful negotiation close: +0.1
- Quick response to support thread: +0.05
- Resolving issue satisfactorily: +0.05
- Offering appropriate discount: +0.02

Negative Actions:
- Slow response (>2 days): -0.03 per day
- Failed negotiation: -0.05
- Unresolved support issue: -0.02 per day
- Outage affecting customer: -0.05

Open Issue Penalty:
- customer_state.open_issue_days tracks unresolved issues
- Penalty = 0.03 per day (capped at 0.15 = 5 days)
- This is SEPARATE from relationship
- Both affect perceived quality

Full Perceived Quality Formula:
  Q_perceived = Q_delivered - expected_quality + relationship_bonus + stickiness_bonus - issue_penalty - quota_penalty

Where:
  Q_delivered = 0.5 * model_quality + 0.3 * fulfillment + 0.2 * reliability
  expected_quality = per-customer expectation level (0.0 to 1.0, higher = harder to satisfy)
  relationship_bonus = relationship_quality_bonus_max * (relationship - 0.5) * 2
  stickiness_bonus = 0.05 * months_subscribed (capped at 6 months)
  issue_penalty = min(0.03 * open_issue_days, 0.15)
  quota_penalty = based on quota satisfaction


Practical Implications:
=======================

1. Enterprise customers need relationship management
   - Quick responses build trust
   - Slow responses compound damage

2. Support threads are critical
   - Every day unresolved = quality penalty
   - Resolution resets open_issue_days to 0

3. Negotiation affects relationship
   - Even if deal doesn't close, good negotiation preserves relationship
   - Aggressive tactics may win deal but damage long-term

4. Relationship cascades
   - Good relationship -> higher perceived quality -> higher satisfaction
   - Higher satisfaction -> more positive posts -> better reputation
   - Better reputation -> more customers

Database: customer_state table
| customer_id | satisfaction | open_issue_days | relationship |
|-------------|--------------|-----------------|--------------|
| 45          | 0.72         | 0               | 0.65         |
| 67          | 0.48         | 3               | 0.42         |
"""

    ax.text(0.5, 0.97, content, fontsize=8, ha='center', va='top',
            transform=ax.transAxes, family='monospace')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# =============================================================================
# PART 6: TOOL REFERENCE
# =============================================================================

def create_tool_category_page(pdf, category, tool_list):
    """Create a page for a category of tools with sample I/O."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_title(f'Part 6: {category}', fontsize=14, fontweight='bold', pad=20)

    y = 0.95
    line_height = 0.018

    for tool_name in tool_list:
        if tool_name not in tools:
            continue

        tool = tools[tool_name]

        # Tool name
        ax.text(0.02, y, f"{tool_name}", fontsize=10, fontweight='bold',
                transform=ax.transAxes, color='#2c3e50')
        y -= line_height * 1.5

        # Description
        desc = tool.get('description', 'No description')[:100]
        ax.text(0.04, y, desc, fontsize=8, transform=ax.transAxes, color='#555')
        y -= line_height * 1.5

        # Parameters
        params = tool.get('parameters', {})
        if params:
            param_strs = []
            for pname, pinfo in params.items():
                if isinstance(pinfo, dict):
                    ptype = pinfo.get('type', 'any')
                    param_strs.append(f"{pname}: {ptype}")
            if param_strs:
                ax.text(0.04, y, f"Params: {', '.join(param_strs[:3])}", fontsize=7,
                        transform=ax.transAxes, color='#7f8c8d', family='monospace')
                y -= line_height

        # Sample input
        example = tool.get('example_call', {})
        if example:
            args = example.get('arguments', {})
            args_str = json.dumps(args)[:70]
            ax.text(0.04, y, f"Input:  {args_str}", fontsize=7,
                    transform=ax.transAxes, color='#27ae60', family='monospace')
            y -= line_height

        # Sample output
        returns = tool.get('returns', {})
        if returns:
            if isinstance(returns, dict):
                ret_keys = list(returns.keys())[:2]
                ret_str = ', '.join([f"{k}: ..." for k in ret_keys])
            else:
                ret_str = str(returns)[:60]
            ax.text(0.04, y, f"Output: {{{ret_str}}}", fontsize=7,
                    transform=ax.transAxes, color='#3498db', family='monospace')
            y -= line_height

        y -= line_height * 0.5

        if y < 0.1:
            break

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def create_tool_reference_pages(pdf):
    """Create all tool reference pages."""
    # Group tools by category
    categories = {
        'Business Configuration': ['set_prices', 'set_model_tiers', 'set_capacity_tier', 'set_usage_quotas'],
        'Marketing & Spend': ['set_daily_spend', 'set_ad_channel_spend'],
        'Customer Communication': ['read_thread', 'get_thread_history', 'send_reply'],
        'Analytics & Monitoring': ['python_exec', 'expand_notification', 'get_cost_info', 'get_social_posts'],
        'Automation': ['register_daily_calculation', 'remove_daily_calculation', 'list_daily_calculations'],
        'Simulation Control': ['next_day', 'get_tool_documentation'],
    }

    for i, (category, tool_list) in enumerate(categories.items()):
        create_tool_category_page(pdf, f"6.{i+1} {category}", tool_list)


def create_python_exec_detail_page(pdf):
    """Create detailed python_exec reference page."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')
    ax.set_title('Tool Reference: python_exec (Detailed)', fontsize=14, fontweight='bold', pad=20)

    content = """
python_exec - SQL Analytics & Custom Calculations
=================================================

This is the most powerful tool - allows executing arbitrary Python code
with read-only SQLite access to the simulation database.

Available in Execution Environment:
- conn: SQLite connection (read-only)
- rows(query, params): Execute query, return list of tuples
- row(query, params): Execute query, return single tuple
- pd: pandas
- np: numpy
- LinearRegression, StandardScaler: sklearn
- json, math, statistics, Counter, defaultdict

Key Database Tables (17 total):
- customers: customer_id, group_id, steepness_left, steepness_right, c_max, expected_quality, ...
- subscriptions: subscription_id, customer_id, plan, listed_price, promotion, effective_price, status, ...
- customer_state: customer_id, satisfaction, relationship, open_issue_days, current_steepness_left, current_steepness_right, ...
- ledger: day, category, amount, notes (all cash flows)
- config_history: day, price_A/B/C, tier_A/B/C, capacity_tier, ...
- social_media_posts: post_id, day, customer_id, sentiment, virality, ...
- threads: thread_id, customer_id, state, thread_type, negotiation_turn
- messages: message_id, thread_id, sender, text, offer_json
- group_reputations: group_id, reputation
- group_awareness: group_id, awareness
- (see tool_docs.json for complete schema)

Sample Queries:

1. Revenue by Plan:
   df = pd.read_sql('''
       SELECT plan, SUM(effective_price) as mrr, COUNT(*) as subs
       FROM subscriptions
       WHERE status = 'subscribed' AND end_day IS NULL
       GROUP BY plan
   ''', conn)
   print(df.to_string())

2. Churn Analysis:
   churned = rows('''
       SELECT c.group_id, COUNT(*) as churns
       FROM subscriptions s
       JOIN customers c ON s.customer_id = c.customer_id
       WHERE s.status = 'cancelled' AND s.end_day > ? - 30
       GROUP BY c.group_id
   ''', (current_day,))

3. Customer Health Score:
   health = rows('''
       SELECT c.group_id,
              AVG(cs.satisfaction) as avg_sat,
              AVG(cs.relationship) as avg_rel,
              SUM(CASE WHEN cs.open_issue_days > 0 THEN 1 ELSE 0 END) as issues
       FROM customers c
       JOIN customer_state cs ON c.customer_id = cs.customer_id
       JOIN subscriptions s ON c.customer_id = s.customer_id
       WHERE s.status = 'subscribed'
       GROUP BY c.group_id
   ''')

4. Social Sentiment Trend:
   sentiment = pd.read_sql('''
       SELECT day, sentiment, COUNT(*) as posts,
              AVG(virality_score) as avg_virality
       FROM social_media_posts
       WHERE day > ? - 14
       GROUP BY day, sentiment
   ''', conn, params=(current_day,))

Output: Always print results - they appear in tool output.
"""

    ax.text(0.5, 0.97, content, fontsize=7.5, ha='center', va='top',
            transform=ax.transAxes, family='monospace')

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


# =============================================================================
# MAIN
# =============================================================================

def main():
    output_path = 'saas_bench_detailed_documentation.pdf'

    print("Generating comprehensive SaaS Bench documentation PDF...")

    with PdfPages(output_path) as pdf:
        # Title and TOC
        print("  Creating title page...")
        create_title_page(pdf)

        # Part 1: System Architecture
        print("  Part 1: System Architecture...")
        create_triangle_diagram(pdf)
        create_agent_interaction_diagram(pdf)
        create_dashboard_flow_diagram(pdf)
        create_tools_overview_page(pdf)

        # Part 2: Customer Groups & Model
        print("  Part 2: Customer Groups & Model...")
        create_individual_groups_page(pdf)
        create_enterprise_groups_page(pdf)
        create_customer_model_static_page(pdf)
        create_customer_model_dynamic_page(pdf)
        create_customer_initialization_page(pdf)

        # Part 3: Customer Lifecycle
        print("  Part 3: Customer Lifecycle...")
        create_individual_lifecycle_diagram(pdf)
        create_enterprise_lifecycle_diagram(pdf)
        create_participation_curves_page(pdf)
        create_participation_curves_explanation_page(pdf)

        # Part 4: Social & Reputation
        print("  Part 4: Social & Reputation System...")
        create_social_media_page(pdf)
        create_reputation_mechanics_page(pdf)
        create_cross_influence_page(pdf)

        # Part 5: Negotiation System
        print("  Part 5: Negotiation System...")
        create_negotiation_flow_page(pdf)
        create_thread_states_page(pdf)
        create_relationship_management_page(pdf)

        # Part 6: Tool Reference
        print("  Part 6: Tool Reference...")
        create_tool_reference_pages(pdf)
        create_python_exec_detail_page(pdf)

    print(f"\nPDF generated: {output_path}")
    return output_path


if __name__ == '__main__':
    main()
