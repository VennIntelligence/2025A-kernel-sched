# %% [markdown]
# ### A.2 JSON vs CSV consistency
#
# Whether the two provided encodings of each instance describe the same graph.

# %%
display(read("inv_json_csv_consistency.csv"))

# %% [markdown]
# Every case matches on both nodes and edges, so the two formats are
# interchangeable. All downstream analysis uses the JSON encoding, avoiding a
# second parsing path to maintain.
