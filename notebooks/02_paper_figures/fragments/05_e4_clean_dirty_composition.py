# %% [markdown]
# ## E4 Clean and Dirty Spill Composition
# This figure decomposes spilled bytes into clean COPY_IN buffers and dirty
# write-back traffic for `id_raw` and `baseline` schedules.

# %%
e2_order = pd.read_csv(RESULTS / "e2_victim_order.csv")

cases = [
    "Conv_Case0",
    "Conv_Case1",
    "FlashAttention_Case0",
    "FlashAttention_Case1",
    "Matmul_Case0",
    "Matmul_Case1",
]
orders = ["id_raw", "baseline"]

composition = e2_order[
    e2_order["victim"].eq("dist_size_cost") & e2_order["order"].isin(orders)
].copy()
composition["case"] = pd.Categorical(composition["case"], categories=cases, ordered=True)
composition["order"] = pd.Categorical(composition["order"], categories=orders, ordered=True)
composition = composition.sort_values(["case", "order"])

case_pos = {case: i for i, case in enumerate(cases)}
order_offsets = {"id_raw": -0.18, "baseline": 0.18}
bar_width = 0.32

fig, ax = make_figure("double_col")
for order in orders:
    subset = composition[composition["order"].eq(order)]
    xs = [case_pos[case] + order_offsets[order] for case in subset["case"].astype(str)]
    ax.bar(
        xs,
        subset["clean_bytes"],
        width=bar_width,
        color=METHOD_PALETTE["secondary"],
        edgecolor="#444444",
        linewidth=0.4,
        label="Clean (COPY_IN)" if order == "id_raw" else None,
    )
    ax.bar(
        xs,
        subset["dirty_bytes"],
        bottom=subset["clean_bytes"],
        width=bar_width,
        color=METHOD_PALETTE["accent_1"],
        edgecolor="#444444",
        linewidth=0.4,
        label="Dirty (write-back)" if order == "id_raw" else None,
    )

for x in range(len(cases)):
    ax.text(
        x + order_offsets["id_raw"],
        -0.03,
        "id",
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="top",
    )
    ax.text(
        x + order_offsets["baseline"],
        -0.03,
        "base",
        transform=ax.get_xaxis_transform(),
        ha="center",
        va="top",
    )

ax.set_ylabel("Spilled bytes")
ax.set_xlabel("Schedule order")
ax.set_xticks(range(len(cases)))
ax.set_xticklabels(["Conv 0", "Conv 1", "FA 0", "FA 1", "Matmul 0", "Matmul 1"])
ax.tick_params(axis="x", pad=16)
ax.set_ylim(bottom=0)
ax.grid(axis="y", alpha=0.3)
ax.legend(ncol=2, loc="lower left", bbox_to_anchor=(0.0, 1.02), borderaxespad=0.0)
fig = save_fig(fig, "e4_clean_dirty_composition.png")
fig

# %% [markdown]
# The table checks whether Conv_Case0 and Conv_Case1 have a higher baseline
# clean-byte share than `id_raw`; the notebook prints an explicit failure if the
# current data does not support that claim.

# %%
share_table = composition.copy()
share_table["spilled_bytes"] = share_table["clean_bytes"] + share_table["dirty_bytes"]
share_table["clean_share"] = share_table["clean_bytes"] / share_table["spilled_bytes"]
clean_share = share_table.pivot(index="case", columns="order", values="clean_share")
display(clean_share.loc[["Conv_Case0", "Conv_Case1"]])

failed_cases = [
    case
    for case in ["Conv_Case0", "Conv_Case1"]
    if clean_share.loc[case, "baseline"] <= clean_share.loc[case, "id_raw"]
]
if failed_cases:
    print(
        "ASSERTION FAILED T4: baseline clean share is not higher than id_raw for "
        + ", ".join(failed_cases)
        + "."
    )
else:
    print("T4 clean-share check passed for Conv_Case0 and Conv_Case1.")

# %% [markdown]
# The stacked bars separate reusable clean spill traffic from dirty write-back
# traffic, making the composition difference visible alongside total spill size.
