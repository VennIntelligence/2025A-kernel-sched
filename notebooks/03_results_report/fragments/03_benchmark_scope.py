# %% [markdown]
# ## 2. Benchmark scope
#
# Just enough scope to interpret the solver: the six instance scales, the three
# problem objectives, and the cache capacities. (Full inventory and validation
# live in `01_data_and_problem`.)

# %%
display(
    ordered_cases(case_summary)[
        ["case", "kernel", "scale", "total_nodes", "total_edges", "op_nodes", "unique_buffers", "total_buf_size"]
    ]
)

display(problem_overview.style.set_properties(**{"text-align": "left"}))
display(capacities)

note(
    "P1 only requires an original-node topological order; P2/P3 additionally "
    "require physical offsets and spill lists, so low P1 pressure does not "
    "automatically imply low P2/P3 cost."
)
