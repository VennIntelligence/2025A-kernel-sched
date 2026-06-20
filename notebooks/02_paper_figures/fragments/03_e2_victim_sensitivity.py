# %% [markdown]
# ## E2 Eviction Policy Sensitivity
# This figure reports the coefficient of variation of extra DDR traffic across
# eviction policies for each schedule order and case.

# %%
e2_cv = pd.read_csv(RESULTS / "e2_victim_cv.csv")
orders = ["capfit_id", "p1", "id_raw", "min_id", "baseline"]
min_visible_cv = 0.0005

plot_data = e2_cv[e2_cv["cv"] >= 0].copy()
plot_data["cv_plot"] = plot_data["cv"].where(plot_data["cv"] >= min_visible_cv, 0.0)
cases = [
    case for case in CASE_ORDER
    if plot_data.loc[plot_data["case"].eq(case), "cv_plot"].max() > 0
]
plot_data = plot_data[plot_data["case"].isin(cases)].copy()
case_pos = {case: i for i, case in enumerate(cases)}
order_pos = {order: i for i, order in enumerate(orders)}
bar_width = 0.17

fig, ax = make_figure("double_col", height=3.35)
for order in orders:
    subset = plot_data[plot_data["order"] == order].sort_values("case")
    xs = [
        case_pos[case] + (order_pos[order] - (len(orders) - 1) / 2) * bar_width
        for case in subset["case"]
    ]
    bars = ax.bar(
        xs,
        subset["cv_plot"],
        width=bar_width,
        label=ORDER_LABELS[order],
        color=ORDER_COLORS[order],
        edgecolor="#333333",
        linewidth=0.35,
    )
    annotate_bars(
        ax,
        bars,
        subset["cv_plot"],
        formatter=lambda v: f"{v * 100:.1f}%",
        fontsize=7.1,
        min_value=min_visible_cv,
    )

add_reference_line(ax, 0.01, "1% reference")
style_bar_axes(ax, ylabel="Victim-rule CV")
ax.set_xticks(range(len(cases)))
ax.set_xticklabels([case_label(c) for c in cases], rotation=0)
ax.set_ylim(0, max(plot_data["cv"].max() * 1.38, 0.012))
ax.set_xlim(-0.55, len(cases) - 0.45)
place_bar_legend(ax, ncol=3)
fig = save_fig(fig, "e2_victim_sensitivity.png")
fig

# %% [markdown]
# The bars compare how much P2 extra traffic changes when only the eviction
# scoring policy changes. Values below the 1% reference line indicate that the
# schedule order dominates this source of variance. Case groups whose victim
# sensitivity is exactly zero for every order are omitted from the chart.
