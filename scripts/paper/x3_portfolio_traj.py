"""Emit explanatory portfolio search-trajectory data.

Explanatory (notebook-only) figure **x3** — NOT a paper figure.  Reconstructs
the cumulative-best portfolio over autoresearch iterations 034-038 and reports
the per-problem win breakdown plus aggregate P1/P2/P3 pressure.  The win/loss
totals are validated against the published headline trajectory in
``e10_portfolio.csv`` (this is a richer view of the same data, not a new run).

Run::

    uv run python scripts/paper/x3_portfolio_traj.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ks_core.constants import CACHE_CAPACITIES

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "paper"
LEDGER = ROOT / "autoresearch" / "ledger.csv"
E10 = OUT / "e10_portfolio.csv"

CASES = [
    "Conv_Case0", "Conv_Case1", "FlashAttention_Case0",
    "FlashAttention_Case1", "Matmul_Case0", "Matmul_Case1",
]
POOL = ["034", "035", "036", "037", "038"]
# Official lexicographic comparison keys per problem.
KEYS = {
    1: ("max_L1", "max_UB", "max_L0A_count", "max_L0B_count", "max_L0C_count", "time"),
    2: ("extra", "spills", "time"),
    3: ("time", "extra", "spills"),
}
L1CAP = CACHE_CAPACITIES["L1"]


def _key(row, p: int) -> tuple[int, ...]:
    return tuple(int(row[k]) for k in KEYS[p])


def main() -> None:
    df = pd.read_csv(LEDGER, dtype={"iter": str})
    base = df[df["iter"] == "000"].set_index(["case", "problem"])
    bt = {(c, p): _key(base.loc[(c, p)], p) for c in CASES for p in (1, 2, 3)}

    desc = df[["iter", "algorithm_desc"]].drop_duplicates().set_index("iter")["algorithm_desc"]

    best: dict[tuple, tuple] = {}      # (case, problem) -> best key so far
    best_row: dict[tuple, pd.Series] = {}  # (case, problem) -> raw metric row
    rows = []
    for it in POOL:
        sub = df[(df["iter"] == it) & (df["valid"] == True)]  # noqa: E712
        for _, r in sub.iterrows():
            cp = (r["case"], int(r["problem"]))
            if cp not in bt:
                continue
            t = _key(r, cp[1])
            if cp not in best or t < best[cp]:
                best[cp] = t
                best_row[cp] = r

        def _count(rel) -> int:
            return sum(1 for cp in bt if cp in best and rel(best[cp], bt[cp]))

        p_wins = {
            p: sum(1 for c in CASES if (c, p) in best and best[(c, p)] < bt[(c, p)])
            for p in (1, 2, 3)
        }
        total_p2_extra = sum(int(best_row[(c, 2)]["extra"]) for c in CASES)
        total_p3_time = sum(int(best_row[(c, 3)]["time"]) for c in CASES)
        mean_l1_pressure = sum(int(best_row[(c, 1)]["max_L1"]) / L1CAP for c in CASES) / len(CASES)
        rows.append(
            {
                "iter": it,
                "desc": desc.get(it, ""),
                "wins": _count(lambda a, b: a < b),
                "losses": _count(lambda a, b: a > b),
                "ties": _count(lambda a, b: a == b),
                "p1_wins": p_wins[1],
                "p2_wins": p_wins[2],
                "p3_wins": p_wins[3],
                "total_p2_extra": total_p2_extra,
                "total_p3_time": total_p3_time,
                "mean_l1_pressure": round(mean_l1_pressure, 4),
            }
        )
    out = pd.DataFrame(rows)

    # Validate win/loss/tie totals against the published headline trajectory.
    e10 = pd.read_csv(E10, dtype={"iter": str}).set_index("iter")
    for _, r in out.iterrows():
        ref = e10.loc[r["iter"]]
        got = (int(r["wins"]), int(r["losses"]), int(r["ties"]))
        exp = (int(ref["wins"]), int(ref["losses"]), int(ref["ties"]))
        assert got == exp, f"iter {r['iter']} win/loss {got} != e10 {exp}"

    out.to_csv(OUT / "x3_portfolio_traj.csv", index=False)
    print(out.to_string(index=False))
    print("wrote results/paper/x3_portfolio_traj.csv (validated vs e10)")


if __name__ == "__main__":
    main()
