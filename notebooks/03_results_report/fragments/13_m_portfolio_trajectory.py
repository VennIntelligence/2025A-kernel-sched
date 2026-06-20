# %% [markdown]
# ## 12. M — portfolio trajectory
#
# From iter034 to iter038, adding candidate orders and prefetch windows
# monotonically increased the win count.

# %%
show_png("e10_portfolio.png")
display(e10)

note(
    "The strength of the portfolio is safety, not complexity: after taking the "
    "minimum under the official key, adding a candidate cannot regress the "
    "selected result."
)

# %% [markdown]
# ### Explanatory: portfolio search trajectory
#
# > **Explanatory figure (notebook-only) — not a paper figure.**
#
# A richer view of the same trajectory than E10: (a) the win count broken down
# by problem, and (b) aggregate P2 extra traffic and P3 time, normalized to the
# first portfolio iteration.

# %%
traj = x3_traj
xs = np.arange(len(traj))

fig, (axA, axB) = make_figure("double_col", ncols=2, height=2.7)
axA.plot(xs, traj["wins"], marker="o", color=METHOD_PALETTE["primary"], label="total")
axA.plot(xs, traj["p1_wins"], marker="s", color=METHOD_PALETTE["secondary"], label="P1")
axA.plot(xs, traj["p2_wins"], marker="^", color=METHOD_PALETTE["accent_3"], label="P2")
axA.plot(xs, traj["p3_wins"], marker="D", color=METHOD_PALETTE["accent_2"], label="P3")
axA.set_xticks(xs)
axA.set_xticklabels(traj["iter"], fontsize=7)
axA.set_xlabel("Iteration")
axA.set_ylabel("Wins vs baseline")
axA.set_title("(a) Win trajectory by problem")
axA.legend(fontsize=7, ncol=2)

p2_0 = traj["total_p2_extra"].iloc[0]
p3_0 = traj["total_p3_time"].iloc[0]
axB.plot(xs, traj["total_p2_extra"] / p2_0, marker="^", color=METHOD_PALETTE["accent_3"], label="P2 extra")
axB.plot(xs, traj["total_p3_time"] / p3_0, marker="D", color=METHOD_PALETTE["primary"], label="P3 time")
axB.set_xticks(xs)
axB.set_xticklabels(traj["iter"], fontsize=7)
axB.set_xlabel("Iteration")
axB.set_ylabel("Relative to iter034")
axB.set_title("(b) Aggregate cost (normalized)")
axB.legend(fontsize=7)
save_fig(fig, "x3_portfolio_trajectory.png")
fig

# %% [markdown]
# **Read.** Total wins climb 8→13 across the five portfolio iterations, and the
# breakdown shows where: P1 is already saturated at 6/6, so every gain comes
# from P2 (1→3) and P3 (1→4). Panel (b) confirms the mechanism — aggregate P2
# extra traffic and P3 time both fall monotonically as candidates are added,
# because selection keeps only improvements.
