# %% [markdown]
# ## E13 — Synthetic Suite: Distribution and Regime Split
# To move from six anecdotal cases to a distribution, we run the same orders on a
# parameterised synthetic suite (36 instances), split into two regimes by whether
# any order can avoid the overflow: `capacity_bound` (spill is forced) vs
# `order_reachable` (a good order reaches zero extra).
#
# **Left (distribution).** Per-instance extra ratio `ours / comparator`; values
# below the dashed tie line favour ours.
# **Right (scope).** Ours' win-rate by regime.
#
# **Honest reading.** Ours' advantage concentrates in the `capacity_bound`
# regime — exactly the regime the certificate (D, Theorem~1) identifies. On
# `order_reachable` instances a simple allocator-friendly or uniform-pressure
# order already reaches zero extra, so clean/dirty shaping has nothing to do.

# %%
import numpy as np
import matplotlib.pyplot as plt

suite = pd.read_csv(RESULTS / "e13_suite.csv")
summary = pd.read_csv(RESULTS / "e13_summary.csv")

comparators = ["cp_list", "cp_free_first", "pressure_uniform", "goodman_hsu", "random_best"]
comp_labels = ["Critical-path", "Delayed-free", "Uniform pressure", "Goodman--Hsu", "Random best"]
regimes = ["capacity_bound", "order_reachable"]
regime_color = {"capacity_bound": METHOD_PALETTE["primary"],
                "order_reachable": METHOD_PALETTE["accent_3"]}
regime_labels = {
    "capacity_bound": "Capacity-bound",
    "order_reachable": "Order-reachable",
}

ratios = {(c, rg): [] for c in comparators for rg in regimes}
for inst_id, g in suite.groupby("inst_id"):
    regime = g["regime"].iloc[0]
    om = g[g["order"] == "ours"]["extra"]
    if om.empty:
        continue
    ours = float(om.iloc[0])
    randoms = g[g["order"].str.startswith("random:")]["extra"]
    for c in comparators:
        if c == "random_best":
            comp = float(randoms.min()) if not randoms.empty else np.nan
        else:
            cv = g[g["order"] == c]["extra"]
            comp = float(cv.iloc[0]) if not cv.empty else np.nan
        if np.isnan(comp):
            continue
        if comp == 0:
            ratio = 1.0 if ours == 0 else np.nan
        else:
            ratio = ours / comp
        if not np.isnan(ratio):
            ratios[(c, regime)].append(ratio)

fig, axes = make_figure("double_col", ncols=2, height=2.75)
axL, axR = axes

box_w = 0.34
positions, data, colors = [], [], []
for i, c in enumerate(comparators):
    for j, rg in enumerate(regimes):
        positions.append(i + (j - 0.5) * (box_w + 0.04))
        vals = ratios[(c, rg)]
        data.append(vals if vals else [np.nan])
        colors.append(regime_color[rg])

bp = axL.boxplot(data, positions=positions, widths=box_w, patch_artist=True,
                 showfliers=False, medianprops=dict(color="#222222", linewidth=1.1))
for patch, color in zip(bp["boxes"], colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.65)
    patch.set_edgecolor("#333333")
    patch.set_linewidth(0.5)
add_reference_line(axL, 1.0, "tie (ratio = 1)")
axL.set_xticks(range(len(comparators)))
axL.set_xticklabels(comp_labels, rotation=22, ha="right")
axL.set_ylabel("Extra ratio (ours / comparator)")
axL.set_ylim(0, 1.05)
axL.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
axL.set_title("(a) Per-instance distribution")
axL.grid(axis="y", alpha=0.22, which="major", linewidth=0.5)
proxies = [plt.Rectangle((0, 0), 1, 1, fc=regime_color[rg], alpha=0.65) for rg in regimes]

x = np.arange(len(comparators))
wb = 0.38
for j, rg in enumerate(regimes):
    vals = [summary[(summary.comparator == c) & (summary.regime == rg)]["ours_win_rate"].iloc[0] * 100
            for c in comparators]
    axR.bar(x + (j - 0.5) * wb, vals, width=wb, color=regime_color[rg], alpha=0.85,
            edgecolor="#333333", linewidth=0.4, label=regime_labels[rg])
add_reference_line(axR, 50.0, "50%")
axR.set_xticks(x)
axR.set_xticklabels(comp_labels, rotation=22, ha="right")
axR.set_ylabel("Ours win-rate (%)")
axR.set_ylim(0, 100)
axR.set_yticks([0, 25, 50, 75, 100])
axR.set_title("(b) Win-rate by regime")
axR.grid(axis="y", alpha=0.22, which="major", linewidth=0.5)
axR.text(0.98, 50, "50%", transform=axR.get_yaxis_transform(),
         ha="right", va="bottom", color="#666666")
fig.legend(proxies, [regime_labels[rg] for rg in regimes],
           loc="upper center", bbox_to_anchor=(0.5, 0.995), ncol=2)
fig.tight_layout(rect=[0.0, 0.0, 1.0, 0.9])
save_fig(fig, "e13_synth_suite.png")
fig

# %%
display(summary[summary.regime != "all"][
    ["comparator", "regime", "n_instances",
     "median_ours_over_comparator_extra", "ours_win_rate"]])

# %% [markdown]
# On `capacity_bound` instances ours dominates the latency-only, random, and
# uniform-pressure baselines (median ratio well below 1, win-rate up to 100%) and
# keeps a 2x median edge over `cp_free_first`. On `order_reachable` instances the
# ratios sit at 1 and the win-rate collapses (0% vs `cp_free_first`): when a good
# order trivially avoids the overflow, clean/dirty shaping adds nothing. This
# regime split is the empirical face of the spill-inevitability certificate.
# Source: `results/paper/e13_suite.csv`, `results/paper/e13_summary.csv`.
