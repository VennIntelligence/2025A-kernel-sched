# %% [markdown]
# ## Part B — Problem framing
#
# ### B.1 The three sub-problems
#
# P1, P2, and P3 form a progression over the same schedule.

# %%
display(read("prob_overview.csv").style.set_properties(**{"text-align": "left"}))

# %% [markdown]
# **P1** optimizes only the peak resident cache demand of a legal topological
# order. **P2** adds physical address assignment and spill/reuse on top of that
# order. **P3** further folds same-pipeline serialization, DAG dependencies, and
# spill/reuse dependencies into a total-time objective. Each problem strictly
# contains the previous one's constraints.
