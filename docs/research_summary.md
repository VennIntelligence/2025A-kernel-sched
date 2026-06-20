# Research Summary — Spill-Cost-Aware Liveness Shaping

This document is the concise source for the final research narrative. The
append-only log in `docs/agent_research_log.md` is kept for traceability, but it
contains failed hypotheses and intermediate claims that were later revised.

## Key Milestones

1. Early P1 work moved from a seed topological order to a memory-aware list
   scheduler, establishing schedule order as the main lever for live pressure.
2. D2S/readiness-gated allocation priorities improved Conv-like P1 schedules,
   but also showed that structure-specific tie-breaks are fragile.
3. `iter031` achieved 6/6 wins on the official P1 key, while exposing that P1
   peak minimization can create UB/L0 pressure that is harmful for P2/P3.
4. The balanced P1 audit reframed the project around capacity overflow, spill
   extra traffic, and final pipeline time rather than P1 alone.
5. `iter034` introduced a unified P1/P2/P3 solver with candidate orders,
   physical placement, spill insertion, and true-cost selection. It was the first
   complete 18/18-valid solution and reached 8/18 wins against baseline.
6. `iter035` and `iter036` separated P2 traffic optimization from P3 timing,
   adding SPILL_IN prefetch windows and time tie-breaks. The result improved to
   11/18 wins.
7. Follow-up diagnosis showed that victim scoring was not the limiting factor:
   schedule order dominated spill traffic by changing which clean buffers remain
   available during overflow.
8. `iter037` widened the P3 prefetch grid, and `iter038` added the `id_raw`
   candidate order. The final solver reached 18/18 valid rows and 13/18 wins.

## Final Solver

The promoted solver is `iter038_id_raw_candidate`, implemented in
`src/ks_core/solver.py` and exposed as the method `algorithms/ours/solve.py`.

- P1 uses the promoted memory-aware list scheduler.
- P2/P3 evaluate a small portfolio of candidate orders: `capfit_id`, `p1`, and
  `id_raw`.
- Physical placement scans the fixed order, assigns cache offsets, and inserts
  SPILL_OUT/SPILL_IN pairs when capacity requires eviction.
- The eviction rule is a cost-aware Belady-style score: far-future buffers are
  preferred, but clean COPY_IN buffers are cheaper to spill than dirty buffers.
- P2 selects by `(extra, spills, time)`.
- P3 selects by `(time, extra, spills)` and scans a wider prefetch-window grid to
  hide reload latency.

## What Failed, And What We Learned

The many negative attempts are best summarized as eliminated directions:

- P1-only tuning overfits the lexicographic P1 key and can damage P2/P3.
- Conv/D2S-specific tie-breaks can help local cases but do not provide a clean
  general method.
- Pipeline-ready and ready-op tie-breaks rarely help when the blocking factor is
  earlier allocation/reload availability.
- Delaying large L1 buffers, narrowing to COPY_IN buffers, DFS variants,
  lazy-free variants, operand-locality, and zigzag-style reorderings did not
  reliably reproduce the useful cheap-buffer residency pattern.
- Victim-scoring variants are secondary. They can affect some rows, but the
  order-induced range is much larger than the victim-policy range.

These results should not be deleted from history: they define the boundary of
the final method. They should not, however, dominate the final paper narrative.

## Final Claims To Preserve

- The final artifacts are valid for all 18 case/problem rows.
- The solver wins 13/18 rows against the contest baseline, including 6/6 on P1.
- The remaining losses are concentrated in Conv0 P2/P3, Conv1 P3, FA0 P2, and
  FA1 P2. They are order-level gaps rather than failures of the spill engine.
- The clean/dirty spill-cost asymmetry is the core useful signal: COPY_IN
  buffers behave like clean pages, while computed buffers behave like dirty pages.
- The schedule should shape the live set so clean buffers remain available near
  overflow peaks as cheap eviction reserves.
- The capacity-overflow integral is useful as a cheap, lifetime-aware proxy, but
  it should not be oversold as uniformly more predictive than peak pressure.
- The portfolio/take-min design is an engineering strength: adding candidates or
  prefetch windows can only improve or tie the selected official key.

## Source Files

- Final solver: `src/ks_core/solver.py` (method entry point `algorithms/ours/solve.py`)
- Best iteration marker: `autoresearch/best_iter.txt`
- Iteration trajectory: `autoresearch/ledger.csv`
- Headline metrics: `results/paper/e1_headline.csv`
- Portfolio trajectory: `results/paper/e10_portfolio.csv`
- Paper thesis and experiment matrix:
  `docs/paper/01_thesis_and_experiments.md`
