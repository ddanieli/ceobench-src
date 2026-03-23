"""Plot noise distributions for each customer group's parameters.
Reads values directly from config.py so it stays in sync."""
import sys
sys.path.insert(0, 'src')

import numpy as np
import matplotlib.pyplot as plt
from saas_bench.config import INITIAL_CUSTOMER_GROUPS

# Build groups dict from config
groups = {}
for gid, cfg in sorted(INITIAL_CUSTOMER_GROUPS.items()):
    label = f"{gid} — {cfg.group_name}"
    params = {
        "q_min": (cfg.q_min_mean, cfg.q_min_std),
        "q_range": (cfg.q_range_mean, cfg.q_range_std),
        "slope": (cfg.slope_mean, cfg.slope_std),
        "lockin_penalty": (cfg.lockin_penalty_mean, cfg.lockin_penalty_std),
        "ads_quality_sens": (cfg.ads_quality_sensitivity_mean, cfg.ads_quality_sensitivity_std),
        "ads_return_sens": (cfg.ads_return_sensitivity_mean, cfg.ads_return_sensitivity_std),
    }
    if not cfg.is_enterprise:
        params["c_max ($/mo)"] = (cfg.c_max_mean, cfg.c_max_std)
        params["usage (units/day)"] = (cfg.usage_demand_mean, cfg.usage_demand_std)
    else:
        params["c_max ($/seat/mo)"] = (cfg.c_max_mean, cfg.c_max_std)
        params["usage (units/seat/day)"] = (cfg.usage_demand_mean, cfg.usage_demand_std)
        params["negotiation_rate"] = (cfg.negotiation_rate_mean, cfg.negotiation_rate_std)
        params["reply_delay (days)"] = (cfg.reply_delay_mean, cfg.reply_delay_std)
        params["max_neg_turns"] = (cfg.max_negotiation_turns_mean, cfg.max_negotiation_turns_std)
    groups[label] = params

# Colors and short names
group_labels = list(groups.keys())
short_names = {l: l.split(" —")[0] for l in group_labels}
colors_list = ["#2196F3", "#4CAF50", "#FF9800", "#E91E63", "#9C27B0", "#00BCD4"]
colors = {l: colors_list[i] for i, l in enumerate(group_labels)}

# Shared params for overlay
shared_params = ["q_min", "q_range", "slope", "lockin_penalty", "ads_quality_sens", "ads_return_sens"]

# ============================================================
# PLOT 1: Overlay comparison
# ============================================================
fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle("Customer Group Parameter Distributions — Overlay Comparison (4x noise, q_range reparameterized)", fontsize=14, fontweight="bold", y=0.98)

for idx, param in enumerate(shared_params):
    ax = axes[idx // 3][idx % 3]
    for gname, params in groups.items():
        if param in params:
            mean, std = params[param]
            x = np.linspace(max(mean - 3.5 * std, -0.1), mean + 3.5 * std, 300)
            y = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mean) / std) ** 2)
            ax.plot(x, y, label=short_names[gname], color=colors[gname], linewidth=2)
            ax.fill_between(x, y, alpha=0.12, color=colors[gname])
    ax.set_title(param, fontsize=13, fontweight="bold")
    ax.set_ylabel("Density")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("noise_distributions_overlay.png", dpi=150, bbox_inches="tight")
plt.close()

# ============================================================
# PLOT 2: Per-group parameter distributions with 25/75 percentiles
# ============================================================
fig, axes = plt.subplots(2, 3, figsize=(20, 12))
fig.suptitle("Per-Group Parameter Distributions with 25th/75th Percentiles (4x noise)", fontsize=16, fontweight="bold", y=0.98)

for gidx, (gname, params) in enumerate(groups.items()):
    ax = axes[gidx // 3][gidx % 3]
    param_names = list(params.keys())
    y_positions = np.arange(len(param_names))
    means = [params[p][0] for p in param_names]
    stds = [params[p][1] for p in param_names]
    p25s = [m - 0.6745 * s for m, s in zip(means, stds)]
    p75s = [m + 0.6745 * s for m, s in zip(means, stds)]

    ax.barh(y_positions, means, height=0.5, color=colors[gname], alpha=0.7, label="Mean")
    ax.errorbar(
        means, y_positions,
        xerr=[np.array(means) - np.array(p25s), np.array(p75s) - np.array(means)],
        fmt="none", ecolor="black", elinewidth=2, capsize=5, label="25th–75th pct"
    )
    for i, (m, p25, p75) in enumerate(zip(means, p25s, p75s)):
        ax.annotate(f"{m:.3g} [{p25:.3g}, {p75:.3g}]", (max(p75 * 1.05, m * 1.1), i),
                    fontsize=7, va="center")

    ax.set_yticks(y_positions)
    ax.set_yticklabels(param_names, fontsize=8)
    ax.set_title(gname.replace("\n", " "), fontsize=11, fontweight="bold", color=colors[gname])
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(True, alpha=0.3, axis="x")
    ax.invert_yaxis()

plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig("noise_distributions_pergroup.png", dpi=150, bbox_inches="tight")
plt.close()

# ============================================================
# PLOT 3: CV heatmap
# ============================================================
group_names_short = [short_names[l] for l in group_labels]
cv_matrix = []
for gname in groups:
    row = []
    for param in shared_params:
        if param in groups[gname]:
            mean, std = groups[gname][param]
            cv = std / mean * 100 if mean != 0 else 0
            row.append(cv)
        else:
            row.append(np.nan)
    cv_matrix.append(row)
cv_matrix = np.array(cv_matrix)

fig, ax = plt.subplots(figsize=(12, 5))
im = ax.imshow(cv_matrix, cmap="YlOrRd", aspect="auto")
ax.set_xticks(range(len(shared_params)))
ax.set_xticklabels(shared_params, fontsize=10, rotation=30, ha="right")
ax.set_yticks(range(len(group_names_short)))
ax.set_yticklabels(group_names_short, fontsize=11)
for i in range(len(group_names_short)):
    for j in range(len(shared_params)):
        val = cv_matrix[i, j]
        if not np.isnan(val):
            ax.text(j, i, f"{val:.0f}%", ha="center", va="center", fontsize=10,
                    color="white" if val > 80 else "black", fontweight="bold")
plt.colorbar(im, label="Coefficient of Variation (%)", shrink=0.8)
ax.set_title("Noise Level (CV = σ/μ) by Customer Group & Parameter (4x noise)", fontsize=14, fontweight="bold")
plt.tight_layout()
plt.savefig("noise_cv_heatmap.png", dpi=150, bbox_inches="tight")
plt.close()

# Print concrete values
print("\n" + "=" * 90)
print("CONCRETE 25th / 75th PERCENTILE VALUES PER GROUP (4x noise, q_range reparameterized)")
print("=" * 90)
for gname, params in groups.items():
    print(f"\n{'─' * 70}")
    print(f"  {gname}")
    print(f"{'─' * 70}")
    print(f"  {'Parameter':<25s} {'Mean':>10s} {'Std':>10s} {'P25':>10s} {'P75':>10s} {'CV%':>8s}")
    print(f"  {'─'*25} {'─'*10} {'─'*10} {'─'*10} {'─'*10} {'─'*8}")
    for pname, (mean, std) in params.items():
        p25 = mean - 0.6745 * std
        p75 = mean + 0.6745 * std
        cv = (std / mean * 100) if mean != 0 else 0
        print(f"  {pname:<25s} {mean:>10.4f} {std:>10.4f} {p25:>10.4f} {p75:>10.4f} {cv:>7.1f}%")

print("\n\nNote: q_max is now sampled as q_min + max(N(q_range_mean, q_range_std), 0.01)")
print("This guarantees q_max > q_min by construction.")
