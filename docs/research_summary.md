# Research Summary — Dependency-Frontier Scheduling with Asymmetric-Cost Spill Planning for NPU Kernels

This document is the concise narrative for the post-review implementation. The
historical AutoResearch ledger remains useful for provenance, but it contains
intermediate claims that are no longer supported and must not be repeated as
current conclusions.

## Revised thesis

The original narrative combined three different observations:

1. backed/clean and dirty spills have canonical costs of `size` and `2*size`;
2. allocator-friendly schedule order can drastically change spill volume;
3. the proposed ordering wins because it explicitly controls clean/dirty
   composition.

The repository establishes the first two. The old candidate-order generators
did not read clean/dirty state, and the former E5 comparison neither held
pressure fixed nor labeled composition correctly. The defensible thesis is:

> Dependency-frontier scheduling provides the scalable structural order;
> weighted fixed-order traffic planning provides lower bounds and concrete
> packing certificates. Cost-aware order repair remains exploratory.

The accounting identity

```text
E = C + 2D = V + D,
```

where `C` and `D` are backed and generated-or-unbacked spill volumes and
`V=C+D`, explains why unbacked bytes add cost. It does not prove that composition dominates order
locality. Mechanism analyses should report both total spill volume and
generated-or-unbacked spill volume.

## Active solver: scalable v2

The production implementation is [`src/ks_core/solver.py`](../src/ks_core/solver.py),
exposed through [`algorithms/ours/solve.py`](../algorithms/ours/solve.py).

Its current components are:

- a generic `unlock_frontier` order that completes ready allocation groups
  capable of jointly unlocking an early consumer;
- true best-fit physical placement;
- a portfolio containing distance/cost and backed-share/fragmentation-adaptive
  victim policies;
- order, policy, and prefetch-window evaluation using the real canonical key;
- graceful rejection of infeasible portfolio members.

P2 minimizes `(extra, spills, time)`. P3 minimizes `(time, extra, spills)`.
Neither production path uses the former overflow-area surrogate as its final
selection criterion.

### Canonical P2

| Case | Scalable v2 | Official | Outcome |
| --- | ---: | ---: | :---: |
| Conv_Case0 | **66,828** | 73,500 | WIN |
| Conv_Case1 | **72,734** | 73,240 | WIN |
| FlashAttention_Case0 | **3,584** | 3,692 | WIN |
| FlashAttention_Case1 | **32,512** | 32,840 | WIN |
| Matmul_Case0 | **34,688** | 34,944 | WIN |
| Matmul_Case1 | **460,800** | **460,800** | TIE; time tie-break win |

This is five strict wins and one tie. The maximum reduction is 9.08%; the
median reduction is 0.866%. All artifacts are canonical-valid with zero
violations. Source:
[`round11_audited_p2.json`](../results/autoresearch_v2/round11_audited_p2.json).
That audited production record is also the source of truth for backed spill
volume `C`, unbacked volume `D`, and total spill volume `V=C+D`.

The paired accounting against official P2 is narrow but informative:

| Case | ΔV | ΔD | ΔE=ΔV+ΔD |
| --- | ---: | ---: | ---: |
| Conv0 | 2,832 | 3,840 | 6,672 |
| Conv1 | 677 | -171 | 506 |
| FA0 | 54 | 54 | 108 |
| FA1 | 164 | 164 | 328 |
| MM0 | 256 | 0 | 256 |
| MM1 | 0 | 0 | 0 |

Every strict win reduces `V`; Conv1 wins despite increasing `D`. This is an
accounting decomposition, not an estimate of independent causal effects.

### Canonical P3

Scalable v2 wins five of six time comparisons, with a median reduction of
3.77%. Conv_Case1 regresses by 4.23%: 1,118,687 versus 1,073,322. P3 extra is a
secondary value selected under a time-first key and must not be mixed with the
P2 table. Source:
[`round6_formal_p3.json`](../results/autoresearch_v2/round6_formal_p3.json).

## Fixed-order weighted traffic planning

[`scripts/agent_direct_search.py`](../scripts/agent_direct_search.py) represents each
gap between mandatory buffer events as an optional residency interval. Keeping
a gap earns the avoided backed/unbacked traffic cost. CP-SAT cumulative
constraints choose gaps; a second stage assigns concrete offsets; the result is
emitted and evaluated in the normal artifact format. This independent packing
stage tries 48 deterministic greedy layouts before falling back to NoOverlap2D;
FA0 and MM0 are recorded as `GREEDY_VALID`.

The optimizer minimizes traffic `E` only. A zero lower-bound gap plus validated
packing certifies **fixed-order minimum traffic**, not the full P2
`(E, spills, time)` key and not the globally best topological order.

| Case / fixed order | Emitted E | Lower bound / known upper bound | Status |
| --- | ---: | ---: | --- |
| Conv0 / `unlock_frontier` | **57,408** | LB 57,408 | traffic certificate |
| Conv0 / `p1` | 81,504 | LB 81,504 | traffic certificate |
| FA0 / `id_raw` | **3,584** | LB 3,584 | traffic certificate |
| FA1 / `capfit_id` | 32,512 | LB 31,936 | FEASIBLE; gap 576 |
| MM0 / `capfit_id` | 34,816 | LB 29,952; legal UB 34,688 | FEASIBLE; not best known UB |

The Conv0 certificates use the same planner and differ only in fixed order:
81,504 to 57,408 is a 29.56% reduction, directly isolating an order bottleneck
for this case. The old MM0 “34,688 OPTIMAL” claim is revoked; 34,688 is instead
the better legal upper bound supplied by the production plan.

FA0 certifies quickly, whereas FA1 and MM0 remain gapped at roughly 120 seconds;
Conv1 does not complete the research path and MM1 was not run. Any future
guarded integration needs timeout, packing/evaluator validation, and fallback.

## Exploratory cost-aware order repair

### Heterogeneous order-repair probes

[`scripts/agent_cost_order_search.py`](../scripts/agent_cost_order_search.py) proposes
topologically legal relocations around spills and keeps only strict improvements
under the asymmetric `(E, spills)` search key.

| Case | Structural order | After repair | Search coverage |
| --- | ---: | ---: | --- |
| Conv_Case0 | 66,828 | **65,532** | seed 0; 10,000 stochastic single-node proposals |
| Conv_Case1 | 72,734 | **70,940** | targeted beam 10; 2 rounds |
| FA0 | 3,584 | 3,584 | 2,000-proposal probe; no observed gain |
| FA1 | 32,512 | 32,512 | 2,000-proposal probe; no observed gain |
| MM0 | 34,688 | 34,688 | repair not run |
| MM1 | 460,800 | 460,800 | repair not run |

The two gains show that cost semantics can affect ordering, but the methods and
budgets are not uniform. Matmul cannot be counted as a negative repair result,
and the repair directory does not persist a complete canonical artifact for
every row. Keep repair as exploratory mechanism evidence.

## Component-ablation boundary

`round7_public_ablation.json` fixes H=0 and selects by `(E, spills)` only. Its
six configurations omit two cells of the frontier/best-fit/adaptive design, so
it is not factorial. Its `full` row is not the production
order/policy/window artifact, and its H=0 `iter038` reference is not the actual
promoted solver on Conv1. Report conditional configurations, not an isolated
synergy estimate.

## Robustness evidence and its boundary

- **Capacity sweep.** This is a controlled H=0 Conv0/L1 study, not the full
  production window portfolio. The `cp_free_first` comparator is cost-blind only
  in its ordering; both sides retain shared best-fit and victim policies that
  include cost semantics.
- **Existing synthetic suite.** These H=0 internal-assigner results do not
  persist per-case canonical artifacts. The 14 wins / 22 ties against the
  selected order-blind comparator are inherited from iter038, which v2 ties on
  all 36. This supports non-regression only.
- **Related-work boundary.** COSMA already jointly optimizes operator schedule,
  allocation, and replacement; Checkmate and DTR address optimal and online
  rematerialization. The specific opportunity here is multi-cache micro-op
  DAGs, asymmetric backed/unbacked spill costs, dependency-frontier scheduling, and a verified
  exact-to-heuristic bridge.

## Evaluator semantics

The current results optimize the repository's canonical model, whose limits
must appear alongside mechanism claims:

1. Backing is a static COPY_IN-membership label. A COPY_IN buffer remains in the
   reload-only class even if a later operation may write it.
2. FREE is a mandatory residency event; a buffer spilled after its final
   semantic use must be reloaded before FREE.
3. `compute_max_vstay` measures logical ALLOC-to-FREE occupancy and does not
   report physical P2 residency.
4. `node.bufs` does not explicitly encode read versus write roles, so dirty
   state transitions cannot yet be formalized rigorously.
5. Online placement spill counts can reflect both capacity and contiguous-
   address fragmentation.

## Claims removed from the current narrative

- the former 2.4–26× headline;
- E5 as fixed-pressure clean/dirty evidence;
- the claim that overflow area Φ participates in production selection;
- the claim that every candidate order is clean/dirty-aware;
- universal superiority across all comparisons;
- universal benefit from cost-aware repair or the exact backend;
- the claim that repair was run uniformly on all six cases;
- the claim that round7 is factorial or its `full` row is production;
- the revoked MM0 34,688 exact/optimal claim;
- complete P2 optimality from a traffic-only fixed-order certificate;
- “first joint scheduling and memory optimization.”

## Sources of record

- Consolidated report:
  [`results/autoresearch_v2/RESEARCH_REPORT.md`](../results/autoresearch_v2/RESEARCH_REPORT.md)
- Scalable P2:
  [`round11_audited_p2.json`](../results/autoresearch_v2/round11_audited_p2.json)
- Scalable P3:
  [`round6_formal_p3.json`](../results/autoresearch_v2/round6_formal_p3.json)
- Cost-aware repair:
  [`agent_cost_order/final_summary.json`](../results/autoresearch_v2/agent_cost_order/final_summary.json)
- Exact planner:
  [`agent_direct/REPORT.md`](../results/autoresearch_v2/agent_direct/REPORT.md)
- Controlled H=0 component ablation:
  [`round7_public_ablation.json`](../results/autoresearch_v2/round7_public_ablation.json)
- Capacity and synthetic boundaries:
  [`round8_capacity_sweep.json`](../results/autoresearch_v2/round8_capacity_sweep.json),
  [`round9_synthetic_summary.json`](../results/autoresearch_v2/round9_synthetic_summary.json)
- Coordination claim ledger:
  [`CLAIM_LEDGER.md`](../results/autoresearch_v2/CLAIM_LEDGER.md)
- Original adversarial-forensics reconstruction:
  [`FORENSIC_REVIEW.md`](../results/autoresearch_v2/FORENSIC_REVIEW.md)
