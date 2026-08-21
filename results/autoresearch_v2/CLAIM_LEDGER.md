# Paper v2 claim ledger (root audit)

Date: 2026-07-11

This file is a coordination checklist, not a paper source. Every headline claim
must map to one of the machine-readable artifacts below.

## Method names and scope

- **Scalable v2**: the production `ks_core.solver.solve` portfolio. Components:
  structural `unlock_frontier`, true best-fit placement, two victim policies,
  and exact objective selection over policy/order/window candidates.
- **Cost-aware repair**: research prototype in `tmp/agent_cost_order_search.py`.
  It edits a legal order and accepts only strict improvements under the
  asymmetric traffic key. The recorded experiments use different proposal
  methods and budgets across cases; MM0/MM1 were not searched. It is exploratory
  mechanism evidence, not a uniform six-case method or the production default.
- **Fixed-order exact planner**: CP-SAT research backend in
  `tmp/agent_direct_search.py`. It optimizes weighted residency gaps for a fixed
  order, then solves concrete packing and validates the artifact. It is an
  oracle / possible future guarded backend, not an unconditional scalable path.
  It certifies minimum **traffic E** for a fixed order when the gap is zero and
  packing validates; it does not optimize the P2 spill-count/time tie-breaks.

## Objective identity

For spilled bytes split into backed/clean volume C and dirty volume D:

    E = C + 2D = (C + D) + D = V + D.

This is an accounting identity. It does not by itself prove that composition is
the dominant scheduling mechanism. Report both V and D when making mechanism
claims.

Paired production-vs-official reductions `(delta V, delta D, delta E)` are:

- Conv0 `(2832, 3840, 6672)`;
- Conv1 `(677, -171, 506)`;
- FA0 `(54, 54, 108)`;
- FA1 `(164, 164, 328)`;
- MM0 `(256, 0, 256)`;
- MM1 `(0, 0, 0)`.

Thus every strict public win reduces `V`; Conv1 wins despite increasing `D`.
FA0 is unbacked-only and both Matmul cases are backed-only, so their class mix
does not identify a composition-shaping mechanism.

## Canonical P2 (scalable v2 vs official)

Source: `results/autoresearch_v2/round10_final_p2.json`.

| Case | Scalable v2 | Official | Interpretation |
|---|---:|---:|---|
| Conv_Case0 | 66,828 | 73,500 | strict P2 win |
| Conv_Case1 | 72,734 | 73,240 | strict P2 win |
| FlashAttention_Case0 | 3,584 | 3,692 | strict P2 win |
| FlashAttention_Case1 | 32,512 | 32,840 | strict P2 win |
| Matmul_Case0 | 34,688 | 34,944 | strict P2 win |
| Matmul_Case1 | 460,800 | 460,800 | P2 tie; time tie-break win |

All six rows are canonical-valid with zero violations. Never mix these official
P2 values with official P3 artifacts.

`round10_final_p2.json` and `round6_formal_p3.json` are metric/validation ledgers;
matching production schedule/memory/spill files are not stored beside them.
Independent artifact replay therefore requires rerunning the deterministic
solver. Do not describe the JSON rows themselves as persisted complete artifacts.

These are 5 wins / 1 tie **against official**. Against the actual promoted
`iter038_id_raw_candidate`, scalable v2 is 3 wins / 2 ties / 1 loss; Conv1
regresses from 72,520 to 72,734. Do not call the round-7 H=0 reference the actual
iter038 production artifact.

## Canonical P3

Source: `results/autoresearch_v2/round6_formal_p3.json`.

P3 time wins on Conv0, FA0, FA1, MM0, MM1; loses on Conv1
(1,118,687 vs 1,073,322). State **5/6 time wins**, not universal dominance.
P3 extra is not the P2 objective and can be worse because P3 minimizes time.

Within our own outputs, P3 uses more traffic and less time than P2 on all six
cases. The `(traffic bytes, cycles)` changes are Conv0 `(2884, -5400)`, Conv1
`(8, -35985)`, FA0 `(512, -8612)`, FA1 `(1792, -11802)`, MM0 `(256, -5560)`,
and MM1 `(128, -11700)`. This is an observed portfolio trade-off, not a global
Pareto-optimality claim.

## Round-7 ablation boundary

Source: `results/autoresearch_v2/round7_public_ablation.json` and
`tmp/ablate_solver_v2.py`.

- Every row fixes `prefetch_window=0` and selects only by `(extra, spills)`, not
  the complete P2 `(extra, spills, time)` key.
- The six configurations are `000, 010, 100, 001, 101, 111` for
  frontier / best-fit / adaptive. Missing `011` and `110` mean this is not a
  complete factorial design.
- Its `full` row is adaptive + best-fit + H=0, not the canonical
  order/policy/window portfolio. It can match production traffic without being
  the same selected artifact.
- The row named `iter038` is an H=0 controlled reference. On Conv1 it is 73,348,
  whereas actual promoted iter038 is 72,520.
- A `best-fit + frontier - reference - full` residual also contains adaptive
  policy; never label it an isolated interaction or synergy estimate.

## Cost-aware order repair

Source: `results/autoresearch_v2/agent_cost_order/final_summary.json`.

- Conv0: 66,828 -> 65,532 (1,296 lower than structural order).
- Conv1: 72,734 -> 70,940 (1,794 lower).
- FA0 and FA1: 2,000 stochastic proposals each, no observed improvement.
- MM0 and MM1: repair search not run; the unchanged rows in `final_summary.json`
  are baseline carry-forwards, not negative search results.

Conv0 uses 10,000 stochastic single-node proposals (seed 0); Conv1 uses a
spill-targeted beam of 10 for two rounds. Post-hoc order inspection associates
both gains with advancing backed ALLOC/COPY_IN-related events. This is evidence
that cost semantics can affect ordering, but not evidence for a uniform repair
algorithm or universal benefit. The repair directory does not contain a complete
canonical-evaluator artifact for every case.

## Fixed-order exact evidence

Source: `results/autoresearch_v2/agent_direct/`.

- Conv0 + unlock_frontier: machine certificate at 57,408, lower bound 57,408,
  gap OPTIMAL, packing OPTIMAL, canonical valid, 112 spills, 0.88 s. Source:
  `P2_Conv_Case0_unlock_frontier_exact.json` plus matching text artifacts.
- Conv0 + p1: machine certificate at 81,504, lower bound 81,504, gap OPTIMAL,
  packing OPTIMAL, canonical valid, 328 spills, 19.49 s. Source:
  `P2_Conv_Case0_p1_exact.json` plus matching text artifacts. Under the same
  planner, changing only the fixed order to unlock_frontier reduces the traffic
  optimum by 29.56%; this isolates an order bottleneck for Conv0 only.
- FA0 + id_raw: machine certificate at 3,584, lower bound 3,584, gap OPTIMAL,
  packing GREEDY_VALID, canonical valid, 14 spills, 2.17 s. Source:
  `P2_FlashAttention_Case0_id_raw_exact.json` plus matching text artifacts.
- FA1 + capfit_id: machine-checkable FEASIBLE artifact at 32,512, lower bound
  31,936, gap 576, packing OPTIMAL, canonical valid, 127 spills, 123.96 s.
  Source: `P2_FlashAttention_Case1_capfit_id_exact.json`; do not call certified
  or optimal.
- MM0 + capfit_id: the reproducible 120.09 s run is FEASIBLE at 34,816 with
  lower bound 29,952 and packing GREEDY_VALID. A known legal heuristic artifact
  on the same order has 34,688, so the audited optimum interval is
  `[29,952, 34,688]`. The old prose-only `34,688 OPTIMAL` claim is revoked.
  Source: `P2_Matmul_Case0_capfit_id_exact.json`.
- Conv1 did not finish exact + packing within the research budget; MM1 not run.

`OPTIMAL` on a packing satisfaction model means packing feasibility was proved;
it is not a layout-quality objective. Machine JSON + matching schedule/memory/
spill files override older prose or hand-entered status metadata.

## Robustness and boundaries

- Capacity sweep (`round8_capacity_sweep.json`): the Conv0 H=0
  four-order/two-policy slice never loses the selected `cp_free_first` order
  comparator for feasible L1 capacities 3,072--16,384. It is one case, one
  cache, and not the full P2 window grid. “Blind” describes only the comparator
  order; both sides use best-fit and select among victim policies that include
  cost semantics. Capacities 2,048 and 2,560 are impossible because a mandatory
  pinned L1 operand set reaches 3,072 bytes.
- Synthetic (`round9_synthetic_summary.json`): H=0 internal-assigner results are
  14 wins / 22 ties / 0 losses vs the selected order-blind comparator, but 36/36
  tie iter038. All 18 order-reachable rows have zero traffic. This is a
  non-regression boundary, not new-module generalization or canonical artifact
  validation.
- Evaluator caveats: static clean labels, FREE as mandatory residency event,
  logical rather than physical `max_vstay`, and missing explicit buffer
  read/write roles.

## Forbidden legacy claims

- No 2.4--26x headline.
- No E5 fixed-pressure composition evidence or old `Dirty-heavy` label.
- No claim that Phi is used by the production solver.
- No claim that all candidate orders use clean/dirty information.
- No claim of first joint scheduling/memory optimization (COSMA predates it).
- No claim of universal cost-aware-repair or exact-backend improvement.
- No claim that repair was run uniformly on all six cases.
- No claim that round-7 is factorial, that its `full` row is the production
  artifact, or that its H=0 `iter038` row is the promoted solver.
- No claim that MM0 is exact/optimal; the current run is FEASIBLE and gapped.
- No claim of complete P2 optimality from a traffic-only fixed-order certificate.
- No claim that the selected “blind” comparator is a cost-blind planner; only
  its order is category-blind.
- No comparison that silently mixes P2 and P3 official schedules.
