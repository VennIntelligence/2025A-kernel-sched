# %% [markdown]
# ### B.5 P3 — execution time
#
# How the time objective grows as the problem adds constraints.

# %%
t = order_cases(read("prob_time.csv"))
display(t)

x = np.arange(len(t))
w = 0.26
off = grouped_offsets(3, w)
series = [
    ("P1_time", "P1", METHOD_PALETTE["primary"]),
    ("P2_time", "P2", METHOD_PALETTE["secondary"]),
    ("P3_time", "P3", METHOD_PALETTE["accent_3"]),
]
fig, ax = make_figure("notebook")
for i, (col, lab, color) in enumerate(series):
    ax.bar(x + off[i], t[col], w, color=color, label=lab)
ax.set_yscale("log")
ax.set_xticks(x)
ax.set_xticklabels([case_label(c) for c in t["case"]])
style_bar_axes(ax, ylabel="Execution time [cycles]")
ax.set_title("Baseline execution time by problem (log scale)")
place_bar_legend(ax, ncol=3)
save_fig(fig, "p3_time_comparison.png")
fig

# %% [markdown]
# P2 time rises noticeably over P1 (spills add traffic), while P3 often lands
# close to P2 — the baseline has limited room to recover time through
# cross-pipeline scheduling, which is precisely where a stronger P3 method has
# to act.
