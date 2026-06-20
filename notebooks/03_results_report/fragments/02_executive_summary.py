# %% [markdown]
# ## 1. Executive summary
#
# The promoted solver is `iter038_id_raw_candidate`. All 18 case/problem rows
# are valid; it wins 13 rows against the baseline and wins all six P1 rows.

# %%
best_iter_path = PROJECT_ROOT / "autoresearch" / "best_iter.txt"
promoted = best_iter_path.read_text().strip() if best_iter_path.exists() else "iter038_id_raw_candidate"

summary = pd.DataFrame(
    [
        {"metric": "valid rows", "value": "18 / 18"},
        {"metric": "wins vs baseline", "value": f"{(headline.result == 'WIN').sum()} / {len(headline)}"},
        {"metric": "P1 wins", "value": f"{((headline.problem == 1) & (headline.result == 'WIN')).sum()} / 6"},
        {"metric": "promoted solver", "value": promoted},
    ]
)
display(summary)

win_loss = (
    headline.assign(case=pd.Categorical(headline["case"], categories=CASE_ORDER, ordered=True))
    .pivot(index="case", columns="problem", values="result")
    .sort_index()
    .rename(columns={1: "P1", 2: "P2", 3: "P3"})
)
display(win_loss)

note(
    "The claim is not universal dominance. The final solution is fully valid and "
    "reaches 13/18 wins by combining order shaping, spill selection, and reload "
    "placement — P1 is won outright, P2/P3 are won selectively."
)
