# %% [markdown]
# ## 10. C3 — spill selection and reload placement decouple
#
# P2 prioritizes extra traffic; P3 prioritizes time. Early SPILL_IN placement
# can hide reload stalls but may increase extra traffic, so selection must
# follow the official key.

# %%
show_png("e8_decoupling.png")

best_prefetch = (
    e8.loc[e8.groupby(["case", "order"])["time"].idxmin()]
    .sort_values(["case", "order"])
    .reset_index(drop=True)
)
display(best_prefetch)

note(
    "We do not claim strict monotonicity of extra over the prefetch window H. The "
    "supported conclusion is that time and extra can be optimized through "
    "separate placement choices."
)
