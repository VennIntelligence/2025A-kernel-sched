# Running and validating the kernel-scheduling repository

Run commands from the repository root (`kernal_scheduling/`). The project is a
Python 3.12 `uv` workspace; do not install dependencies with `pip`.

This guide distinguishes the production solver from two research-only layers:

- **scalable v2** — `ks_core.solver.solve`, the default algorithm;
- **fixed-order weighted traffic planner** — research-only CP-SAT oracle that
  can certify minimum `E` for one order; it is not integrated into the default
  solver and does not optimize P2's spill/time tie-breaks;
- **cost-aware repair** — heterogeneous exploratory order searches, not a
  uniform production stage.

## 0. Environment and correctness gate

```bash
make setup
# equivalent dependency command:
uv sync --all-extras

make test
# or:
uv run pytest -v
```

Sanity-check the editable workspace package:

```bash
uv run python -c "from ks_core import solver; print(solver.solve.__module__)"
```

## 1. Validate scalable v2

The post-review validator invokes `algorithms.ours.solve`, evaluates every
artifact with the canonical evaluator, and attaches official metrics only after
the schedule has been generated.

### P2 extra traffic

```bash
uv run python scripts/validate_solver_v2.py \
  --problems 2 \
  --output results/autoresearch_v2/round11_audited_p2.json
```

Expected summary: five strict P2 wins and one tie against the official
artifacts; every row valid with zero violations. This audited output is also the
source of record for production backed volume `C`, generated/unbacked volume
`D`, and total spill volume `V=C+D`.

### P3 pipeline time

```bash
uv run python scripts/validate_solver_v2.py \
  --problems 3 \
  --output results/autoresearch_v2/round6_formal_p3.json
```

Expected summary: five time wins and one loss. Conv_Case1 is the loss. Do not
substitute P3 spill traffic for the P2 objective: P3 uses a time-first key.

To run a subset while iterating:

```bash
uv run python scripts/validate_solver_v2.py \
  --problems 2 \
  --cases Conv_Case0 FlashAttention_Case0 \
  --output results/autoresearch_v2/local_check.json
```

## 2. Run the fixed-order exact planner

Full reference: [`scripts/agent_direct_search.md`](../scripts/agent_direct_search.md).

The planner chooses weighted residency gaps for a fixed order, then runs an
independent continuous-packing stage: 48 deterministic greedy attempts followed
by NoOverlap2D only if those attempts fail. It emits schedule/memory/spill files
and runs the canonical evaluator. A zero gap plus validated packing certifies
minimum traffic `E` for that fixed order. It does not certify minimum spill
count or time among equal-E plans.

```bash
uv run python scripts/agent_direct_search.py \
  --cases Conv_Case0 \
  --exact-order unlock_frontier \
  --time-limit 30 \
  --out results/autoresearch_v2/agent_direct
```

For Conv_Case0, the expected fixed-order result is 57,408 extra with objective
equal to its lower bound, a validated contiguous packing, 112 spills, and zero
violations.

The three current machine-checkable traffic certificates can be reproduced as:

```bash
# Conv0 / unlock_frontier: E = LB = 57,408
uv run python scripts/agent_direct_search.py \
  --cases Conv_Case0 --exact-order unlock_frontier --time-limit 30 \
  --out results/autoresearch_v2/agent_direct

# Conv0 / p1: E = LB = 81,504
uv run python scripts/agent_direct_search.py \
  --cases Conv_Case0 --exact-order p1 --time-limit 30 \
  --out results/autoresearch_v2/agent_direct

# FA0 / id_raw: E = LB = 3,584
uv run python scripts/agent_direct_search.py \
  --cases FlashAttention_Case0 --exact-order id_raw --time-limit 30 \
  --out results/autoresearch_v2/agent_direct
```

Accepted fixed-order names are `unlock_frontier`, `id_raw`, `capfit_id`,
`capfit`, and `p1`. This research path is not uniformly scalable. Any future
production integration must use a timeout and retain the default solver as a
validated fallback. In the current study, FA1 is machine-checkable feasible at
32,512 against lower bound 31,936, but is not certified. The old MM0 “34,688
OPTIMAL” result is revoked: the reproducible CP-SAT incumbent is 34,816 with
lower bound 29,952, while the legal production result 34,688 provides a better
upper bound. Conv1 does not complete the research path and MM1 was not run.

## 3. Run cost-aware order repair

Full reference: [`scripts/agent_cost_order_search.md`](../scripts/agent_cost_order_search.md).

The repair code contains several exploratory searches rather than one uniform
six-case algorithm. The recorded runs use the asymmetric traffic key but differ
in proposal family and budget:

```bash
# Conv0: seed-0 stochastic single-node hill search, 10,000 proposals
uv run python scripts/agent_cost_order_search.py unlock_hill \
  --cases Conv_Case0 --iters 10000 --seed 0

# Conv1: targeted spill-frontier beam, width 10 for two rounds
uv run python scripts/agent_cost_order_search.py unlock_targeted \
  --cases Conv_Case1 --rounds 2 --beam 10

# Smaller no-gain probes on FA0 and FA1
uv run python scripts/agent_cost_order_search.py unlock_hill \
  --cases FlashAttention_Case0 FlashAttention_Case1 --iters 2000 --seed 0

# Compare the saved orders; this command does not itself run those searches
uv run python scripts/agent_cost_order_search.py final
```

The source-of-record output is
`results/autoresearch_v2/agent_cost_order/final_summary.json`. Expected
additional improvements over the structural order are limited to:

- Conv_Case0: 66,828 → 65,532;
- Conv_Case1: 72,734 → 70,940;
- FA0/FA1: no observed gain under their 2,000-proposal probes;
- MM0/MM1: repair search not run.

The directory does not persist a complete canonical artifact for every repair
row. Treat the Conv gains as exploratory mechanism evidence, not as a uniform
method, production default, or four-case negative result.

## 3a. Ablation and capacity-sweep diagnostics

`scripts/ablate_solver_v2.py` takes no arguments. It generates the public-case
victim/placement-policy ablation grid, an L1-capacity sweep on `Conv_Case0`
(2,048–16,384 bytes, including pinned-set infeasibility), and a synthetic-suite
regression check against a cost-blind ordering comparator and `iter038`:

```bash
uv run python scripts/ablate_solver_v2.py
```

Outputs go to `results/autoresearch_v2/round7_public_ablation.json`,
`round8_capacity_sweep.json`, `round9_synthetic.json`, and
`round9_synthetic_summary.json`. `round7_public_ablation.json` is not the
production source: it fixes H=0, selects by `(E, spills)` without the time
tie-break, and omits two cells of the full frontier/best-fit/adaptive
factorial design — its `full` row is not the selected production artifact.

## 3b. Canonically validated synthetic re-evaluation

The internal synthetic benchmarks (36-instance suite, 8-instance oracle set,
clean/dirty pair) are re-run with the full production portfolio and validated
row-by-row with the canonical evaluator:

```bash
uv run python scripts/paper/v2_synth_suite.py
```

Expected summary: the production solver ties the previous portfolio on all 36
suite instances, records zero losses against the four cost-blind order
baselines and best-of-8 random orders (wins concentrate in the capacity-bound
regime), and matches the fixed-order CP-SAT traffic optimum on its own
selected order for all 8 oracle instances. Outputs go to
`results/paper/v2_synth_{suite,summary,oracle,pair}.csv`; instances are reused
verbatim, never regenerated.

## 4. Standard experiment runner

The general runner loads `algorithms/<name>/solve.py` and writes schedules plus
metrics under the configured output directory:

```bash
uv run python experiments/run_experiment.py experiments/configs/exp001_baseline01.yaml
```

`algorithms/baseline` is an adapter around stored official artifacts; running
that configuration re-evaluates the reference rather than regenerating it with
a disclosed scheduling algorithm.

Useful repository-level checks:

```bash
uv run python scripts/validate_schedule.py --dir results/
uv run python scripts/compare_results.py
```

## 5. Paper figures

The publication figure suite used by `paper/src/*` (bridge_conv0,
headline_reductions, vd_plane, order_headroom, certificate_ladder, gap_model,
frontier_mechanism, paired_accounting, ablation_attribution, robustness,
p3_tradeoff) is regenerated from the SSOT CSVs in `results/paper/` with:

```bash
uv run python scripts/paper/v3_story_figures.py          # all figures
uv run python scripts/paper/v3_story_figures.py vd_plane # one stem
```

PDFs go to `paper/assets/figures/` (PNG previews are cached under `output/`,
which is gitignored and safe to delete/regenerate).

Some legacy tables under `results/paper/` (the non-`v2_*` CSVs) contain parts of
the pre-review narrative. Do not use them as the source for the public v2
headline. The current v2 sources are listed in the next section.

## 6. Artifact map and replay boundary

The production implementation is `src/ks_core/solver.py`. The two
research-only entry points are `scripts/agent_cost_order_search.py` (order repair)
and `scripts/agent_direct_search.py` (fixed-order exact planning); calling the
production `solve` interface does not invoke either research script. Audited
outputs are grouped under `results/autoresearch_v2/`, with
`RESEARCH_REPORT.md` as the consolidated evidence map.

Regenerate the audited P1 ledger with:

```bash
uv run python scripts/validate_solver_v2.py \
  --problems 1 \
  --output results/autoresearch_v2/round12_audited_p1.json
```

The public JSON files and synthetic CSV files are metric/validation ledgers,
not complete archived artifact bundles. In particular,
`scripts/paper/v2_synth_suite.py` constructs and canonically validates 252
schedule/memory/spill runs in memory, then persists their metrics. Reproducing
those rows therefore requires rerunning the script; the repository reuses its
versioned instances and fixed seeds rather than generating new instances. The
three zero-gap fixed-order certificates are stronger persistence artifacts:
they include matching schedule, memory, and spill files.

For a comparable replay, preserve the published capacities, evaluator version,
and lexicographic objectives. Replacing physical P2 residency with the logical
P1 peak, treating static backed/generated labels as dynamic dirty state, or
accepting a gap lower bound without contiguous packing changes the problem.
Record the Git revision, `uv.lock`, hardware, and software environment before a
run. One-shot wall times are provenance only, not stable performance claims.

## 7. Sources of record

| Claim or artifact | Source |
| --- | --- |
| Scalable P2 and production C/D/V | `results/autoresearch_v2/round11_audited_p2.json` |
| Scalable P3 | `results/autoresearch_v2/round6_formal_p3.json` |
| Controlled H=0 component ablation | `results/autoresearch_v2/round7_public_ablation.json` |
| Cost-aware repair | `results/autoresearch_v2/agent_cost_order/final_summary.json` |
| Fixed-order exact evidence | `results/autoresearch_v2/agent_direct/` |
| Capacity sweep | `results/autoresearch_v2/round8_capacity_sweep.json` |
| Synthetic boundary (H=0 diagnostic) | `results/autoresearch_v2/round9_synthetic_summary.json` |
| Canonically validated synthetic re-evaluation | `results/paper/v2_synth_{suite,summary,oracle,pair}.csv` |
| Consolidated narrative | `results/autoresearch_v2/RESEARCH_REPORT.md` |

The former E5 residency figure, 2.4–26× headline, 72-combination dominance
claim, and overflow-area-surrogate claim are not valid v2 sources.

Interpret the boundary files narrowly:

- round7 is H=0, selects by `(E, spills)` without time, and is not factorial;
  its `full` row is not the production artifact;
- round8 covers only Conv0/L1 at H=0; `cp_free_first` is cost-blind only as an
  ordering, while both sides share cost-aware planning machinery;
- round9 uses the H=0 internal assigner and does not persist per-case canonical
  artifacts. Its 36/36 tie with iter038 supports non-regression only.

## 8. Build the website

```bash
cd web
npm install
npm run lint
npm run build
npm run dev       # local development server
```

The website uses bilingual strings in `web/src/lib/i18n.ts` and numerical
tables in `web/src/data/paperTables.ts`. Update both languages whenever public
claims change.

## 9. Build the v2 paper

The LaTeX tree under `paper/` uses the post-review evidence map and can be built
with:

```bash
bash paper/build.sh all
```

A successful PDF build checks typesetting, not numerical provenance. Use the v2
claim ledger and consolidated report for the final claim audit before
distribution.
