# %% [markdown]
# ## 9. C2 — overflow surrogate and objective mismatch
#
# The value of the overflow surrogate Φ is not that it dramatically beats peak
# pressure. It is lifetime-aware, cheap, and useful for portfolio selection.
# Separately, the P1 lexicographic key and the P2/P3 objectives can be
# misaligned.

# %%
show_png("e6_surrogate.png")
display(e6_corr)

show_png("e7_misalignment_worst_ratio.png")
display(e7)

global_corr = e6_corr[e6_corr["case"].eq("ALL")].iloc[0]
note(
    f"Global Spearman: Φ–extra = {global_corr['spearman_phi_extra']:.4f}, "
    f"peak–extra = {global_corr['spearman_peak_extra']:.4f}. Both are strong, so "
    "Φ's advantage should not be overstated; its real benefit is being a cheap, "
    "lifetime-aware selection signal."
)
