# %% [markdown]
# ### B.6 Cross-case difficulty
#
# A normalized side-by-side of where each instance is hard.

# %%
d = order_cases(read("prob_difficulty.csv")).set_index("case").reindex(CASE_ORDER)
display(d)

fig, ax = make_figure("notebook")
im = ax.imshow(d.values, cmap=COLORMAPS["coverage"], aspect="auto", vmin=0, vmax=1)
ax.set_xticks(range(len(d.columns)))
ax.set_xticklabels(d.columns, rotation=22, ha="right")
ax.set_yticks(range(len(d.index)))
ax.set_yticklabels([case_label(c) for c in d.index])
for i in range(d.shape[0]):
    for j in range(d.shape[1]):
        v = d.iat[i, j]
        ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                color="white" if v < 0.6 else "black", fontsize=7)
fig.colorbar(im, ax=ax, label="Normalized (column max = 1)")
ax.set_title("Cross-case difficulty indicators")
save_fig(fig, "difficulty_heatmap.png")
fig

# %% [markdown]
# Each column is normalized to its own maximum. Matmul_Case1 saturates several
# dimensions and is the hardest instance overall; FlashAttention's difficulty is
# concentrated in UB pressure; Conv sits in between. This is the difficulty
# landscape the method is evaluated against.
