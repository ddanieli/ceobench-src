"""Plot q_min + bias and product quality over time for each initial customer group.

One plot per group (S1-S3, E1-E3), all 5 v2 runs overlaid.
q_min trajectory is reconstructed from:
  - Initial q_min_mean (from config)
  - Global q_bias drift (0.0015/day, applied every 30 days)
  - Group-specific q_bias drift (applied every 30 days)
  - Competitor events (stochastic per-run, additive jumps to ALL groups)
Product quality is reconstructed from dev spending + research boosts per run.
"""

import sqlite3
import math
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path

RUNS_DIR = Path(__file__).parent.parent / "bash_agent_runs"
RUN_IDS = ["0774b7fe", "011ec1f9", "c983e3ff", "d940ec72", "f5c39aee"]
RUN_LABELS = ["Run 1", "Run 2", "Run 3", "Run 4", "Run 5"]
RUN_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

# Initial group config (from config.py)
INITIAL_GROUPS = {
    'S1': {'name': 'Price-Sensitive Individuals', 'q_min_mean': 0.10, 'q_max_mean': 0.55},
    'S2': {'name': 'Quality-Focused Individuals', 'q_min_mean': 0.30, 'q_max_mean': 0.85},
    'S3': {'name': 'Power Users', 'q_min_mean': 0.25, 'q_max_mean': 0.80},
    'E1': {'name': 'Cost-Cutting Enterprises', 'q_min_mean': 0.20, 'q_max_mean': 0.65},
    'E2': {'name': 'Quality-First Enterprises', 'q_min_mean': 0.40, 'q_max_mean': 0.90},
    'E3': {'name': 'Strategic Partners', 'q_min_mean': 0.45, 'q_max_mean': 0.80},
}

# Drift rates
GLOBAL_Q_BIAS_DRIFT = 0.0015  # per day
GROUP_Q_BIAS_DRIFT = {
    'S1': 0.0, 'S2': 0.0, 'S3': 0.0025,
    'E1': 0.0, 'E2': 0.0, 'E3': 0.0,
}

BASE_PRODUCT_QUALITY = 0.05


def get_competitor_events(run_id: str) -> list:
    """Get competitor events from a run's DB. Returns list of (day, boost_amount, description)."""
    db_path = RUNS_DIR / f"run_{run_id}" / "world.db"
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT start_day, boost_amount, description FROM competitor_events ORDER BY start_day"
    ).fetchall()
    conn.close()
    return [(r['start_day'], r['boost_amount'], r['description']) for r in rows]


def reconstruct_qmin_with_competitors(group_id: str, max_day: int, competitor_events: list) -> tuple:
    """Reconstruct q_min_mean over time including competitor event boosts.

    Competitor events add an instant boost to q_min (and q_max) for ALL groups equally.
    """
    initial_qmin = INITIAL_GROUPS[group_id]['q_min_mean']
    group_drift_rate = GROUP_Q_BIAS_DRIFT.get(group_id, 0.0)

    # Build competitor boost lookup: day -> cumulative boost up to that day
    competitor_boost_by_day = {}
    cumulative_comp = 0.0
    for day, boost, _ in sorted(competitor_events, key=lambda x: x[0]):
        cumulative_comp += boost
        competitor_boost_by_day[day] = cumulative_comp

    days = list(range(0, max_day + 1))
    qmin_values = []

    cumulative_drift = 0.0
    cumulative_competitor = 0.0
    last_drift_day = 0

    for d in days:
        # Drift applied every 30 days
        if d > 0 and d % 30 == 0:
            drift_days = d - last_drift_day
            global_bias = ((1 + GLOBAL_Q_BIAS_DRIFT) ** drift_days - 1)
            group_bias = ((1 + group_drift_rate) ** drift_days - 1) if group_drift_rate != 0 else 0.0
            cumulative_drift += global_bias + group_bias
            last_drift_day = d

        # Competitor events: instant jump on the event day
        if d in competitor_boost_by_day:
            cumulative_competitor = competitor_boost_by_day[d]

        qmin_values.append(initial_qmin + cumulative_drift + cumulative_competitor)

    return days, qmin_values


def get_product_quality_series(run_id: str) -> tuple:
    """Extract product quality (base + q_shared_bonus) over time from a run's DB."""
    db_path = RUNS_DIR / f"run_{run_id}" / "world.db"
    if not db_path.exists():
        return [], []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        "SELECT day, spend_development FROM config_history ORDER BY day"
    ).fetchall()
    if not rows:
        conn.close()
        return [], []

    max_day = rows[-1]['day']
    spend_by_day = {r['day']: r['spend_development'] for r in rows}

    # Research project completions
    research_boosts = {}
    try:
        rp_rows = conn.execute("""
            SELECT expected_completion_day, quality_boost_applied
            FROM research_projects
            WHERE status = 'completed' AND quality_boost_applied > 0
        """).fetchall()
        for r in rp_rows:
            day = r['expected_completion_day']
            boost = r['quality_boost_applied']
            research_boosts[day] = research_boosts.get(day, 0) + boost
    except Exception:
        pass

    conn.close()

    # Reconstruct q_shared_bonus day by day
    days = list(range(1, max_day + 1))
    q_shared = 0.0
    quality_series = []

    for d in days:
        spend_dev = spend_by_day.get(d, 0.0)
        improvement = 0.008 * math.log(1 + spend_dev / 1000) if spend_dev > 0 else 0.0
        q_shared += improvement
        if d in research_boosts:
            q_shared += research_boosts[d]
        quality_series.append(BASE_PRODUCT_QUALITY + q_shared)

    return days, quality_series


def get_max_day(run_id: str) -> int:
    cp_path = RUNS_DIR / f"run_{run_id}" / "checkpoint.json"
    if cp_path.exists():
        with open(cp_path) as f:
            return json.load(f).get('day', 0)
    return 0


def main():
    output_pdf = Path(__file__).parent.parent / "bash_agent_runs" / "qmin_quality_plots.pdf"

    # Get max day and competitor events per run
    run_days = {}
    run_competitors = {}
    for rid in RUN_IDS:
        run_days[rid] = get_max_day(rid)
        run_competitors[rid] = get_competitor_events(rid)

    overall_max = max(run_days.values()) if run_days else 100
    print(f"Run days: {run_days}")
    print(f"Overall max day: {overall_max}")
    for rid in RUN_IDS:
        events = run_competitors[rid]
        print(f"Run {rid}: {len(events)} competitor events" +
              (f" (days: {[e[0] for e in events]}, boosts: {[f'{e[1]:.3f}' for e in events]})" if events else ""))

    # Pre-compute product quality series for each run
    quality_data = {}
    for rid in RUN_IDS:
        days, quality = get_product_quality_series(rid)
        quality_data[rid] = (days, quality)
        if days:
            print(f"Run {rid}: {len(days)} days quality, range [{quality[0]:.4f}, {quality[-1]:.4f}]")

    groups = ['S1', 'S2', 'S3', 'E1', 'E2', 'E3']

    with PdfPages(str(output_pdf)) as pdf:
        for gid in groups:
            info = INITIAL_GROUPS[gid]
            fig, ax1 = plt.subplots(1, 1, figsize=(14, 7))

            for i, (rid, label, color) in enumerate(zip(RUN_IDS, RUN_LABELS, RUN_COLORS)):
                max_d = run_days[rid]
                events = run_competitors[rid]

                # q_min with competitor events (per-run)
                days_qmin, qmin_vals = reconstruct_qmin_with_competitors(gid, max_d, events)
                ax1.plot(days_qmin, qmin_vals, color=color, linewidth=2, linestyle='-',
                         label=f'q_min ({label})', alpha=0.9)

                # Mark competitor events with vertical lines + annotations
                for evt_day, evt_boost, evt_desc in events:
                    if evt_day <= max_d:
                        ax1.axvline(x=evt_day, color=color, linestyle=':', alpha=0.4, linewidth=0.8)
                        # Small triangle marker at the event day on the q_min curve
                        if evt_day < len(qmin_vals):
                            ax1.plot(evt_day, qmin_vals[evt_day], marker='^', color=color,
                                     markersize=8, zorder=15)

                # Product quality (per-run)
                q_days, q_vals = quality_data[rid]
                if q_days:
                    ax1.plot(q_days, q_vals, color=color, linewidth=1.5, linestyle='--',
                             alpha=0.7, label=f'Product Q ({label})')

            # Reference: drift-only q_min (no competitor events) as thin gray line
            days_ref, qmin_ref = reconstruct_qmin_with_competitors(gid, overall_max, [])
            ax1.plot(days_ref, qmin_ref, 'k-', linewidth=1, alpha=0.3,
                     label='q_min (drift only, no competitors)', zorder=1)

            ax1.set_xlabel('Day', fontsize=12)
            ax1.set_ylabel('Quality Score', fontsize=12)
            ax1.set_title(
                f'{gid}: {info["name"]}\n'
                f'q_min (solid) vs Product Quality (dashed) — including competitor events (▲)',
                fontsize=13, fontweight='bold')

            # Legend outside plot area for clarity
            ax1.legend(loc='upper left', fontsize=8, framealpha=0.9, ncol=2)
            ax1.grid(True, alpha=0.3)
            ax1.set_xlim(0, max(overall_max, 30))

            # Annotation box with drift rates and competitor summary
            group_drift = GROUP_Q_BIAS_DRIFT.get(gid, 0.0)
            total_drift = GLOBAL_Q_BIAS_DRIFT + group_drift
            drift_text = (
                f"Initial q_min: {info['q_min_mean']:.2f}  |  q_max: {info['q_max_mean']:.2f}\n"
                f"Global drift: {GLOBAL_Q_BIAS_DRIFT}/day  |  Group drift: {group_drift}/day\n"
                f"▲ = competitor event (raises q_min for ALL groups)\n"
                f"Solid = q_min (threshold)  |  Dashed = product quality"
            )
            ax1.text(0.98, 0.02, drift_text, transform=ax1.transAxes,
                     fontsize=8, verticalalignment='bottom', horizontalalignment='right',
                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

            plt.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)

    print(f"\nSaved PDF: {output_pdf}")
    return str(output_pdf)


if __name__ == '__main__':
    main()
