# P1 Balanced Score

The official P1 promotion score is lexicographic:

```text
(violations, max_L1, max_UB, max_L0A_count, max_L0B_count, max_L0C_count, time)
```

That score is useful for matching the contest objective, but it can promote schedules that win by a small `max_L1` margin while badly regressing L0 residency or time. The balanced score is a side report only; it does not change official promotion.

## Definition

For each P1 case, compare every metric against `baseline01`.

```text
ratio = candidate / baseline                    if baseline > 0
ratio = 1                                       if baseline == 0 and candidate == 0
ratio = 1 + candidate / hardware_capacity       if baseline == 0 and candidate > 0
```

The scored metrics and weights are:

```text
max_L1          0.30
max_UB          0.15
max_L0A_count   0.10
max_L0B_count   0.10
max_L0C_count   0.10
time            0.25
```

For each ratio:

```text
log_ratio = max(log2(ratio), -2.0)
case_score = weighted_sum(log_ratio) + 0.35 * max_positive_log_ratio
balanced_score = mean(case_score over available P1 cases)
```

Lower is better. `baseline01` has score `0.0`. Improvements are capped at `4x` so one very good metric cannot hide a large regression elsewhere.

## Current Ranking

Generated with:

```bash
uv run python scripts/report_p1_balance.py
```

Top full-suite rows:

| rank | run | balanced_score | geo L1 ratio | geo L0B ratio | geo time ratio |
| ---: | --- | ---: | ---: | ---: | ---: |
| 0 | baseline01 | 0.0000 | 1.000x | 1.000x | 1.000x |
| 1 | iter013_conv_memtype_id_tiebreak_full | 3.4177 | 0.085x | 99.293x | 1.019x |
| 2 | iter022_d2s_ready_alloc_first_full | 3.7665 | 0.075x | 182.620x | 1.030x |
| 3 | iter020_d2s_alloc_first_full | 3.8422 | 0.082x | 182.620x | 1.030x |
| 4 | iter015_d2s_conv_id_tiebreak_full | 4.3511 | 0.085x | 414.131x | 1.040x |
| 5 | iter031_d2s_transfer_feed_alloc_first_full | 4.3826 | 0.074x | 472.499x | 1.046x |

## Interpretation

`iter031` is the official P1 best, but it is not the balanced best. It improves geometric L1 ratio slightly versus `iter013`, but its L0B and time regressions are much worse.

The clearest regression is Conv:

```text
iter013 Conv_Case1: max_L1=14040, max_L0B_count=1,    time=573395
iter031 Conv_Case1: max_L1=13786, max_L0B_count=5264, time=650044
```

This trades a `1.8%` L1 improvement for a `5264x` L0B regression and a `13.4%` time regression. Future P1 work should use `iter013` or `iter022` as the balanced reference, not `iter031`, unless the goal is strictly official lexicographic promotion.
