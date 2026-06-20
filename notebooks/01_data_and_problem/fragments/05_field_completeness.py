# %% [markdown]
# ### A.4 Node-field completeness
#
# Whether the fields the scheduler depends on are actually present.

# %%
display(read("inv_field_completeness.csv"))

# %% [markdown]
# For every case the per-field counts equal the corresponding node totals:
# operation nodes all carry `Pipe`/`Cycles`/`Bufs`, and cache nodes all carry
# `BufId`/`Size`/`Type`. No field is missing, so schedule, memory, and time
# metrics can be computed directly from the raw schema.
