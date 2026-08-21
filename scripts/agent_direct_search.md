# `agent_direct_search.py`

Fixed-order weighted traffic planner. For one fixed topological order, it
chooses weighted residency gaps and runs an independent continuous-packing
stage (48 deterministic greedy layout attempts, falling back to NoOverlap2D
only if those fail), then emits schedule/memory/spill files and scores them
with the canonical evaluator. A zero gap plus validated packing certifies
minimum traffic `E` for that fixed order — it does **not** certify minimum
spill count or time among equal-`E` plans, and it is not integrated into the
default solver (`ks_core.solver.solve` never calls it).

This prototype deliberately does not read baseline schedules or case names
while proposing candidates; it searches generic list-scheduler weights and
scores every completed order with the repository's concrete address
assignment plus the canonical evaluator.

## Usage

```bash
uv run python scripts/agent_direct_search.py \
  --cases Conv_Case0 --exact-order unlock_frontier --time-limit 30 \
  --out results/autoresearch_v2/agent_direct
```

- `--cases` — one or more case names, or `all`.
- `--exact-order {unlock_frontier,id_raw,capfit_id,capfit,p1}` — skip the
  weight search and certify traffic for this fixed order directly.
- `--trials` — number of weight-search trials when `--exact-order` is not
  given (e.g. `--trials 300`).
- `--time-limit` — seconds allotted to the CP-SAT packing fallback.
- `--out` — output directory for schedule/memory/spill/JSON artifacts.

## Reproducing the three current machine-checkable certificates

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

## Known scope and caveats

- This research path is not uniformly scalable across all six cases. Any
  future production integration must use a timeout and retain the default
  solver as a validated fallback.
- FA1 is machine-checkable feasible at 32,512 against lower bound 31,936, but
  is not certified.
- The old MM0 "34,688 OPTIMAL" result is revoked: the reproducible CP-SAT
  incumbent is 34,816 with lower bound 29,952, while the legal production
  result 34,688 provides a better upper bound.
- Conv1 does not complete the research path and MM1 was not run.

## Source of record

Audited outputs live under `results/autoresearch_v2/agent_direct/`, with
`REPORT.md` in that directory as the consolidated summary. See also
`results/autoresearch_v2/RESEARCH_REPORT.md` and `docs/research_summary.md`
for the paper-facing narrative.
