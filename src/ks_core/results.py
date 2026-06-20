"""Load experiment result artifacts in the project-standard layout."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from ks_core.graph import load_json
from ks_core.io import read_memory_txt, read_schedule_txt, read_spill_txt
from ks_core.metrics import load_metrics
from ks_core.types import ProblemInstance, Schedule


def load_experiment_bundle(
    project_root: Path,
    experiment_name: str,
    case_order: Iterable[str],
    problems: Iterable[int] = (1, 2, 3),
) -> dict[str, Any]:
    """Load instances, solution artifacts, and metrics for one experiment."""
    result_dir = project_root / "results" / experiment_name
    instances: dict[int, dict[str, ProblemInstance]] = {}
    orders: dict[int, dict[str, list[int]]] = {}
    memories: dict[int, dict[str, dict[int, int]]] = {}
    spills: dict[int, dict[str, list[tuple[int, int]]]] = {}
    schedules: dict[int, dict[str, Schedule]] = {}

    cases = list(case_order)
    for problem_id in problems:
        instances[problem_id] = {}
        orders[problem_id] = {}
        memories[problem_id] = {}
        spills[problem_id] = {}
        schedules[problem_id] = {}

        for case in cases:
            instance = load_json(
                project_root / "data" / "raw" / "json" / f"{case}.json",
                problem_id=problem_id,
            )
            schedule = load_schedule_result(result_dir, case, problem_id)
            instances[problem_id][case] = instance
            orders[problem_id][case] = schedule.order
            memories[problem_id][case] = schedule.memory
            spills[problem_id][case] = schedule.spill_entries
            schedules[problem_id][case] = schedule

    return {
        "result_dir": result_dir,
        "instances": instances,
        "orders": orders,
        "memories": memories,
        "spills": spills,
        "schedules": schedules,
        "metrics": pd.DataFrame(load_metrics(_required(result_dir / "metrics.json"))),
    }


def load_schedule_result(result_dir: Path, case_name: str, problem_id: int) -> Schedule:
    """Load one schedule, including memory/spill artifacts for P2/P3."""
    metadata = _result_metadata(result_dir)
    schedule = Schedule(
        case_name=case_name,
        problem_id=problem_id,
        algorithm=metadata.get("algorithm", result_dir.name),
        order=read_schedule_txt(
            _required(result_dir / "schedules" / f"P{problem_id}_{case_name}_schedule.txt")
        ),
    )
    if problem_id >= 2:
        schedule.memory = read_memory_txt(
            _required(result_dir / "memory" / f"P{problem_id}_{case_name}_memory.txt")
        )
        schedule.spill_entries = read_spill_txt(
            _required(result_dir / "spills" / f"P{problem_id}_{case_name}_spill.txt")
        )
    return schedule


def _result_metadata(result_dir: Path) -> dict[str, Any]:
    path = result_dir / "metadata.json"
    if not path.exists():
        return {}

    import json

    with open(path) as f:
        return json.load(f)


def _required(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Missing result artifact: {path}")
    return path
