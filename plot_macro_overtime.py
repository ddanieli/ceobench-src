"""Simulate PMI via Ornstein-Uhlenbeck process, then plot multiplier over time
for each variable × each initial customer group."""
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from numpy.random import Generator, PCG64

# === PMI OU Process Parameters (from config.py) ===
PMI_INITIAL = 49.37
PMI_LONG_RUN_MEAN = 49.37
PMI_CYCLE_AMPLITUDE = 8.0
PMI_CYCLE_PERIOD_DAYS = 548
PMI_THETA = 0.015  # mean reversion rate
PMI_SIGMA = 0.4    # daily volatility
PMI_FLOOR = 30.0
PMI_CEILING = 70.0
RANDOM_PHASE = False
FIXED_PHASE = 4.71239  # 3π/2 — starts at trough (recession first)
SEED = 42
N_DAYS = 1095  # 3 years

# === MACRO_SENSITIVITY for initial groups (3x original) ===
GROUPS = {
    'S1': {'name': 'Price-Sensitive Individuals', 'betas': {'lead_generation': 1.50, 'willingness_to_pay': 1.80, 'deal_velocity': 0.0, 'seat_count': 0.0}},
    'S2': {'name': 'Quality-Focused Individuals', 'betas': {'lead_generation': 0.75, 'willingness_to_pay': 0.60, 'deal_velocity': 0.0, 'seat_count': 0.0}},
    'S3': {'name': 'Power Users', 'betas': {'lead_generation': 0.90, 'willingness_to_pay': 0.45, 'deal_velocity': 0.0, 'seat_count': 0.0}},
    'E1': {'name': 'Cost-Cutting Enterprises', 'betas': {'lead_generation': 1.35, 'willingness_to_pay': 1.20, 'deal_velocity': 1.35, 'seat_count': 1.05}},
    'E2': {'name': 'Quality-First Enterprises', 'betas': {'lead_generation': 0.45, 'willingness_to_pay': 0.30, 'deal_velocity': 0.60, 'seat_count': 0.24}},
}

DIMENSIONS = ['lead_generation', 'willingness_to_pay', 'deal_velocity', 'seat_count']
DIM_LABELS = {
    'lead_generation': 'Lead Generation',
    'willingness_to_pay': 'Willingness to Pay',
    'deal_velocity': 'Deal Velocity',
    'seat_count': 'Seat Count',
}

GROUP_COLORS = {
    'S1': '#e74c3c',
    'S2': '#3498db',
    'S3': '#2ecc71',
    'E1': '#e67e22',
    'E2': '#9b59b6',
}

# === Simulate PMI ===
rng = Generator(PCG64(SEED))
macro_seed = int(rng.integers(0, 2**63))
macro_rng = Generator(PCG64(macro_seed ^ 0x4D414352))

if RANDOM_PHASE:
    phase_offset = float(macro_rng.uniform(0, 2 * math.pi))
else:
    # Consume the RNG draw to keep stream consistent, then use fixed phase
    _ = float(macro_rng.uniform(0, 2 * math.pi))
    phase_offset = FIXED_PHASE

pmi_series = np.zeros(N_DAYS)
pmi_current = PMI_INITIAL

for day in range(N_DAYS):
    # Sinusoidal cycle mean
    cycle_mean = PMI_LONG_RUN_MEAN + PMI_CYCLE_AMPLITUDE * math.sin(
        2 * math.pi * day / PMI_CYCLE_PERIOD_DAYS + phase_offset
    )
    # OU step
    noise = float(macro_rng.normal(0, PMI_SIGMA))
    pmi_current = pmi_current + PMI_THETA * (cycle_mean - pmi_current) + noise
    pmi_current = max(PMI_FLOOR, min(PMI_CEILING, pmi_current))
    pmi_series[day] = pmi_current

# === Compute multipliers ===
def compute_multiplier(pmi_arr, beta):
    return np.maximum(0.5, 1.0 + beta * (pmi_arr - 50.0) / 50.0)

days = np.arange(N_DAYS)
months = days / 30.0  # for x-axis in months

# Also compute the sinusoidal mean for reference
cycle_mean_series = PMI_LONG_RUN_MEAN + PMI_CYCLE_AMPLITUDE * np.sin(
    2 * np.pi * days / PMI_CYCLE_PERIOD_DAYS + phase_offset
)

# === Build PDF ===
output_path = '/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench/macro_overtime_report.pdf'

with PdfPages(output_path) as pdf:

    # === Page 1: PMI over time ===
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={'height_ratios': [2, 1]})
    fig.suptitle(f'Simulated PMI Over {N_DAYS} Days (Seed={SEED})', fontsize=15, fontweight='bold')

    ax1.plot(days, pmi_series, color='#2c3e50', linewidth=0.8, alpha=0.9, label='Daily PMI')
    ax1.plot(days, cycle_mean_series, color='#e74c3c', linewidth=1.5, linestyle='--', alpha=0.7, label='Cycle Mean (sinusoidal)')
    ax1.axhline(y=50, color='gray', linestyle=':', alpha=0.5, label='Neutral (PMI=50)')
    ax1.fill_between(days, 50, pmi_series, where=pmi_series >= 50, alpha=0.15, color='green')
    ax1.fill_between(days, 50, pmi_series, where=pmi_series < 50, alpha=0.15, color='red')
    ax1.set_ylabel('PMI', fontsize=12)
    ax1.set_ylim(35, 65)
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    # Month labels on top
    ax1_top = ax1.twiny()
    ax1_top.set_xlim(ax1.get_xlim())
    month_ticks = [0, 182, 365, 547, 730, 912, 1095]
    ax1_top.set_xticks(month_ticks)
    ax1_top.set_xticklabels(['Month 0', '6', '12', '18', '24', '30', '36'], fontsize=8)

    # Trend indicator
    # Rolling 30-day average
    rolling_pmi = np.convolve(pmi_series, np.ones(30)/30, mode='same')
    trend = np.where(rolling_pmi >= 58, 'Strong Expansion',
             np.where(rolling_pmi >= 52, 'Expansion',
              np.where(rolling_pmi >= 48, 'Neutral',
               np.where(rolling_pmi >= 42, 'Contraction', 'Severe Contraction'))))

    # Color-coded trend bar
    trend_colors = {'Strong Expansion': '#27ae60', 'Expansion': '#82e0aa',
                    'Neutral': '#f9e79f', 'Contraction': '#f5b7b1', 'Severe Contraction': '#e74c3c'}
    for i in range(len(days) - 1):
        ax2.axvspan(days[i], days[i+1], color=trend_colors[trend[i]], alpha=0.8)
    ax2.set_yticks([])
    ax2.set_xlabel('Day', fontsize=12)
    ax2.set_ylabel('Cycle Phase', fontsize=10)
    # Legend for trend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=c, label=l) for l, c in trend_colors.items()]
    ax2.legend(handles=legend_elements, loc='upper center', ncol=5, fontsize=7, bbox_to_anchor=(0.5, 1.3))
    ax2.set_xlim(0, N_DAYS)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    pdf.savefig(fig)
    plt.close(fig)

    # === Pages 2-5: One page per dimension, multiplier over time for all groups ===
    for dim in DIMENSIONS:
        fig, axes = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={'height_ratios': [1, 3]})
        fig.suptitle(f'{DIM_LABELS[dim]} Multiplier Over Time', fontsize=15, fontweight='bold')

        # Top: PMI reference
        ax_pmi = axes[0]
        ax_pmi.plot(days, pmi_series, color='#2c3e50', linewidth=0.6, alpha=0.7)
        ax_pmi.axhline(y=50, color='gray', linestyle=':', alpha=0.5)
        ax_pmi.fill_between(days, 50, pmi_series, where=pmi_series >= 50, alpha=0.1, color='green')
        ax_pmi.fill_between(days, 50, pmi_series, where=pmi_series < 50, alpha=0.1, color='red')
        ax_pmi.set_ylabel('PMI', fontsize=9)
        ax_pmi.set_ylim(35, 65)
        ax_pmi.set_xticklabels([])
        ax_pmi.grid(True, alpha=0.2)
        ax_pmi.set_title('PMI (reference)', fontsize=9, color='gray')

        # Bottom: multipliers
        ax_mult = axes[1]
        has_data = False

        for gid, ginfo in GROUPS.items():
            beta = ginfo['betas'][dim]
            if beta == 0:
                continue
            has_data = True
            mult = compute_multiplier(pmi_series, beta)
            # Smooth for readability (7-day rolling avg)
            mult_smooth = np.convolve(mult, np.ones(7)/7, mode='same')
            ax_mult.plot(days, mult_smooth, color=GROUP_COLORS[gid], linewidth=1.5, alpha=0.85,
                        label=f'{gid}: {ginfo["name"]} (β={beta:.2f})')
            # Show raw as faint background
            ax_mult.plot(days, mult, color=GROUP_COLORS[gid], linewidth=0.3, alpha=0.25)

        if not has_data:
            ax_mult.text(0.5, 0.5, 'N/A for initial individual groups (S1-S3)\nOnly applies to enterprise groups (E1, E2)',
                        transform=ax_mult.transAxes, ha='center', va='center', fontsize=14, color='gray')

        ax_mult.axhline(y=1.0, color='black', linestyle='--', alpha=0.5, linewidth=1)
        ax_mult.set_xlabel('Day', fontsize=11)
        ax_mult.set_ylabel('Multiplier', fontsize=11)
        ax_mult.set_xlim(0, N_DAYS)
        if has_data:
            ax_mult.legend(loc='upper left', fontsize=9)
        ax_mult.grid(True, alpha=0.3)

        # Month labels on top
        ax_top = ax_mult.twiny()
        ax_top.set_xlim(0, N_DAYS)
        ax_top.set_xticks(month_ticks)
        ax_top.set_xticklabels(['Month 0', '6', '12', '18', '24', '30', '36'], fontsize=8)

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        pdf.savefig(fig)
        plt.close(fig)

    # === Page 6: Per-group panels (all dimensions over time) ===
    fig, axes = plt.subplots(3, 2, figsize=(14, 12))
    fig.suptitle('All Dimensions Over Time — Per Group', fontsize=14, fontweight='bold')

    dim_colors = {
        'lead_generation': '#e74c3c',
        'willingness_to_pay': '#3498db',
        'deal_velocity': '#e67e22',
        'seat_count': '#2ecc71',
    }

    for idx, (gid, ginfo) in enumerate(GROUPS.items()):
        ax = axes[idx // 2][idx % 2]

        for dim in DIMENSIONS:
            beta = ginfo['betas'][dim]
            if beta == 0:
                continue
            mult = compute_multiplier(pmi_series, beta)
            mult_smooth = np.convolve(mult, np.ones(7)/7, mode='same')
            ax.plot(days, mult_smooth, color=dim_colors[dim], linewidth=1.5,
                    label=f'{DIM_LABELS[dim]} (β={beta:.2f})')

        ax.axhline(y=1.0, color='black', linestyle='--', alpha=0.5)
        ax.set_title(f'{gid}: {ginfo["name"]}', fontsize=11, fontweight='bold')
        ax.set_xlabel('Day', fontsize=8)
        ax.set_ylabel('Multiplier', fontsize=8)
        ax.set_xlim(0, N_DAYS)
        ax.legend(fontsize=7, loc='upper left')
        ax.grid(True, alpha=0.3)

    # PMI in the 6th subplot
    ax_pmi = axes[2][1]
    ax_pmi.plot(days, pmi_series, color='#2c3e50', linewidth=0.7)
    ax_pmi.axhline(y=50, color='gray', linestyle=':', alpha=0.5)
    ax_pmi.fill_between(days, 50, pmi_series, where=pmi_series >= 50, alpha=0.15, color='green')
    ax_pmi.fill_between(days, 50, pmi_series, where=pmi_series < 50, alpha=0.15, color='red')
    ax_pmi.set_title('PMI (reference)', fontsize=11, fontweight='bold')
    ax_pmi.set_xlabel('Day', fontsize=8)
    ax_pmi.set_ylabel('PMI', fontsize=8)
    ax_pmi.set_xlim(0, N_DAYS)
    ax_pmi.set_ylim(35, 65)
    ax_pmi.grid(True, alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    pdf.savefig(fig)
    plt.close(fig)

    # === Page 7: Statistics summary ===
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.axis('off')
    ax.set_title('Multiplier Statistics Over 3-Year Simulation', fontsize=14, fontweight='bold', pad=20)

    col_labels = ['Group', 'Dimension', 'β', 'Mean', 'Min', 'Max', 'Std', '% Time < 1.0', '% Time > 1.05']
    rows = []
    for gid, ginfo in GROUPS.items():
        for dim in DIMENSIONS:
            beta = ginfo['betas'][dim]
            if beta == 0:
                continue
            mult = compute_multiplier(pmi_series, beta)
            rows.append([
                gid, DIM_LABELS[dim], f'{beta:.2f}',
                f'{np.mean(mult):.4f}', f'{np.min(mult):.4f}', f'{np.max(mult):.4f}',
                f'{np.std(mult):.4f}',
                f'{100 * np.mean(mult < 1.0):.1f}%',
                f'{100 * np.mean(mult > 1.05):.1f}%',
            ])

    t = ax.table(cellText=rows, colLabels=col_labels, loc='center', cellLoc='center')
    t.auto_set_font_size(False)
    t.set_fontsize(8)
    t.scale(1.0, 1.4)
    for (row, col), cell in t.get_celld().items():
        if row == 0:
            cell.set_facecolor('#2c3e50')
            cell.set_text_props(color='white', fontweight='bold', fontsize=7)
        elif row % 2 == 0:
            cell.set_facecolor('#ecf0f1')

    # PMI stats
    ax.text(0.5, 0.06,
            f'PMI Stats — Mean: {np.mean(pmi_series):.2f}, Min: {np.min(pmi_series):.2f}, '
            f'Max: {np.max(pmi_series):.2f}, Std: {np.std(pmi_series):.2f}, '
            f'% Time in Contraction (<50): {100*np.mean(pmi_series<50):.1f}%',
            transform=ax.transAxes, ha='center', fontsize=10,
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#f0f0f0', edgecolor='gray'))

    plt.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)

print(f'PDF saved to: {output_path}')
print(f'PMI stats: mean={np.mean(pmi_series):.2f}, min={np.min(pmi_series):.2f}, max={np.max(pmi_series):.2f}')
