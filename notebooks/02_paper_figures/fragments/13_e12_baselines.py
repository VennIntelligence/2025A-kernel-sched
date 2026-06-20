# %% [markdown]
# ## E12 — Standard Scheduler Baselines on the Real Cases (controlled order swap)
# This is the controlled experiment that attributes the spill-traffic gap to the
# *schedule order* rather than to the spill/address engine: every order
# (literature baselines and ours) is fed through the *same* frozen `assign`
# engine, and only the order changes.
#
# We compare against three motif-agnostic literature schedulers — `cp_list`
# (latency-only critical-path list scheduling), `pressure_uniform` (uniform-byte
# min-peak-live, memory-aware but clean/dirty blind), and `goodman_hsu`
# (integrated-prepass latency/pressure switching) — plus a `cp_free_first`
# allocator-friendly latency companion.
#
# **Punchline.** Generic memory-pressure awareness is *not* enough: the two
# clean/dirty-blind memory-aware schedulers (`pressure_uniform`, `goodman_hsu`)
# pay 2.4–26x more P2 spill traffic than our clean/dirty-aware liveness shaping.
# `cp_list` is a latency-only stress baseline and is measured with the same
# engine under `far_only/80` (audited in the CSV); read it as an upper-bound on
# pathology, not as the main control.

# %%
import numpy as np

e12 = pd.read_csv(RESULTS / "e12_baselines.csv")
p2 = e12[e12["problem"] == 2].copy()

cases = CASE_ORDER
orders = ["cp_list", "cp_free_first", "pressure_uniform", "goodman_hsu", "ours"]

extra = {o: [float(p2[(p2.case == c) & (p2.order == o)]["extra"].iloc[0]) for c in cases]
         for o in orders}

fig, ax = make_figure("double_col", height=3.6)
x = np.arange(len(cases))
w = 0.17
all_vals = []
for i, o in enumerate(orders):
    xs = x + (i - (len(orders) - 1) / 2) * w
    bars = ax.bar(
        xs,
        extra[o],
        width=w,
        label=ORDER_LABELS[o],
        color=ORDER_COLORS[o],
        edgecolor="#333333",
        linewidth=0.35,
    )
    all_vals.extend(extra[o])
    annotate_bars(ax, bars, extra[o], fontsize=7.3)

ax.set_yscale("log")
style_bar_axes(ax, ylabel="P2 extra DDR traffic (log scale)")
ax.set_xticks(x)
ax.set_xticklabels([case_label(c) for c in cases])
ax.set_ylim(max(1, min(all_vals) * 0.65), max(all_vals) * 2.4)
place_bar_legend(ax, ncol=3)
fig.tight_layout()
save_fig(fig, "e12_baselines.png")
fig

# %%
ratio_rows = []
for o in ["cp_list", "cp_free_first", "pressure_uniform", "goodman_hsu"]:
    mult = [extra[o][i] / extra["ours"][i] for i in range(len(cases))]
    ratio_rows.append({"comparator": o,
                       "min_x_over_ours": round(min(mult), 3),
                       "median_x_over_ours": round(float(np.median(mult)), 3),
                       "max_x_over_ours": round(max(mult), 3)})
display(pd.DataFrame(ratio_rows))

# %% [markdown]
# Under the same engine, the clean/dirty-blind memory-aware schedulers
# `pressure_uniform` and `goodman_hsu` lose on every real case, with P2 extra
# medians roughly an order of magnitude above ours. `cp_free_first` is a strong
# companion (near-tie on the four tighter cases) but is still dominated under the
# official multi-objective key by spill count / time, and loses 2.4x on Conv 0.
# This isolates the clean/dirty-aware ordering — not generic memory awareness —
# as the lever for C1. Source: `results/paper/e12_baselines.csv` (rows with
# `problem == 2`); win/loss under official keys in `e12_winloss.csv`.
