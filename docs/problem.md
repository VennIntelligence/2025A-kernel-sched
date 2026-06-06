### 1. Problem Essence

Given a neural-operator computation DAG whose nodes are hardware operations or cache-management events, construct valid topological schedules and cache-address assignments for a SIMD/NPU core so as to minimize peak cache residency, spill-induced extra DDR traffic, and finally total pipelined execution time under multi-cache/multi-pipe resource constraints.  

### 2. Input / Output Specification

**Input**

| item           |              type | meaning                                                                        |
| -------------- | ----------------: | ------------------------------------------------------------------------------ |
| `Nodes`        |      `list[Node]` | All DAG nodes: operation nodes + cache-management nodes.                       |
| `Edges`        | `list[[int,int]]` | Directed dependencies `[src_node_id, dst_node_id]`; schedule must respect all. |
| operation node |            object | Has `Id, Op, Pipe, Cycles, Bufs`; `Op != ALLOC/FREE`.                          |
| cache node     |            object | Has `Id, Op, BufId, Size, Type`; `Op in {ALLOC, FREE}`.                        |

**Graph-level rules**

- Ignoring cache-management nodes, computation starts from `COPY_IN`, proceeds through on-chip operations, and ends at `COPY_OUT`.
- Root nodes are exactly `ALLOC` nodes, and leaf nodes are exactly `FREE` nodes.
- `ALLOC` edges usually point to the producer of the corresponding buffer; consumers of that buffer point to its `FREE` node; producer-consumer dependencies are also explicit edges.

Sample task files, provided in equivalent JSON and CSV formats:

| task                   | nodes | edges | buffers `[OBSERVED]` | op nodes `[OBSERVED]` |
| ---------------------- | ----: | ----: | -------------------: | --------------------: |
| `Matmul_Case0`         |  4160 |  7104 |                 1216 |                  1728 |
| `Matmul_Case1`         | 30976 | 55040 |                 8960 |                 13056 |
| `FlashAttention_Case0` |  1716 |  2712 |                  572 |                   572 |
| `FlashAttention_Case1` |  6952 | 11184 |                 2328 |                  2296 |
| `Conv_Case0`           |  2580 |  3869 |                  831 |                   918 |
| `Conv_Case1`           | 36086 | 85653 |                12013 |                 12060 |

**Output**

```text
Attachment.rar
├── Problem1
│   └── <task>_schedule.txt
├── Problem2
│   ├── <task>_schedule.txt
│   ├── <task>_memory.txt
│   └── <task>_spill.txt
└── Problem3
    ├── <task>_schedule.txt
    ├── <task>_memory.txt
    └── <task>_spill.txt
```

| file                  | exact format                                   | required content                                                                                                                    |
| --------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `<task>_schedule.txt` | one node id per line                           | Problem 1: all original node ids exactly once. Problems 2/3: all original nodes + inserted `SPILL_OUT/SPILL_IN` nodes exactly once. |
| `<task>_memory.txt`   | `BufId:Offset` per line                        | Initial physical cache offset for each buffer.                                                                                      |
| `<task>_spill.txt`    | `BufId:NewOffset` per line; empty if no spills | Spill operations in order; each row defines target buffer and reload offset.                                                        |

Submission archive name: `Ａ<队号>.rar`. 

### 3. Objective & Metric

| problem   | optimization target                                            | metric/formula                                                                                                                                                                                                                                                            | direction                                                  |
| --------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Problem 1 | minimize peak resident cache demand of a valid topological schedule | Prefix maximum of `V_stay` over a complete schedule, as defined below. Problem 1 only asks for node order and does not require address assignment.                                                                                                                        | minimize `maxV_stay`                                       |
| Problem 2 | assign physical cache offsets and spills under capacity limits | Total extra data movement: sum over spills. If target buffer is not used by any `COPY_IN`, cost `2*Size`; if target buffer is used by a `COPY_IN`, cost `Size`.                                                                                                           | minimize                                                   |
| Problem 3 | improve runtime without materially increasing extra movement   | Total execution time `T = max_i E(v_i)` after adding spill nodes and address-reuse dependencies. For each node: `S(v_i) ≥ 0`; same pipe is serial in schedule order; `S(v_i) ≥ E(u)` for all predecessor edges; `E(v_i)=S(v_i)+Cycles(v_i)`; cache nodes have `Cycles=0`. | minimize `T`, optionally joint-optimize with spill traffic |

`[AMBIGUOUS: no single official scalar metric combines runtime and extra data movement; Problem 3 only says extra movement must not “significantly” increase, but gives no threshold.]`   

**Problem 1 `maxV_stay` definition**

For schedule `S = (v_1, ..., v_N)`, traverse all scheduled nodes:

```text
M_v = Size(v)   if Op_v = ALLOC
M_v = -Size(v)  if Op_v = FREE
M_v = 0         otherwise

V_stay(0) = 0
V_stay(i) = V_stay(i-1) + M_{v_i}
maxV_stay = max_i V_stay(i)
```

Operation nodes are still traversed, but they contribute `0`.

### 4. Constraints & Boundaries

**Hard constraints**

| constraint               | rule                                                                                                                                   |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| DAG validity             | Schedule must be a topological ordering of all required nodes.                                                                         |
| Node coverage            | No missing/duplicate node ids in each schedule.                                                                                        |
| Cache address interval   | For Problems 2/3, buffer `b` with `Size=s` and `Offset=o` occupies contiguous `[o, o+s-1]` in cache `Type`.                              |
| Capacity                 | For Problems 2/3, initial/reload offsets must fit within cache capacity: `0 ≤ Offset` and `Offset + Size ≤ Capacity(Type)`.             |
| Non-overlap              | For Problems 2/3, same-cache buffers resident at the same time cannot overlap physical address intervals.                                |
| Address reuse dependency | In `ALLOC` execution order, if buffer `b` reuses physical space of earlier buffer `a`, add dependency `FREE(a) -> ALLOC(b)` before timing evaluation. |
| Pipe exclusivity         | A hardware pipe executes at most one node at a time and follows schedule order for nodes on that pipe.                                 |
| Spill node ids           | If original graph has `N` nodes, the first spill creates ids `N` and `N+1`; spill operation `k` (1-indexed) creates `SPILL_OUT id=N+2(k-1)`, `SPILL_IN id=N+2(k-1)+1`. |
| Spill pipes              | `SPILL_OUT` uses `MTE3`; `SPILL_IN` uses `MTE2`; both have `Bufs=[target BufId]`.                                                      |
| Spill dependencies       | Add `ALLOC -> SPILL_OUT -> SPILL_IN -> FREE`; for operation nodes whose `Bufs` contains the target `BufId`, executed users precede `SPILL_OUT`, and unexecuted users follow `SPILL_IN`. |

**Hardware cache capacities**

| cache | capacity |
| ----- | -------: |
| `L1`  |     4096 |
| `UB`  |     1024 |
| `L0A` |      256 |
| `L0B` |      256 |
| `L0C` |      512 |

**Spill cycle formulas**

```text
If target buffer is not used by any COPY_IN:
  Cycles(SPILL_OUT) = Size*2 + 150
  Cycles(SPILL_IN)  = Size*2 + 150

If target buffer is used by a COPY_IN:
  Cycles(SPILL_OUT) = 0
  Cycles(SPILL_IN)  = Size*2 + 150
```

`[INFERRED]` A spilled buffer frees its old cache interval after `SPILL_OUT` and becomes resident again at `NewOffset` after `SPILL_IN`; memory feasibility should be checked over residency segments, not only logical `ALLOC..FREE` lifetime.   

### 5. Data Schema

**JSON files**

```text
field_name | type | description | example_value
Nodes | list[object] | all graph nodes | [{"Id":0,"Op":"ALLOC","BufId":0,"Size":1,"Type":"UB"}, ...]
Edges | list[list[int,int]] | dependency edges [src,dst] | [0,1]

Nodes[].Id | int | unique node id; samples are contiguous 0..N-1 [OBSERVED] | 0
Nodes[].Op | string | operation name or cache directive | "ALLOC", "COPY_IN"
Nodes[].BufId | int? | cache-node buffer id; present only for ALLOC/FREE | 0
Nodes[].Size | int? | cache-node buffer size in abstract cache units | 1
Nodes[].Type | string? | cache type for ALLOC/FREE | "UB"
Nodes[].Pipe | string? | execution unit for operation nodes | "MTE2"
Nodes[].Cycles | int? | execution latency for operation nodes | 15
Nodes[].Bufs | list[int]? | input/output buffer ids used by operation node | [0]

Edges[][0] | int | source node id | 0
Edges[][1] | int | destination node id | 1
```

**CSV files**

Each task also has `<task>_Nodes.csv` and `<task>_Edges.csv`. The CSV data carries the same graph as the JSON file.

`<task>_Nodes.csv`:

```text
Id,Op,BufId,Size,Type,Pipe,Cycles,Bufs
0,ALLOC,0,1,UB,,,
1,COPY_IN,,,,MTE2,15,"0"
```

| CSV column | JSON field | type after parsing | meaning |
| ---------- | ---------- | ------------------ | ------- |
| `Id`       | `Id`       | `int`              | Node id. |
| `Op`       | `Op`       | `str`              | Operation/cache directive. |
| `BufId`    | `BufId`    | `int?`             | Present for `ALLOC/FREE`; blank for operation nodes. |
| `Size`     | `Size`     | `int?`             | Present for `ALLOC/FREE`; blank for operation nodes. |
| `Type`     | `Type`     | `str?`             | Present for `ALLOC/FREE`; blank for operation nodes. |
| `Pipe`     | `Pipe`     | `str?`             | Present for operation nodes; blank for `ALLOC/FREE`. |
| `Cycles`   | `Cycles`   | `int?`             | Present for operation nodes; blank for `ALLOC/FREE`. |
| `Bufs`     | `Bufs`     | `list[int]?`       | Quoted comma-separated buffer ids for operation nodes; blank for `ALLOC/FREE`. |

`<task>_Edges.csv`:

```text
StartNodeId,EndNodeId
0,1
```

| CSV column    | JSON field | type after parsing | meaning |
| ------------- | ---------- | ------------------ | ------- |
| `StartNodeId` | `Edges[][0]` | `int`            | Source node id. |
| `EndNodeId`   | `Edges[][1]` | `int`            | Destination node id. |

`[OBSERVED]` In all six sample tasks, parsing CSV rows with comma-separated `Bufs` reproduces the JSON `Nodes` and `Edges` exactly. `Bufs` may contain multiple ids, for example `"3,1"` or `"4,1,0,3"`; the maximum observed list length is 7.

**Observed JSON enums**

```text
Op =
  ALLOC, FREE,
  COPY_IN, COPY_OUT, COPY, MOVE,
  MATMUL, CONV, CONV_ADD,
  ADD, SUB, MUL, MAX, EXP, REC, ROWMAX, ROWSUM, COMPACT, D2S

Pipe =
  MTE1, MTE2, MTE3, FIXP, CUBE, VECTOR

Type =
  L1, UB, L0A, L0B, L0C

Size observed =
  1, 2, 4, 6, 8, 16, 24, 32, 36, 48, 64, 72, 96, 128, 144, 192, 256, 384, 768, 1536

Cycles observed =
  integer range 10..3771
```

**Node-shape invariant**

```text
Cache node:
  {"Id": int, "Op": "ALLOC"|"FREE", "BufId": int, "Size": int, "Type": str}

Operation node:
  {"Id": int, "Op": str, "Pipe": str, "Cycles": int, "Bufs": list[int]}
```

`[OBSERVED]` In all six JSON files, every `BufId` has exactly one `ALLOC` and one `FREE`, and every referenced `Bufs[]` id has a corresponding allocation.

### 6. Solution Space

| component            | applicable solution class                                                                                                                                                         |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Problem 1 schedule   | precedence-constrained DAG scheduling / weighted live-memory minimization / list scheduling with memory-aware priority.                                                           |
| Problem 2 allocation | dynamic storage allocation / interval packing / online or offline first-fit-best-fit with compaction-aware ordering; spill selection resembles register allocation with eviction. |
| Problem 3 runtime    | resource-constrained project scheduling / multi-pipe list scheduling / latency-hiding pipeline scheduling.                                                                        |

**Baseline implied**

```text
1. Produce any topological order.
2. Compute maxV_stay by ALLOC/FREE prefix scan.
3. Assign cache offsets by first-fit over live intervals.
4. When no interval fits, choose a resident buffer to spill, insert SPILL_OUT/SPILL_IN, then reload at a feasible NewOffset.
5. Evaluate runtime by serializing same-pipe operations in schedule order plus DAG/reuse/spill dependencies.
```

**Hints / allowed optimization directions**

| operator family | hinted strategy                                                                                                                                                   |
| --------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Matmul          | block scheduling; interleave `COPY_IN -> MOVE -> MATMUL/MMAD -> COPY_OUT`; zigzag block traversal can reduce repeated B-matrix reloads versus row-wise traversal. |
| FlashAttention  | interleave block stages to exploit both `CUBE` and `VECTOR`; account for Q/K/V reuse and row-wise merged outputs.                                                 |
| Conv            | choose depth-first vs breadth-first scheduling depending on feature-map/kernel residency tradeoff.                                                                |
| All             | revise Problem 1 schedule if needed for Problem 2 spill minimization; Problem 3 may optimize schedule or memory allocation.                                       |

Framework auto-inserts synchronization instructions; solver only outputs node order, memory offsets, and spill list.    

### 7. Key Ambiguities / Traps

| trap                                                                                                                           | consequence                                                                                    |
| ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| Problem 1 says to ignore physical cache length limits and only output a schedule.                                               | Do not add Problem 2/3 address-capacity constraints to Problem 1 validation.                   |
| Address reuse creates extra dependencies.                                                                                      | Memory allocation can worsen runtime even if spill traffic is unchanged.                       |
| Same-pipe order is schedule order, not arbitrary earliest-ready order.                                                         | Timing evaluator must not reorder operations within a pipe.                                    |
| `COPY_IN`-origin buffers have special spill semantics.                                                                         | Extra movement is `Size`, not `2*Size`; `SPILL_OUT` cycles are `0`.                            |
| `spill.txt` gives only `BufId:NewOffset`; node ids are generated implicitly.                                                   | Wrong id generation breaks schedule validation.                                                |
| Cache lifetimes are schedule-dependent.                                                                                        | Reordering changes both peak memory and feasible address reuse.                                |
| Spill splits physical residency, not logical buffer identity.                                                                  | Same `BufId` may appear multiple times in `spill.txt`; each reload may use a different offset. |
| Problem 3 “not significantly increase” is undefined.                                                                           | Need report Pareto tradeoff or define own threshold explicitly.                                |
| Document uses mixed naming style (`Cube/Vector`, diagrams mention `MMAD`); JSON uses exact strings `CUBE`, `VECTOR`, `MATMUL`. | Solvers should parse exact JSON strings, not normalize blindly.                                |
| Sample graphs are only validation cases.                                                                                       | Hardcoding Matmul/FA/Conv motifs may fail on arbitrary future DAGs.                            |
| `Size` unit is not bytes.                                                                                                      | Treat `Size` and capacities as abstract consistent units.                                      |
| Zero-cycle cache nodes still matter.                                                                                           | They affect topology, lifetime, reuse dependencies, and feasibility.                           |
