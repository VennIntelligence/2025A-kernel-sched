# %% [markdown]
# ## E14 — Optimal Oracle (CP-SAT): Theorem 1 and Theorem 3 Validation
# On small capacity-bound graphs (<= 30 nodes) we compute exact capacity-only
# optima with CP-SAT and use them to (i) measure our heuristic's optimality gap
# *for the order it selects* and (ii) empirically check the two theorems.
#
# **Left (Theorem 3).** Scatter of overflow area `A(S)` against the capacity-only
# optimal extra `E*(S)`; the shaded band is the empirical area-extra ratio
# `E*/A in [0.56, 1.13]`, i.e. a tight constant factor exactly as Theorem~3
# predicts under bounded absence length.
# **Right (Theorem 1).** Per instance, the certificate lower bound `lb_T1`
# against the achieved extra. The bound holds on every instance, and the achieved
# extra equals the per-order capacity-only optimum (`gap_real_vs_fixed = 1`): the
# frozen engine is optimal *given the order*, so the residual lever is the order.
#
# **Honesty.** The joint optimum over all orders (M3) is `SKIPPED`, so we do *not*
# claim a gap to the global optimum — only per-order optimality plus the two
# theorem bounds.

# %%
import numpy as np

oracle = pd.read_csv(RESULTS / "e14_oracle.csv")

fig, axes = make_figure("double_col", ncols=2, height=3.05)
axS, axB = axes

A = oracle["A_ours"].to_numpy(dtype=float)
E = oracle["ours_order_extra_caponly"].to_numpy(dtype=float)
caches = oracle["bound_cache"].to_numpy()

lo, hi = 0.5641, 1.1282
xs = np.array([0.0, A.max() * 1.12])
axS.fill_between(xs, lo * xs, hi * xs, color="#cccccc", alpha=0.30, zorder=0,
                 label=r"Thm 3 band $[0.56,1.13]\cdot A$")
axS.plot(xs, lo * xs, ls="--", color="#888888", lw=0.9, zorder=1)
axS.plot(xs, hi * xs, ls="-.", color="#555555", lw=0.9, zorder=1)
cache_color = {"UB": METHOD_PALETTE["primary"], "L0C": METHOD_PALETTE["secondary"]}
for cache in ["UB", "L0C"]:
    m = caches == cache
    if m.any():
        axS.scatter(A[m], E[m], s=55, color=cache_color[cache], marker="o",
                    edgecolors="#222222", linewidth=0.5, alpha=0.85, zorder=3,
                    label=f"bound = {cache}")
axS.set_xlabel("Overflow area $A(S)$")
axS.set_ylabel("Capacity-only optimal extra $E^\\star(S)$")
axS.set_title("(a) Area--extra band")
axS.set_xlim(left=0)
axS.set_ylim(bottom=0)
axS.set_box_aspect(1)
axS.legend(loc="upper left", frameon=True, facecolor="white",
           framealpha=0.92, edgecolor="#bbbbbb")
axS.grid(alpha=0.3)

n = len(oracle)
x = np.arange(n)
wb = 0.40
axB.bar(x - wb / 2, oracle["lb_T1"], width=wb, color=METHOD_PALETTE["neutral"],
        edgecolor="#333333", linewidth=0.4, label="Theorem 1 lower bound")
axB.bar(x + wb / 2, oracle["ours_real_extra"], width=wb, color=METHOD_PALETTE["primary"],
        edgecolor="#333333", linewidth=0.4, label="Ours (= per-order optimum)")
axB.set_xticks(x)
axB.set_xticklabels([str(i) for i in range(n)])
axB.set_xlabel("Oracle instance")
axB.set_ylabel("Extra")
axB.set_title("(b) Lower bound vs achieved")
axB.set_box_aspect(1)
axB.legend(loc="upper left", frameon=True, facecolor="white",
           framealpha=0.92, edgecolor="#bbbbbb")
axB.grid(axis="y", alpha=0.3)
fig.tight_layout(w_pad=1.2)
save_fig(fig, "e14_oracle.png")
fig

# %%
summary14 = pd.DataFrame({
    "metric": ["instances", "all ratio_Wstar > 1 (capacity-bound)",
               "Thm1 bound holds (E* >= lb_T1)", "ratio E*/A range",
               "gap_real_vs_fixed (median)", "joint status"],
    "value": [n,
              bool((oracle["ratio_Wstar"] > 1).all()),
              bool((oracle["ours_order_extra_caponly"] >= oracle["lb_T1"]).all()),
              f"[{oracle['ratio_E_over_A'].min():.3f}, {oracle['ratio_E_over_A'].max():.3f}]",
              round(float(oracle["gap_real_vs_fixed"].median()), 3),
              oracle["joint_status"].iloc[0]],
})
display(summary14)

# %% [markdown]
# Every oracle instance is genuinely capacity-bound (`ratio_Wstar = 1.375 > 1`),
# the Theorem~1 lower bound holds on all of them, and the area-extra ratio stays
# inside a narrow `[0.56, 1.13]` band, validating Theorem~3's constant-factor
# claim. `gap_real_vs_fixed = 1` shows the spill engine reaches the capacity-only
# optimum for the chosen order; the remaining freedom is the schedule order, in
# line with the E2/E13 evidence. Source: `results/paper/e14_oracle.csv`.
