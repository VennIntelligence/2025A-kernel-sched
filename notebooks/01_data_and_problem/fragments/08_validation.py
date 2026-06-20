# %% [markdown]
# ### A.7 Structural validation
#
# Three checks that the graphs are well-formed enough to schedule: edge
# quality, buffer lifecycle closure, and DAG legality.

# %%
display(read("inv_edge_validation.csv"))

# %% [markdown]
# No self-loops, no edges referencing missing nodes, and no isolated nodes —
# the edge set is clean for topological analysis.

# %%
display(read("inv_buffer_consistency.csv"))

# %% [markdown]
# Every `BufId` has exactly one `ALLOC` and one `FREE`, and every operation's
# buffer reference resolves to an allocation. Buffer lifecycles are closed, so
# residency and physical-address reuse can be computed over `ALLOC..FREE`
# intervals.

# %%
display(read("inv_dag_topology.csv"))

# %% [markdown]
# Each instance is a valid DAG whose roots are all `ALLOC` and whose leaves are
# all `FREE`; the topological-generation count reflects each kernel's dependency
# depth.

# %%
display(read("inv_integrity_summary.csv"))

# %% [markdown]
# The roll-up combines node contiguity, buffer lifecycle, edge references,
# acyclicity, root/leaf legality, and field completeness into one verdict: all
# six instances pass. The data is trustworthy; the rest of the notebook frames
# the optimization problem on top of it.
