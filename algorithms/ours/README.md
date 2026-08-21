# ours — scalable v2

The production kernel-scheduling method and comparison counterpart to
`algorithms/baseline/`.

[`solve.py`](solve.py) is intentionally thin: it re-exports `solve` from
[`ks_core.solver`](../../src/ks_core/solver.py), the single source of truth used
by the experiment runner as `algorithms.ours.solve`.

The original implementation was promoted from iter038. The active post-review
v2 solver now combines:

1. a generic `unlock_frontier` order that completes ready predecessor groups
   capable of jointly unlocking an early consumer;
2. true best-fit physical placement;
3. distance/cost and backed-share/fragmentation-adaptive victim policies;
4. a portfolio of legal orders, policies, and prefetch windows;
5. final selection by the real canonical key—`(extra, spills, time)` for P2
   and `(time, extra, spills)` for P3.

The structural order itself does not claim to infer dynamic backing state.
Under the current evaluator, COPY_IN membership is a static backed-buffer label:
a backed spill is charged one reload, while an unbacked/generated spill is
charged write plus reload. Explicit asymmetric cost enters victim selection and
the final P2 key.

## Validated headline

Against the stored official P2 artifacts, scalable v2 has five strict wins and
one tie; all six schedules are canonical-valid with zero violations. For P3
time, it has five wins and one loss (Conv_Case1).

Machine-readable sources:

- [`round11_audited_p2.json`](../../results/autoresearch_v2/round11_audited_p2.json)
  — production P2 metrics plus audited `C`, `D`, and `V=C+D`
- [`round6_formal_p3.json`](../../results/autoresearch_v2/round6_formal_p3.json)

`round7_public_ablation.json` is not the production source: it fixes H=0,
selects by `(E, spills)` without the time tie-break, and omits two cells of a
full frontier/best-fit/adaptive factorial design. Its `full` row is not the
selected production artifact.

## What is not part of the default solver

- [`scripts/agent_cost_order_search.py`](../../scripts/agent_cost_order_search.py) is a
  research-only order-repair exploration. Conv0 uses 10,000 seed-0 stochastic
  single-node proposals; Conv1 uses a targeted beam of 10 for two rounds.
  FA0/FA1 received 2,000-proposal probes with no observed gain; MM0/MM1 were not
  searched. These heterogeneous runs do not define a uniform six-case method.
- [`scripts/agent_direct_search.py`](../../scripts/agent_direct_search.py) is a
  fixed-order weighted traffic planner. It certifies minimum `E` for a fixed
  order when the lower bound is met and the independent continuous-packing stage
  validates. Packing tries deterministic greedy layouts before NoOverlap2D; it does not certify
  the P2 spill/time tie-breaks. Machine certificates are Conv0/unlock 57,408,
  Conv0/p1 81,504, and FA0/id_raw 3,584. FA1 is feasible at 32,512 versus lower
  bound 31,936. MM0's old 34,688-OPTIMAL claim is withdrawn: the CP incumbent is
  34,816 with lower bound 29,952, while the legal production result 34,688 is a
  better upper bound. The planner is not integrated into the default solver.
- The former overflow-area Φ surrogate is not used for production selection.

The capacity and synthetic studies are controlled H=0 checks, not production
portfolio reruns. Capacity covers only Conv0/L1, and “blind” describes only the
comparator ordering; both sides retain cost-aware planning machinery. Synthetic
results use the internal assigner and do not persist per-case canonical
artifacts; all 36 tie iter038, so they establish non-regression only.

## Evaluator scope

Current results optimize the repository's artifact semantics: backed status is
static, FREE requires residency, `max_vstay` is logical rather than physical,
and buffer read/write roles are not explicit. See
[`docs/research_summary.md`](../../docs/research_summary.md) for interpretation.

| Aspect | Value |
| --- | --- |
| Implementation | `ks_core.solver` |
| `Schedule.algorithm` tag | `ours` |
| Provenance | iter038 + post-review v2 AutoResearch evidence |
| Production mode | scalable portfolio with canonical objective selection |
