# %% [markdown]
# ## E10 — Portfolio Improvement Trajectory
# The autoresearch ledger records how the portfolio changed across iterations.
# This figure keeps the last timestamp for each iteration and counts wins
# against the frozen baseline under the official lexicographic keys.

# %%
import numpy as np

e10 = pd.read_csv(RESULTS / "e10_portfolio.csv")
display(e10)

labels = ["capfit", "+id order", "+P2 tiebreak", "+P3 prefetch", "+id_raw"]
x = np.arange(len(e10))

fig, ax = make_figure("single_col", height=2.7)
ax.step(x, e10["wins"], where="mid", color=METHOD_PALETTE["primary"], linewidth=1.6)
ax.scatter(x, e10["wins"], color=METHOD_PALETTE["primary"], zorder=3)
ax.set_xticks(x)
ax.set_xticklabels(e10["iter"])
ax.set_xlabel("Autoresearch iteration")
ax.set_ylabel("Wins vs baseline")
for xi, wins, label in zip(x, e10["wins"], labels):
    ax.annotate(label, (xi, wins), textcoords="offset points", xytext=(0, 7),
                ha="center", fontsize=7)
save_fig(fig, "e10_portfolio.png")
fig

# %% [markdown]
# The win count is monotone across the selected portfolio iterations. The final
# promoted candidate reaches the 13-win headline count used in E1.
