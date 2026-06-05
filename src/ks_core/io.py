"""I/O utilities — schedule reading/writing, result management."""

from __future__ import annotations

import json
from pathlib import Path

from ks_core.types import Schedule


def read_schedule_txt(path: Path) -> list[int]:
    """Read a schedule file (one node ID per line)."""
    with open(path) as f:
        return [int(line.strip()) for line in f if line.strip()]


def write_schedule_txt(order: list[int], path: Path) -> None:
    """Write a schedule to a text file (one node ID per line)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for node_id in order:
            f.write(f"{node_id}\n")


def save_result(schedule: Schedule, output_dir: Path) -> None:
    """Save a complete schedule result to a directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save schedule order
    sched_dir = output_dir / "schedules"
    sched_dir.mkdir(exist_ok=True)
    write_schedule_txt(
        schedule.order,
        sched_dir / f"P{schedule.problem_id}_{schedule.case_name}_schedule.txt",
    )

    # Save metrics
    if schedule.metrics:
        metrics_path = output_dir / "metrics.json"
        # Append to existing metrics if file exists
        existing: list[dict] = []
        if metrics_path.exists():
            with open(metrics_path) as f:
                existing = json.load(f)
        existing.append(
            {
                "case": schedule.case_name,
                "problem": schedule.problem_id,
                "algorithm": schedule.algorithm,
                **schedule.metrics,
            }
        )
        with open(metrics_path, "w") as f:
            json.dump(existing, f, indent=2)


def get_project_root() -> Path:
    """Walk up from this file to find the project root (contains pyproject.toml)."""
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    raise FileNotFoundError("Could not find project root (no pyproject.toml found)")


def data_dir() -> Path:
    """Return the path to data/raw/."""
    return get_project_root() / "data" / "raw"


def results_dir() -> Path:
    """Return the path to results/."""
    return get_project_root() / "results"
