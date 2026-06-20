# %% [markdown]
# ## E3 Order Sensitivity
# This figure compares P2 extra DDR traffic across schedule orders while holding
# the eviction policy fixed at `dist_size_cost`.

# %%
e2_order = pd.read_csv(RESULTS / "e2_victim_order.csv")
e1_headline = pd.read_csv(RESULTS / "e1_headline.csv")
e2_cv = pd.read_csv(RESULTS / "e2_victim_cv.csv")

orders = ["capfit_id", "p1", "id_raw", "min_id", "baseline"]
cases = CASE_ORDER

plot_data = e2_order[e2_order["victim"].eq("dist_size_cost")].copy()
plot_data["case"] = pd.Categorical(plot_data["case"], categories=cases, ordered=True)
plot_data["order"] = pd.Categorical(plot_data["order"], categories=orders, ordered=True)
baseline_extra = (
    e1_headline[e1_headline["problem"].eq(2)]
    .set_index("case")
    .reindex(cases)["base_extra"]
)

case_pos = {case: i for i, case in enumerate(cases)}
order_pos = {order: i for i, order in enumerate(orders)}
bar_width = 0.16

fig, ax = make_figure("double_col", height=3.6)
all_vals = []
for i, order in enumerate(orders):
    subset = plot_data[plot_data["order"].eq(order)].sort_values("case")
    xs = [
        case_pos[case] + (order_pos[order] - (len(orders) - 1) / 2) * bar_width
        for case in subset["case"].astype(str)
    ]
    bars = ax.bar(
        xs,
        subset["extra"],
        width=bar_width,
        label=ORDER_LABELS[order],
        color=ORDER_COLORS[order],
        edgecolor="#333333",
        linewidth=0.35,
    )
    all_vals.extend(subset["extra"].to_list())
    annotate_bars(ax, bars, subset["extra"], fontsize=7.3)

for x, value in enumerate(baseline_extra):
    ax.hlines(
        value,
        x - 0.46,
        x + 0.46,
        colors="#222222",
        linestyles="--",
        linewidth=0.9,
        label="P2 baseline (E1)" if x == 0 else None,
    )

ax.set_yscale("log")
style_bar_axes(ax, ylabel="P2 extra DDR traffic (log scale)")
ax.set_xticks(range(len(cases)))
ax.set_xticklabels([case_label(c) for c in cases])
ax.set_ylim(max(1, min(all_vals) * 0.65), max(all_vals) * 2.15)
place_bar_legend(ax, ncol=3)
fig = save_fig(fig, "e3_order_sensitivity.png")
fig

# %% [markdown]
# The ratio table compares each case's order-induced extra range against the
# largest victim-policy range from E2; at least one case should exceed 10x.

# %%
order_ranges = plot_data.groupby("case", observed=True)["extra"].agg(
    order_extra_min="min",
    order_extra_max="max",
)
order_ranges["order_range"] = (
    order_ranges["order_extra_max"] - order_ranges["order_extra_min"]
)
victim_ranges = (
    e2_cv.assign(victim_range=e2_cv["extra_max"] - e2_cv["extra_min"])
    .groupby("case")["victim_range"]
    .max()
)
ratio_table = order_ranges.join(victim_ranges).reset_index()
ratio_table["order_vs_victim_range"] = ratio_table.apply(
    lambda row: float("inf")
    if row["victim_range"] == 0 and row["order_range"] > 0
    else row["order_range"] / row["victim_range"],
    axis=1,
)
display(ratio_table)

if (ratio_table["order_vs_victim_range"] > 10).any():
    strongest = ratio_table.loc[ratio_table["order_vs_victim_range"].idxmax()]
    print(
        "T3 ratio check passed: "
        f"{strongest['case']} order range is "
        f"{strongest['order_vs_victim_range']:.2f}x the victim-policy range."
    )
else:
    print("ASSERTION FAILED T3: no case has order range > 10x victim-policy range.")

# %% [markdown]
# The grouped bars show that changing the schedule order produces much larger
# swings in extra traffic than changing the local eviction scoring policy alone.
