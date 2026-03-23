"""Plot macro (PMI) impact on each variable for each initial customer group."""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

# MACRO_SENSITIVITY for initial groups (from config.py)
GROUPS = {
    'S1': {'name': 'Price-Sensitive Individuals', 'betas': {'lead_generation': 0.50, 'willingness_to_pay': 0.60, 'deal_velocity': 0.0, 'seat_count': 0.0}},
    'S2': {'name': 'Quality-Focused Individuals', 'betas': {'lead_generation': 0.25, 'willingness_to_pay': 0.20, 'deal_velocity': 0.0, 'seat_count': 0.0}},
    'S3': {'name': 'Power Users', 'betas': {'lead_generation': 0.30, 'willingness_to_pay': 0.15, 'deal_velocity': 0.0, 'seat_count': 0.0}},
    'E1': {'name': 'Cost-Cutting Enterprises', 'betas': {'lead_generation': 0.45, 'willingness_to_pay': 0.40, 'deal_velocity': 0.45, 'seat_count': 0.35}},
    'E2': {'name': 'Quality-First Enterprises', 'betas': {'lead_generation': 0.15, 'willingness_to_pay': 0.10, 'deal_velocity': 0.20, 'seat_count': 0.08}},
}

DIMENSIONS = ['lead_generation', 'willingness_to_pay', 'deal_velocity', 'seat_count']
DIM_LABELS = {
    'lead_generation': 'Lead Generation',
    'willingness_to_pay': 'Willingness to Pay',
    'deal_velocity': 'Deal Velocity',
    'seat_count': 'Seat Count',
}
DIM_DESCRIPTIONS = {
    'lead_generation': 'Scales daily signup/lead count',
    'willingness_to_pay': 'Scales customer budget ceiling (c_max)',
    'deal_velocity': 'Scales enterprise deal speed (inverted for delay)',
    'seat_count': 'Amplifies enterprise seat count drift',
}

PMI = np.linspace(30, 70, 200)
PMI_NEUTRAL = 50

# Colors for groups
COLORS = {
    'S1': '#e74c3c',  # red
    'S2': '#3498db',  # blue
    'S3': '#2ecc71',  # green
    'E1': '#e67e22',  # orange
    'E2': '#9b59b6',  # purple
}

def multiplier(pmi, beta):
    return np.maximum(0.5, 1.0 + beta * (pmi - 50.0) / 50.0)

# Key PMI reference points
PMI_POINTS = [35, 40, 45, 50, 55, 60, 65]
PMI_LABELS_MAP = {
    35: 'Severe\nContraction',
    40: 'Contraction',
    45: 'Mild\nContraction',
    50: 'Neutral',
    55: 'Expansion',
    60: 'Strong\nExpansion',
    65: 'Boom',
}

output_path = '/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench/macro_impact_report.pdf'

with PdfPages(output_path) as pdf:
    # === Page 1: Title + Summary Table ===
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis('off')
    ax.set_title('Macroeconomic (PMI) Impact on Customer Groups\nSaaS Bench Simulation',
                 fontsize=18, fontweight='bold', pad=20)

    # Summary table
    col_labels = ['Group', 'Description', 'Lead Gen β', 'WTP β', 'Deal Vel β', 'Seat Count β']
    table_data = []
    for gid, ginfo in GROUPS.items():
        b = ginfo['betas']
        table_data.append([
            gid, ginfo['name'],
            f"{b['lead_generation']:.2f}", f"{b['willingness_to_pay']:.2f}",
            f"{b['deal_velocity']:.2f}" if b['deal_velocity'] > 0 else 'N/A',
            f"{b['seat_count']:.2f}" if b['seat_count'] > 0 else 'N/A',
        ])

    table = ax.table(cellText=table_data, colLabels=col_labels, loc='center',
                     cellLoc='center', colWidths=[0.08, 0.28, 0.12, 0.12, 0.12, 0.14])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.8)
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor('#2c3e50')
            cell.set_text_props(color='white', fontweight='bold')
        elif row % 2 == 0:
            cell.set_facecolor('#ecf0f1')

    # Formula
    ax.text(0.5, 0.12, 'Formula:  multiplier = max(0.5,  1.0 + β × (PMI − 50) / 50)',
            transform=ax.transAxes, ha='center', fontsize=13, fontfamily='monospace',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#f0f0f0', edgecolor='gray'))
    ax.text(0.5, 0.04, 'PMI > 50 = expansion (multiplier > 1.0)  |  PMI < 50 = contraction (multiplier < 1.0)',
            transform=ax.transAxes, ha='center', fontsize=10, color='gray')

    plt.tight_layout()
    pdf.savefig(fig)
    plt.close(fig)

    # === Page 2: Numerical table — multipliers at key PMI points ===
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
    fig.suptitle('Exact Multiplier Values at Key PMI Levels', fontsize=14, fontweight='bold', y=0.98)

    for idx, dim in enumerate(DIMENSIONS):
        ax = axes[idx // 2][idx % 2]
        ax.axis('off')
        ax.set_title(f'{DIM_LABELS[dim]}', fontsize=12, fontweight='bold', pad=5)

        col_labels_t = ['Group'] + [f'PMI={p}' for p in PMI_POINTS]
        rows = []
        for gid, ginfo in GROUPS.items():
            beta = ginfo['betas'][dim]
            if beta == 0:
                rows.append([gid] + ['N/A'] * len(PMI_POINTS))
            else:
                vals = [max(0.5, 1.0 + beta * (p - 50) / 50) for p in PMI_POINTS]
                rows.append([gid] + [f'{v:.3f}' for v in vals])

        t = ax.table(cellText=rows, colLabels=col_labels_t, loc='center',
                     cellLoc='center')
        t.auto_set_font_size(False)
        t.set_fontsize(8)
        t.scale(1.0, 1.5)
        for (row, col), cell in t.get_celld().items():
            if row == 0:
                cell.set_facecolor('#34495e')
                cell.set_text_props(color='white', fontweight='bold', fontsize=7)
            else:
                # Color code: red for <1, green for >1, gray for N/A
                txt = cell.get_text().get_text()
                if txt == 'N/A':
                    cell.set_facecolor('#f5f5f5')
                    cell.set_text_props(color='#aaa')
                elif col > 0:
                    try:
                        v = float(txt)
                        if v < 0.95:
                            cell.set_facecolor('#fadbd8')
                        elif v > 1.05:
                            cell.set_facecolor('#d5f5e3')
                        else:
                            cell.set_facecolor('#fef9e7')
                    except ValueError:
                        pass

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    pdf.savefig(fig)
    plt.close(fig)

    # === Pages 3-6: One page per dimension, all groups overlaid ===
    for dim in DIMENSIONS:
        fig, ax = plt.subplots(figsize=(11, 6))

        has_data = False
        for gid, ginfo in GROUPS.items():
            beta = ginfo['betas'][dim]
            if beta == 0:
                continue
            has_data = True
            mult = multiplier(PMI, beta)
            ax.plot(PMI, mult, color=COLORS[gid], linewidth=2.5, label=f'{gid}: {ginfo["name"]} (β={beta:.2f})')

            # Annotate key points
            for ref_pmi in [35, 45, 55, 65]:
                ref_mult = max(0.5, 1.0 + beta * (ref_pmi - 50) / 50)
                ax.plot(ref_pmi, ref_mult, 'o', color=COLORS[gid], markersize=5)

        if not has_data:
            ax.text(0.5, 0.5, f'N/A for all initial groups\n(Only applies to enterprise groups)',
                    transform=ax.transAxes, ha='center', va='center', fontsize=14, color='gray')

        ax.axhline(y=1.0, color='black', linestyle='--', alpha=0.5, linewidth=1)
        ax.axvline(x=50, color='black', linestyle='--', alpha=0.3, linewidth=1)
        ax.fill_betweenx([0.4, 1.5], 30, 50, alpha=0.05, color='red')
        ax.fill_betweenx([0.4, 1.5], 50, 70, alpha=0.05, color='green')

        ax.set_xlabel('PMI (ISM Purchasing Managers Index)', fontsize=12)
        ax.set_ylabel('Multiplier', fontsize=12)
        ax.set_title(f'{DIM_LABELS[dim]}\n{DIM_DESCRIPTIONS[dim]}', fontsize=14, fontweight='bold')
        ax.set_xlim(30, 70)
        if has_data:
            ax.legend(loc='upper left', fontsize=9)
        ax.grid(True, alpha=0.3)

        # Secondary x-axis labels
        ax2 = ax.twiny()
        ax2.set_xlim(30, 70)
        ax2.set_xticks([35, 42, 48, 50, 52, 58, 65])
        ax2.set_xticklabels(['Severe\nContr.', 'Contr.', 'Neutral-', '50', 'Neutral+', 'Expan.', 'Boom'], fontsize=7)

        plt.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

    # === Page 7: Per-group view — one subplot per group, all dimensions ===
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    fig.suptitle('Macro Impact by Customer Group (All Dimensions)', fontsize=14, fontweight='bold')

    dim_colors = {
        'lead_generation': '#e74c3c',
        'willingness_to_pay': '#3498db',
        'deal_velocity': '#e67e22',
        'seat_count': '#2ecc71',
    }

    for idx, (gid, ginfo) in enumerate(GROUPS.items()):
        ax = axes[idx // 3][idx % 3]
        for dim in DIMENSIONS:
            beta = ginfo['betas'][dim]
            if beta == 0:
                continue
            mult = multiplier(PMI, beta)
            ax.plot(PMI, mult, color=dim_colors[dim], linewidth=2,
                    label=f'{DIM_LABELS[dim]} (β={beta:.2f})')

        ax.axhline(y=1.0, color='black', linestyle='--', alpha=0.5, linewidth=1)
        ax.axvline(x=50, color='black', linestyle='--', alpha=0.3)
        ax.set_title(f'{gid}: {ginfo["name"]}', fontsize=10, fontweight='bold')
        ax.set_xlabel('PMI', fontsize=8)
        ax.set_ylabel('Multiplier', fontsize=8)
        ax.set_xlim(30, 70)
        ax.legend(fontsize=7, loc='upper left')
        ax.grid(True, alpha=0.3)

    # Hide empty subplot
    axes[1][2].axis('off')

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    pdf.savefig(fig)
    plt.close(fig)

    # === Page 8: Percentage change summary (bar chart at key PMI points) ===
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.suptitle('Percentage Change from Neutral (PMI=50) at Key PMI Levels', fontsize=13, fontweight='bold')

    for pidx, ref_pmi in enumerate([40, 55, 65]):
        ax = axes[pidx]
        pmi_dev = (ref_pmi - 50) / 50

        x = np.arange(len(GROUPS))
        width = 0.18

        for didx, dim in enumerate(DIMENSIONS):
            pct_changes = []
            for gid in GROUPS:
                beta = GROUPS[gid]['betas'][dim]
                if beta == 0:
                    pct_changes.append(0)
                else:
                    pct_changes.append(beta * pmi_dev * 100)

            bars = ax.bar(x + didx * width, pct_changes, width, label=DIM_LABELS[dim],
                         color=dim_colors[dim], alpha=0.85)

        ax.set_xticks(x + 1.5 * width)
        ax.set_xticklabels(GROUPS.keys())
        ax.set_ylabel('% Change')
        label = 'Contraction' if ref_pmi < 50 else 'Expansion' if ref_pmi <= 58 else 'Strong Expansion'
        ax.set_title(f'PMI = {ref_pmi} ({label})', fontsize=11)
        ax.axhline(y=0, color='black', linewidth=0.8)
        ax.grid(True, alpha=0.2, axis='y')
        if pidx == 0:
            ax.legend(fontsize=7)

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    pdf.savefig(fig)
    plt.close(fig)

print(f'PDF saved to: {output_path}')
