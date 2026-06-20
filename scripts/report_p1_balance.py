"""Report balanced P1 scores for AutoResearch iterations."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any

from ks_core.io import get_project_root
from ks_core.metrics import load_metrics


MEMORY_CAPACITY = {
    "max_L1": 4096,
    "max_UB": 1024,
    "max_L0A_count": 256,
    "max_L0B_count": 256,
    "max_L0C_count": 512,
}
MEMORY_KEYS = tuple(MEMORY_CAPACITY)
METRIC_WEIGHTS = {
    "max_L1": 0.30,
    "max_UB": 0.15,
    "max_L0A_count": 0.10,
    "max_L0B_count": 0.10,
    "max_L0C_count": 0.10,
    "time": 0.25,
}
IMPROVEMENT_FLOOR_LOG2 = -2.0
WORST_REGRESSION_WEIGHT = 0.35
FULL_P1_CASES = 6


def main() -> int:
    args = _parse_args()
    root = get_project_root()
    baseline_rows = _p1_by_case(load_metrics(root / args.baseline))

    aggregate_rows: list[dict[str, Any]] = []
    case_rows: list[dict[str, Any]] = []
    _add_run(
        aggregate_rows,
        case_rows,
        "baseline01",
        baseline_rows,
        baseline_rows,
        args,
    )

    results_dir = root / args.results_dir
    for metrics_path in sorted(results_dir.glob("iter*/metrics.json")):
        rows = _p1_by_case(load_metrics(metrics_path))
        if rows:
            _add_run(aggregate_rows, case_rows, metrics_path.parent.name, rows, baseline_rows, args)

    aggregate_rows.sort(key=lambda row: (row["case_count"] != FULL_P1_CASES, row["balanced_score"]))
    _write_csv(root / args.output, aggregate_rows)
    _write_csv(root / args.case_output, case_rows)
    _print_summary(aggregate_rows, args.top)
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", default="results/autoresearch")
    parser.add_argument("--baseline", default="results/exp001_baseline01/metrics.json")
    parser.add_argument("--output", default="results/autoresearch/p1_balance_report.csv")
    parser.add_argument("--case-output", default="results/autoresearch/p1_balance_cases.csv")
    parser.add_argument("--top", type=int, default=12)
    return parser.parse_args()


def _p1_by_case(rows: list[dict[str, Any]]) -> dict[tuple[str, int], dict[str, Any]]:
    return {
        (str(row["case"]), int(row["problem"])): row
        for row in rows
        if int(row.get("problem", 0)) == 1
    }


def _add_run(
    aggregate_rows: list[dict[str, Any]],
    case_rows: list[dict[str, Any]],
    run_name: str,
    rows: dict[tuple[str, int], dict[str, Any]],
    baseline_rows: dict[tuple[str, int], dict[str, Any]],
    args: argparse.Namespace,
) -> None:
    shared_keys = sorted(set(rows) & set(baseline_rows))
    scored = [
        _score_case(run_name, rows[key], baseline_rows[key])
        for key in shared_keys
    ]
    case_rows.extend(scored)
    if not scored:
        return

    worst = max(scored, key=lambda row: row["balanced_score"])
    aggregate_rows.append(
        {
            "run": run_name,
            "case_count": len(scored),
            "balanced_score": _mean(row["balanced_score"] for row in scored),
            "geo_max_L1_ratio": _geo_mean(row["max_L1_ratio"] for row in scored),
            "geo_max_UB_ratio": _geo_mean(row["max_UB_ratio"] for row in scored),
            "geo_max_L0B_count_ratio": _geo_mean(row["max_L0B_count_ratio"] for row in scored),
            "geo_time_ratio": _geo_mean(row["time_ratio"] for row in scored),
            "avg_cache_pressure": _mean(row["cache_pressure_mean"] for row in scored),
            "worst_capacity_pressure": max(row["worst_capacity_pressure"] for row in scored),
            "worst_case": worst["case"],
            "worst_metric": worst["worst_regression_metric"],
            "worst_metric_ratio": worst["worst_regression_ratio"],
        }
    )


def _score_case(
    run_name: str,
    row: dict[str, Any],
    baseline: dict[str, Any],
) -> dict[str, Any]:
    ratios = {
        key: _ratio_against_baseline(
            _as_float(row.get(key)),
            _as_float(baseline.get(key)),
            MEMORY_CAPACITY.get(key, 1),
        )
        for key in METRIC_WEIGHTS
    }
    log_ratios = {
        key: max(_log2(value), IMPROVEMENT_FLOOR_LOG2)
        for key, value in ratios.items()
    }
    weighted_log_ratio = sum(log_ratios[key] * weight for key, weight in METRIC_WEIGHTS.items())
    positive_regressions = {
        key: max(_log2(value), 0.0)
        for key, value in ratios.items()
    }
    worst_regression_metric, worst_regression_log = max(
        positive_regressions.items(),
        key=lambda item: item[1],
    )
    balanced_score = weighted_log_ratio + WORST_REGRESSION_WEIGHT * worst_regression_log

    capacity_pressures = {
        key: _as_float(row.get(key)) / capacity
        for key, capacity in MEMORY_CAPACITY.items()
    }
    worst_capacity_metric, worst_capacity_pressure = max(
        capacity_pressures.items(),
        key=lambda item: item[1],
    )

    return {
        "run": run_name,
        "case": row["case"],
        "problem": int(row["problem"]),
        "balanced_score": balanced_score,
        "weighted_log_ratio": weighted_log_ratio,
        "worst_regression_metric": worst_regression_metric,
        "worst_regression_ratio": ratios[worst_regression_metric],
        "worst_regression_log2": worst_regression_log,
        "cache_pressure_mean": _mean(capacity_pressures.values()),
        "worst_capacity_metric": worst_capacity_metric,
        "worst_capacity_pressure": worst_capacity_pressure,
        **{f"{key}_ratio": ratios[key] for key in METRIC_WEIGHTS},
        **{f"{key}_log2": log_ratios[key] for key in METRIC_WEIGHTS},
        **{f"{key}_pressure": capacity_pressures[key] for key in MEMORY_KEYS},
        **{key: _as_float(row.get(key)) for key in MEMORY_KEYS},
        "time": _as_float(row.get("time")),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _print_summary(rows: list[dict[str, Any]], top: int) -> None:
    full_rows = [row for row in rows if row["case_count"] == FULL_P1_CASES]
    partial_rows = [row for row in rows if row["case_count"] != FULL_P1_CASES]

    print("Full P1 balanced ranking:")
    for row in full_rows[:top]:
        print(
            f"{row['balanced_score']:.4f}  {row['run']}  "
            f"cases={row['case_count']} worst={row['worst_case']}:{row['worst_metric']} "
            f"ratio={row['worst_metric_ratio']:.2f}"
        )

    if partial_rows:
        print("\nPartial P1 balanced ranking:")
        for row in partial_rows[:top]:
            print(
                f"{row['balanced_score']:.4f}  {row['run']}  "
                f"cases={row['case_count']} worst={row['worst_case']}:{row['worst_metric']} "
                f"ratio={row['worst_metric_ratio']:.2f}"
            )


def _mean(values: Any) -> float:
    numbers = list(values)
    return sum(numbers) / len(numbers)


def _geo_mean(values: Any) -> float:
    numbers = [max(float(value), 1e-12) for value in values]
    return 2 ** _mean(_log2(value) for value in numbers)


def _ratio_against_baseline(value: float, baseline: float, zero_baseline_scale: int) -> float:
    if baseline > 0:
        return value / baseline
    if value == 0:
        return 1.0
    return 1.0 + value / zero_baseline_scale


def _log2(value: float) -> float:
    return math.log2(max(value, 1e-12))


def _as_float(value: Any) -> float:
    return float(value) if value not in (None, "") else 0.0


if __name__ == "__main__":
    raise SystemExit(main())
