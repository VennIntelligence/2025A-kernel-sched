# %% [markdown]
# ## E8 — Prefetch selection/placement decoupling
# This sweep varies the prefetch window while holding the victim policy fixed,
# exposing whether placement timing can improve P3 latency independently of the
# order selected to shape liveness.

# %%
prefetch = pd.read_csv(RESULTS / "e8_prefetch.csv")
valid_prefetch = prefetch[(prefetch["time"] >= 0) & (prefetch["extra"] >= 0)].copy()

case_order = [
    "Conv_Case0",
    "Conv_Case1",
    "FlashAttention_Case0",
    "FlashAttention_Case1",
    "Matmul_Case0",
    "Matmul_Case1",
]
order_scores = valid_prefetch.groupby(["case", "order"], as_index=False)["time"].min()
selected_orders = (
    order_scores.sort_values(["case", "time", "order"])
    .drop_duplicates("case")
    .set_index("case")["order"]
)
assert set(selected_orders.index) == set(case_order)

fig, axes = make_figure("double_col", ncols=2, height=3.05)
for idx, case in enumerate(case_order):
    order = selected_orders.loc[case]
    curve = valid_prefetch[
        (valid_prefetch["case"] == case) & (valid_prefetch["order"] == order)
    ].sort_values("H")
    style = get_method_style(idx)
    label = case.replace("FlashAttention_Case", "FA ").replace("_Case", " ")
    axes[0].plot(curve["H"], curve["time"], label=label, **style)
    axes[1].plot(curve["H"], curve["extra"], label=label, **style)

axes[0].set_xlabel("Prefetch window H")
axes[0].set_ylabel("P3 time [cycles]")
axes[0].set_title("(a) Time")
axes[1].set_xlabel("Prefetch window H")
axes[1].set_ylabel("Extra DDR traffic")
axes[1].set_title("(b) Extra")
for ax in axes:
    ax.grid(True, alpha=0.25)
    ax.set_box_aspect(1)

handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, -0.08),
           ncol=6, frameon=False, columnspacing=0.9, handletextpad=0.35)
fig.tight_layout(rect=[0.0, 0.11, 1.0, 1.0], w_pad=1.2)
save_fig(fig, "e8_decoupling.png")

# %% [markdown]
# Each line uses the order whose sweep attains the lowest P3 time for that
# case. The left panel shows that several cases prefer a nonzero prefetch
# window, while the right panel tracks the corresponding DDR traffic. The
# pattern supports selection/placement decoupling: order selection controls the
# liveness shape, and prefetch placement can trade additional traffic for lower
# latency without changing the chosen order family.
