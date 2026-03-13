"""Generate diagrams for the BossBench Simulator Design Wiki."""

import math
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'wiki_diagrams')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Style
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'figure.facecolor': 'white',
    'axes.facecolor': '#fafafa',
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linestyle': '--',
})

# Color palette
COLORS = {
    'S1': '#3498db', 'S2': '#2ecc71', 'S3': '#9b59b6',
    'E1': '#e74c3c', 'E2': '#f39c12', 'E3': '#1abc9c',
}
GROUP_NAMES = {
    'S1': 'S1: Price-Sensitive', 'S2': 'S2: Quality-Focused', 'S3': 'S3: Power Users',
    'E1': 'E1: Cost-Cutting', 'E2': 'E2: Quality-First', 'E3': 'E3: Strategic',
}

# Customer group params
GROUPS = {
    'S1': {'c_max': 50.0, 'steepness_left': 1.0, 'steepness_right': 2.0, 'expected_quality': 0.55, 'market_share': 0.38},
    'S2': {'c_max': 140.0, 'steepness_left': 1.0, 'steepness_right': 2.0, 'expected_quality': 0.70, 'market_share': 0.25},
    'S3': {'c_max': 180.0, 'steepness_left': 1.0, 'steepness_right': 2.0, 'expected_quality': 0.65, 'market_share': 0.17},
    'E1': {'c_max': 55.0, 'steepness_left': 1.0, 'steepness_right': 2.0, 'expected_quality': 0.60, 'market_share': 0.05, 'seats': '50-500'},
    'E2': {'c_max': 120.0, 'steepness_left': 1.0, 'steepness_right': 2.0, 'expected_quality': 0.75, 'market_share': 0.04, 'seats': '100-1000'},
    'E3': {'c_max': 100.0, 'steepness_left': 1.0, 'steepness_right': 2.0, 'expected_quality': 0.65, 'market_share': 0.03, 'seats': '200-2000'},
}


def sigmoid(x):
    x = max(min(x, 500), -500)
    return 1.0 / (1.0 + math.exp(-x))


def compute_required_quality(cost, steepness_left, steepness_right, c_max):
    """Compute required quality using asymmetric sigmoid with smooth blending.

    Uses a Hermite-interpolated blend around the midpoint so the two halves
    join with matching derivatives (no visible kink).
    """
    if cost > c_max:
        return float('inf')
    normalized_cost = cost / c_max

    # Left half: sigmoid centered at 0.25
    sigmoid_left = steepness_left * (normalized_cost - 0.25) * 10
    q_left = 0.5 * sigmoid(sigmoid_left)

    # Right half: sigmoid centered at 0.75
    sigmoid_right = steepness_right * (normalized_cost - 0.75) * 10
    q_right = 0.5 + 0.5 * sigmoid(sigmoid_right)

    # Smooth blend using a smoothstep (Hermite) around the midpoint
    # This eliminates the kink by gradually transitioning between the halves
    blend_width = 0.30  # blend over [0.20, 0.80] — wide enough for all c_max values
    t = (normalized_cost - 0.5) / blend_width  # ranges from -1..+1 in blend zone
    t = max(-1.0, min(1.0, t))
    # Smoothstep: maps [-1, 1] → [0, 1] with zero derivatives at endpoints
    s = t * 0.5 + 0.5  # map to [0, 1]
    alpha = s * s * (3 - 2 * s)  # Hermite smoothstep

    return (1 - alpha) * q_left + alpha * q_right


# =========================================================================
# 1. Participation Curves for all 6 groups
# =========================================================================
def plot_participation_curves():
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Individual groups
    ax = axes[0]
    for gid in ['S1', 'S2', 'S3']:
        g = GROUPS[gid]
        prices = np.linspace(0, g['c_max'], 200)
        q_req = [compute_required_quality(p, g['steepness_left'], g['steepness_right'], g['c_max']) for p in prices]
        ax.plot(prices, q_req, color=COLORS[gid], linewidth=2.5, label=GROUP_NAMES[gid])
        ax.axvline(g['c_max'], color=COLORS[gid], linestyle=':', alpha=0.5, linewidth=1)
        ax.axhline(g['expected_quality'], color=COLORS[gid], linestyle='--', alpha=0.3, linewidth=1)
    ax.set_xlabel('Price ($/month)', fontsize=12)
    ax.set_ylabel('Q_required (minimum quality)', fontsize=12)
    ax.set_title('Individual Customer Groups (S1-S3)')
    ax.legend(loc='upper left', fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.set_xlim(0, 200)

    # Enterprise groups (per-seat)
    ax = axes[1]
    for gid in ['E1', 'E2', 'E3']:
        g = GROUPS[gid]
        prices = np.linspace(0, g['c_max'], 200)
        q_req = [compute_required_quality(p, g['steepness_left'], g['steepness_right'], g['c_max']) for p in prices]
        ax.plot(prices, q_req, color=COLORS[gid], linewidth=2.5, label=f"{GROUP_NAMES[gid]} ({g.get('seats', '')} seats)")
        ax.axvline(g['c_max'], color=COLORS[gid], linestyle=':', alpha=0.5, linewidth=1)
        ax.axhline(g['expected_quality'], color=COLORS[gid], linestyle='--', alpha=0.3, linewidth=1)
    ax.set_xlabel('Price ($/seat/month)', fontsize=12)
    ax.set_ylabel('Q_required (minimum quality)', fontsize=12)
    ax.set_title('Enterprise Customer Groups (E1-E3)')
    ax.legend(loc='upper left', fontsize=10)
    ax.set_ylim(0, 1.05)
    ax.set_xlim(0, 140)

    fig.suptitle('Asymmetric Sigmoid Participation Curves', fontsize=16, fontweight='bold', y=1.02)
    fig.text(0.5, -0.02, 'Solid line = Q_required(price). Dashed = expected_quality. Dotted = c_max budget limit.\nCustomer subscribes iff Q_perceived ≥ Q_required(price) AND price ≤ c_max',
             ha='center', fontsize=10, style='italic')
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, '01_participation_curves.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {path}")


# =========================================================================
# 2. Growth Rate Formula Breakdown
# =========================================================================
def plot_growth_rate_breakdown():
    fig, ax = plt.subplots(figsize=(18, 9))
    ax.axis('off')

    # Title
    ax.text(0.5, 0.97, 'Growth Rate Formula', fontsize=18, fontweight='bold',
            ha='center', va='top', transform=ax.transAxes)

    # Main formula box
    formula_box = FancyBboxPatch((0.08, 0.80), 0.84, 0.10, boxstyle="round,pad=0.02",
                                  facecolor='#2c3e50', edgecolor='white', linewidth=2)
    ax.add_patch(formula_box)
    ax.text(0.5, 0.85, 'growth_rate = base_rate × reputation × (marketing + awareness + network + organic)',
            fontsize=13, fontweight='bold', color='white', ha='center', va='center',
            transform=ax.transAxes, family='monospace')

    # Factor boxes — evenly spaced with wider boxes
    box_w = 0.135
    gap = 0.155
    start_x = 0.04
    factors = [
        ('base_rate', '#e74c3c', 'market_share × α\n(α = 100.0)', 'Per-group weight\nscaling ad effectiveness'),
        ('reputation', '#f39c12', '0.6 + 0.8 × rep\n(rep ∈ [0, 1])', 'Multiplier: 0.6 → 1.4\nBased on group reputation'),
        ('marketing', '#3498db', '√(spend/100) × 0.5\nPer-channel effect.', '5 ad channels\n√ diminishing returns'),
        ('awareness', '#2ecc71', 'awareness ∈ [0, 1]\n+growth/500 − 0.02/d', 'Brand recognition\nBuilt by marketing, decays'),
        ('network', '#9b59b6', '0.2×ln(1+n/10)\n+ WoM contribution', 'Existing customers\n+ word of mouth × β'),
        ('organic', '#1abc9c', '= 0.1 (constant)', 'SEO, press, discovery\nIndependent baseline'),
    ]

    for i, (name, color, formula, desc) in enumerate(factors):
        x_left = start_x + i * gap
        x_center = x_left + box_w / 2
        # Box
        box = FancyBboxPatch((x_left, 0.42), box_w, 0.30, boxstyle="round,pad=0.01",
                              facecolor=color, edgecolor='white', alpha=0.9, linewidth=1.5)
        ax.add_patch(box)
        # Name
        ax.text(x_center, 0.68, name, fontsize=11, fontweight='bold', color='white',
                ha='center', va='center', transform=ax.transAxes)
        # Formula
        ax.text(x_center, 0.57, formula, fontsize=8, color='white',
                ha='center', va='center', transform=ax.transAxes, family='monospace')
        # Description
        ax.text(x_center, 0.47, desc, fontsize=7.5, color='white',
                ha='center', va='center', transform=ax.transAxes, style='italic')
        # Arrow from main formula to factor
        ax.annotate('', xy=(x_center, 0.72), xytext=(x_center, 0.80),
                    arrowprops=dict(arrowstyle='->', color=color, lw=2),
                    transform=ax.transAxes)

    # Poisson sampling note
    poisson_box = FancyBboxPatch((0.2, 0.18), 0.6, 0.14, boxstyle="round,pad=0.02",
                                  facecolor='#34495e', edgecolor='#7f8c8d', linewidth=2)
    ax.add_patch(poisson_box)
    ax.text(0.5, 0.28, 'n_new = Poisson(growth_rate)', fontsize=13, fontweight='bold',
            color='#ecf0f1', ha='center', va='center', transform=ax.transAxes, family='monospace')
    ax.text(0.5, 0.22, 'Random sampling adds natural variance to customer arrivals',
            fontsize=10, color='#bdc3c7', ha='center', va='center', transform=ax.transAxes, style='italic')
    ax.annotate('', xy=(0.5, 0.32), xytext=(0.5, 0.42),
                arrowprops=dict(arrowstyle='->', color='#7f8c8d', lw=2.5),
                transform=ax.transAxes)

    # Market share table at bottom
    ax.text(0.5, 0.10, 'Market Shares:  S1=0.38   S2=0.25   S3=0.17   E1=0.05   E2=0.04   E3=0.03',
            fontsize=10, ha='center', va='center', transform=ax.transAxes,
            family='monospace', color='#555',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#ecf0f1', edgecolor='#bdc3c7'))

    path = os.path.join(OUTPUT_DIR, '02_growth_rate_formula.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {path}")


# =========================================================================
# 3. Daily Simulation Loop Flowchart
# =========================================================================
def plot_daily_loop():
    fig, ax = plt.subplots(figsize=(11, 16))
    ax.axis('off')
    ax.set_xlim(0, 11)
    ax.set_ylim(2.5, 22.5)

    steps = [
        ('step_day()', '#2c3e50', 'Entry point: day += 1, get config'),
        ('Compute Usage', '#3498db', 'total_usage per customer (daily_usage_rate × seat_count)'),
        ('Service Metrics', '#e74c3c', 'overload, outage probability, p95 latency, error rate'),
        ('Update Global State', '#f39c12', 'q_dev growth/decay, ease improvement'),
        ('Customer Satisfaction', '#2ecc71', 'Update satisfaction EMA, reliability EMA, relationships'),
        ('Process Issues', '#9b59b6', 'Generate issues (Poisson), resolve with ops spend'),
        ('Billing Decisions', '#e67e22', 'At billing day (mod 30): Cancel / Upgrade / Downgrade'),
        ('Social Media', '#1abc9c', 'Generate posts based on satisfaction events'),
        ('Enterprise Negotiations', '#c0392b', 'Process replies, timeouts, deal closings'),
        ('New Customers', '#2980b9', 'Growth rate model → Poisson(growth_rate)'),
        ('Process Billing', '#27ae60', 'Collect payments: price × seat_count'),
        ('Process Costs', '#8e44ad', 'Infrastructure + ops + dev + ad spend + model costs'),
        ('Cash Check', '#c0392b', 'if cash < 0 → GAME OVER (immediate shutdown)'),
    ]

    box_w, box_h = 7.0, 1.05
    x_center = 5.5
    y_start = 21.0
    y_step = 1.35

    for i, (title, color, desc) in enumerate(steps):
        y = y_start - i * y_step

        # Box
        rect = FancyBboxPatch((x_center - box_w/2, y - box_h/2), box_w, box_h,
                               boxstyle="round,pad=0.1", facecolor=color, alpha=0.9,
                               edgecolor='white', linewidth=1.5)
        ax.add_patch(rect)

        # Title — top of box
        ax.text(x_center - box_w/2 + 0.3, y + 0.22, title, fontsize=12, fontweight='bold',
                color='white', va='center')
        # Desc — below title, single line
        ax.text(x_center - box_w/2 + 0.3, y - 0.18, desc, fontsize=9, color='#ecf0f1',
                va='center', style='italic')

        # Step number
        ax.text(x_center + box_w/2 - 0.35, y + 0.30, f'{i}', fontsize=9, color='#ffffff80',
                ha='center', va='center', fontweight='bold')

        # Arrow to next
        if i < len(steps) - 1:
            ax.annotate('', xy=(x_center, y - box_h/2 - 0.02),
                        xytext=(x_center, y - box_h/2 - y_step + box_h/2 + 0.02),
                        arrowprops=dict(arrowstyle='<-', color='#7f8c8d', lw=1.5))

    # Title
    ax.text(5.5, 22, 'Daily Simulation Loop (step_day)', fontsize=16, fontweight='bold',
            ha='center', va='center', color='#2c3e50')

    path = os.path.join(OUTPUT_DIR, '03_daily_loop_flowchart.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {path}")


# =========================================================================
# 4. Quality Perception Pipeline
# =========================================================================
def plot_quality_pipeline():
    fig, ax = plt.subplots(figsize=(18, 10))
    ax.axis('off')
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 10)

    # Title
    ax.text(9, 9.6, 'Perceived Quality Pipeline', fontsize=18, fontweight='bold',
            ha='center', color='#2c3e50')

    # Q_delivered box
    box = FancyBboxPatch((0.5, 5.8), 3.5, 2.8, boxstyle="round,pad=0.15",
                          facecolor='#3498db', edgecolor='white', linewidth=2)
    ax.add_patch(box)
    ax.text(2.25, 8.1, 'Q_delivered', fontsize=14, fontweight='bold', color='white', ha='center')
    ax.text(2.25, 7.5, 'q_model + q_dev', fontsize=11, color='#ecf0f1', ha='center', family='monospace')
    ax.text(2.25, 6.7, 'Tier 1: 0.55   Tier 2: 0.65\nTier 3: 0.75   Tier 4: 0.85\nTier 5: 0.95',
            fontsize=9, color='#d4e6f1', ha='center')

    # Arrow
    ax.annotate('', xy=(4.5, 7.2), xytext=(4.0, 7.2),
                arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=2.5))

    # expected_quality box — taller to avoid overlap
    box2 = FancyBboxPatch((4.5, 5.8), 3.2, 2.8, boxstyle="round,pad=0.15",
                           facecolor='#e74c3c', edgecolor='white', linewidth=2)
    ax.add_patch(box2)
    ax.text(6.1, 8.1, '− expected_quality', fontsize=12, fontweight='bold', color='white', ha='center')
    ax.text(6.1, 7.3, 'Per-customer expectation', fontsize=9, color='#fadbd8', ha='center')
    ax.text(6.1, 6.6, 'S1: 0.55   S2: 0.70\nS3: 0.65   E1: 0.60\nE2: 0.75   E3: 0.65',
            fontsize=9, color='#fadbd8', ha='center', family='monospace')

    # Arrow
    ax.annotate('', xy=(8.2, 7.2), xytext=(7.7, 7.2),
                arrowprops=dict(arrowstyle='->', color='#2ecc71', lw=2.5))

    # Bonuses box
    box3 = FancyBboxPatch((8.2, 5.8), 3.5, 2.8, boxstyle="round,pad=0.15",
                           facecolor='#2ecc71', edgecolor='white', linewidth=2)
    ax.add_patch(box3)
    ax.text(9.95, 8.1, '+ Bonuses', fontsize=13, fontweight='bold', color='white', ha='center')
    ax.text(9.95, 7.2, 'relationship_bonus\n= 0.45 × (rel − 0.5) × 2\nRange: −0.45 to +0.45',
            fontsize=8.5, color='#d5f5e3', ha='center', family='monospace')
    ax.text(9.95, 6.2, 'stickiness_bonus\n= 0.05 × ln(1 + days/30)',
            fontsize=8.5, color='#d5f5e3', ha='center', family='monospace')

    # Arrow
    ax.annotate('', xy=(12.2, 7.2), xytext=(11.7, 7.2),
                arrowprops=dict(arrowstyle='->', color='#e67e22', lw=2.5))

    # Penalties box
    box4 = FancyBboxPatch((12.2, 5.8), 4.0, 2.8, boxstyle="round,pad=0.15",
                           facecolor='#e67e22', edgecolor='white', linewidth=2)
    ax.add_patch(box4)
    ax.text(14.2, 8.1, '− Penalties', fontsize=13, fontweight='bold', color='white', ha='center')
    ax.text(14.2, 7.2, 'quota_penalty\n= 0.10 × (1 − quota/demand)',
            fontsize=8.5, color='#fdebd0', ha='center', family='monospace')

    # Result box — wider, formula split into 2 lines
    result_box = FancyBboxPatch((2.5, 1.2), 13, 3.2, boxstyle="round,pad=0.2",
                                 facecolor='#2c3e50', edgecolor='#f39c12', linewidth=3)
    ax.add_patch(result_box)
    ax.text(9, 3.8, 'Q_perceived = (Q_delivered − expected_quality)',
            fontsize=11, fontweight='bold', color='#f39c12', ha='center', family='monospace')
    ax.text(9, 3.2, '+ relationship_bonus + stickiness_bonus − quota_penalty',
            fontsize=11, fontweight='bold', color='#f39c12', ha='center', family='monospace')
    ax.text(9, 2.5, 'Customer subscribes iff  Q_perceived ≥ Q_required(price)  AND  price ≤ c_max',
            fontsize=11, color='#ecf0f1', ha='center')
    ax.text(9, 1.8, 'At billing day: if no plan has Q_perceived ≥ Q_required → CANCEL',
            fontsize=10, color='#bdc3c7', ha='center', style='italic')

    # Arrow from pipeline to result
    ax.annotate('', xy=(9, 4.4), xytext=(9, 5.8),
                arrowprops=dict(arrowstyle='->', color='#f39c12', lw=3))

    path = os.path.join(OUTPUT_DIR, '04_quality_pipeline.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {path}")


# =========================================================================
# 5. Model Tiers Chart
# =========================================================================
def plot_model_tiers():
    tiers = [1, 2, 3, 4, 5]
    quality = [0.55, 0.65, 0.75, 0.85, 0.95]
    cost = [0.0004, 0.0020, 0.0050, 0.0080, 0.0200]
    cost_per_m = [c * 1000 for c in cost]  # $/M tokens
    labels = ['Tier 1\n(Haiku)', 'Tier 2\n(Mini)', 'Tier 3\n(Sonnet)', 'Tier 4\n(GPT-4o)', 'Tier 5\n(Opus)']
    colors_tiers = ['#3498db', '#2ecc71', '#f39c12', '#e67e22', '#e74c3c']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Quality bars
    bars1 = ax1.bar(labels, quality, color=colors_tiers, edgecolor='white', linewidth=1.5, width=0.6)
    for bar, q in zip(bars1, quality):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{q:.2f}', ha='center', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Base Quality (0-1)', fontsize=12)
    ax1.set_title('Quality per Tier', fontsize=14, fontweight='bold')
    ax1.set_ylim(0, 1.1)

    # Cost bars
    bars2 = ax2.bar(labels, cost_per_m, color=colors_tiers, edgecolor='white', linewidth=1.5, width=0.6)
    for bar, c in zip(bars2, cost_per_m):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'${c:.1f}', ha='center', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Cost ($/M tokens)', fontsize=12)
    ax2.set_title('Cost per Tier', fontsize=14, fontweight='bold')
    ax2.set_ylim(0, 25)

    fig.suptitle('Model Tiers: Quality vs Cost Tradeoff', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, '05_model_tiers.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {path}")


# =========================================================================
# 6. Ad Channel Effectiveness Heatmap
# =========================================================================
def plot_ad_channel_heatmap():
    channels = ['Social Media', 'Search Ads', 'LinkedIn', 'Content Mktg', 'Referral Prog']
    groups = ['S1', 'S2', 'S3', 'E1', 'E2', 'E3']

    # Mean effectiveness values
    data = np.array([
        [0.45, 0.32, 0.26, 0.004, 0.002, 0.001],   # social_media
        [0.20, 0.50, 0.45, 0.012, 0.016, 0.008],    # search_ads
        [0.07, 0.26, 0.20, 0.026, 0.036, 0.030],    # linkedin
        [0.13, 0.45, 0.50, 0.012, 0.024, 0.020],    # content_marketing
        [0.32, 0.39, 0.45, 0.016, 0.020, 0.024],    # referral_program
    ])

    cost_mult = [0.40, 1.00, 2.30, 0.70, 0.25]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), gridspec_kw={'width_ratios': [4, 1.2]})

    # Heatmap
    im = ax1.imshow(data, cmap='YlOrRd', aspect='auto')
    ax1.set_xticks(range(len(groups)))
    ax1.set_xticklabels([f'{g}\n{GROUP_NAMES[g].split(": ")[1]}' for g in groups], fontsize=10)
    ax1.set_yticks(range(len(channels)))
    ax1.set_yticklabels(channels, fontsize=11)

    # Annotate cells
    for i in range(len(channels)):
        for j in range(len(groups)):
            val = data[i, j]
            color = 'white' if val > 0.25 else 'black'
            ax1.text(j, i, f'{val:.3f}', ha='center', va='center', fontsize=10,
                    color=color, fontweight='bold')

    ax1.set_title('Ad Channel Effectiveness by Group (mean)', fontsize=14, fontweight='bold')
    fig.colorbar(im, ax=ax1, shrink=0.8, label='Effectiveness Multiplier')

    # Cost multiplier bar chart
    bars = ax2.barh(channels, cost_mult, color=['#3498db', '#2ecc71', '#e67e22', '#9b59b6', '#1abc9c'],
                     edgecolor='white', linewidth=1.5)
    for bar, c in zip(bars, cost_mult):
        ax2.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
                f'{c:.2f}×', ha='left', va='center', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Cost Multiplier', fontsize=11)
    ax2.set_title('Cost per $', fontsize=14, fontweight='bold')
    ax2.set_xlim(0, 3.0)
    ax2.invert_yaxis()

    fig.suptitle('Advertising Channels: Effectiveness & Cost', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, '06_ad_channel_heatmap.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {path}")


# =========================================================================
# 7. Reputation Influence Matrix Heatmap
# =========================================================================
def plot_reputation_matrix():
    groups = ['S1', 'S2', 'S3', 'E1', 'E2', 'E3']
    full_names = {
        'S1': 'Price-Sensitive', 'S2': 'Quality-Focused', 'S3': 'Power Users',
        'E1': 'Cost-Cutting', 'E2': 'Quality-First', 'E3': 'Strategic',
    }
    matrix = np.array([
        [1.0, 0.05, 0.15, 0.02, 0.01, 0.01],
        [0.05, 1.0, 0.08, 0.03, 0.15, 0.05],
        [0.20, 0.12, 1.0, 0.25, 0.30, 0.20],
        [0.02, 0.03, 0.05, 1.0, 0.10, 0.08],
        [0.02, 0.18, 0.08, 0.15, 1.0, 0.22],
        [0.02, 0.05, 0.15, 0.25, 0.25, 1.0],
    ])

    fig, ax = plt.subplots(figsize=(12, 9))
    im = ax.imshow(matrix, cmap='Blues', aspect='auto', vmin=0, vmax=1)

    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([f'{g}\n{full_names[g]}' for g in groups], fontsize=10)
    ax.set_yticks(range(len(groups)))
    ax.set_yticklabels([f'{g} ({full_names[g]})' for g in groups], fontsize=10)

    ax.set_xlabel('Target (influenced)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Source (influencer)', fontsize=12, fontweight='bold')

    # Annotate
    for i in range(len(groups)):
        for j in range(len(groups)):
            val = matrix[i, j]
            color = 'white' if val > 0.5 else 'black'
            ax.text(j, i, f'{val:.2f}', ha='center', va='center', fontsize=11,
                    color=color, fontweight='bold')

    ax.set_title('Reputation Influence Matrix\nI[source][target] = influence strength',
                 fontsize=14, fontweight='bold')
    fig.colorbar(im, ax=ax, shrink=0.8, label='Influence Strength')

    # Key insight box
    ax.text(0.5, -0.12, 'Key: S3 (Power Users) are the strongest cross-group influencers → tech leads drive enterprise adoption',
            fontsize=10, ha='center', transform=ax.transAxes, style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#eaf2f8', edgecolor='#aed6f1'))

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, '07_reputation_matrix.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {path}")


# =========================================================================
# 8. Capacity Tiers Visualization
# =========================================================================
def plot_capacity_tiers():
    tiers = [0, 1, 2, 3]
    capacity = [35_000, 100_000, 280_000, 700_000]
    cost_per_day = [80, 200, 500, 1_200]
    labels = ['T0\nServerless', 'T1\nSmall', 'T2\nMedium', 'T3\nEnterprise']
    colors_cap = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c']

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 7))
    fig.subplots_adjust(wspace=0.35)

    # Capacity
    bars1 = ax1.bar(labels, [c/1000 for c in capacity], color=colors_cap, edgecolor='white', linewidth=1.5, width=0.55)
    for bar, c in zip(bars1, capacity):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
                f'{c:,}', ha='center', fontsize=10, fontweight='bold')
    ax1.set_ylabel('Capacity (K units)', fontsize=12)
    ax1.set_title('Capacity Units', fontsize=14, fontweight='bold')
    ax1.tick_params(axis='x', labelsize=10)

    # Daily cost
    bars2 = ax2.bar(labels, cost_per_day, color=colors_cap, edgecolor='white', linewidth=1.5, width=0.55)
    for bar, c in zip(bars2, cost_per_day):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 15,
                f'${c}/day', ha='center', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Cost ($/day)', fontsize=12)
    ax2.set_title('Daily Infrastructure Cost', fontsize=14, fontweight='bold')
    ax2.tick_params(axis='x', labelsize=10)

    # Cost efficiency
    efficiency = [cap / cost for cap, cost in zip(capacity, cost_per_day)]
    bars3 = ax3.bar(labels, efficiency, color=colors_cap, edgecolor='white', linewidth=1.5, width=0.55)
    for bar, e in zip(bars3, efficiency):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                f'{e:.0f}', ha='center', fontsize=10, fontweight='bold')
    ax3.set_ylabel('Units per $', fontsize=12)
    ax3.set_title('Cost Efficiency (units/$)', fontsize=14, fontweight='bold')
    ax3.tick_params(axis='x', labelsize=10)

    fig.suptitle('Infrastructure Capacity Tiers', fontsize=16, fontweight='bold', y=1.02)
    fig.text(0.5, -0.02, 'Higher tiers offer more capacity at better cost efficiency (units per dollar)',
             ha='center', fontsize=10, style='italic')
    path = os.path.join(OUTPUT_DIR, '08_capacity_tiers.png')
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {path}")


if __name__ == '__main__':
    print("Generating BossBench Wiki Diagrams...")
    plot_participation_curves()
    plot_growth_rate_breakdown()
    plot_daily_loop()
    plot_quality_pipeline()
    plot_model_tiers()
    plot_ad_channel_heatmap()
    plot_reputation_matrix()
    plot_capacity_tiers()
    print(f"\nAll diagrams saved to: {OUTPUT_DIR}")
