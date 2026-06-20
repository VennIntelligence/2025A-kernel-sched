# %% [markdown]
# ## 7. C1 mechanism — clean vs dirty residency
#
# COPY_IN buffers behave like clean pages whose spill-out needs no write-back;
# computed buffers behave like dirty pages whose spill costs 2× (write-back then
# read-back).

# %%
show_png("e4_clean_dirty_composition.png")
show_png("e5_peak_residency.png")

composition = e2_order[
    e2_order["order"].isin(["id_raw", "baseline"]) & e2_order["victim"].eq("dist_size_cost")
].copy()
composition["spilled_bytes"] = composition["clean_bytes"] + composition["dirty_bytes"]
composition["clean_share"] = composition["clean_bytes"] / composition["spilled_bytes"]
display(
    composition[["case", "order", "extra", "clean_bytes", "dirty_bytes", "clean_share"]].sort_values(["case", "order"])
)

note(
    "Do not conflate E4 and E5: E4 is about spill-byte composition; E5 is about "
    "clean/dirty residency along the schedule timeline."
)

# %% [markdown]
# ### Explanatory: anatomy of spill cost (Conv_Case0)
#
# > **Explanatory figure (notebook-only) — not a paper figure.**
#
# Why dirty residency is expensive, worked on a real instance: (a) the L1
# clean/dirty residency timeline at the high-pressure window; (b) the
# decomposition of P2 extra traffic into clean (×1) and dirty (×2) bytes. This
# shows the *mechanism*, not a baseline comparison — on Conv_Case0 the promoted
# order does not even win P2, yet the cost is still dominated by dirty write-backs.

# %%
tl = x2_timeline.copy()
tl["total"] = tl["live_clean"] + tl["live_dirty"]
peak = int(tl["total"].idxmax())
lo, hi = max(0, peak - 90), min(len(tl) - 1, peak + 90)
seg = tl.iloc[lo:hi]
L1cap = int(capacities.set_index("cache").loc["L1", "capacity"])

fig, (axA, axB) = make_figure("double_col", ncols=2, height=2.7)
axA.fill_between(seg["pos"], 0, seg["live_clean"], color=METHOD_PALETTE["primary"], alpha=0.75, label="clean (no write-back)")
axA.fill_between(seg["pos"], seg["live_clean"], seg["total"], color=METHOD_PALETTE["accent_3"], alpha=0.8, label="dirty (write-back)")
add_reference_line(axA, L1cap, "L1 capacity", color=METHOD_PALETTE["accent_1"])
axA.set_xlabel("Schedule step")
axA.set_ylabel("L1 residency [bytes]")
axA.set_title("(a) Clean/dirty residency at peak")
axA.legend(fontsize=7, loc="upper right")

row = x2_split[x2_split["order"] == "id_raw"].iloc[0]
axB.bar(0, row["clean_bytes"], color=METHOD_PALETTE["primary"], label=f"clean ×1 ({int(row['clean_count'])} spills)")
axB.bar(0, row["dirty_bytes"], bottom=row["clean_bytes"], color=METHOD_PALETTE["accent_3"], label=f"dirty ×2 ({int(row['dirty_count'])} spills)")
axB.set_xlim(-1, 1)
axB.set_xticks([0])
axB.set_xticklabels(["P2 extra"])
axB.set_ylabel("Extra DDR traffic [bytes]")
axB.set_title("(b) Spill-cost decomposition")
axB.legend(fontsize=7, loc="upper left")
save_fig(fig, "x2_clean_dirty_steps.png")
fig

# %% [markdown]
# **Read.** At the L1 high-pressure window, dirty residency (orange) dwarfs
# clean residency (blue), and the spill bill follows: the large majority of the
# P2 extra traffic is dirty write-back+read-back bytes. This is exactly why the
# method shapes liveness so that more of what stays resident — and what must be
# evicted — is clean, halving its spill cost.
