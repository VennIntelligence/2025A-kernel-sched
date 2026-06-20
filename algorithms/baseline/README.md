# Baseline

The baseline is the canonical reference adapter. It does not solve at runtime;
`solve()` reads the frozen artifacts in `results/exp001_baseline01/` and returns a
project-standard `Schedule`.

## Algorithm Summary

- **Problem 1**: topological instruction scheduling with no spill
- **Problem 2**: stored P2 schedule, memory layout, and spill entries
- **Problem 3**: stored P3 schedule, memory layout, and spill entries

## Interface

```python
from algorithms.baseline.solve import solve

schedule = solve(instance, config={})
```

`solve()` always returns `Schedule`. For P2/P3, `schedule.memory` and
`schedule.spill_entries` contain the concrete memory layout and spill entries
required by `ks_core.metrics.evaluate()`.

## Artifact Source

| Path | Content |
|------|---------|
| `results/exp001_baseline01/schedules/` | P1/P2/P3 schedule files |
| `results/exp001_baseline01/memory/` | P2/P3 memory layout files |
| `results/exp001_baseline01/spills/` | P2/P3 spill files |
| `results/exp001_baseline01/metrics.json` | canonical evaluated metrics |
| `results/exp001_baseline01/policy_benchmark.json` | policy comparison artifact |
