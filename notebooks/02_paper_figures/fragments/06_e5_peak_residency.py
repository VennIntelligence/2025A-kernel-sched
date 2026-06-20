# %% [markdown]
# ## E5 — Peak L1 residency decomposition (C1 main figure)
# Decomposes the live L1 working set of `Conv_Case0` into clean (cheap-to-spill,
# `COPY_IN`-backed) and dirty bytes, for our raw-ID order and the contest baseline.
# Both panels share x and y axes so the absolute residency is directly comparable;
# clean vs dirty use the shared paper palette; the L1 capacity line is emphasised
# and the region above it (forced overflow) is shaded.

# %%
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

L1_CAP = 4096
residency = {
    "Dirty-heavy order": pd.read_csv(RESULTS / "e5_residency_id_raw.csv"),
    "Lower-dirty reference order": pd.read_csv(RESULTS / "e5_residency_baseline.csv"),
}

clean_c = METHOD_PALETTE["primary"]
dirty_c = METHOD_PALETTE["accent_3"]
y_max = max((d["live_clean"] + d["live_dirty"]).max() for d in residency.values())
y_top = float(y_max) * 1.08
focus_start = 1650

fig, axes = make_figure("double_col", ncols=2, height=2.45, sharex=True, sharey=True)
plt.rcParams.update({
    "axes.labelsize": 10,
    "axes.titlesize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
})

legend_handles = None
for ax, (panel, (name, df)) in zip(axes, enumerate(residency.items(), start=1)):
    df = df[df["pos"] >= focus_start].copy()
    pos = df["pos"].to_numpy()
    clean = df["live_clean"].to_numpy()
    dirty = df["live_dirty"].to_numpy()
    total = clean + dirty

    # Clean reserve: solid fill from baseline.
    ax.fill_between(pos, 0, clean, facecolor=clean_c, alpha=0.9,
                    linewidth=0, step="post", label="Clean")
    # Dirty reserve stacked on top.
    ax.fill_between(pos, clean, total, facecolor=dirty_c, alpha=0.55,
                    linewidth=0.0, step="post", label="Dirty")
    ax.fill_between(pos, L1_CAP, total, where=(total > L1_CAP),
                    facecolor="#d9d9d9", edgecolor="none", alpha=0.22,
                    step="post", zorder=1.5)

    ax.axhline(L1_CAP, color="#444444", lw=1.2, ls="--",
               label=f"L1 capacity ({L1_CAP})", zorder=3)

    # Report the global peak in a stable corner instead of using a long arrow
    # with a hard-coded data offset.
    i_peak = int(total.argmax())
    ax.text(0.97, 0.9, f"peak {int(total[i_peak] / 1000):.0f}k",
            transform=ax.transAxes, ha="right", va="top")

    ax.set_title(f"({chr(96 + panel)}) {name}", loc="left")
    ax.tick_params(axis="both", labelsize=9)
    ax.set_ylim(0, y_top)
    ax.set_xlim(pos.min(), pos.max())
    ax.grid(axis="y", alpha=0.18, linewidth=0.45)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "0" if v == 0 else f"{v / 1000:.0f}k"))
    if legend_handles is None:
        legend_handles, legend_labels = ax.get_legend_handles_labels()

axes[0].set_ylabel("L1 residency")
for ax in axes:
    ax.set_xlabel("Schedule position")
fig.legend(legend_handles, legend_labels, loc="upper center",
           bbox_to_anchor=(0.5, 0.995), ncol=3)
fig.tight_layout(rect=[0.0, 0.0, 1.0, 0.88])
fig = save_fig(fig, "e5_peak_residency.png")
fig

# %% [markdown]
# **Read.** Stacked live L1 volume over schedule position: solid blue = clean
# (spill cost `Size`), orange = dirty (spill cost `2*Size`); the dashed line is
# the L1 capacity (4096 abstract units), and pale grey bands mark volume forced
# above capacity. With a shared y-axis the two schedules are on the same scale.
# **Pattern.** Both schedules drive L1 far above capacity in the later compute
# phase, so spilling is unavoidable here (consistent with the working-set
# certificate, E9). `Conv_Case0` is one of our five order-level losses: the
# baseline compresses the overflow peaks far lower (total peak 7488 vs our
# 14592, dominated by *dirty* volume), i.e. it shapes liveness better here. The
# decomposition exposes *what* sits resident at the overflow peaks — the clean
# fraction is the share that can be evicted at half price.
# **Takeaway.** The lever is the clean/dirty *composition* of the live set inside
# the overflow window — set by the schedule order, not the eviction policy (C1).
# This figure is shown honestly as the negative example we aim to learn from but
# have not yet generalised (see Limitations).
