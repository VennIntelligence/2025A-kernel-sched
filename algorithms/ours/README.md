# ours

The proposed kernel-scheduling method, the comparison counterpart to
`algorithms/baseline/`.

`solve.py` is a thin entry point: it re-exports `solve` from
[`ks_core.solver`](../../src/ks_core/solver.py), which is the single source of
truth for the implementation. The experiment runner loads it as
`algorithms.ours.solve`.

This solver is iter038, the final candidate promoted by the AutoResearch search
process. The search history, ledger, and per-iteration ablation snapshots that
produced it live under [`autoresearch/`](../../autoresearch/) at the repository
root; `autoresearch/best_iter.txt` records which iteration is promoted.

| Aspect | Value |
| ------ | ----- |
| Implementation | `ks_core.solver` |
| `Schedule.algorithm` tag | `ours` |
| Provenance | `autoresearch/iterations/iter038_id_raw_candidate/` |
