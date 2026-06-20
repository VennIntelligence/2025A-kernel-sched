# %% [markdown]
# ## E7 — Objective mismatch in P1 residency
# This table compares the lexicographic P1 order with the best low-overflow
# order among the promoted candidates. The key signal is whether peak residency
# exceeds the physical capacity that P2/P3 must satisfy.

# %%
import numpy as np

e7 = pd.read_csv(RESULTS / "e7_misalign.csv")

def highlight_capacity_excess(data):
    styles = pd.DataFrame("", index=data.index, columns=data.columns)
    styles.loc[data["max_UB"] > 1024, "max_UB"] = "background-color: #f6c1bf"
    styles.loc[data["max_L1"] > 4096, "max_L1"] = "background-color: #f6c1bf"
    return styles

display(
    e7.style
    .apply(highlight_capacity_excess, axis=None)
    .format({"worst_over_ratio": "{:.2f}"})
)

# %% [markdown]
# The P1 order optimizes a lexicographic peak-residency objective, but some of
# its cache peaks are far above the capacities that the spill planner must obey.
# The low-overflow candidate has lower worst resident-to-capacity pressure.

# %%
pivot = e7.pivot(index="case", columns="order_kind", values="worst_over_ratio")
case_order = e7["case"].drop_duplicates()
pivot = pivot.reindex(case_order)[["p1", "phi_best"]]

fig, ax = make_figure("double_col", height=3.55)
x = np.arange(len(pivot))
width = 0.32
bars_p1 = ax.bar(
    x - width / 2,
    pivot["p1"],
    width,
    label=ORDER_LABELS["p1"],
    color=ORDER_COLORS["p1"],
    edgecolor="#333333",
    linewidth=0.35,
)
bars_phi = ax.bar(
    x + width / 2,
    pivot["phi_best"],
    width,
    label=ORDER_LABELS["phi_best"],
    color=ORDER_COLORS["phi_best"],
    edgecolor="#333333",
    linewidth=0.35,
)
annotate_bars(ax, bars_p1, pivot["p1"], formatter=compact_ratio, fontsize=7.6)
annotate_bars(ax, bars_phi, pivot["phi_best"], formatter=compact_ratio, fontsize=7.6)
add_reference_line(ax, 1.0, "capacity")
style_bar_axes(ax, ylabel="Worst residency / capacity")
ax.set_xticks(x, [case_label(c) for c in pivot.index], rotation=0)
ax.set_ylim(0, max(pivot.max()) * 1.22)
place_bar_legend(ax, ncol=3)
save_fig(fig, "e7_misalignment_worst_ratio.png")

# %% [markdown]
# The bar chart normalizes the worst cache-residency peak by its capacity. A
# value above one means the raw order cannot fit without spilling; the gap shows
# why the low-overflow ordering is a better input to the P2/P3 memory planner.
