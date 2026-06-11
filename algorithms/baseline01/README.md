# Baseline GPT Solution

GPT 第一轮生成的求解方案。保留原始输出作为 baseline 对照。

## 算法概述

- **Problem 1**：基于拓扑排序的指令调度（op_id_jit / 无 spill）
- **Problem 2**：Belady-Cost eviction policy 的寄存器分配
- **Problem 3**：Belady-Cost + fragment 优化

## 原始输出

| 目录 | 内容 |
|------|------|
| `Problem1/` | 6 个 case 的 schedule.txt |
| `Problem2/` | 6 个 case 的 schedule.txt + memory.txt + spill.txt |
| `Problem3/` | 6 个 case 的 schedule.txt + memory.txt + spill.txt |
| `metrics.csv` | 汇总评估指标 |
| `policy_benchmark.json` | 5 种 eviction policy 的对比数据 |

## Benchmark Results

| Case | P1 Time | P2 Time (belady_cost) | P3 Time (best) |
|------|---------|----------------------|----------------|
| Conv_Case0 | 359,570 | 535,312 | 535,312 |
| Conv_Case1 | 573,395 | 1,150,333 | 1,073,322 (fragment) |
| FlashAttention_Case0 | 31,429 | 53,374 (cheap) | 46,761 |
| FlashAttention_Case1 | 113,445 | 193,059 | 193,059 |
| Matmul_Case0 | 82,773 | 194,331 | 194,331 |
| Matmul_Case1 | 583,525 | 1,800,218 | 1,800,218 |
