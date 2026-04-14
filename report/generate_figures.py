"""Generate all publication-quality figures for the research report."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns
from pathlib import Path

# === Config ===
FIG_DIR = Path(__file__).parent / "figures"
FIG_DIR.mkdir(exist_ok=True)

# Publication style
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.grid': True,
    'grid.alpha': 0.3,
})

COLORS = {
    'majority_voting': '#3498DB',
    'structured_debate': '#E74C3C',
    'hierarchical': '#2ECC71',
    'evidence_weighted': '#9B59B6',
}
STRATEGY_LABELS = {
    'majority_voting': 'Majority\nVoting',
    'structured_debate': 'Structured\nDebate',
    'hierarchical': 'Hierarchical\nAuthority',
    'evidence_weighted': 'Evidence-\nWeighted',
}
STRATEGY_SHORT = {
    'majority_voting': 'Voting',
    'structured_debate': 'Debate',
    'hierarchical': 'Hierarchy',
    'evidence_weighted': 'Evidence',
}

# Load data
data_dir = Path(__file__).parent
insights = json.loads((data_dir / "insights.json").read_text())
overview = json.loads((data_dir / "overview.json").read_text())
heatmap_data = json.loads((data_dir / "heatmap.json").read_text())
deadlock_data = json.loads((data_dir / "deadlocks.json").read_text())
debates_data = json.loads((data_dir / "debates.json").read_text())

strat_eff = insights.get("strategy_effectiveness", [])
stat_tests = insights.get("statistical_tests", {})
behavioral_dna = insights.get("behavioral_dna", [])
source_impact = insights.get("source_quality_impact", {})
misinfo = insights.get("misinformation_resistance", {})
round_quality = insights.get("argument_quality_over_time", {})
effect_sizes = insights.get("cross_strategy_effect_sizes", [])


# =====================================================================
# FIGURE 1: Strategy Accuracy Comparison with Confidence Intervals
# =====================================================================
def fig1_strategy_accuracy():
    fig, ax = plt.subplots(figsize=(8, 4.5))
    strategies = [s['strategy'] for s in strat_eff]
    accuracies = [s['accuracy'] * 100 for s in strat_eff]
    ci_lower = [s.get('accuracy_ci_lower', 0) * 100 for s in strat_eff]
    ci_upper = [s.get('accuracy_ci_upper', 1) * 100 for s in strat_eff]
    errors_lower = [a - l for a, l in zip(accuracies, ci_lower)]
    errors_upper = [u - a for a, u in zip(accuracies, ci_upper)]
    labels = [STRATEGY_LABELS.get(s, s) for s in strategies]
    colors = [COLORS.get(s, '#666') for s in strategies]

    bars = ax.bar(range(len(strategies)), accuracies, color=colors, edgecolor='black',
                  linewidth=1.2, width=0.65, zorder=3)
    ax.errorbar(range(len(strategies)), accuracies,
                yerr=[errors_lower, errors_upper],
                fmt='none', ecolor='black', elinewidth=2, capsize=8, capthick=2, zorder=4)

    ax.set_xticks(range(len(strategies)))
    ax.set_xticklabels(labels, fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontweight='bold')
    ax.set_title('Strategy Accuracy with 95% Confidence Intervals', fontweight='bold', pad=15)
    ax.set_ylim(0, 110)
    ax.axhline(y=50, color='grey', linestyle='--', alpha=0.5, label='Random baseline')

    for bar, acc in zip(bars, accuracies):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 3,
                f'{acc:.0f}%', ha='center', va='bottom', fontweight='bold', fontsize=12)

    ax.legend(loc='upper right')
    fig.savefig(FIG_DIR / "fig1_strategy_accuracy.pdf")
    fig.savefig(FIG_DIR / "fig1_strategy_accuracy.png")
    plt.close()
    print("  Fig 1: Strategy accuracy with CIs")


# =====================================================================
# FIGURE 2: Multi-metric Strategy Comparison (Grouped Bar)
# =====================================================================
def fig2_strategy_metrics():
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    axes = axes.flatten()

    metrics = [
        ('accuracy', 'Accuracy', 100, '%'),
        ('deadlock_rate', 'Deadlock Rate', 100, '%'),
        ('avg_aggressiveness', 'Aggressiveness', 100, '%'),
        ('avg_confidence', 'Avg Confidence', 100, '%'),
        ('avg_novelty', 'Argument Novelty', 100, '%'),
        ('position_change_rate', 'Position Change Rate', 100, '%'),
    ]

    for i, (key, title, mult, unit) in enumerate(metrics):
        ax = axes[i]
        vals = [s.get(key, 0) * mult for s in strat_eff]
        strategies = [s['strategy'] for s in strat_eff]
        colors = [COLORS.get(s, '#666') for s in strategies]
        labels = [STRATEGY_SHORT.get(s, s) for s in strategies]

        bars = ax.bar(range(len(vals)), vals, color=colors, edgecolor='black', linewidth=0.8, width=0.6)
        ax.set_xticks(range(len(vals)))
        ax.set_xticklabels(labels, fontsize=9, fontweight='bold')
        ax.set_title(title, fontweight='bold', fontsize=11)
        ax.set_ylabel(unit, fontsize=9)

        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                    f'{v:.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    fig.suptitle('Multi-Dimensional Strategy Comparison', fontweight='bold', fontsize=14, y=1.02)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig2_strategy_metrics.pdf")
    fig.savefig(FIG_DIR / "fig2_strategy_metrics.png")
    plt.close()
    print("  Fig 2: Multi-metric comparison")


# =====================================================================
# FIGURE 3: Misinformation Resistance
# =====================================================================
def fig3_misinformation():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

    # Left: Truth vs Misinfo pie
    truth = misinfo.get('truth_win_rate', 0) * 100
    misinfo_rate = misinfo.get('misinformation_win_rate', 0) * 100
    sizes = [truth, misinfo_rate]
    labels_pie = [f'Truth Wins\n({truth:.0f}%)', f'Misinfo Wins\n({misinfo_rate:.0f}%)']
    colors_pie = ['#2ECC71', '#E74C3C']
    explode = (0.05, 0.05)

    wedges, texts, autotexts = ax1.pie(sizes, labels=labels_pie, colors=colors_pie,
                                        explode=explode, autopct='', startangle=90,
                                        textprops={'fontweight': 'bold', 'fontsize': 12},
                                        wedgeprops={'edgecolor': 'black', 'linewidth': 1.5})
    ax1.set_title('Misinformation Battle\nOutcomes (n=8)', fontweight='bold', fontsize=12)

    # Right: Role win rates
    roles = misinfo.get('bias_role_win_rates', {})
    if roles:
        role_names = list(roles.keys())
        role_vals = [roles[r] * 100 for r in role_names]
        role_colors = {'truth_teller': '#2ECC71', 'liar': '#E74C3C', 'manipulator': '#F39C12'}
        bar_colors = [role_colors.get(r, '#666') for r in role_names]
        role_labels = [r.replace('_', ' ').title() for r in role_names]

        bars = ax2.barh(range(len(role_names)), role_vals, color=bar_colors,
                        edgecolor='black', linewidth=1.2, height=0.5)
        ax2.set_yticks(range(len(role_names)))
        ax2.set_yticklabels(role_labels, fontweight='bold', fontsize=11)
        ax2.set_xlabel('Win Rate (%)', fontweight='bold')
        ax2.set_title('Win Rate by Agent Role', fontweight='bold', fontsize=12)
        ax2.set_xlim(0, 50)

        for bar, v in zip(bars, role_vals):
            ax2.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2.,
                    f'{v:.0f}%', ha='left', va='center', fontweight='bold', fontsize=11)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig3_misinformation.pdf")
    fig.savefig(FIG_DIR / "fig3_misinformation.png")
    plt.close()
    print("  Fig 3: Misinformation resistance")


# =====================================================================
# FIGURE 4: Behavioral DNA Radar Charts
# =====================================================================
def fig4_behavioral_dna():
    n_models = len(behavioral_dna)
    if n_models == 0:
        print("  Fig 4: SKIPPED (no DNA data)")
        return

    fig, axes = plt.subplots(1, n_models, figsize=(5 * n_models, 5),
                              subplot_kw=dict(polar=True))
    if n_models == 1:
        axes = [axes]

    dims = ['confidence', 'volatility', 'aggressiveness', 'escalation',
            'cooperation', 'novelty_retention', 'stubbornness', 'evidence_use',
            'verbosity', 'hedging']
    dim_labels = ['Confidence', 'Volatility', 'Aggression', 'Escalation',
                  'Cooperation', 'Novelty\nRetention', 'Stubbornness', 'Evidence\nUse',
                  'Verbosity', 'Hedging']

    model_colors = ['#3498DB', '#E74C3C', '#2ECC71']

    for i, dna in enumerate(behavioral_dna):
        ax = axes[i]
        norm = dna.get('dna_normalized', {})
        values = [norm.get(d, 0) * 100 for d in dims]
        values.append(values[0])  # Close the polygon

        angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
        angles.append(angles[0])

        ax.fill(angles, values, color=model_colors[i % len(model_colors)], alpha=0.25)
        ax.plot(angles, values, color=model_colors[i % len(model_colors)],
                linewidth=2.5, marker='o', markersize=5)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(dim_labels, fontsize=8, fontweight='bold')
        ax.set_ylim(0, 100)
        ax.set_yticks([25, 50, 75, 100])
        ax.set_yticklabels(['25', '50', '75', '100'], fontsize=7, alpha=0.6)

        model_name = dna['model_id'].split('/')[-1].replace(':free', '').replace('-versatile', '')
        archetype = dna.get('archetype', {}).get('name', '?')
        ax.set_title(f'{model_name}\n"{archetype}"', fontweight='bold',
                     fontsize=11, pad=20)

    fig.suptitle('Model Behavioral DNA Fingerprints', fontweight='bold', fontsize=14, y=1.05)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig4_behavioral_dna.pdf")
    fig.savefig(FIG_DIR / "fig4_behavioral_dna.png")
    plt.close()
    print("  Fig 4: Behavioral DNA radar charts")


# =====================================================================
# FIGURE 5: Argument Quality Over Rounds
# =====================================================================
def fig5_round_evolution():
    rounds = round_quality.get('rounds', [])
    if len(rounds) < 2:
        print("  Fig 5: SKIPPED (insufficient rounds)")
        return

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = [r['round'] for r in rounds]

    metrics_plot = [
        ('avg_novelty', 'Novelty', '#F39C12', 'o'),
        ('avg_aggressiveness', 'Aggressiveness', '#E74C3C', 's'),
        ('avg_confidence', 'Confidence', '#3498DB', '^'),
        ('avg_sentiment', 'Sentiment', '#2ECC71', 'D'),
    ]

    for key, label, color, marker in metrics_plot:
        vals = [r.get(key, 0) * 100 if key != 'avg_sentiment' else (r.get(key, 0) + 1) * 50
                for r in rounds]
        ax.plot(x, vals, color=color, linewidth=2.5, marker=marker, markersize=8,
                label=label, zorder=3)

    ax.set_xlabel('Round Number', fontweight='bold')
    ax.set_ylabel('Score (normalized %)', fontweight='bold')
    ax.set_title('Argument Quality Evolution Over Debate Rounds', fontweight='bold', pad=15)
    ax.legend(loc='best', framealpha=0.9)
    ax.set_xticks(x)

    fig.savefig(FIG_DIR / "fig5_round_evolution.pdf")
    fig.savefig(FIG_DIR / "fig5_round_evolution.png")
    plt.close()
    print("  Fig 5: Round evolution")


# =====================================================================
# FIGURE 6: Aggressiveness Heatmap (Model x Strategy)
# =====================================================================
def fig6_aggressiveness_heatmap():
    if not heatmap_data:
        print("  Fig 6: SKIPPED (no heatmap data)")
        return

    models = sorted(set(h['model_id'].split('/')[-1].replace(':free', '').replace('-versatile', '')
                       for h in heatmap_data))
    strategies = sorted(set(h['strategy'] for h in heatmap_data))

    matrix = np.zeros((len(models), len(strategies)))
    model_idx = {m: i for i, m in enumerate(models)}
    strat_idx = {s: i for i, s in enumerate(strategies)}

    for h in heatmap_data:
        m = h['model_id'].split('/')[-1].replace(':free', '').replace('-versatile', '')
        s = h['strategy']
        matrix[model_idx[m]][strat_idx[s]] = h.get('avg_aggressiveness', 0)

    fig, ax = plt.subplots(figsize=(8, 4))
    strat_labels = [STRATEGY_SHORT.get(s, s) for s in strategies]

    im = sns.heatmap(matrix, annot=True, fmt='.3f', cmap='YlOrRd',
                     xticklabels=strat_labels, yticklabels=models,
                     linewidths=2, linecolor='black',
                     cbar_kws={'label': 'Aggressiveness Score'},
                     ax=ax)

    ax.set_title('Aggressiveness Heatmap (Model x Strategy)', fontweight='bold', fontsize=13, pad=15)
    ax.set_xlabel('Strategy', fontweight='bold')
    ax.set_ylabel('Model', fontweight='bold')

    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig6_heatmap.pdf")
    fig.savefig(FIG_DIR / "fig6_heatmap.png")
    plt.close()
    print("  Fig 6: Aggressiveness heatmap")


# =====================================================================
# FIGURE 7: Effect Size Matrix
# =====================================================================
def fig7_effect_sizes():
    if not effect_sizes:
        print("  Fig 7: SKIPPED (no effect sizes)")
        return

    metrics_list = sorted(set(e['metric'] for e in effect_sizes))
    comparisons = sorted(set(e['strategy_1'] + ' vs ' + e['strategy_2'] for e in effect_sizes))

    matrix = np.zeros((len(metrics_list), len(comparisons)))
    metric_idx = {m: i for i, m in enumerate(metrics_list)}
    comp_idx = {c: i for i, c in enumerate(comparisons)}

    for e in effect_sizes:
        m = e['metric']
        c = e['strategy_1'] + ' vs ' + e['strategy_2']
        matrix[metric_idx[m]][comp_idx[c]] = abs(e['cohens_d'])

    fig, ax = plt.subplots(figsize=(10, 4))
    comp_labels = [c.replace('majority_voting', 'Vote').replace('structured_debate', 'Debate')
                   .replace('hierarchical', 'Hier.').replace('evidence_weighted', 'Evid.')
                   for c in comparisons]

    im = sns.heatmap(matrix, annot=True, fmt='.2f', cmap='RdYlGn_r',
                     xticklabels=comp_labels, yticklabels=metrics_list,
                     linewidths=1, linecolor='black',
                     cbar_kws={'label': "|Cohen's d|"},
                     vmin=0, vmax=1.5, ax=ax)

    ax.set_title("Cross-Strategy Effect Size Matrix (|Cohen's d|)", fontweight='bold', fontsize=13, pad=15)
    ax.set_xlabel('Strategy Comparison', fontweight='bold')

    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig7_effect_sizes.pdf")
    fig.savefig(FIG_DIR / "fig7_effect_sizes.png")
    plt.close()
    print("  Fig 7: Effect size matrix")


# =====================================================================
# FIGURE 8: Source Reliability Impact
# =====================================================================
def fig8_source_reliability():
    fig, ax = plt.subplots(figsize=(6, 4.5))

    win_rel = source_impact.get('avg_winning_source_reliability', 0)
    lose_rel = source_impact.get('avg_losing_source_reliability', 0)
    effect_d = source_impact.get('reliability_effect_size', 0)
    p_val = source_impact.get('reliability_ttest', {}).get('p_value', 1.0)

    bars = ax.bar(['Winning\nPositions', 'Losing\nPositions'],
                  [win_rel, lose_rel],
                  color=['#E74C3C', '#2ECC71'], edgecolor='black',
                  linewidth=1.5, width=0.5)

    for bar, v in zip(bars, [win_rel, lose_rel]):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.02,
                f'{v:.2f}', ha='center', va='bottom', fontweight='bold', fontsize=14)

    ax.set_ylabel('Avg Source Reliability Score', fontweight='bold')
    ax.set_title('Source Reliability of Winning vs Losing Positions', fontweight='bold', pad=15)
    ax.set_ylim(0, 1.0)

    # Add significance annotation
    sig_text = f"p = {p_val:.4f}{'***' if p_val < 0.001 else '**' if p_val < 0.01 else '*' if p_val < 0.05 else ' (ns)'}"
    ax.text(0.5, 0.85, sig_text, transform=ax.transAxes, ha='center',
            fontsize=12, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.8))
    ax.text(0.5, 0.76, f"|d| = {abs(effect_d):.2f} (large effect)", transform=ax.transAxes,
            ha='center', fontsize=10, fontstyle='italic')

    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig8_source_reliability.pdf")
    fig.savefig(FIG_DIR / "fig8_source_reliability.png")
    plt.close()
    print("  Fig 8: Source reliability impact")


# =====================================================================
# FIGURE 9: System Architecture Diagram (text-based)
# =====================================================================
def fig9_architecture():
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')

    box_style = dict(boxstyle='round,pad=0.4', facecolor='#ECF0F1', edgecolor='#2C3E50', linewidth=2)
    highlight_style = dict(boxstyle='round,pad=0.4', facecolor='#3498DB', edgecolor='#2C3E50', linewidth=2)
    strategy_style = dict(boxstyle='round,pad=0.3', facecolor='#E8DAEF', edgecolor='#8E44AD', linewidth=1.5)

    # Title
    ax.text(6, 7.5, 'System Architecture', ha='center', fontsize=16, fontweight='bold')

    # Top: Scenarios
    ax.text(2, 6.5, 'Scenario\nEngine', ha='center', va='center', fontsize=10, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#FADBD8', edgecolor='#E74C3C', linewidth=2))
    ax.text(2, 5.7, '43 scenarios\n4 categories', ha='center', fontsize=8, fontstyle='italic', color='#666')

    # LLM Providers
    ax.text(6, 6.5, 'LLM Provider\nLayer', ha='center', va='center', fontsize=10, fontweight='bold',
            bbox=highlight_style, color='white')
    ax.text(6, 5.7, 'Groq  |  Cerebras  |  OpenRouter\nRate limiting + Retry logic', ha='center', fontsize=8, color='#666')

    # Metrics
    ax.text(10, 6.5, 'Metrics\nCollector', ha='center', va='center', fontsize=10, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#D5F5E3', edgecolor='#27AE60', linewidth=2))
    ax.text(10, 5.7, '9 behavioral\ndimensions', ha='center', fontsize=8, fontstyle='italic', color='#666')

    # Middle: Strategies
    strategies_pos = [(1.5, 4), (4.5, 4), (7.5, 4), (10.5, 4)]
    strategy_names = ['Majority\nVoting', 'Structured\nDebate', 'Hierarchical\nAuthority', 'Evidence-\nWeighted']
    for (x, y), name in zip(strategies_pos, strategy_names):
        ax.text(x, y, name, ha='center', va='center', fontsize=9, fontweight='bold', bbox=strategy_style)

    ax.text(6, 4.8, 'LangGraph State Machine Orchestration', ha='center', fontsize=9,
            fontweight='bold', fontstyle='italic', color='#8E44AD')

    # Bottom: Agents
    agent_positions = [(2, 2.2), (6, 2.2), (10, 2.2)]
    agent_names = ['Agent Alpha\n(Groq 70B)', 'Agent Beta\n(Cerebras 8B)', 'Agent Gamma\n(Groq 8B)']
    for (x, y), name in zip(agent_positions, agent_names):
        ax.text(x, y, name, ha='center', va='center', fontsize=9, fontweight='bold', bbox=box_style)

    # DB + Analytics
    ax.text(6, 0.6, 'SQLite DB  |  Statistical Analysis  |  Behavioral DNA  |  Export Engine',
            ha='center', va='center', fontsize=9, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#FEF9E7', edgecolor='#F39C12', linewidth=2))

    # Arrows (simplified)
    arrow_props = dict(arrowstyle='->', lw=1.5, color='#2C3E50')
    for x in [2, 6, 10]:
        ax.annotate('', xy=(x, 2.8), xytext=(x, 3.4), arrowprops=arrow_props)
    for (x, _) in strategies_pos:
        ax.annotate('', xy=(x, 3.4), xytext=(x, 5.0), arrowprops=dict(arrowstyle='->', lw=1, color='#8E44AD'))
    ax.annotate('', xy=(6, 1.1), xytext=(6, 1.7), arrowprops=arrow_props)

    fig.savefig(FIG_DIR / "fig9_architecture.pdf")
    fig.savefig(FIG_DIR / "fig9_architecture.png")
    plt.close()
    print("  Fig 9: Architecture diagram")


# =====================================================================
# RUN ALL
# =====================================================================
if __name__ == '__main__':
    print("Generating publication figures...")
    fig1_strategy_accuracy()
    fig2_strategy_metrics()
    fig3_misinformation()
    fig4_behavioral_dna()
    fig5_round_evolution()
    fig6_aggressiveness_heatmap()
    fig7_effect_sizes()
    fig8_source_reliability()
    fig9_architecture()
    print(f"\nAll figures saved to {FIG_DIR}/")
    print(f"Files: {[f.name for f in FIG_DIR.glob('*.png')]}")
