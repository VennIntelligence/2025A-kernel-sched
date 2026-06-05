# %% [markdown]
# ## 2. 操作类型分布
#
# 逐 case 统计各操作类型的数量，了解 DAG 的组成结构。

# %%
for case in cases:
    inst = load_json(DATA_DIR / f"{case}.json")
    op_counts = pd.Series([n.op for n in inst.nodes]).value_counts()
    print(f"\n=== {case} ===")
    print(op_counts)

# %% [markdown]
# > **数据说明**: 每个 case 中各操作类型（ALLOC、FREE、COMPUTE 等）的出现次数。
# > **数据分布**: ALLOC/FREE 内存管理操作通常占节点总数的显著比例。
# > **核心发现**: 理解操作类型分布有助于后续设计针对性的调度策略 —
# > 计算密集型 case 可能更关注指令并行度，内存密集型 case 可能更关注 spill/reload 成本。
