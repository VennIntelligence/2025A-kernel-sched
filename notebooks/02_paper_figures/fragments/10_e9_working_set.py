# %% [markdown]
# ## E9 — Constrained Working-Set Lower Bound
# This panel compares the smallest observed peak working set against cache
# capacity after restricting the order set to schedules with near-optimal spill
# extra cost.

# %%
import numpy as np

e9 = pd.read_csv(RESULTS / "e9_working_set.csv")
e9_display = e9.sort_values(["case", "cache"]).copy()
with pd.option_context("display.max_rows", None, "display.max_columns", None):
    display(e9_display)

# Focus on the (case, cache) pairs that are ever capacity-bound: that is where
# the certificate D bites. For each we contrast the unconstrained min-over-all
# orders (ratio_all) against the near-optimal-extra restricted bound
# (ratio_nearopt) -- the gap is exactly the methodological pitfall the paper
# warns about (an unconstrained min can falsely look capacity-safe).
bound = e9_display[e9_display["bound_class"] == "capacity_bound"].copy()
bound = bound.sort_values("ratio_nearopt").reset_index(drop=True)
bound["label"] = bound.apply(lambda r: f"{case_label(r['case'])}\n{r['cache']}", axis=1)

x = np.arange(len(bound))
w = 0.32
is_headline = (bound["case"] == "Matmul_Case1") & (bound["cache"] == "L1")

fig, ax = make_figure("double_col", height=4.05)
bars_all = ax.bar(
    x - w / 2,
    bound["ratio_all"],
    width=w,
    color=ORDER_COLORS["ratio_all"],
    edgecolor="#333333",
    linewidth=0.35,
    label=ORDER_LABELS["ratio_all"],
)
bars_near = ax.bar(
    x + w / 2,
    bound["ratio_nearopt"],
    width=w,
    color=ORDER_COLORS["ratio_nearopt"],
    edgecolor="#333333",
    linewidth=0.35,
    label=ORDER_LABELS["ratio_nearopt"],
)
annotate_bars(ax, bars_all, bound["ratio_all"], formatter=compact_ratio, fontsize=7.6)
annotate_bars(ax, bars_near, bound["ratio_nearopt"], formatter=compact_ratio, fontsize=7.6)
add_reference_line(ax, 1.0, "capacity", axis="y")
ax.set_yscale("log")
style_bar_axes(ax, xlabel="Benchmark case / cache", ylabel="Min working set / capacity")
ax.set_xticks(x)
ax.set_xticklabels(bound["label"])
ax.set_ylim(0.02, max(bound["ratio_nearopt"].max(), bound["ratio_all"].max()) * 2.25)
place_bar_legend(ax, ncol=3)

# Call out the headline misjudgment: 0.031 (looks safe) vs 8.5 (bound).
hi = int(np.where(is_headline.to_numpy())[0][0])
ax.annotate("0.03x looks safe,\nbut 8.5x near-optimal",
            xy=(hi + w / 2, bound["ratio_nearopt"].iloc[hi]),
            xytext=(hi - 1.7, 11.0),
            arrowprops=dict(arrowstyle="->", color="#333333", lw=0.8),
            ha="left", va="top")
save_fig(fig, "e9_working_set.png")
fig

# %% [markdown]
# **Read.** For every capacity-bound `(case, cache)`, the grey bar is the working
# set minimised over *all* orders and the coloured bar is the same quantity
# restricted to near-optimal-extra orders; the dashed line is capacity (ratio 1).
# Log scale.
# **Pattern.** The two Matmul L1 entries (and FA1 L1) collapse to ~0.03 under the
# unconstrained min -- a schedule that is catastrophic for P2 but has a tiny peak
# pollutes the bound. Under the near-optimal restriction the same caches sit far
# above capacity (Matmul C1/L1 = 8.5, highlighted).
# **Takeaway.** The certificate D must be evaluated inside the near-optimal-extra
# subset; there it soundly proves reordering cannot avoid overflow. Conv C1/L1
# also exceeds capacity but its peak is mostly clean (rematerializable), so the
# excess is cost-recoverable rather than infeasible.
