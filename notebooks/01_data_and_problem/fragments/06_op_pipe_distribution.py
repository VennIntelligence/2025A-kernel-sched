# %% [markdown]
# ### A.5 Operation-type & pipeline distribution
#
# The computational composition of each kernel.

# %%
op_pivot = (
    order_cases(read("inv_op_distribution.csv"))
    .pivot(index="case", columns="category", values="count")
    .reindex(CASE_ORDER)
    .fillna(0)
)
fig, ax = make_figure("notebook")
op_pivot.plot(kind="bar", stacked=True, ax=ax, width=0.78, colormap="tab20", legend=False)
ax.set_xticklabels([case_label(c) for c in op_pivot.index], rotation=0)
style_bar_axes(ax, ylabel="Operation-node count")
ax.set_title("Operation-type composition (excluding ALLOC/FREE)")
ax.legend(title="Op", ncol=1, bbox_to_anchor=(1.01, 1.0), loc="upper left", fontsize=7)
save_fig(fig, "op_type_distribution.png")
fig

# %% [markdown]
# Conv and Matmul are dominated by their core compute operator plus data
# movement; FlashAttention spreads across more operator types, so its schedule
# must interleave several compute stages rather than one dominant kind.

# %%
pipe_pivot = (
    order_cases(read("inv_pipe_distribution.csv"))
    .pivot(index="case", columns="category", values="count")
    .reindex(CASE_ORDER)
    .fillna(0)
)
fig, ax = make_figure("notebook")
pipe_pivot.plot(kind="bar", stacked=True, ax=ax, width=0.78, colormap="tab20", legend=False)
ax.set_xticklabels([case_label(c) for c in pipe_pivot.index], rotation=0)
style_bar_axes(ax, ylabel="Node count")
ax.set_title("Pipeline usage composition")
ax.legend(title="Pipe", ncol=1, bbox_to_anchor=(1.01, 1.0), loc="upper left", fontsize=7)
save_fig(fig, "pipe_distribution.png")
fig

# %% [markdown]
# Conv/Matmul concentrate on data movement and the CUBE pipeline, whereas
# FlashAttention also exercises VECTOR/FIXP pipelines. The more pipelines a
# kernel spans, the more cross-pipeline parallelism P3's time objective can —
# and must — exploit.
