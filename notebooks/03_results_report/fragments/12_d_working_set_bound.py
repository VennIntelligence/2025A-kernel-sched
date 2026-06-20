# %% [markdown]
# ## 11. D — working-set bound
#
# The working-set bound must be read over the near-optimal-extra subset. The
# minimum over *all* orders can falsely suggest a case is easy.

# %%
show_png("e9_working_set.png")

capacity_bound = e9[e9["bound_class"].eq("capacity_bound")][
    ["case", "cache", "capacity", "ratio_all", "ratio_nearopt", "nearopt_order", "clean_frac_at_peak"]
].sort_values(["case", "cache"])
display(capacity_bound)

matmul1_l1 = e9[(e9["case"].eq("Matmul_Case1")) & (e9["cache"].eq("L1"))].iloc[0]
note(
    f"For Matmul_Case1/L1, ratio_all = {matmul1_l1['ratio_all']:.5f} but "
    f"ratio_nearopt = {matmul1_l1['ratio_nearopt']:.1f}. The unconstrained minimum "
    "is misleading; the near-optimal subset is the honest bound."
)
