# Iter 032: d2s_copyin_feed_alloc_first

## Hypothesis
Narrowing transfer-feed priority to only COPY_IN-feeding ALLOCs may keep Conv_Case0 max_L1 at 6912 while reducing L0B fan-out.

## Result
Suite: p1_fast.

All 3 rows were valid with 0 violations.

Against baseline01: 2 wins, 1 loss, 0 ties.

Against iter031 on fast-suite rows: 0 wins, 1 loss, 2 ties. Not run on full suite.

| case | max_L1 | max_UB | max_L0A_count | max_L0B_count | max_L0C_count | time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Conv_Case0 | 39010 | 0 | 0 | 1 | 0 | 361481 |
| FlashAttention_Case0 | 256 | 8258 | 24 | 32 | 4 | 31063 |
| Matmul_Case0 | 128 | 0 | 57 | 448 | 8 | 82308 |

## Findings
COPY_IN-only narrowing fails. It restores low L0B and better time, but Conv_Case0 max_L1 explodes to 39010. The L0B-feeding MOVE ALLOCs are necessary to keep L1 low under the current priority structure.

## Next
Keep iter031 as best. Further P1 work should seek a different way to reduce L0B without giving up the 6912 max_L1 win.
