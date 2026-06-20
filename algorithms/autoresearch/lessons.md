# AutoResearch Lessons

This file is append-only during iterative work. Each iteration should record the
hypothesis, result summary, and the next concrete adjustment.

## Iteration Template

```markdown
---

## Iter NNN: slug (YYYY-MM-DD)

### Hypothesis
- ...

### Result Summary
- Suite: ...
- Valid rows: ...
- Baseline comparison: ...
- Best comparison: ...

### Findings
- ...

### Next Step
- ...
``` 

---

## Iter 002: memory_aware_list (2026-06-08)

### Hypothesis
- A P1 ready-list scheduler that prioritizes FREE, then last-use operations, then ALLOC should reduce the seed order's excessive live allocation pressure.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: all 3 matching rows improved versus iter001, but fast suite cannot promote.

### Findings
- The heuristic sharply reduced FlashAttention_Case0 and Matmul_Case0 max_L1.
- Conv_Case0 still opened too many L1/L0B buffers and regressed time versus baseline01.

### Next Step
- Run the same candidate on p1_full as a separate promotion iteration.

---

## Iter 003: memory_aware_list_full (2026-06-08)

### Hypothesis
- The iter002 memory-aware scheduler should remain valid on all P1 cases and improve over the current AutoResearch best.

### Result Summary
- Suite: p1_full.
- Valid rows: 6/6, all with 0 violations.
- Baseline comparison: 4 wins, 2 losses, 0 ties.
- Best comparison: 6 wins, 0 losses, 0 ties according to the runner.
- Promotion: promoted to `iter003_memory_aware_list_full`.

### Findings
- The scheduler is a clear improvement over the seed topological order and is now the AutoResearch best.
- It is not yet a stable P1 endpoint against baseline01 because Conv_Case0 and Conv_Case1 retain high max_L1 and L0B counts.

### Next Step
- Stay in PE/P1 and try a Conv-focused release-aware allocation priority that avoids opening many independent tiles before local consumers and frees are scheduled.

---

## Iter 004: release_unlock_ops (2026-06-08)

### Hypothesis
- Prioritizing operation nodes that immediately unlock a `FREE` successor should shorten local buffer lifetimes and reduce Conv_Case0 max_L1 below 82106.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: metrics and schedules were identical to iter003 on all fast-suite rows.

### Findings
- Operation-level `FREE` unlock priority had no practical effect.
- Conv pressure builds during ALLOC selection: many small L0B allocations are opened while their local consumers are still blocked.

### Next Step
- Try an ALLOC-side successor-readiness priority so allocations that can immediately feed a non-FREE successor are chosen before independent buffers that cannot be consumed yet.

---

## Iter 005: alloc_successor_readiness (2026-06-08)

### Hypothesis
- Conv pressure builds because ALLOC priority opens many independent buffers that cannot be consumed yet. Scheduling ALLOC nodes whose non-FREE successors are closest to ready should shorten local lifetimes.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: 3 wins, 0 losses, 0 ties against iter003 on fast-suite rows.

### Findings
- Conv_Case0 max_L1 improved from 82106 to 16132.
- FlashAttention_Case0 improved by P1 score despite higher max_UB because max_L1 fell from 512 to 256.
- Matmul_Case0 improved L0A/L0C counts with equal max_L1 and max_UB.
- Conv_Case0 L0B count stayed at 290, so L0B fan-out remains a separate problem.

### Next Step
- Run the same solver on p1_full as iter006 and promote if it is no worse than iter003 across all six P1 rows.

---

## Iter 006: alloc_successor_readiness_full (2026-06-08)

### Hypothesis
- The iter005 ALLOC successor-readiness scheduler should scale to the full P1 suite and improve over iter003 on all rows.

### Result Summary
- Suite: p1_full.
- Run status: manually stopped after more than five minutes.
- Valid rows: partial metrics showed 5/5 completed rows valid, but the suite did not finish and no ledger rows were written.
- Best comparison: partial rows were promising, including Conv_Case1 max_L1 dropping from 290554 to 14746.

### Findings
- The heuristic was useful but the implementation was too slow because every scheduling step scanned large ready sets and recomputed ALLOC successor-readiness.

### Next Step
- Keep the same heuristic direction but make ALLOC selection heap-backed.

---

## Iter 007: alloc_successor_heap (2026-06-08)

### Hypothesis
- A heap-backed ALLOC ready queue should preserve successor-readiness behavior while making large ready sets cheap enough for full-suite runs.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: 3 wins, 0 losses, 0 ties against iter003 on fast-suite rows.

### Findings
- Runtime was fixed: p1_fast completed quickly.
- The heap version improved fast-suite P1 scores versus iter003.
- Code review found this was not a pure data-structure optimization: ALLOC pressure changed from dynamic `_post_pressure(node, current)` to static `node.size * CACHE_WEIGHT`.

### Next Step
- Run the heap version on p1_full as iter008.

---

## Iter 008: alloc_successor_heap_full (2026-06-08)

### Hypothesis
- The iter007 heap-backed ALLOC successor-readiness scheduler should remain valid and improve over iter003 across the full P1 suite.

### Result Summary
- Suite: p1_full.
- Valid rows: 6/6, all with 0 violations.
- Baseline comparison: 4 wins, 2 losses, 0 ties.
- Best comparison: 6 wins, 0 losses, 0 ties against iter003.
- Promotion: promoted to `iter008_alloc_successor_heap_full`.

### Findings
- L1 improved sharply: Conv_Case0 82106 -> 16132, Conv_Case1 290554 -> 14746, FlashAttention_Case1 2560 -> 256, Matmul_Case1 4864 -> 128.
- L0B fan-out remains severe: Conv_Case1 max_L0B_count is still 5264, and Matmul_Case1 is still 3840.
- Code review found an existing waiter tie-break bug: `node.buf_id or -1` treats buffer 0 as missing.

### Next Step
- Run a single-variable bugfix iteration replacing `node.buf_id or -1` with an explicit `None` check before starting new L0B-specific heuristics.

---

## Iter 009: buf_id_waiter_fix (2026-06-08)

### Hypothesis
- The ALLOC waiter tie-break treats `buf_id=0` as missing. Replacing `node.buf_id or -1` with an explicit `None` check should preserve correctness and may improve buffer-0 cases.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: 0 wins, 0 losses, 3 ties against iter008 on fast-suite rows.

### Findings
- Fast-suite schedules were unchanged, but the tie-break bug was removed.

### Next Step
- Run the same bugfix on p1_full as iter010.

---

## Iter 010: buf_id_waiter_fix_full (2026-06-08)

### Hypothesis
- The explicit `None` check should be no worse than iter008 on the full P1 suite and may improve cases involving buffer 0.

### Result Summary
- Suite: p1_full.
- Valid rows: 6/6, all with 0 violations.
- Baseline comparison: 5 wins, 1 loss, 0 ties.
- Best comparison: 1 win, 0 losses, 5 ties against iter008.
- Promotion: promoted to `iter010_buf_id_waiter_fix_full`.

### Findings
- Conv_Case1 improved: max_L1 14746 -> 13786 and time 666766 -> 650044.
- All other rows tied iter008.
- The remaining baseline loss is Conv_Case0 because max_L1 is 16132 versus baseline01's 7488.
- L0B fan-out is still unresolved: Conv_Case1 max_L0B_count remains 5264 and Matmul_Case1 remains 3840.

### Next Step
- Diagnose Conv_Case0's remaining L1 peak and try one targeted P1 heuristic that reduces L1 without losing the full-suite gains.

---

## Iter 011: alloc_id_tiebreak (2026-06-08)

### Hypothesis
- For equal ALLOC successor-readiness, preserving original node-id order may reduce Conv_Case0's remaining L1 peak by keeping tile-local chains closer to the baseline order.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 0 wins, 2 losses, 1 tie.
- Best comparison: Conv_Case0 improved, but FlashAttention_Case0 and Matmul_Case0 regressed badly by P1 score.

### Findings
- Conv_Case0 improved versus iter010: max_L1 16132 -> 14980, max_L0B_count 290 -> 136, time 445495 -> 382915.
- FlashAttention_Case0 regressed max_L1 256 -> 3328.
- Matmul_Case0 regressed max_L1 128 -> 9216.
- Node-id ALLOC tie-break is useful for Conv-like structure but harmful for mixed-memory FA/Matmul structure.

### Next Step
- Try a structure-gated version: use node-id ALLOC tie-break only for instances whose ALLOC memory types are exactly the Conv-style `L1/L0B` set; keep iter010 behavior elsewhere.

---

## Iter 012: conv_memtype_id_tiebreak (2026-06-08)

### Hypothesis
- The node-id ALLOC tie-break from iter011 is useful for Conv-like `L1/L0B` graphs but harmful for mixed-memory FlashAttention/Matmul graphs. Gating it on the ALLOC memory-type set should preserve Conv_Case0 gains without regressing other fast-suite cases.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: 1 win, 0 losses, 2 ties against iter010 on fast-suite rows.

### Findings
- Conv_Case0 improved versus iter010: max_L1 16132 -> 14980, max_L0B_count 290 -> 136, time 445495 -> 382915.
- FlashAttention_Case0 and Matmul_Case0 matched iter010 exactly.

### Next Step
- Run the same memory-type gate on p1_full as iter013 to check Conv_Case1.

---

## Iter 013: conv_memtype_id_tiebreak_full (2026-06-08)

### Hypothesis
- The `L1/L0B` memory-type gate should improve Conv_Case0 while preserving iter010 behavior on non-Conv rows.

### Result Summary
- Suite: p1_full.
- Valid rows: 6/6, all with 0 violations.
- Baseline comparison: 4 wins, 1 loss, 1 tie.
- Best comparison: 1 win, 1 loss, 4 ties against iter010.
- Promotion: not promoted.

### Findings
- Conv_Case0 improved, but Conv_Case1 regressed max_L1 from 13786 to 14040.
- Conv_Case1 improved max_L0B_count from 5264 to 1 and time from 650044 to 573395, but P1 score treats the max_L1 regression as a loss.
- Conv_Case0 has `D2S` nodes while Conv_Case1 does not, suggesting the node-id tie-break should target `L1/L0B + D2S` structure rather than all `L1/L0B` graphs.

### Next Step
- Try a narrower `L1/L0B` plus `D2S` gate for node-id ALLOC tie-break.

---

## Iter 014: d2s_conv_id_tiebreak (2026-06-08)

### Hypothesis
- The node-id ALLOC tie-break should apply only to the `L1/L0B + D2S` structure seen in Conv_Case0. This should keep Conv_Case0 gains while preserving iter010 behavior on fast non-D2S rows.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: 1 win, 0 losses, 2 ties against iter010 on fast-suite rows.

### Findings
- Conv_Case0 improved: max_L1 16132 -> 14980, max_L0B_count 290 -> 136, time 445495 -> 382915.
- FlashAttention_Case0 and Matmul_Case0 tied iter010 exactly.

### Next Step
- Run the same solver on p1_full as iter015.

---

## Iter 015: d2s_conv_id_tiebreak_full (2026-06-08)

### Hypothesis
- The `L1/L0B + D2S` gate should improve Conv_Case0 while leaving Conv_Case1 and all non-Conv rows tied with iter010.

### Result Summary
- Suite: p1_full.
- Valid rows: 6/6, all with 0 violations.
- Baseline comparison: 5 wins, 1 loss, 0 ties.
- Best comparison: 1 win, 0 losses, 5 ties against iter010.
- Promotion: promoted to `iter015_d2s_conv_id_tiebreak_full`.

### Findings
- The gate promoted cleanly.
- Conv_Case0 improved versus iter010: max_L1 16132 -> 14980, max_L0B_count 290 -> 136, time 445495 -> 382915.
- All other rows tied iter010.
- Remaining P1 gap: Conv_Case0 max_L1 is still above baseline01's 7488.

### Next Step
- Continue P1 on Conv_Case0 L1. Try pressure-aware gating for large L1 buffers around D2S/CONV_ADD chains, but preserve Conv_Case1's lower max_L1.

---

## Iter 016: d2s_large_l1_delay (2026-06-08)

### Hypothesis
- Conv_Case0's remaining peak is caused by many large L1 buffers being live at once. Delaying `L1` allocations of size at least 1024 inside the D2S-gated scheduler should reduce max_L1.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: 0 wins, 1 loss, 2 ties against iter015 on fast-suite rows.
- Promotion: not run on full suite.

### Findings
- max_L1 did not improve: Conv_Case0 stayed at 14980.
- max_L0B_count regressed from 136 to 286.
- Static large-L1 deferral is too blunt; it delays useful local progress without changing the L1 peak.

### Next Step
- Try a peak-contributor operation priority: in D2S-gated graphs, prioritize ready ops that touch currently large live L1 buffers so their FREE dependencies can be reached sooner.

---

## Iter 017: d2s_large_live_op_priority (2026-06-08)

### Hypothesis
- In D2S-gated graphs, prioritizing ready operations that touch currently live large L1 buffers should advance those buffers toward their FREE dependencies and reduce Conv_Case0 max_L1.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: 0 wins, 0 losses, 3 ties against iter015 on fast-suite rows.
- Promotion: not run on full suite.

### Findings
- The schedule was identical to iter015 on Conv_Case0.
- Operation-level peak-touch priority had no opportunity to change ready-op ordering.

### Next Step
- Move the peak-contributor idea to ALLOC priority: in D2S-gated graphs, delay large L1 buffers with multiple operation users, because these are likely long live ranges spanning CONV and CONV_ADD.

---

## Iter 018: d2s_multiuse_l1_delay (2026-06-08)

### Hypothesis
- In D2S-gated graphs, large L1 buffers with multiple operation users are likely long live ranges spanning CONV and CONV_ADD. Delaying these ALLOCs should reduce Conv_Case0 max_L1.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: 0 wins, 1 loss, 2 ties against iter015 on fast-suite rows.
- Promotion: not run on full suite.

### Findings
- max_L1 did not improve.
- Conv_Case0 max_L0B_count regressed from 136 to 290 and time regressed from 382915 to 445495.
- Delaying multi-use large L1 buffers breaks useful local progress.

### Next Step
- Try the opposite structure-specific signal: prioritize ALLOC nodes feeding D2S so D2S groups complete before the next wave of large CONV inputs opens.

---

## Iter 019: d2s_alloc_first (2026-06-08)

### Hypothesis
- In Conv_Case0, D2S output groups are delayed behind the next wave of large CONV inputs, causing old large L1 buffers to overlap with new large L1 buffers. Prioritizing ALLOC nodes that directly feed D2S should complete D2S groups earlier and reduce max_L1.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: 1 win, 0 losses, 2 ties against iter015 on fast-suite rows.

### Findings
- Conv_Case0 max_L1 improved 14980 -> 12194.
- Conv_Case0 max_L0B_count improved 136 -> 1.
- Conv_Case0 time improved 382915 -> 361481.
- FlashAttention_Case0 and Matmul_Case0 tied iter015 exactly.

### Next Step
- Run the same solver on p1_full as iter020 and promote if Conv_Case1 and other rows remain tied.

---

## Iter 020: d2s_alloc_first_full (2026-06-08)

### Hypothesis
- The iter019 D2S-first allocation priority should reduce Conv_Case0 max_L1 without changing Conv_Case1 or non-Conv rows.

### Result Summary
- Suite: p1_full.
- Valid rows: 6/6, all with 0 violations.
- Baseline comparison: 5 wins, 1 loss, 0 ties.
- Best comparison: 1 win, 0 losses, 5 ties against iter015.
- Promotion: promoted to `iter020_d2s_alloc_first_full`.

### Findings
- Conv_Case0 max_L1 improved 14980 -> 12194.
- Conv_Case0 max_L0B_count improved 136 -> 1.
- Conv_Case0 time improved 382915 -> 361481.
- All other full-suite rows tied iter015.
- The remaining P1 loss is still Conv_Case0 versus baseline01 max_L1 7488.

### Next Step
- Continue P1 on Conv_Case0 max_L1 by analyzing the new iter020 peak window.

---

## Iter 021: d2s_ready_alloc_first (2026-06-08)

### Hypothesis
- The iter020 D2S-first priority opens D2S output buffers too early. Prioritizing D2S-feeding ALLOCs only when their D2S successor is nearly ready (`successor_wait <= 2`) should retain the late-window benefit while avoiding long early lifetimes.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: 1 win, 0 losses, 2 ties against iter020 on fast-suite rows.

### Findings
- Conv_Case0 max_L1 improved 12194 -> 7488, matching baseline01.
- Conv_Case0 max_L0B_count stayed at 1.
- Conv_Case0 time stayed at 361481.
- FlashAttention_Case0 and Matmul_Case0 tied iter020 exactly.

### Next Step
- Run the same solver on p1_full as iter022 and promote if all non-fast rows remain no worse.

---

## Iter 022: d2s_ready_alloc_first_full (2026-06-08)

### Hypothesis
- The iter021 readiness-threshold D2S allocation priority should reduce Conv_Case0 max_L1 while leaving all other full-suite rows no worse than iter020.

### Result Summary
- Suite: p1_full.
- Valid rows: 6/6, all with 0 violations.
- Baseline comparison: 5 wins, 1 loss, 0 ties.
- Best comparison: 1 win, 0 losses, 5 ties against iter020.
- Promotion: promoted to `iter022_d2s_ready_alloc_first_full`.

### Findings
- Conv_Case0 max_L1 improved 12194 -> 7488, matching baseline01.
- Conv_Case0 max_L0B_count stayed at 1.
- Conv_Case0 time stayed at 361481, still 1911 slower than baseline01.
- Conv_Case0 now ties baseline on all P1 memory keys; its only baseline loss is time.

### Next Step
- Tune the D2S readiness threshold to see whether `successor_wait <= 1` keeps memory equal while improving time.

---

## Iter 023: d2s_ready1_alloc_first (2026-06-08)

### Hypothesis
- Tightening the D2S readiness threshold from `successor_wait <= 2` to `<= 1` may keep Conv_Case0 memory equal while improving time.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: 0 wins, 1 loss, 2 ties against iter022 on fast-suite rows.
- Promotion: not run on full suite.

### Findings
- The threshold `<= 1` is too strict and falls back to the pre-D2S-ready behavior.
- Conv_Case0 max_L1 regressed from 7488 to 14980.

### Next Step
- Try the looser threshold `<= 3` to map the boundary of useful D2S prioritization.

---

## Iter 024: d2s_ready3_alloc_first (2026-06-08)

### Hypothesis
- Loosening the D2S readiness threshold from `successor_wait <= 2` to `<= 3` may keep the memory gains while improving or preserving time.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: 0 wins, 1 loss, 2 ties against iter022 on fast-suite rows.
- Promotion: not run on full suite.

### Findings
- Conv_Case0 max_L1 regressed from 7488 to 10180.
- Time did not improve.
- The useful readiness threshold for D2S-first allocation is exactly `successor_wait <= 2`.

### Next Step
- Stop threshold tuning. Try a critical-path operation tie-break to improve Conv_Case0 time while preserving memory.

---

## Iter 026: d2s_effective_successor_wait (2026-06-08)

### Hypothesis
- Replacing raw successor indegree with effective successor wait should treat a join as ready when all missing predecessors are already ready ALLOC nodes.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: 1 win, 0 losses, 2 ties against iter022 on fast-suite rows.
- Promotion: not run on full suite.

### Findings
- Conv_Case0 stayed identical to iter022; the intended time improvement did not occur.
- Implementation issue: when a new sibling ALLOC became ready, already-ready sibling ALLOC heap keys were not refreshed.
- FlashAttention_Case0 max_UB unexpectedly improved because effective wait was applied outside the D2S gate, but that was not the intended variable.

### Next Step
- Retry effective successor wait with sibling ALLOC heap refresh, scoped to the D2S-gated path.

---

## Iter 027: d2s_effective_wait_refresh (2026-06-08)

### Hypothesis
- Refreshing sibling ALLOC heap keys when a new ready ALLOC appears should make effective successor wait affect D2S joins and improve Conv_Case0 time.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: 0 wins, 0 losses, 3 ties against iter022 on fast-suite rows.
- Promotion: not run on full suite.

### Findings
- The refreshed effective-wait implementation still matched iter022 exactly on the fast suite.
- The existing `successor_wait <= 2` D2S gate already captures the join readiness needed for memory.
- The remaining Conv_Case0 time gap is not solved by ALLOC successor-wait refinement.

### Next Step
- Diagnose Conv_Case0 pipeline timing directly before adding a new time-oriented heuristic.

---

## Iter 028: d2s_move_before_d2s (2026-06-08)

### Hypothesis
- Penalizing D2S operations should let MOVE nodes run first on MTE1 and reduce Conv_Case0 time.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: 0 wins, 0 losses, 3 ties against iter022 on fast-suite rows.
- Promotion: not run on full suite.

### Findings
- Penalizing D2S operations had no effect.
- The relevant MOVE nodes were not ready yet; the ordering problem occurs earlier in ALLOC priority.

### Next Step
- Prioritize ALLOCs feeding COPY_IN/MOVE transfer chains before D2S-ready ALLOCs, while keeping large CONV input ALLOCs behind D2S.

---

## Iter 029: d2s_pipe_ready_ops (2026-06-08)

### Hypothesis
- A pipe-aware earliest-start tie-break for ready operations should avoid placing topologically-ready but resource-delayed D2S operations before earlier executable MOVE nodes.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: 0 wins, 0 losses, 3 ties against iter022 on fast-suite rows.
- Promotion: not run on full suite.

### Findings
- Ready-op ordering did not change.
- The MOVE nodes that should precede D2S are not ready because their input ALLOCs are delayed by D2S-ready allocation priority.

### Next Step
- Move the fix to ALLOC priority: let ALLOCs feeding COPY_IN/MOVE transfer chains run before D2S-ready ALLOCs, but keep large CONV input ALLOCs behind D2S.

---

## Iter 030: d2s_transfer_feed_alloc_first (2026-06-08)

### Hypothesis
- Conv_Case0's remaining time gap comes from D2S-ready allocation priority delaying ALLOCs that feed COPY_IN/MOVE transfer chains. Prioritizing transfer-feeding ALLOCs before D2S-ready ALLOCs should restore early MOVE readiness while keeping large CONV inputs behind D2S.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 3 wins, 0 losses, 0 ties.
- Best comparison: 1 win, 0 losses, 2 ties against iter022 on fast-suite rows.

### Findings
- Conv_Case0 max_L1 improved 7488 -> 6912 versus iter022/baseline01.
- Conv_Case0 max_L0B_count regressed 1 -> 300 and time regressed 361481 -> 394430.
- Despite the L0B/time regression, P1 dictionary score improves because max_L1 is lower.

### Next Step
- Run the same solver on p1_full as iter031.

---

## Iter 031: d2s_transfer_feed_alloc_first_full (2026-06-08)

### Hypothesis
- The transfer-feed ALLOC priority should remain no worse than iter022 across the full P1 suite because it only affects the D2S-gated Conv_Case0 structure.

### Result Summary
- Suite: p1_full.
- Valid rows: 6/6, all with 0 violations.
- Baseline comparison: 6 wins, 0 losses, 0 ties.
- Best comparison: 1 win, 0 losses, 5 ties against iter022.
- Promotion: promoted to `iter031_d2s_transfer_feed_alloc_first_full`.

### Findings
- First full-suite AutoResearch result with 6/6 P1 wins against baseline01 by official dictionary score.
- Conv_Case0 max_L1 improved to 6912, below baseline01's 7488.
- Tradeoff: Conv_Case0 max_L0B_count regressed to 300 and time to 394430.

### Next Step
- Try to keep Conv_Case0 max_L1 at 6912 while reducing its L0B fan-out by narrowing transfer-feed priority.

---

## Iter 032: d2s_copyin_feed_alloc_first (2026-06-08)

### Hypothesis
- Narrowing transfer-feed priority to only COPY_IN-feeding ALLOCs may keep Conv_Case0 max_L1 at 6912 while reducing L0B fan-out.

### Result Summary
- Suite: p1_fast.
- Valid rows: 3/3, all with 0 violations.
- Baseline comparison: 2 wins, 1 loss, 0 ties.
- Best comparison: 0 wins, 1 loss, 2 ties against iter031 on fast-suite rows.
- Promotion: not run on full suite.

### Findings
- COPY_IN-only narrowing fails: Conv_Case0 max_L1 regressed 6912 -> 39010 while max_L0B_count improved 300 -> 1 and time improved 394430 -> 361481.
- L0B-feeding MOVE ALLOCs are necessary to keep L1 low under the current priority structure.

### Next Step
- Keep iter031 as best. Further P1 work should seek a different way to reduce L0B without giving up max_L1 6912.

---

## Balanced P1 Audit (2026-06-08)

### Finding
- The official lexicographic P1 score is not a balanced quality signal. It can prefer a small `max_L1` win even when L0 residency and time regress heavily.
- A side-report balanced score was added in `scripts/report_p1_balance.py`. It compares each metric against `baseline01` on a log scale, caps extreme improvements at 4x, and adds a penalty for the worst positive regression.

### Result Summary
- `iter031_d2s_transfer_feed_alloc_first_full` remains the official P1 best.
- Under the balanced score, the best full-suite AutoResearch result is `iter013_conv_memtype_id_tiebreak_full`; `iter022_d2s_ready_alloc_first_full` is the second candidate.
- `iter031` ranks behind them because its geometric L0B ratio is much worse (`472.5x` vs `99.3x` for iter013), while its L1 advantage is smaller.

### Next Step
- Use `iter013` or `iter022` as the balanced reference for future P1 work. Continue reporting official promotion separately, but do not treat official promotion alone as a global-quality signal.

---

## Iter 033–036: unified P1/P2/P3 (2026-06-11)

### Hypothesis
- 32 轮 P1 词典序调优偏离了全局目标。直接构建统一求解器:P1 复用 iter031;
  P2/P3 用多候选序 + 首适配地址 + Belady spill,按各题官方词典键模拟选优。

### Result Summary
- iter034 (full): 首批 18/18 valid 行,vs baseline 8 胜 10 负;晋升。
- iter035 (full): P3 解耦 + SPILL_IN 预取窗口,vs baseline 10 胜 8 负;晋升。
- iter036 (full): P2 时间 tiebreak,vs baseline 11 胜 7 负;晋升。

### Findings
- capfit_id(原始 id 块顺序 + 容量节流)是最大单项收益:结构无关地复刻了"块状串行"形态,L0 残留 1~3、L1≈baseline。
- P3 的时间损失主要在 reload 阻塞,提前若干步预取 SPILL_IN(不驱逐)即可大幅缓解。
- 驱逐评分变体(距离/成本/字节)收益 < 量噪声;剩余 Conv/FA P2 extra 差距是序级问题,baseline 的序能让大 COPY_IN 缓冲驻留到 spill 窗口期间(半价 spill),我们的容量节流提前 FREE 它们。
- 教训:词典序晋升信号必须与"被晋升解能否进 P2/P3 容量预算"同时检查,否则会再次出现 max_UB 33010 这种胜负注。

### Next Step
- Conv0/1 P2: 重载窗口感知的 COPY_IN 驻留;Matmul1 P2: zigzag 顺序砍半 B 矩阵重载。

---

## Iter 037: p3_prefetch_grid (2026-06-11)

### Hypothesis
- P2 minimizes extra (a prefetch window can only raise extra, so a tight grid
  is enough), but P3 minimizes time where reload-hiding prefetch is the main
  lever. Widening only the P3 prefetch-window grid should cut P3 time with no
  P2 risk. Selection takes the min over candidates, so this is monotonic.

### Result Summary
- Suite: full.
- Valid rows: 18/18, 0 violations.
- Best comparison (vs iter036): 3 wins, 0 losses, 15 ties. Promoted.
- Baseline comparison: 12 wins, 6 losses (was 11/7).

### Findings
- Branch the window grid on problem_id: P3 uses {0,5,40,80,120}, P2 keeps {0,5,40}.
- FlashAttention_Case0 P3 47608 -> 46167 flips to a win vs baseline (46761).
- FlashAttention_Case1 P3 192438 -> 184475; Matmul_Case0 P3 192380 -> 191353.
- Runtime ~3 min on full suite; acceptable.

### Next Step
- Attack P2 extra losses via a new candidate order, not a new spill policy
  (victim scoring was already confirmed saturated).

---

## Iter 038: id_raw_candidate (2026-06-11)

### Hypothesis
- Feeding baseline's own order into our spill engine nearly matched its extra,
  so the P2 gap is the candidate order, not the engine. A pure node-id list
  order (FREE > op > ALLOC, no capacity throttle) should reproduce baseline's
  key property — keep cheap COPY_IN buffers resident through the L1 overflow
  window so they can be evicted at half price.

### Result Summary
- Suite: full.
- Valid rows: 18/18, 0 violations.
- Best comparison (vs iter037): 7 wins, 0 losses, 11 ties. Promoted.
- Baseline comparison: 13 wins, 5 losses (was 12/6).

### Findings
- Added `_id_raw_order` as a 3rd candidate in `_candidate_orders`; selection
  takes the min, so it is strictly monotonic (no regression possible).
- Conv_Case1 P2 77820 -> 72520 flips to a win vs baseline (73240).
- FA0 P2 4444 -> 3904; Conv1 P3 +14.6% -> +3.6%; FA1 P3 -> 180364; M0 P3 ->
  186820; M1 P3 -> 1771132 all improve.
- The win uses the existing `dist_size_cost` victim; cost-first victim adds
  nothing on any of our candidate orders (rechecked: dist >= cost everywhere).
- Diagnostic: on capfit_id the simultaneously-live COPY_IN count peaks at 272
  (M1) / 72 (M0) vs L1's 32-tile capacity, so Matmul1's 460800 extra is near
  the working-set floor; zigzag cannot halve it (earlier lesson corrected).

### Next Step
- Remaining 5 baseline losses (Conv0 P2/P3, Conv1 P3, FA0 P2, FA1 P2) are all
  order-level. DFS, lazy-free, and operand-locality/zigzag reorders were all
  tried and either failed or regressed. The monotonic candidate-expansion lever
  (add order / add window, take min) is now exhausted; further gains need a
  principled generator for baseline-style cheap-buffer-resident interleaving.
