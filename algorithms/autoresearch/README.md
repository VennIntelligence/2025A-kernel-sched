# AutoResearch

AutoResearch is the controlled iteration workspace for kernel scheduling
experiments. Each candidate solver is saved under `iterations/`, while large
runtime artifacts are written under `results/autoresearch/`.

## Workflow

1. Create a new immutable candidate directory:

   ```bash
   mkdir -p algorithms/autoresearch/iterations/iter002_name
   ```

2. Write the candidate solver to:

   ```text
   algorithms/autoresearch/iterations/iter002_name/solve.py
   ```

3. Run it only through the iteration runner:

   ```bash
   uv run python scripts/run_iteration.py --iter 002 --slug name --suite p1_fast
   ```

The runner copies the candidate into `algorithms/autoresearch/solve.py`, runs the
experiment into a unique result directory, appends `ledger.csv`, and restores the
current best solver unless the candidate is promoted.

## State Files

| Path | Purpose |
| ---- | ------- |
| `solve.py` | Current promoted AutoResearch solver. |
| `best_iter.txt` | Iteration directory name for the current promoted solver. |
| `ledger.csv` | Append-only summary of baseline and iteration metrics. |
| `lessons.md` | Human/agent-maintained lessons from each iteration. |
| `iterations/iterNNN_slug/solve.py` | Immutable candidate solver snapshot. |

`results/exp001_baseline01/` remains the canonical baseline reference.
