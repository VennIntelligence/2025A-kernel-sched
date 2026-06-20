# %% [markdown]
# ## 6. C1 — order dominates victim policy
#
# Precise claim: we do **not** say victim policy is always below 1%. The safer,
# supported statement is that order-induced traffic ranges dominate
# victim-policy ranges.

# %%
show_png("e2_victim_sensitivity.png")
show_png("e3_order_sensitivity.png")

order_range = e2_order.groupby("case")["extra"].agg(order_min="min", order_max="max")
order_range["order_range"] = order_range["order_max"] - order_range["order_min"]
victim_range = (
    e2_order.groupby(["case", "order"])["extra"]
    .agg(victim_min="min", victim_max="max")
    .assign(victim_range=lambda df: df["victim_max"] - df["victim_min"])
    .groupby("case")["victim_range"]
    .max()
)
range_table = order_range.join(victim_range).reset_index()
range_table["order_vs_victim_range"] = range_table["order_range"] / range_table["victim_range"].replace(0, pd.NA)
display(range_table)

cv_summary = pd.DataFrame(
    [
        {"metric": "rows with CV < 1%", "value": int((e2_cv["cv"] < 0.01).sum())},
        {"metric": "total rows", "value": len(e2_cv)},
        {"metric": "max CV", "value": f"{e2_cv['cv'].max() * 100:.2f}%"},
    ]
)
display(cv_summary)

note(
    "Victim scoring is not irrelevant, but it is not the main bottleneck. The "
    "schedule decides whether cheap clean buffers exist at overflow windows."
)
