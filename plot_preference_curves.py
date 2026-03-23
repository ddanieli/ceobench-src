"""Plot participation curves for all customer groups: initial, end-of-sim group, end-of-sim day-0 customer.
Scenario: 5x drift, 8x dev/R&D, 8x competitor boost (values from config)."""
import sys
sys.path.insert(0, 'src')

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from saas_bench.config import (
    GROUP_PREFERENCE_DRIFT, INDIVIDUAL_PREFERENCE_DRIFT,
    CUSTOMER_GROUP_S1, CUSTOMER_GROUP_S2, CUSTOMER_GROUP_S3,
    CUSTOMER_GROUP_E1, CUSTOMER_GROUP_E2, CUSTOMER_GROUP_E3,
    generate_discoverable_groups,
)

# Build group config lookup
ALL_GROUPS = {}
for g in [CUSTOMER_GROUP_S1, CUSTOMER_GROUP_S2, CUSTOMER_GROUP_S3,
          CUSTOMER_GROUP_E1, CUSTOMER_GROUP_E2, CUSTOMER_GROUP_E3]:
    ALL_GROUPS[g.group_id] = g

# Generate discoverable groups with seed 42 (same as the simulation)
rng = np.random.default_rng(42)
discoverable = generate_discoverable_groups(rng)
ALL_GROUPS.update(discoverable)

# Simulation parameters
TOTAL_DAYS = 1095  # 3 years

# Values now match config.py directly (5× drift already baked in, 8× competitor)
GLOBAL_Q_BIAS_DRIFT = 0.0015  # per day (5× original 0.0003)

# Competitor events: ~18 events, 8× boost → mean ~0.33 each → total ~6.0
# Simulated from lognormal(mu=-1.77, sigma=1.2) clipped to [0.032, 2.80]
COMPETITOR_TOTAL_BOOST = 6.0  # estimated mean total over 3 years


def sigmoid(x):
    x = np.clip(x, -500, 500)
    return 1.0 / (1.0 + np.exp(-x))


def compute_required_quality(cost, c_max, q_min, q_max, steepness_left, steepness_right=3.0):
    """Compute Q_required curve (participation constraint)."""
    result = np.zeros_like(cost, dtype=float)
    q_range = q_max - q_min
    half_range = q_range / 2.0

    for i, c in enumerate(cost):
        if c_max <= 0:
            result[i] = q_max
        elif c > c_max:
            result[i] = q_max
        else:
            nc = c / c_max
            if nc < 0.5:
                si = steepness_left * (nc - 0.25) * 10
                result[i] = q_min + half_range * sigmoid(si)
            else:
                si = steepness_right * (nc - 0.75) * 10
                result[i] = q_min + half_range + half_range * sigmoid(si)
    return result


def compute_drifted_params(group_id, group_cfg, days=TOTAL_DAYS, include_individual=False):
    """Compute drifted q_min, q_max, c_max, steepness_left after `days` days."""
    q_min = group_cfg.q_min_mean
    q_max = group_cfg.q_max_mean
    c_max = group_cfg.c_max_mean
    sl = 1.0  # steepness_left_factor starts at 1.0

    # 1. Global q_bias drift (additive)
    global_bias = GLOBAL_Q_BIAS_DRIFT * days
    q_min += global_bias
    q_max += global_bias

    # 2. Competitor events (additive, same to both)
    q_min += COMPETITOR_TOTAL_BOOST
    q_max += COMPETITOR_TOTAL_BOOST

    # 3. Group drift (5× already in config values)
    gd = GROUP_PREFERENCE_DRIFT.get(group_id, {})
    if 'q_bias_drift' in gd:
        bias = gd['q_bias_drift'] * days
        q_min += bias
        q_max += bias
    if 'c_max_drift' in gd:
        c_max *= (1.0 + gd['c_max_drift']) ** days
        c_max = max(10.0, min(c_max, 2000.0))
    if 'steepness_left_drift' in gd:
        sl *= (1.0 + gd['steepness_left_drift']) ** days
        sl = max(0.5, min(sl, 3.0))

    # 4. Individual drift (5× already in config values, only for day-0 customers who stayed the whole sim)
    if include_individual:
        id_ = INDIVIDUAL_PREFERENCE_DRIFT.get(group_id, {})
        if 'q_bias_drift' in id_:
            bias = id_['q_bias_drift'] * days
            q_min += bias
            q_max += bias
        if 'c_max_drift' in id_:
            c_max *= (1.0 + id_['c_max_drift']) ** days
            c_max = max(10.0, min(c_max, 2000.0))
        if 'steepness_left_drift' in id_:
            sl *= (1.0 + id_['steepness_left_drift']) ** days
            sl = max(0.5, min(sl, 3.0))

    return q_min, q_max, c_max, sl


def plot_group(ax, group_id, group_cfg):
    """Plot 3 curves for one customer group."""
    # --- Initial parameters ---
    q_min_0 = group_cfg.q_min_mean
    q_max_0 = group_cfg.q_max_mean
    c_max_0 = group_cfg.c_max_mean

    # Default steepness (sampled from exponential, mean ~1.0 for left, ~2.0 for right)
    steepness_left_0 = 1.0
    steepness_right = 2.0

    # --- End-of-sim group parameters ---
    q_min_g, q_max_g, c_max_g, sl_g = compute_drifted_params(group_id, group_cfg, include_individual=False)

    # --- End-of-sim day-0 customer parameters ---
    q_min_i, q_max_i, c_max_i, sl_i = compute_drifted_params(group_id, group_cfg, include_individual=True)

    # Each curve gets its own x-range ending at its c_max
    # X-axis spans 0 to max c_max * 1.1 for context
    x_max = max(c_max_0, c_max_g, c_max_i) * 1.1
    x_max = max(x_max, 50)  # at least $50

    # Compute each curve only up to its own c_max
    cost_0 = np.linspace(0, c_max_0, 500)
    cost_g = np.linspace(0, c_max_g, 500)
    cost_i = np.linspace(0, c_max_i, 500)

    y_initial = compute_required_quality(cost_0, c_max_0, q_min_0, q_max_0, steepness_left_0, steepness_right)
    y_group = compute_required_quality(cost_g, c_max_g, q_min_g, q_max_g, sl_g, steepness_right)
    y_indiv = compute_required_quality(cost_i, c_max_i, q_min_i, q_max_i, sl_i, steepness_right)

    # Plot — each curve ends at (c_max, q_max)
    ax.plot(cost_0, y_initial, 'b-', linewidth=2,
            label=f'Initial (q_min={q_min_0:.2f}, q_max={q_max_0:.2f}, c_max=${c_max_0:.0f})')
    ax.plot(cost_g, y_group, 'r--', linewidth=2,
            label=f'End group mean (q_min={q_min_g:.2f}, q_max={q_max_g:.2f}, c_max=${c_max_g:.0f})')
    ax.plot(cost_i, y_indiv, 'g:', linewidth=2.5,
            label=f'Day-0 customer (q_min={q_min_i:.2f}, q_max={q_max_i:.2f}, c_max=${c_max_i:.0f})')

    # Endpoint dots at (c_max, q_max) for each curve
    ax.plot(c_max_0, q_max_0, 'bo', markersize=7)
    ax.plot(c_max_g, q_max_g, 'rs', markersize=7)
    ax.plot(c_max_i, q_max_i, 'g^', markersize=7)

    ax.set_xlim(0, x_max)
    ax.set_title(f'{group_id}: {group_cfg.group_name}', fontsize=11, fontweight='bold')
    ax.set_xlabel('Price ($/month)')
    ax.set_ylabel('Required Quality')
    ax.legend(fontsize=7, loc='upper left')
    ax.grid(True, alpha=0.3)


# --- Generate PDF ---
# Sort: S1-S3, E1-E3, D_S01-D_S10, D_E01-D_E10
def sort_key(gid):
    if gid.startswith('S'):
        return (0, int(gid[1:]))
    elif gid.startswith('E'):
        return (1, int(gid[1:]))
    elif gid.startswith('D_S'):
        return (2, int(gid[3:]))
    elif gid.startswith('D_E'):
        return (3, int(gid[3:]))
    return (9, 0)

group_ids = sorted(ALL_GROUPS.keys(), key=sort_key)
n_groups = len(group_ids)

output_path = 'preference_curves.pdf'
with PdfPages(output_path) as pdf:
    # One group per page for readability
    for gid in group_ids:
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        plot_group(ax, gid, ALL_GROUPS[gid])
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

print(f'PDF saved to {output_path}')
print(f'Total groups: {n_groups}')
for gid in group_ids:
    g = ALL_GROUPS[gid]
    q_min_i, q_max_i, c_max_i, sl_i = compute_drifted_params(gid, g, include_individual=True)
    print(f'  {gid:6s} ({g.group_name:30s}): initial q=[{g.q_min_mean:.2f}, {g.q_max_mean:.2f}] c_max=${g.c_max_mean:.0f}  →  day-0 customer q=[{q_min_i:.2f}, {q_max_i:.2f}] c_max=${c_max_i:.0f}')
