# %% [markdown]
# ## Part A — Data inventory & validation
#
# ### A.1 Raw file inventory
#
# What the dataset physically contains.

# %%
display(read("inv_file_inventory.csv"))

# %% [markdown]
# The dataset is 6 JSON case files plus 12 CSV files (a Nodes/Edges pair per
# case). The file set is complete, so we can move on to checking that the two
# formats agree.
