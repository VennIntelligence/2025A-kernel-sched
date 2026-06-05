# %% [markdown]
# ## 1. Case 总览
#
# 加载全部 case 并汇总关键统计量：节点数、边数、计算操作数、内存分配数、总 buffer 大小。

# %%
summaries = []
for case in cases:
    inst = load_json(DATA_DIR / f"{case}.json")
    ops = [n for n in inst.nodes if n.op not in ("ALLOC", "FREE")]
    allocs = [n for n in inst.nodes if n.op == "ALLOC"]
    summaries.append({
        "case": case,
        "total_nodes": len(inst.nodes),
        "total_edges": len(inst.edges),
        "compute_ops": len(ops),
        "alloc_ops": len(allocs),
        "total_buf_size": sum(n.size for n in allocs),
    })

df_summary = pd.DataFrame(summaries)
df_summary

# %% [markdown]
# > **表格说明**: 6 个 case 的关键规模指标。
# > **数据分布**: Case 0 为小规模实例（千级节点），Case 1 为大规模实例（万级节点）。
# > **核心发现**: 三种 kernel（Conv、FlashAttention、Matmul）在图结构复杂度上差异显著，
# > 后续算法设计需要关注不同规模下的 scalability。
