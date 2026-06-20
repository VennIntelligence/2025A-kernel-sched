# %% [markdown]
# ### B.4 P2 — spill cost
#
# How much traffic the baseline spends to fit the working set on-chip.

# %%
p2 = order_cases(read("prob_p2.csv"))
display(p2)

x = np.arange(len(p2))
w = 0.38
off = grouped_offsets(2, w)
fig, ax = make_figure("notebook")
ax2 = ax.twinx()
ax2.spines["right"].set_visible(True)
b1 = ax.bar(x + off[0], p2["spills"], w, color=METHOD_PALETTE["primary"], label="spills")
b2 = ax2.bar(x + off[1], p2["extra"], w, color=METHOD_PALETTE["accent_3"], label="extra traffic")
ax.set_xticks(x)
ax.set_xticklabels([case_label(c) for c in p2["case"]])
ax.set_xlabel("Benchmark case")
ax.set_ylabel("Spill count")
ax2.set_ylabel("Extra DDR traffic [bytes]")
ax.set_title("Baseline P2 spill count and extra traffic")
ax.legend([b1, b2], ["spills", "extra traffic"], loc="upper left", frameon=False, fontsize=8)
save_fig(fig, "p2_spill_cost.png")
fig

# %% [markdown]
# `spill_density` normalizes spills by operation count so difficulty is not
# confounded by raw instance size. Matmul_Case1 is heaviest on both axes;
# Conv_Case1 has many spills but less extra traffic, showing that buffer-size
# structure — not just spill count — drives the actual data movement P2 pays for.
