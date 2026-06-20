"""E16 -- solver wall-clock runtime measurement for the six contest cases."""

from __future__ import annotations

import csv
import statistics
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import harness as H  # noqa: E402
from ks_core.solver import solve  # noqa: E402

RESULTS = ROOT / "results" / "paper"
OUT_CSV = RESULTS / "e16_runtime.csv"
PROBLEMS = (1, 2, 3)
REPEATS = 3
FIELDS = [
    "case",
    "problem",
    "solve_time_median_s",
    "solve_time_min_s",
    "solve_time_max_s",
    "nodes",
    "edges",
    "buffers",
]


def _buffer_count(inst: Any) -> int:
    return sum(1 for node in inst.nodes if node.op == "ALLOC" and node.buf_id is not None)


def _measure_case_problem(case: str, problem: int) -> dict[str, Any]:
    inst = H.load_instance(case, problem)
    times: list[float] = []
    for repeat in range(REPEATS):
        print(f"E16 measure {case} P{problem} repeat {repeat + 1}/{REPEATS}", flush=True)
        t0 = time.perf_counter()
        solve(inst)
        times.append(time.perf_counter() - t0)

    return {
        "case": case,
        "problem": problem,
        "solve_time_median_s": statistics.median(times),
        "solve_time_min_s": min(times),
        "solve_time_max_s": max(times),
        "nodes": len(inst.nodes),
        "edges": len(inst.edges),
        "buffers": _buffer_count(inst),
    }


def _fmt_seconds(value: float) -> str:
    return f"{value:.6f}"


def _print_summary(rows: list[dict[str, Any]]) -> None:
    print("--- E16 solver wall-clock runtime ---")
    print("case,problem,median_s,min_s,max_s,nodes,edges,buffers")
    for row in rows:
        print(
            f"{row['case']},P{row['problem']},"
            f"{_fmt_seconds(row['solve_time_median_s'])},"
            f"{_fmt_seconds(row['solve_time_min_s'])},"
            f"{_fmt_seconds(row['solve_time_max_s'])},"
            f"{row['nodes']},{row['edges']},{row['buffers']}"
        )


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = [
        _measure_case_problem(case, problem)
        for case in H.CASES
        for problem in PROBLEMS
    ]

    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **row,
                    "solve_time_median_s": _fmt_seconds(row["solve_time_median_s"]),
                    "solve_time_min_s": _fmt_seconds(row["solve_time_min_s"]),
                    "solve_time_max_s": _fmt_seconds(row["solve_time_max_s"]),
                }
            )

    _print_summary(rows)
    print(f"Wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
