# %% [markdown]
# ## E11 — C1 Generality on a Synthetic Capacity-Bound Kernel
# To show that spill-cost-aware liveness shaping (C1) is not a Conv_Case0
# artifact, we build a synthetic GEMM-style accumulation kernel with a different
# tile geometry (512 B / 256 B). Its L1 working set exceeds capacity under every
# schedule (mandatory overflow, like Matmul_Case1), so the only lever left is the
# *cost* of the unavoidable spills — exactly what C1 governs.
#
# **Left (controlled ablation).** The same DAG structure with the reserve loaded
# via `COPY_IN` (clean) vs produced by a compute op (dirty). For a fixed schedule
# the spill *count* and peak residency are identical, yet extra DDR traffic
# doubles for the dirty reserve — isolating clean/dirty asymmetry as the cause.
#
# **Right (order sweep, clean instance).** Scheduler orders that keep the clean
# reserve resident at the overflow window pay an order of magnitude less than
# naive / random topological orders, and extra falls as clean residency at the
# peak rises.

# %%
import numpy as np

abl = pd.read_csv(RESULTS / "e11_synth_ablation.csv")
sweep = pd.read_csv(RESULTS / "e11_synth_orders.csv")

orders = ["capfit_id", "p1", "id_raw", "min_id"]
abl["order"] = pd.Categorical(abl["order"], categories=orders, ordered=True)
abl = abl.sort_values(["order", "reserve"])

fig, axes = make_figure("double_col", ncols=2, height=3.05)
ax_abl, ax_sweep = axes

x = np.arange(len(orders))
w = 0.36
clean_extra = [abl[(abl.order == o) & (abl.reserve == "clean")]["extra"].iloc[0] for o in orders]
dirty_extra = [abl[(abl.order == o) & (abl.reserve == "dirty")]["extra"].iloc[0] for o in orders]
ax_abl.bar(x - w / 2, clean_extra, width=w, color=METHOD_PALETTE["secondary"],
           edgecolor="#444444", linewidth=0.4, label="Clean reserve (COPY_IN)")
ax_abl.bar(x + w / 2, dirty_extra, width=w, color=METHOD_PALETTE["accent_1"],
           edgecolor="#444444", linewidth=0.4, label="Dirty reserve")
ax_abl.set_xticks(x)
ax_abl.set_xticklabels(orders, rotation=30, ha="right")
ax_abl.set_ylabel("Extra DDR traffic")
ax_abl.set_xlabel("Schedule order")
ax_abl.set_title("(a) Controlled ablation")
ax_abl.set_box_aspect(1)
ax_abl.legend(loc="upper left", frameon=True, facecolor="white",
              framealpha=0.92, edgecolor="#bbbbbb")
ax_abl.grid(axis="y", alpha=0.3)

for family, color, marker in (("random", METHOD_PALETTE["neutral"], "o"),
                              ("scheduler", METHOD_PALETTE["primary"], "D")):
    grp = sweep[sweep.family == family]
    ax_sweep.scatter(grp["clean_frac_at_peak"], grp["extra"], s=58, alpha=0.86,
                     color=color, marker=marker, edgecolors="none", label=family)
ax_sweep.set_xlabel("Clean fraction of L1 residency at peak")
ax_sweep.set_ylabel("Extra DDR traffic")
ax_sweep.set_title("(b) Order sweep")
ax_sweep.set_box_aspect(1)
ax_sweep.legend(loc="upper right", frameon=True, facecolor="white",
                framealpha=0.92, edgecolor="#bbbbbb")
ax_sweep.grid(alpha=0.3)

fig.tight_layout(w_pad=1.2)
save_fig(fig, "e11_synth_generality.png")

# %%
min_peak = int(sweep["peak_total"].min())
cap = 4096
summary = pd.DataFrame({
    "metric": ["clean capfit_id extra", "dirty capfit_id extra",
               "min working set (bytes)", "L1 capacity", "min peak / capacity",
               "best scheduler extra", "best random extra"],
    "value": [int(abl[(abl.order == "capfit_id") & (abl.reserve == "clean")]["extra"].iloc[0]),
              int(abl[(abl.order == "capfit_id") & (abl.reserve == "dirty")]["extra"].iloc[0]),
              min_peak, cap, round(min_peak / cap, 4),
              int(sweep[sweep.family == "scheduler"]["extra"].min()),
              int(sweep[sweep.family == "random"]["extra"].min())],
})
display(summary)

# %% [markdown]
# The kernel is genuinely capacity-bound (min working set / capacity > 1, so no
# order avoids the overflow), yet extra DDR traffic ranges over an order of
# magnitude. The doubling in the ablation confirms the mechanism is the
# clean/dirty cost gradient — not the spill count or the peak — and the sweep
# shows our generic scheduler orders land in the cheap, clean-reserve regime on a
# workload outside the six contest cases. This is direct generality evidence for
# C1 and complements the working-set criterion D from E9.
