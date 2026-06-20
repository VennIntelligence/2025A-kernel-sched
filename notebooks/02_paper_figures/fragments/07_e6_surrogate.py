# %% [markdown]
# ## E6 — Surrogate Signals for P2 Extra Traffic
# This figure compares two cheap surrogate signals for downstream P2 extra traffic: the lifetime-aware overflow integral $\Phi$ and a peak-over-capacity measure that only captures instantaneous pressure.

# %%
surrogate = pd.read_csv(RESULTS / "e6_surrogate.csv")
corr = pd.read_csv(RESULTS / "e6_corr.csv")
global_corr = corr.loc[corr["case"] == "ALL"].iloc[0]

fig, axes = make_figure("double_col", ncols=2, height=3.05)
ax_phi, ax_peak = axes
for idx, (case, group) in enumerate(surrogate.groupby("case", sort=True)):
    style = get_method_style(idx)
    label = case.replace("FlashAttention_Case", "FA ").replace("_Case", " ")
    scatter_kw = {
        "s": 62,
        "alpha": 0.86,
        "color": style["color"],
        "marker": style["marker"],
        "edgecolors": "white",
        "linewidths": 0.55,
        "label": label,
    }
    ax_phi.scatter(group["phi"], group["extra_p2"], **scatter_kw)
    ax_peak.scatter(group["peak_over"], group["extra_p2"], **scatter_kw)

rho_phi = global_corr["spearman_phi_extra"]
rho_peak = global_corr["spearman_peak_extra"]
ax_phi.set_title(f"(a) Overflow integral $\\Phi$  ($\\rho={rho_phi:.3f}$)")
ax_phi.set_xlabel("Capacity-overflow integral $\\Phi$")
ax_phi.set_ylabel("P2 extra DDR traffic")
ax_peak.set_title(f"(b) Peak over-capacity  ($\\rho={rho_peak:.3f}$)")
ax_peak.set_xlabel("Peak over-capacity")
ax_peak.set_ylabel("P2 extra DDR traffic")
for ax in axes:
    ax.margins(x=0.08, y=0.08)
    ax.set_box_aspect(1)
handles, labels = ax_phi.get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.08),
           ncol=6, frameon=False, columnspacing=0.9, handletextpad=0.35)
fig.tight_layout(rect=[0.0, 0.11, 1.0, 1.0], w_pad=1.2)
save_fig(fig, "e6_surrogate.png")

# %% [markdown]
# The left panel uses cumulative pressure over the full allocation/free timeline, while the right panel measures only the worst instantaneous over-capacity point. The near-identical global coefficients make this a comparison of two practical proxy signals rather than evidence of a material predictive gap.

# %%
display(corr)
case_corr = corr.loc[corr["case"] != "ALL"]
phi_gt_peak = (case_corr["spearman_phi_extra"] > case_corr["spearman_peak_extra"]).sum()
phi_tie_peak = (case_corr["spearman_phi_extra"] == case_corr["spearman_peak_extra"]).sum()
phi_lt_peak = (case_corr["spearman_phi_extra"] < case_corr["spearman_peak_extra"]).sum()
print(f"per-case: phi>peak in {phi_gt_peak}, tie in {phi_tie_peak}, phi<peak in {phi_lt_peak}")

# %% [markdown]
# Globally, $\Phi$ and peak over-capacity are almost identical as Spearman predictors of P2 extra traffic (0.957 vs 0.955), so the difference is not evidence that $\Phi$ is significantly better. Per case, $\Phi$ is not uniformly dominant: phi>peak in 3 cases, tie in 1, and phi<peak in 2. Its value is instead methodological: it is a cheap, lifetime-aware proxy that can be shared with the differentiable stage and makes the portfolio's official-key take-min selection inexpensive, supporting contribution M rather than serving as an independent claim that it outpredicts peak pressure.
