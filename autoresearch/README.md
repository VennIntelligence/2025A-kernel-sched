# AutoResearch

AutoResearch is the controlled iteration *process* that searched for the kernel
scheduling solver — the lab notebook, kept separate from the methods themselves.
The promoted result of this search is shipped as the method
[`algorithms/ours/`](../algorithms/ours/) (implemented in `ks_core.solver`).

Each candidate solver is an immutable snapshot under `iterations/`; large runtime
artifacts are written under `results/autoresearch/`.

## Workflow

1. Create a new immutable candidate directory:

   ```bash
   mkdir -p autoresearch/iterations/iter039_name
   ```

2. Write the candidate solver to:

   ```text
   autoresearch/iterations/iter039_name/solve.py
   ```

3. Run it only through the iteration runner:

   ```bash
   uv run python scripts/run_iteration.py --iter 039 --slug name --suite p1_fast
   ```

The runner copies the candidate into `algorithms/ours/solve.py`, runs the
experiment into a unique result directory, appends `ledger.csv`, and restores the
current best solver unless the candidate is promoted.

> The search is complete: iter038 was promoted and lifted into `ks_core.solver`
> as the permanent home. The runner and this directory are retained for
> provenance and reproducibility.

## State Files

| Path | Purpose |
| ---- | ------- |
| `best_iter.txt` | Iteration directory name for the current promoted solver. |
| `ledger.csv` | Append-only summary of baseline and iteration metrics. |
| `lessons.md` | Human/agent-maintained lessons from each iteration. |
| `p1_balance.md` | P1 balanced-scoring methodology vs the baseline. |
| `iterations/iterNNN_slug/solve.py` | Immutable candidate solver snapshot. |

`results/exp001_baseline01/` remains the canonical baseline reference.
