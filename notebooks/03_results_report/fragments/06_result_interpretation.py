# %% [markdown]
# ## 5. Result interpretation
#
# Translating the win/loss matrix into the paper narrative — without overstating
# 13/18 as universal dominance.

# %%
interpretation = pd.DataFrame(
    [
        {"observation": "P1 wins all cases", "evidence": "6 / 6 P1 rows are WIN", "interpretation": "the memory-aware order is strong for the official P1 key"},
        {"observation": "P2/P3 wins are mixed", "evidence": "P2 has 3 wins; P3 has 4 wins", "interpretation": "physical placement, spill cost, and time placement add separate constraints"},
        {"observation": "Conv0 remains hard", "evidence": "Conv_Case0 loses P2 and P3", "interpretation": "the schedule still lacks enough cheap clean buffers at the right overflow window"},
        {"observation": "Matmul is stable", "evidence": "Matmul_Case0 and Matmul_Case1 win P1/P2/P3", "interpretation": "the candidate-order portfolio plus prefetch is sufficient for these cases"},
        {"observation": "FA has split behavior", "evidence": "FA P2 rows lose narrowly; FA P3 rows win", "interpretation": "prefetch placement improves time even when traffic is not always lower"},
    ]
)
display(interpretation)

note(
    "The losses are boundaries and next-step evidence, not something to hide. "
    "They support the thesis that schedule order is the main lever."
)
