"""Evaluate baseline01 result artifacts against recorded metrics.json values."""

from __future__ import annotations

import sys

from ks_core.graph import load_json
from ks_core.io import get_project_root
from ks_core.metrics import CANONICAL_METRIC_KEYS, evaluate, load_metrics
from ks_core.results import load_schedule_result

EXPERIMENT_NAME = "exp001_baseline01"
METRIC_COLUMNS = CANONICAL_METRIC_KEYS


def main() -> None:
    root = get_project_root()
    result_dir = root / "results" / EXPERIMENT_NAME
    rows = load_metrics(result_dir / "metrics.json")
    failures: list[str] = []

    print("problem case                      metric          computed      expected")
    print("------- ------------------------- --------------- ------------- -------------")

    for row in rows:
        result = evaluate_row(root, row)
        failures.extend(
            f"P{row['problem']} {row['case']}: {error}" for error in result.errors
        )

        for column in METRIC_COLUMNS:
            expected = int(row[column])
            actual = result.metrics[column]
            status = "OK" if actual == expected else "FAIL"
            if actual != expected:
                failures.append(
                    f"P{row['problem']} {row['case']} {column}: "
                    f"computed {actual}, expected {expected}"
                )
            print(
                f"P{row['problem']:<6} {row['case']:<25} {column:<15} "
                f"{actual:<13} {expected:<13} {status}"
            )

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"  {failure}")
        sys.exit(1)

    print(f"\nAll baseline01 metrics matched for {len(rows)} rows.")


def evaluate_row(root, row):
    problem_id = int(row["problem"])
    case_name = row["case"]
    instance = load_json(
        root / "data" / "raw" / "json" / f"{case_name}.json",
        problem_id=problem_id,
    )
    schedule = load_schedule_result(root / "results" / EXPERIMENT_NAME, case_name, problem_id)
    return evaluate(
        instance,
        schedule.order,
        schedule.memory or None,
        schedule.spill_entries or None,
    )


if __name__ == "__main__":
    main()
