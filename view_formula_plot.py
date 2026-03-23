"""Plot effect score vs view count for social media posts."""
import numpy as np
import matplotlib.pyplot as plt

scores = np.linspace(-1.0, 1.0, 200)
abs_scores = np.abs(scores)
base_views = 50  # min base

# Current formula: viral_mult = 1 + |eff|^2 * 9
current_mult = 1.0 + abs_scores**2 * 9.0
current_views = base_views * current_mult

# Proposed exponential: viral_mult = exp(|eff| * k) where k chosen so score=1.0 -> ~50x
# exp(1.0 * 3.9) ≈ 49x, exp(0.5 * 3.9) ≈ 7x
k = 3.9
exp_mult = np.exp(abs_scores * k)
exp_views = base_views * exp_mult

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Left: multiplier
ax = axes[0]
ax.plot(scores, current_mult, 'b-', linewidth=2, label='Current: 1 + |s|² × 9')
ax.plot(scores, exp_mult, 'r-', linewidth=2, label=f'Exponential: exp(|s| × {k})')
ax.set_xlabel('Effect Score', fontsize=12)
ax.set_ylabel('View Multiplier', fontsize=12)
ax.set_title('View Multiplier vs Effect Score', fontsize=13)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.axvline(0, color='gray', alpha=0.3)
ax.axvline(-0.6, color='orange', alpha=0.5, linestyle='--', label='Viral threshold')
ax.axvline(0.6, color='orange', alpha=0.5, linestyle='--')

# Right: actual views (base=50)
ax = axes[1]
ax.plot(scores, current_views, 'b-', linewidth=2, label='Current')
ax.plot(scores, exp_views, 'r-', linewidth=2, label='Exponential')
ax.set_xlabel('Effect Score', fontsize=12)
ax.set_ylabel('Views (base=50)', fontsize=12)
ax.set_title('View Count vs Effect Score', fontsize=13)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.axvline(0, color='gray', alpha=0.3)
ax.axvline(-0.6, color='orange', alpha=0.5, linestyle='--')
ax.axvline(0.6, color='orange', alpha=0.5, linestyle='--')

# Annotate key points on exp curve
for s_val in [0.0, 0.3, 0.6, 0.8, 1.0]:
    v = base_views * np.exp(s_val * k)
    ax.annotate(f'{v:.0f}', xy=(s_val, v), fontsize=9,
                textcoords='offset points', xytext=(10, 5),
                arrowprops=dict(arrowstyle='->', color='red', alpha=0.5))

plt.tight_layout()
plt.savefig('/scratch/gpfs/ZHUANGL/hc5019/claude_code_workspace/claude-code-minion/projects/saas-bench/view_formula_plot.png', dpi=150, bbox_inches='tight')
print("Saved to view_formula_plot.png")
