"""Unified metrics computation and comparison utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ks_core.types import Metrics, Schedule


def compute_metrics(schedule: Schedule) -> Metrics:
    """Compute standardized metrics from a schedule.

    NOTE: This is a placeholder. The actual implementation needs the
    simulator to replay the schedule against the DAG constraints.
    """
    return Metrics(
        total_time=schedule.metrics.get("time", 0),
        num_spills=schedule.metrics.get("spills", 0),
        extra_memory=schedule.metrics.get("extra", 0),
        violations=schedule.metrics.get("viol", 0),
        schedule_length=len(schedule.order),
    )


def load_metrics(path: Path) -> dict[str, Any]:
    """Load metrics from a JSON results file."""
    with open(path) as f:
        return json.load(f)


def save_metrics(metrics: Metrics, path: Path) -> None:
    """Save metrics to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "total_time": metrics.total_time,
        "num_spills": metrics.num_spills,
        "extra_memory": metrics.extra_memory,
        "violations": metrics.violations,
        "schedule_length": metrics.schedule_length,
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def compare_experiments(result_dirs: list[Path]) -> list[dict[str, Any]]:
    """Compare metrics across multiple experiment result directories.

    Returns a list of dicts suitable for pandas DataFrame construction.
    """
    rows: list[dict[str, Any]] = []
    for d in result_dirs:
        metrics_path = d / "metrics.json"
        if not metrics_path.exists():
            continue
        data = load_metrics(metrics_path)
        data["experiment"] = d.name
        rows.append(data)
    return rows
