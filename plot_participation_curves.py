"""Plot customer participation curves for CEOBench Notion doc.

Shows the required quality Q_required(price) for different customer groups,
using the asymmetric sigmoid model from the simulation.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# --- Asymmetric sigmoid participation curve (from simulation.py) ---
def sigmoid(x):
    x = np.clip(x, -500, 500)
    return 1.0 / (1.0 + np.exp(-x))

def q_required(cost, steepness_left, steepness_right, c_max, q_max, q_min):
    """Compute required quality at a given price using asymmetric sigmoid."""
    result = np.where(cost > c_max, q_max, 0.0)
    norm = cost / c_max
    q_range = q_max - q_min

    # Left half (price < c_max/2)
    left_input = steepness_left * (norm - 0.25) * 10
    left_val = q_min + (q_range / 2.0) * sigmoid(left_input)

    # Right half (price >= c_max/2)
    right_input = steepness_right * (norm - 0.75) * 10
    right_val = q_min + (q_range / 2.0) + (q_range / 2.0) * sigmoid(right_input)

    curve = np.where(norm < 0.5, left_val, right_val)
    return np.where(cost > c_max, q_max, curve)

# --- Customer group parameters (from config.py) ---
# Using mean steepness values: left ~ exponential(1)+0.2 ≈ 1.2, right ~ exponential(2)+0.8 ≈ 2.8
# But we use representative values that show the distinct shapes
groups = {
    'S1 — Freelancers': {
        'q_min': 0.10, 'q_max': 0.55, 'c_max': 50.0,
        'steepness_left': 1.0, 'steepness_right': 2.5,
        'color': '#2196F3', 'ls': '-', 'lw': 2.5,
    },
    'S2 — Professionals': {
        'q_min': 0.30, 'q_max': 0.85, 'c_max': 140.0,
        'steepness_left': 1.2, 'steepness_right': 2.8,
        'color': '#4CAF50', 'ls': '-', 'lw': 2.5,
    },
    'S3 — Power Users': {
        'q_min': 0.25, 'q_max': 0.80, 'c_max': 180.0,
        'steepness_left': 1.1, 'steepness_right': 2.6,
        'color': '#FF9800', 'ls': '-', 'lw': 2.5,
    },
    'E1 — Cost-Cutters': {
        'q_min': 0.20, 'q_max': 0.65, 'c_max': 55.0,
        'steepness_left': 1.0, 'steepness_right': 2.4,
        'color': '#9C27B0', 'ls': '--', 'lw': 2.2,
    },
    'E2 — Quality-First': {
        'q_min': 0.40, 'q_max': 0.90, 'c_max': 120.0,
        'steepness_left': 1.3, 'steepness_right': 3.0,
        'color': '#F44336', 'ls': '--', 'lw': 2.2,
    },
    'E3 — Strategic Partners': {
        'q_min': 0.45, 'q_max': 0.80, 'c_max': 100.0,
        'steepness_left': 1.2, 'steepness_right': 2.7,
        'color': '#00BCD4', 'ls': '--', 'lw': 2.2,
    },
}

# --- Plot ---
fig, ax = plt.subplots(figsize=(11, 6.5))
fig.patch.set_facecolor('#FAFAFA')
ax.set_facecolor('#FAFAFA')

for name, g in groups.items():
    prices = np.linspace(0, g['c_max'] * 1.05, 500)
    q_req = q_required(prices, g['steepness_left'], g['steepness_right'],
                       g['c_max'], g['q_max'], g['q_min'])
    is_enterprise = name.startswith('E')
    label_suffix = ' (per seat)' if is_enterprise else ''
    ax.plot(prices, q_req, color=g['color'], ls=g['ls'], lw=g['lw'],
            label=f"{name}{label_suffix}", zorder=3)

    # Mark c_max with a dot
    ax.plot(g['c_max'], g['q_max'], 'o', color=g['color'], markersize=7, zorder=4)

    # Annotate c_max
    offset_y = 0.02
    if 'E3' in name:
        offset_y = -0.05
    ax.annotate(f"${g['c_max']:.0f}", (g['c_max'], g['q_max'] + offset_y),
                fontsize=8, color=g['color'], ha='center', fontweight='bold')

# Shade the "subscribe" region
ax.fill_between([0, 200], [1.0, 1.0], alpha=0.04, color='green', zorder=1)
ax.text(175, 0.95, 'Subscribe\n(Q ≥ Q_req)', fontsize=9, color='green', alpha=0.5,
        ha='center', va='top', style='italic')

# Reference quality line (Day 1 base quality = 0.50)
ax.axhline(y=0.50, color='gray', ls=':', lw=1.2, alpha=0.6, zorder=2)
ax.text(185, 0.505, 'Day 1 Base\nQuality (0.50)', fontsize=8, color='gray',
        ha='left', va='bottom', alpha=0.7)

# Formatting
ax.set_xlabel('Monthly Price ($)', fontsize=12, fontweight='bold')
ax.set_ylabel('Required Quality (Q_required)', fontsize=12, fontweight='bold')
ax.set_title('CEOBench: Customer Participation Curves by Segment',
             fontsize=14, fontweight='bold', pad=12)
ax.set_xlim(0, 200)
ax.set_ylim(0, 1.0)
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f'${x:.0f}'))
ax.legend(loc='upper left', fontsize=9, framealpha=0.9, edgecolor='#DDD')
ax.grid(True, alpha=0.3, ls='-', lw=0.5)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Add annotation about the asymmetric sigmoid
ax.text(0.98, 0.02,
        'Asymmetric sigmoid: gentler at low prices, steeper near budget cap\n'
        'Enterprise prices are per-seat/month  •  Dots = budget cap (c_max)',
        transform=ax.transAxes, fontsize=7.5, ha='right', va='bottom',
        color='#666', style='italic')

plt.tight_layout()
out_path = '/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench/participation_curves.png'
fig.savefig(out_path, dpi=180, bbox_inches='tight', facecolor='#FAFAFA')
print(f"Saved to {out_path}")
