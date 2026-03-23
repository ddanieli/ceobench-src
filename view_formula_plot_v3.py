"""Plot views vs effect score — linear 1x-3x below viral, exponential 3x-100x above."""
import numpy as np
import matplotlib.pyplot as plt

scores = np.linspace(0, 1.0, 200)
viral_threshold = 0.6

def view_multiplier(s, threshold=0.6):
    """Linear 1x-3x below threshold, exponential 3x-100x above."""
    if s <= threshold:
        return 1.0 + s * (3.0 - 1.0) / threshold
    else:
        base_at_threshold = 3.0
        k = np.log(100.0 / base_at_threshold) / (1.0 - threshold)  # 3x -> 100x
        return base_at_threshold * np.exp(k * (s - threshold))

vmult = np.vectorize(view_multiplier)
mults = vmult(scores)

sub_counts = [100, 1_000, 10_000, 100_000, 1_000_000]

fig, axes = plt.subplots(2, 3, figsize=(16, 10))
axes = axes.flatten()

for i, subs in enumerate(sub_counts):
    ax = axes[i]
    base = max(50, subs * 0.1)
    views = base * mults

    ax.plot(scores, views, 'b-', linewidth=2)
    ax.axvline(viral_threshold, color='orange', alpha=0.6, linestyle='--', label=f'Viral threshold ({viral_threshold})')
    ax.set_xlabel('|Effect Score|', fontsize=11)
    ax.set_ylabel('Views', fontsize=11)
    ax.set_title(f'{subs:,} subscribers (base={base:,.0f})', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    for s_val in [0.0, 0.3, 0.6, 0.8, 1.0]:
        v = base * view_multiplier(s_val)
        ax.annotate(f'{v:,.0f}', xy=(s_val, v), fontsize=8,
                    textcoords='offset points', xytext=(8, 5),
                    arrowprops=dict(arrowstyle='->', color='blue', alpha=0.4))

ax = axes[5]
for subs in sub_counts:
    base = max(50, subs * 0.1)
    views = base * mults
    ax.plot(scores, views, linewidth=2, label=f'{subs:,} subs')
ax.axvline(viral_threshold, color='orange', alpha=0.6, linestyle='--')
ax.set_xlabel('|Effect Score|', fontsize=11)
ax.set_ylabel('Views (log scale)', fontsize=11)
ax.set_title('All subscriber counts (log scale)', fontsize=12, fontweight='bold')
ax.set_yscale('log')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

plt.suptitle('Views vs Score — Linear 1×→3× (<0.6) | Exponential 3×→100× (≥0.6)', fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench/view_formula_plot_v3.png', dpi=150, bbox_inches='tight')
print("Saved")
