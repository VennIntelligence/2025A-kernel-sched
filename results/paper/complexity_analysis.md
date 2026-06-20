# Autoresearch Solver Complexity Analysis

This note analyzes `src/ks_core/solver.py` (the promoted "ours" solver) with

- `N = |V|`: number of DAG nodes,
- `E = |E|`: number of DAG edges,
- `B`: number of buffers (`ALLOC` nodes),
- `K = 3`: number of candidate topological orders,
- `W`: prefetch-window grid size (`W = 3` for P2 and `W = 5` for P3).

## Stage Breakdown

| Stage | Entry point | Time complexity | Notes |
| --- | --- | --- | --- |
| Candidate order generation | `_candidate_orders()` -> `_memory_aware_order()` | `O(K (N log N + E))` under heap-based ready-set maintenance | Each candidate builds adjacency/indegree arrays, maintains ready nodes, and emits one topological order. The abstract list-scheduling cost is `O(N log N + E)`. The current Python implementation uses set scans for some FREE/op choices, so its conservative worst case is `O(K (N^2 + E log N))`; in the paper-level bound we treat the ready set as a priority queue. |
| Address assignment and spill insertion | `_assign_memory_with_spills()` | `O(N + E + B^2)` per `(order, window)` | The scan over the order and buffer-use preprocessing is linear. Best-fit placement scans free intervals, and Belady victim selection scans resident buffers. With `B` allocations, the worst-case resident scan cost is `O(B^2)`. |
| Pipeline simulation | `compute_total_time()` in `src/ks_core/evaluator.py` | `O(N + E)` per assigned schedule | The evaluator builds predecessor lists, adds spill dependencies, and performs one pass over the scheduled nodes. Cache address readiness arrays are bounded by fixed hardware capacities, so address checks are constant with respect to `N`, `E`, and `B`. |
| Portfolio selection | outer loop in `solve()` | `O(K W (N + E + B^2))` plus candidate generation | P2 evaluates `3 x 3` `(candidate, window)` combinations. P3 evaluates `3 x 5` combinations. Each combination runs address assignment, extra-traffic scoring, and total-time simulation. |

## Overall Time Complexity

Candidate generation is performed once per candidate, then the portfolio evaluates all candidate/window pairs:

```text
O(K (N log N + E) + K W (N + E + B^2)).
```

Because `W >= 1`, this is commonly summarized as

```text
O(K W (N log N + E + B^2)).
```

For the paper statement, when `E = O(N)` or the DAG edge term is folded into the topological-scheduling pass, the bound can be written as:

```text
O(K W (N log N + B^2)).
```

With the fixed portfolio constants used by the solver (`K = 3`, `W = 3` for P2 and `W = 5` for P3), the asymptotic scaling is dominated by list scheduling plus the quadratic worst-case spill allocator:

```text
P2: O(N log N + E + B^2)
P3: O(N log N + E + B^2)
```

where P3 has a larger constant because it evaluates five prefetch windows instead of three.

## Space Complexity

The solver stores adjacency lists, indegrees, candidate orders, buffer states, memory offsets, spill entries, and evaluator predecessor/state maps:

```text
O(N + E + B + S)
```

where `S` is the number of spill entries. Since the spill engine can emit at most a bounded number of spill/reload records per buffer in the intended allocator regime, this is summarized as:

```text
O(N + E + B)
```

The evaluator also uses fixed-size per-cache address-readiness arrays whose size is bounded by hardware capacities and therefore does not scale with the DAG.
