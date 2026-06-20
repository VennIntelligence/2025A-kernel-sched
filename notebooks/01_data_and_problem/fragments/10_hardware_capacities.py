# %% [markdown]
# ### B.2 Hardware capacities and P1 pressure
#
# The on-chip capacities the schedule must respect. *This is the capacity table
# the supplement reports.*

# %%
display(read("prob_capacities.csv"))

# %% [markdown]
# L1 and UB are the capacity-binding levels for peak residency; L0A/L0B/L0C are
# small matrix-compute buffers. The chart below expresses each instance's
# baseline P1 peak as a multiple of the relevant capacity, so a bar above 1.0
# means a legal order alone overflows that cache.

# %%
p1 = order_cases(read("prob_p1.csv"))
display(p1)

x = np.arange(len(p1))
w = 0.38
off = grouped_offsets(2, w)
fig, ax = make_figure("notebook")
b1 = ax.bar(x + off[0], p1["L1_ratio"], w, color=METHOD_PALETTE["primary"], label="L1")
b2 = ax.bar(x + off[1], p1["UB_ratio"], w, color=METHOD_PALETTE["secondary"], label="UB")
add_reference_line(ax, 1.0, "capacity", color=METHOD_PALETTE["accent_1"])
annotate_bars(ax, b1, formatter=lambda v: f"{v:.1f}x", rotation=0, fontsize=7)
annotate_bars(ax, b2, formatter=lambda v: f"{v:.1f}x", rotation=0, fontsize=7, min_value=0.01)
ax.set_xticks(x)
ax.set_xticklabels([case_label(c) for c in p1["case"]])
style_bar_axes(ax, ylabel="Peak residency / capacity")
ax.set_title("Baseline P1 peak residency relative to capacity")
place_bar_legend(ax, ncol=3)
save_fig(fig, "p1_peak_vs_capacity.png")
fig

# %% [markdown]
# L1 is over capacity for every Conv/Matmul instance and worst on Matmul_Case1
# (8.5×). UB pressure is unique to FlashAttention (up to 2.4×), where L1 is
# actually under capacity. So spill/reuse cannot be an L1-only concern — UB is
# the binding constraint on FlashAttention.
