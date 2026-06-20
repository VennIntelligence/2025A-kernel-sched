# %% [markdown]
# ## E1 — Headline comparison
# This table compares the promoted solver against the baseline on the official
# lexicographic objective for each benchmark and problem variant.

# %%
headline = pd.read_csv(RESULTS / "e1_headline.csv")
display(headline)

# %% [markdown]
# The full table records the metrics used in the paper headline result. The
# `result` column is computed from the official objective key for P1, P2, and P3.

# %%
case_order = [
    "Conv_Case0",
    "Conv_Case1",
    "FlashAttention_Case0",
    "FlashAttention_Case1",
    "Matmul_Case0",
    "Matmul_Case1",
]
headline["case"] = pd.Categorical(headline["case"], categories=case_order, ordered=True)
pivot = (
    headline.pivot(index="case", columns="problem", values="result")
    .rename(columns={1: "P1", 2: "P2", 3: "P3"})
    .reindex(case_order)
)
display(pivot)

# %% [markdown]
# The 6x3 summary shows where the promoted solver wins or loses under the
# official keys. The promoted solver wins 13 of the 18 comparisons.
