# Cost-aware order-search findings

Evaluated against the shared round-5 working tree containing unlock_frontier, best-fit free-space selection, and share_adaptive_25.

No official-baseline schedule is read by any generator/search. Official metrics are loaded only here after order selection.

The only robust gain over the new structure-only unlock frontier came from bounded exact-cost local search. It advances dependency chains associated with expensive spill events; the accepted Conv0/Conv1 moves pull a clean ALLOC/COPY_IN chain earlier, changing the live clean reserve and avoiding dirty writeback/reload traffic.

| Case | Cost search | Strong blind | Official | Delta vs blind |
|---|---:|---:|---:|---:|
| Conv_Case0 | 65,532 | 66,828 | 73,500 | -1,296 |
| Conv_Case1 | 70,940 | 72,734 | 73,240 | -1,794 |
| FlashAttention_Case0 | 3,584 | 3,584 | 3,692 | +0 |
| FlashAttention_Case1 | 32,512 | 32,512 | 32,840 | +0 |
| Matmul_Case0 | 34,688 | 34,688 | 34,944 | +0 |
| Matmul_Case1 | 460,800 | 460,800 | 460,800 | +0 |

## Failed directions

- Global clean-first/dirty-first allocation priorities destroyed locality, often increasing traffic by an order of magnitude.
- Merely weighting last-use release by 1x/2x produced the same order on most frontiers; the semantic signal rarely broke a real choice.
- Capacity/overflow surrogates correlated poorly with exact spill traffic; low overflow could still choose expensive victims or fragment the allocator.
- Random tie-breaking and unguided block moves mostly regressed; useful moves were sparse and concentrated around exact spill frontiers.

## Interpretation

A defensible revised method is a two-level optimizer: a structure-only unlock-frontier schedule provides locality, then a bounded asymmetric-cost repair pass proposes topologically legal moves around observed spill events and keeps a move only if exact 1x-clean/2x-dirty traffic improves. This is genuinely cost-aware in ordering, unlike the former candidate portfolio, but the gains beyond the strong structural scheduler are concentrated in Conv.
