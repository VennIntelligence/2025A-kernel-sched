"""Baseline01 adapter backed by canonical experiment result artifacts."""

from __future__ import annotations

from pathlib import Path

from ks_core.io import get_project_root, read_memory_txt, read_schedule_txt, read_spill_txt
from ks_core.types import ProblemInstance, Schedule

DEFAULT_RESULT_DIR = Path("results/exp001_baseline01")


def solve(
    instance: ProblemInstance,
    config: dict | None = None,
) -> Schedule:
    """Return the stored baseline01 solution in the project-standard shape."""
    result_dir = _result_dir(config or {})
    schedule = Schedule(
        case_name=instance.case_name,
        problem_id=instance.problem_id,
        algorithm="baseline01",
        order=read_schedule_txt(
            _required_artifact(
                result_dir
                / "schedules"
                / f"P{instance.problem_id}_{instance.case_name}_schedule.txt"
            )
        ),
    )

    if instance.problem_id == 1:
        return schedule

    schedule.memory = read_memory_txt(
        _required_artifact(
            result_dir / "memory" / f"P{instance.problem_id}_{instance.case_name}_memory.txt"
        )
    )
    schedule.spill_entries = read_spill_txt(
        _required_artifact(
            result_dir / "spills" / f"P{instance.problem_id}_{instance.case_name}_spill.txt"
        )
    )
    return schedule


def _result_dir(config: dict) -> Path:
    configured = Path(config.get("result_dir", DEFAULT_RESULT_DIR))
    return configured if configured.is_absolute() else get_project_root() / configured


def _required_artifact(path: Path) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"Missing baseline01 artifact: {path}")
    return path


if __name__ == "__main__":
    import argparse

    from ks_core.graph import load_json
    from ks_core.io import data_dir

    parser = argparse.ArgumentParser(description="Load a baseline01 solution")
    parser.add_argument("--case", required=True, help="Case name, e.g. Conv_Case0")
    parser.add_argument("--problem", type=int, default=1, help="Problem ID (1/2/3)")
    args = parser.parse_args()

    json_path = data_dir() / "json" / f"{args.case}.json"
    instance = load_json(json_path, problem_id=args.problem)
    schedule = solve(instance)
    print(f"Loaded baseline schedule: {len(schedule.order)} steps")
