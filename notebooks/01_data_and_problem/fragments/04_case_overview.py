# %% [markdown]
# ### A.3 Benchmark scale overview
#
# The size and shape of each instance. *This is the table the paper reports as
# its benchmark instances.*

# %%
display(order_cases(read("inv_case_summary.csv")))

# %% [markdown]
# Three kernel families (Conv, FlashAttention, Matmul) each appear at two
# scales: a small `Case0` and a large `Case1`. Instance size spans roughly
# 1.7K–36K nodes, giving a clear scale gradient. The `op_nodes` /
# `alloc_nodes` split and the buffer / pipe counts foreshadow where the memory
# and scheduling pressure will concentrate.
