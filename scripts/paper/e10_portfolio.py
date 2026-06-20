from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any

from ks_core.metrics import load_metrics


ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "autoresearch" / "ledger.csv"
BASELINE = ROOT / "results" / "exp001_baseline01" / "metrics.json"
OUT = ROOT / "results" / "paper" / "e10_portfolio.csv"

ITERS = ["034", "035", "036", "037", "038"]
OFFICIAL_KEYS = {
    1: ("max_L1", "max_UB", "max_L0A_count", "max_L0B_count", "max_L0C_count", "time"),
    2: ("extra", "spills", "time"),
    3: ("time", "extra", "spills"),
}


def _to_ints(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    for key in (
        "problem", "max_L1", "max_UB", "max_L0A_count", "max_L0B_count",
        "max_L0C_count", "spills", "extra", "time", "schedule_len", "violations",
    ):
        out[key] = int(out[key])
    return out


def _result(row: dict[str, Any], baseline: dict[str, Any]) -> str:
    keys = OFFICIAL_KEYS[row["problem"]]
    ours_key = tuple(row[key] for key in keys)
    base_key = tuple(baseline[key] for key in keys)
    if ours_key < base_key:
        return "WIN"
    if ours_key > base_key:
        return "LOSS"
    return "TIE"


def main() -> None:
    baseline = {
        (row["case"], int(row["problem"])): _to_ints(row)
        for row in load_metrics(BASELINE)
    }
    grouped = defaultdict(list)
    with LEDGER.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["iter"] in ITERS:
                grouped[row["iter"]].append(_to_ints(row))

    rows = []
    for iter_id in ITERS:
        iter_rows = grouped[iter_id]
        assert iter_rows, iter_id
        latest = max(row["timestamp"] for row in iter_rows)
        latest_rows = [row for row in iter_rows if row["timestamp"] == latest]
        assert len(latest_rows) == 18, (iter_id, latest, len(latest_rows))

        counts = {"WIN": 0, "LOSS": 0, "TIE": 0}
        for row in latest_rows:
            counts[_result(row, baseline[(row["case"], row["problem"])])] += 1

        descs = sorted({row["algorithm_desc"] for row in latest_rows})
        rows.append({
            "iter": iter_id,
            "desc": "+".join(descs),
            "wins": counts["WIN"],
            "losses": counts["LOSS"],
            "ties": counts["TIE"],
        })

    wins = [row["wins"] for row in rows]
    assert wins == sorted(wins), wins

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["iter", "desc", "wins", "losses", "ties"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"wins={wins}")
    print(f"wrote {OUT}")
    print(f"DONE T10 portfolio: {OUT}")


if __name__ == "__main__":
    main()
