# %% [markdown]
# ### B.3 Baseline metrics — full table
#
# The reference point all later work is measured against.

# %%
bm = read("prob_baseline_metrics.csv")
bm["case"] = pd.Categorical(bm["case"], categories=CASE_ORDER, ordered=True)
display(bm.sort_values(["case", "problem"]).reset_index(drop=True))

# %% [markdown]
# These 18 rows (6 cases × 3 problems) carry the peak cache, spill count, extra
# DDR traffic, and time that define the baseline. They are taken straight from
# the same source as the paper's headline comparison (`e1_headline.csv`), so the
# problem-framing numbers here cannot drift from the headline results.
