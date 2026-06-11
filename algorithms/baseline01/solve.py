"""Baseline GPT solver — wraps the pre-computed results as a solve() interface.

This algorithm doesn't actually compute anything at runtime. It loads
the pre-existing schedule files produced by GPT's first-round solution.
It serves as the baseline for comparison with new algorithms.
"""

from __future__ import annotations

from pathlib import Path

from ks_core.io import read_schedule_txt
from ks_core.types import ProblemInstance, Schedule

SOLUTION_DIR = Path(__file__).parent


def solve(instance: ProblemInstance, config: dict | None = None) -> Schedule:
    """Load the pre-computed GPT baseline schedule for this instance.

    Args:
        instance: Problem instance (only case_name and problem_id are used).
        config: Unused for baseline.

    Returns:
        Schedule with the pre-computed node ordering.
    """
    problem_dir = SOLUTION_DIR / f"Problem{instance.problem_id}"
    schedule_file = problem_dir / f"{instance.case_name}_schedule.txt"

    if not schedule_file.exists():
        raise FileNotFoundError(
            f"No baseline schedule for {instance.case_name} P{instance.problem_id}: "
            f"{schedule_file}"
        )

    order = read_schedule_txt(schedule_file)

    return Schedule(
        case_name=instance.case_name,
        problem_id=instance.problem_id,
        algorithm="baseline_gpt",
        order=order,
    )


if __name__ == "__main__":
    import argparse
    from ks_core.graph import load_json
    from ks_core.io import data_dir

    parser = argparse.ArgumentParser(description="Run baseline GPT solver")
    parser.add_argument("--case", required=True, help="Case name, e.g. Conv_Case0")
    parser.add_argument("--problem", type=int, default=1, help="Problem ID (1/2/3)")
    args = parser.parse_args()

    json_path = data_dir() / "json" / f"{args.case}.json"
    instance = load_json(json_path, problem_id=args.problem)
    result = solve(instance)
    print(f"✅ Loaded baseline schedule: {len(result.order)} steps")
