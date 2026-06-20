# %% [markdown]
# ## Part C — A real schedule, walked
#
# > **Explanatory figure (notebook-only) — not a paper figure.**
#
# To make the problem concrete we walk one real instance (Conv_Case0) under the
# promoted `id_raw` order: (a) how on-chip *demand* evolves across the whole
# schedule, and (b) the DAG structure inside the highest-pressure window.

# %%
occ = read("x1_dag_occupancy.csv")
nodes = read("x1_dag_nodes.csv")
edges = read("x1_dag_edges.csv")
caps = read("prob_capacities.csv").set_index("cache")["capacity"]

peak_pos = int(occ.loc[occ["L1"].idxmax(), "pos"])
HALF = 14
lo, hi = peak_pos - HALF, peak_pos + HALF

fig, (ax_top, ax_bot) = make_figure("notebook", nrows=2)

# (a) demand curve over the whole schedule
ax_top.plot(occ["pos"], occ["L1"], color=METHOD_PALETTE["primary"], label="L1 demand")
ax_top.plot(occ["pos"], occ["UB"], color=METHOD_PALETTE["secondary"], label="UB demand")
add_reference_line(ax_top, caps["L1"], "L1 capacity", color=METHOD_PALETTE["accent_1"])
ax_top.axvspan(lo, hi, color="#999999", alpha=0.22, label="zoom window")
ax_top.set_xlabel("Schedule step")
ax_top.set_ylabel("On-chip demand [bytes]")
ax_top.set_title("(a) On-chip memory demand along the Conv_Case0 schedule")
ax_top.legend(ncol=2, fontsize=7, loc="upper left")

# (b) swimlane of the high-pressure window
LANES = {"FREE": 0, "compute/move": 1, "COPY_IN": 2, "ALLOC": 3}
COLOR = {
    "ALLOC": METHOD_PALETTE["secondary"],
    "FREE": METHOD_PALETTE["accent_1"],
    "COPY_IN": METHOD_PALETTE["accent_3"],
}


def lane(op):
    return LANES.get(op, LANES["compute/move"])


def ncolor(op):
    return COLOR.get(op, METHOD_PALETTE["primary"])


win = nodes[(nodes["sched_pos"] >= lo) & (nodes["sched_pos"] <= hi)].copy()
xpos = dict(zip(win["id"], win["sched_pos"]))
ypos = {nid: lane(op) for nid, op in zip(win["id"], win["op"])}
win_ids = set(win["id"])
for s, dst in zip(edges["src"], edges["dst"]):
    if s in win_ids and dst in win_ids:
        ax_bot.annotate(
            "", xy=(xpos[dst], ypos[dst]), xytext=(xpos[s], ypos[s]),
            arrowprops=dict(arrowstyle="-|>", color="#cccccc", lw=0.6, shrinkA=5, shrinkB=5),
        )
for r in win.itertuples():
    ax_bot.scatter(r.sched_pos, lane(r.op), s=80, color=ncolor(r.op),
                   edgecolor="black", linewidth=0.4, zorder=3)
ax_bot.set_yticks(list(LANES.values()))
ax_bot.set_yticklabels(list(LANES.keys()))
ax_bot.set_ylim(-0.5, 3.5)
ax_bot.set_xlabel("Schedule step")
ax_bot.set_title("(b) DAG structure within the peak-pressure window")
save_fig(fig, "x1_dag_walk.png")
fig

# %% [markdown]
# **Read.** Panel (a) shows L1 *demand* climbing far above the 4 KB L1 capacity
# in a mid-schedule window — this is demand before any spilling, so it makes the
# need for P2's spill/reuse machinery concrete: a legal order alone cannot keep
# the working set on-chip. Panel (b) zooms into that window: `ALLOC` admits
# buffers, `COPY_IN` brings in clean (already-backed) data, compute/move nodes
# consume them, and `FREE` releases them. The band of simultaneously-live
# `ALLOC`s is exactly what drives the peak — and what the paper's liveness
# shaping reorders to flatten.
