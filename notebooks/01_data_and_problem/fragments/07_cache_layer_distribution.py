# %% [markdown]
# ### A.6 Cache-layer allocation
#
# How statically allocated buffer bytes distribute across memory types.

# %%
cache = order_cases(read("inv_cache_layer.csv"))
display(cache)

# %%
cache_pivot = (
    cache.pivot(index="case", columns="mem_type", values="total_size")
    .reindex(CASE_ORDER)
    .fillna(0)
)
fig, ax = make_figure("notebook")
cache_pivot.plot(
    kind="bar", stacked=True, ax=ax, width=0.74,
    color=METHOD_COLOR_LIST[: cache_pivot.shape[1]], legend=False,
)
ax.set_xticklabels([case_label(c) for c in cache_pivot.index], rotation=0)
style_bar_axes(ax, ylabel="Total allocated size [bytes]")
ax.set_title("Allocated buffer size by memory type")
ax.legend(title="MemType", ncol=cache_pivot.shape[1], loc="upper left", bbox_to_anchor=(0.0, 1.12), fontsize=7)
save_fig(fig, "cache_layer_distribution.png")
fig

# %% [markdown]
# Static L1 demand dominates for the large instances and is the principal
# source of on-chip pressure. FlashAttention additionally leans on UB, so UB
# capacity — not just L1 — can become the binding constraint, a point the P1
# analysis below makes quantitative.
