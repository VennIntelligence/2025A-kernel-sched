# Direct P2 optimization prototype

This prototype never reads an official baseline schedule and has no case-name
or operator-motif branches. It optimizes the primary P2 traffic component `E`
for a fixed order, then validates the emitted schedule, memory map, and spill
list with `ks_core.metrics.evaluate`. It does not optimize the secondary P2
spill-count and time tie-breaks, so every certificate below is a
**fixed-order traffic certificate**, not a complete lexicographic P2 certificate.

## Main result

For the generic `unlock_frontier` topological order on `Conv_Case0`, global
fixed-order traffic optimization produces:

| method | extra | spills | validity |
|---|---:|---:|---|
| previous promoted order + heuristic eviction | 88,044 | 339 | valid |
| `unlock_frontier` + scalable heuristic eviction | 66,828 | 140 | valid |
| `unlock_frontier` + exact eviction | **57,408** | **112** | valid |
| official artifact (comparison only) | 73,500 | 141 | valid |

The traffic-optimal result is 14.1% below the scalable heuristic, 21.9% below the
official artifact, and 34.8% below the previous promoted solver. CP-SAT reports
`OPTIMAL`, its objective equals the lower bound (57,408), and the concrete
NoOverlap2D feasibility solve reports `OPTIMAL`. Canonical evaluation reports
zero violations.

Artifacts:

- `P2_Conv_Case0_unlock_frontier_exact.json`
- `P2_Conv_Case0_unlock_frontier_exact_schedule.txt`
- `P2_Conv_Case0_unlock_frontier_exact_memory.txt`
- `P2_Conv_Case0_unlock_frontier_exact_spill.txt`

The same planner now has two additional standalone zero-gap certificates:

- `P2_Conv_Case0_p1_exact.json` plus
  `P2_Conv_Case0_p1_exact_{schedule,memory,spill}.txt`;
- `P2_FlashAttention_Case0_id_raw_exact.json` plus
  `P2_FlashAttention_Case0_id_raw_exact_{schedule,memory,spill}.txt`.

Other fixed-order results obtained during the prototype:

| case/order | emitted extra | lower bound / known upper bound | machine status |
|---|---:|---:|---|
| Conv_Case0 / `p1` | 81,504 | LB 81,504 | gap OPTIMAL; packing OPTIMAL; valid; 328 spills; 19.49 s |
| FlashAttention_Case0 / `id_raw` | 3,584 | LB 3,584 | gap OPTIMAL; packing GREEDY_VALID; valid; 14 spills; 2.17 s |
| FlashAttention_Case1 / `capfit_id` | 32,512 | LB 31,936 | gap FEASIBLE; packing OPTIMAL; valid; 127 spills; 123.96 s |
| Matmul_Case0 / `capfit_id` | 34,816 | LB 29,952; known legal UB 34,688 | gap FEASIBLE; packing GREEDY_VALID; valid; 272 spills; 120.09 s |

The FA1 row is a machine-checkable feasible result, not a zero-gap certificate.
The MM0 run supersedes the old prose-only claim that 34,688 was `OPTIMAL`.
Its CP-SAT incumbent (34,816) is worse than the already known legal heuristic
plan (34,688) on the same fixed order, so the correct audited interval for the
traffic optimum is `[29,952, 34,688]`.

## Formulation

For a fixed topological order, every buffer has mandatory events: ALLOC, each
user, and FREE. Keeping it resident between two consecutive events avoids one
spill charge. Each gap is therefore an optional interval whose benefit is the
canonical evaluator cost (`size` for COPY_IN-backed data, `2*size` otherwise).
Per-memory cumulative constraints select keep/spill gaps. A second packing
stage assigns concrete byte offsets to maximal residency segments. The
prototype then inserts canonical SPILL_OUT/SPILL_IN nodes and runs the normal
evaluator.

This makes cost awareness part of the optimizer itself, rather than only an
analysis or a local victim score. The cumulative optimum is a lower bound on
concrete fixed-order traffic. If a zero-gap selection packs and the emitted
artifact validates at the same `E`, it certifies minimum traffic for that fixed
order. For a legal plan with repeated interruptions inside one mandatory-event
gap, the binary gap mapping may charge only one of them; the proof uses
`relaxation traffic <= plan traffic`, not equality for every non-normalized plan.

## Usage

```bash
uv run python tmp/agent_direct_search.py \
  --cases Conv_Case0 \
  --exact-order unlock_frontier \
  --time-limit 30 \
  --out results/autoresearch_v2/agent_direct
```

The script also accepts `id_raw`, `capfit_id`, `capfit`, and `p1` as fixed
orders. Its older `--trials` mode is exploratory list-scheduler weight search;
the exact-order mode is the result reported here.

## Integration recommendation

Use the exact model as a research oracle and, only after more study, as a guarded
backend. Conv0/unlock and FA0 certify in 0.88 s and 2.17 s, while Conv0/p1 takes
19.49 s. FA1 retains a 576-byte gap after 123.96 s, MM0 retains a 4,864-byte gap
after 120.09 s, and Conv1's research run did not complete cumulative selection
plus packing. Similar node counts therefore do not yet justify a hard scaling
threshold. A production integration must impose a timeout, validate the
concrete layout, and fall back to the heuristic portfolio.

The stronger research direction is a two-level direct optimizer:

1. generic structural frontier scheduling to shorten expensive live ranges;
2. weighted residency-gap optimization (exact for small cases, approximated for
   large cases).

This is more defensible than claiming that clean/dirty composition alone is the
optimization mechanism. On Conv0, the same exact planner certifies 81,504 for
`p1` and 57,408 for `unlock_frontier`: changing only the fixed order reduces the
traffic optimum by 29.56%. On the `unlock_frontier` order, exact traffic planning
then improves the scalable heuristic from 66,828 to 57,408 (14.1%). These are
same-case isolation results; they do not establish universal gains.

## Evaluator/model cautions

- Clean/dirty is a static buffer label: any buffer ever used by COPY_IN is
  treated as clean for every later spill. Conv_Case1 has 30 such buffers that
  later appear as the first operand of CONV/CONV_ADD. The current winning
  schedule does not spill those buffers after that later operation, so its
  reported extra is unaffected, but another order could be undercharged if the
  first operand is a destination.
- FREE is modeled as a mandatory residency event: a buffer spilled after its
  final semantic use must be reloaded before FREE. That is an artifact-format
  rule, not a hardware traffic necessity, and can distort alternative orders.
- `compute_max_vstay` reports logical ALLOC-to-FREE occupancy and ignores spill
  residency. It must not be interpreted as physical peak occupancy of a P2
  schedule.
- The scalable assigner is an online, contiguous-address heuristic. Its spill
  count mixes capacity pressure, victim choice, and address fragmentation. A
  live-byte/clean-share plot alone does not isolate these causes.
- `OPTIMAL` in the packing column means the satisfaction model proved
  feasibility; the packing stage has no layout-quality objective.
- The source of truth for a run is its `*_exact.json` plus matching schedule,
  memory, and spill files. Prose-only historical statuses must not override a
  newer machine record.
- `node.bufs` has no explicit read/write annotation. Static cleanliness and
  destination inference should be formalized before making a semantic theorem
  about dirty state transitions.
