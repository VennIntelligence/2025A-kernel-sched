# %% [markdown]
# ## E15 — Applicability across regimes
#
# Compact conference figure summarising how the promoted solver compares to the
# literature baselines on the synthetic suite, split by regime: *capacity-bound*
# instances (on-chip pressure forces spills) versus *order-reachable* instances
# (a legal order alone can avoid most spills). Panel (a) is the win rate; panel
# (b) is the median extra-traffic ratio (ours / comparator; below 1.0 is better).

# %%
e15 = pd.read_csv(RESULTS / "e13_summary.csv")

COMPARATORS = [
    ("cp_list", "CP"),
    ("cp_free_first", "CP-free"),
    ("pressure_uniform", "Pressure"),
    ("goodman_hsu", "G-Hsu"),
    ("random_best", "Random"),
]
REGIMES = [
    ("capacity_bound", "Capacity-bound"),
    ("order_reachable", "Order-reachable"),
]

df = e15[e15["comparator"].isin([n for n, _ in COMPARATORS])]
df = df[df["regime"].isin([n for n, _ in REGIMES])]

fig, axes = make_figure("double_col", nrows=1, ncols=2, height=2.35)
ax_win, ax_ratio = axes

colors = {"capacity_bound": METHOD_PALETTE["primary"], "order_reachable": METHOD_PALETTE["secondary"]}
bar_w = 0.34
x = list(range(len(COMPARATORS)))

for offset, (regime, label) in zip(grouped_offsets(len(REGIMES), bar_w), REGIMES):
    subset = df[df["regime"] == regime].set_index("comparator")
    win = [subset.loc[n, "ours_win_rate"] * 100 for n, _ in COMPARATORS]
    ratio = [subset.loc[n, "median_ours_over_comparator_extra"] for n, _ in COMPARATORS]
    ax_win.bar([i + offset for i in x], win, width=bar_w, label=label, color=colors[regime], edgecolor="black", linewidth=0.4)
    ax_ratio.bar([i + offset for i in x], ratio, width=bar_w, label=label, color=colors[regime], edgecolor="black", linewidth=0.4)

tick_labels = [label for _, label in COMPARATORS]
for ax in axes:
    ax.set_xticks(x)
    ax.set_xticklabels(tick_labels, rotation=20, ha="right")
    ax.grid(axis="y", color="#cccccc", linewidth=0.5, alpha=0.45)
    ax.set_axisbelow(True)

ax_win.set_title("(a) Win rate")
ax_win.set_ylabel("Ours wins [%]")
ax_win.set_ylim(0, 105)
ax_win.set_yticks([0, 25, 50, 75, 100])

ax_ratio.set_title("(b) Extra traffic ratio")
ax_ratio.set_ylabel("Median ours / comparator")
ax_ratio.set_ylim(0, 1.08)
ax_ratio.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
ax_ratio.axhline(1.0, color="#555555", linestyle="--", linewidth=0.8)
ax_ratio.text(len(COMPARATORS) - 0.54, 1.0, "tie", va="bottom", ha="right", color="#555555", fontsize=8)

handles, labels = ax_win.get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.05))
save_fig(fig, "e15_applicability.png")
fig

# %% [markdown]
# **Read.** Across both regimes the promoted solver wins the large majority of
# pairwise comparisons and never exceeds parity on median extra traffic. The
# margin is largest on capacity-bound instances, where liveness shaping has the
# most room to convert dirty residency into avoidable spills — exactly the
# setting the method targets.
