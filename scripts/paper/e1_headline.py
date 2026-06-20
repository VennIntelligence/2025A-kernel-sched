"""Build the E1 headline comparison table."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from ks_core.metrics import load_metrics

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "results" / "exp001_baseline01" / "metrics.json"
OURS = ROOT / "results" / "autoresearch" / "iter038_id_raw_candidate" / "metrics.json"
OUT = ROOT / "results" / "paper" / "e1_headline.csv"

CASES = (
    "Conv_Case0",
    "Conv_Case1",
    "FlashAttention_Case0",
    "FlashAttention_Case1",
    "Matmul_Case0",
    "Matmul_Case1",
)
PROBLEMS = (1, 2, 3)
OFFICIAL_KEYS = {
    1: ("max_L1", "max_UB", "max_L0A_count", "max_L0B_count", "max_L0C_count", "time"),
    2: ("extra", "spills", "time"),
    3: ("time", "extra", "spills"),
}
COLUMNS = (
    "case",
    "problem",
    "ours_max_L1",
    "ours_max_UB",
    "ours_spills",
    "ours_extra",
    "ours_time",
    "base_max_L1",
    "base_max_UB",
    "base_spills",
    "base_extra",
    "base_time",
    "result",
)


def index_metrics(rows: list[dict[str, Any]]) -> dict[tuple[str, int], dict[str, Any]]:
    return {(row["case"], int(row["problem"])): row for row in rows}


def result_for(ours: dict[str, Any], baseline: dict[str, Any]) -> str:
    keys = OFFICIAL_KEYS[int(ours["problem"])]
    ours_key = tuple(ours[key] for key in keys)
    base_key = tuple(baseline[key] for key in keys)
    if ours_key < base_key:
        return "WIN"
    if ours_key > base_key:
        return "LOSS"
    return "TIE"


def main() -> None:
    baseline = index_metrics(load_metrics(BASELINE))
    ours = index_metrics(load_metrics(OURS))
    expected = {(case, problem) for case in CASES for problem in PROBLEMS}

    assert set(baseline) == expected, sorted(expected - set(baseline))
    assert set(ours) == expected, sorted(expected - set(ours))

    rows = []
    for case in CASES:
        for problem in PROBLEMS:
            key = (case, problem)
            ours_row = ours[key]
            base_row = baseline[key]
            rows.append(
                {
                    "case": case,
                    "problem": problem,
                    "ours_max_L1": ours_row["max_L1"],
                    "ours_max_UB": ours_row["max_UB"],
                    "ours_spills": ours_row["spills"],
                    "ours_extra": ours_row["extra"],
                    "ours_time": ours_row["time"],
                    "base_max_L1": base_row["max_L1"],
                    "base_max_UB": base_row["max_UB"],
                    "base_spills": base_row["spills"],
                    "base_extra": base_row["extra"],
                    "base_time": base_row["time"],
                    "result": result_for(ours_row, base_row),
                }
            )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    win_count = sum(row["result"] == "WIN" for row in rows)
    assert len(rows) == 18, len(rows)
    assert win_count == 13, win_count
    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"rows={len(rows)} WIN={win_count}")


if __name__ == "__main__":
    main()
