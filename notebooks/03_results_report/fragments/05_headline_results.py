# %% [markdown]
# ## 4. Headline results
#
# The core source for the paper's headline numbers, from
# `results/paper/e1_headline.csv`.

# %%
headline_display = ordered_cases(headline)[
    [
        "case", "problem", "result",
        "ours_max_L1", "ours_spills", "ours_extra", "ours_time",
        "base_max_L1", "base_spills", "base_extra", "base_time",
    ]
]
display(headline_display)

problem_summary = (
    headline.groupby(["problem", "result"], as_index=False)
    .size()
    .pivot(index="problem", columns="result", values="size")
    .fillna(0)
    .astype(int)
    .rename(index={1: "P1", 2: "P2", 3: "P3"})
)
display(problem_summary)

losses = headline[headline["result"].eq("LOSS")][
    ["case", "problem", "ours_extra", "base_extra", "ours_time", "base_time"]
].reset_index(drop=True)
display(losses)

note(
    "The five remaining losses stay visible. They show the residual gap is "
    "order-level cheap-buffer residency, not an evaluator or artifact-validity "
    "problem."
)
