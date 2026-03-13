"""Plot participation curves for different customer types showing q_max scaling."""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

def sigmoid(x):
    x = np.clip(x, -500, 500)
    return 1.0 / (1.0 + np.exp(-x))

def compute_required_quality(cost, steepness_left, steepness_right, c_max, q_max):
    """Vectorized version of _compute_required_quality."""
    result = np.zeros_like(cost, dtype=float)
    half_qmax = q_max / 2.0

    # Beyond c_max: steep shoot-up
    beyond = cost > c_max
    overshoot = (cost[beyond] - c_max) / c_max
    result[beyond] = q_max + 10.0 * overshoot

    # Within budget
    within = ~beyond
    nc = cost[within] / c_max  # normalized 0-1

    left = nc < 0.5
    right = ~left

    # Left half
    si_left = steepness_left * (nc[left] - 0.25) * 10
    result_within = np.zeros_like(nc)
    result_within[left] = half_qmax * sigmoid(si_left)

    # Right half
    si_right = steepness_right * (nc[right] - 0.75) * 10
    result_within[right] = half_qmax + half_qmax * sigmoid(si_right)

    result[within] = result_within
    return result


# Define sample customers from different groups
customers = [
    {
        'label': 'S1 Price-Sensitive\n(sl=0.8, sr=1.8, c=$50, q_max=0.55)',
        'steepness_left': 0.8, 'steepness_right': 1.8,
        'c_max': 50, 'q_max': 0.55,
        'color': '#e74c3c', 'linestyle': '-'
    },
    {
        'label': 'S2 Quality Pro\n(sl=1.2, sr=2.8, c=$140, q_max=0.85)',
        'steepness_left': 1.2, 'steepness_right': 2.8,
        'c_max': 140, 'q_max': 0.85,
        'color': '#3498db', 'linestyle': '-'
    },
    {
        'label': 'S3 Power User\n(sl=1.5, sr=3.0, c=$180, q_max=0.80)',
        'steepness_left': 1.5, 'steepness_right': 3.0,
        'c_max': 180, 'q_max': 0.80,
        'color': '#2ecc71', 'linestyle': '-'
    },
    {
        'label': 'E1 Cost-Cutting\n(sl=0.9, sr=2.0, c=$55, q_max=0.65)',
        'steepness_left': 0.9, 'steepness_right': 2.0,
        'c_max': 55, 'q_max': 0.65,
        'color': '#9b59b6', 'linestyle': '--'
    },
    {
        'label': 'E2 Quality-First\n(sl=1.3, sr=3.2, c=$120, q_max=0.90)',
        'steepness_left': 1.3, 'steepness_right': 3.2,
        'c_max': 120, 'q_max': 0.90,
        'color': '#e67e22', 'linestyle': '--'
    },
    {
        'label': 'E3 Strategic Partner\n(sl=1.0, sr=2.5, c=$100, q_max=0.80)',
        'steepness_left': 1.0, 'steepness_right': 2.5,
        'c_max': 100, 'q_max': 0.80,
        'color': '#1abc9c', 'linestyle': '--'
    },
]

fig, axes = plt.subplots(2, 1, figsize=(14, 12), gridspec_kw={'height_ratios': [3, 1]})

# Top plot: Full curves
ax = axes[0]
max_price = 250

for cust in customers:
    prices = np.linspace(0, max_price, 1000)
    q_req = compute_required_quality(
        prices, cust['steepness_left'], cust['steepness_right'],
        cust['c_max'], cust['q_max']
    )
    # Clip for display (steep shoot-up goes very high)
    q_req_display = np.clip(q_req, 0, 1.5)

    ax.plot(prices, q_req_display, label=cust['label'],
            color=cust['color'], linestyle=cust['linestyle'], linewidth=2.0)

    # Mark c_max with a dot
    ax.plot(cust['c_max'], cust['q_max'], 'o', color=cust['color'], markersize=8, zorder=5)

    # Draw horizontal dashed line at q_max
    ax.axhline(y=cust['q_max'], color=cust['color'], alpha=0.2, linestyle=':', linewidth=1)

ax.set_xlabel('Monthly Price ($)', fontsize=13)
ax.set_ylabel('Q_required (quality needed to satisfy)', fontsize=13)
ax.set_title('Participation Curves by Customer Group — q_max Scaling\n'
             '(dots = c_max points, dashed lines = q_max ceilings)', fontsize=14)
ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax.set_xlim(0, max_price)
ax.set_ylim(0, 1.5)
ax.axhline(y=1.0, color='gray', alpha=0.3, linestyle='-', linewidth=0.5)
ax.grid(True, alpha=0.3)

# Add "unaffordable zone" annotation
ax.fill_between([0, max_price], 1.0, 1.5, alpha=0.05, color='red')
ax.text(max_price - 5, 1.35, 'Effectively\nunaffordable', ha='right', va='center',
        fontsize=10, color='red', alpha=0.5, style='italic')

# Bottom plot: Zoomed into the normal range (0 to 1.0)
ax2 = axes[1]
for cust in customers:
    prices = np.linspace(0, cust['c_max'] * 1.1, 500)
    q_req = compute_required_quality(
        prices, cust['steepness_left'], cust['steepness_right'],
        cust['c_max'], cust['q_max']
    )
    q_req_display = np.clip(q_req, 0, 1.0)

    ax2.plot(prices, q_req_display, label=cust['label'].split('\n')[0],
             color=cust['color'], linestyle=cust['linestyle'], linewidth=2.0)
    ax2.plot(cust['c_max'], cust['q_max'], 'o', color=cust['color'], markersize=8, zorder=5)

ax2.set_xlabel('Monthly Price ($)', fontsize=13)
ax2.set_ylabel('Q_required', fontsize=13)
ax2.set_title('Zoomed View — Each curve reaches its q_max at c_max (individual/enterprise)', fontsize=12)
ax2.legend(loc='upper left', fontsize=9, ncol=2)
ax2.set_xlim(0, 200)
ax2.set_ylim(0, 1.0)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench/participation_curves_qmax.png',
            dpi=150, bbox_inches='tight')
print("Plot saved to participation_curves_qmax.png")
