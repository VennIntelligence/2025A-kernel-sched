"""Validate schedule files — check constraint satisfaction and compute metrics."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ks_core.graph import load_json
from ks_core.io import get_project_root, read_memory_txt, read_schedule_txt, read_spill_txt
from ks_core.metrics import evaluate


def validate_schedule(
    case_name: str,
    problem_id: int,
    schedule_path: Path,
    memory_path: Path | None = None,
    spill_path: Path | None = None,
) -> tuple[list[str], dict[str, int]]:
    """Validate a schedule and compute metrics.

    Returns (errors, metrics). errors is empty when valid.
    """
    root = get_project_root()
    json_path = root / "data" / "raw" / "json" / f"{case_name}.json"
    if not json_path.exists():
        return [f"Data file not found: {json_path}"], {}

    instance = load_json(json_path, problem_id=problem_id)
    order = read_schedule_txt(schedule_path)
    memory = read_memory_txt(memory_path) if memory_path else None
    spills = read_spill_txt(spill_path) if spill_path else []

    result = evaluate(instance, order, memory, spills)
    return result.errors, result.metrics


def _print_result(label: str, errors: list[str], metrics: dict[str, int]) -> bool:
    if errors:
        print(f"FAIL  {label}")
        for error in errors:
            print(f"      {error}")
        return False
    metric_text = ", ".join(f"{k}={v}" for k, v in metrics.items())
    print(f"OK    {label}  ({metric_text})")
    return True


def _parse_schedule_path(path: Path, default_problem: int) -> tuple[str, int]:
    stem = path.stem.removesuffix("_schedule")
    parts = stem.split("_", 1)
    if len(parts) == 2 and parts[0].startswith("P") and parts[0][1:].isdigit():
        return parts[1], int(parts[0][1:])
    parent = path.parent.name
    if parent.startswith("Problem") and parent.removeprefix("Problem").isdigit():
        return stem, int(parent.removeprefix("Problem"))
    return stem, default_problem


def _sibling_artifact(schedule_path: Path, suffix: str) -> Path | None:
    artifact_name = schedule_path.name.replace("_schedule.txt", f"_{suffix}.txt")
    candidate = schedule_path.with_name(artifact_name)
    if candidate.exists():
        return candidate

    artifact_dir = {"memory": "memory", "spill": "spills"}.get(suffix, suffix)
    candidate = schedule_path.parent.parent / artifact_dir / artifact_name
    return candidate if candidate.exists() else None


def _print_summary(rows: list[tuple[str, int, bool, dict[str, int]]]) -> None:
    if not rows:
        return
    all_keys: list[str] = []
    for *_, metrics in rows:
        for key in metrics:
            if key not in all_keys:
                all_keys.append(key)

    headers = ["case", "P", "status"] + all_keys
    table: list[list[str]] = []
    for case, pid, ok, metrics in rows:
        table.append(
            [case, str(pid), "OK" if ok else "FAIL"]
            + [str(metrics.get(key, "")) for key in all_keys]
        )

    widths = [max(len(header), *(len(row[i]) for row in table)) for i, header in enumerate(headers)]
    sep = "  "
    fmt = sep.join(f"{{:<{w}}}" for w in widths)

    print("\n" + "=" * (sum(widths) + len(sep) * (len(widths) - 1)))
    print(fmt.format(*headers))
    print("-" * (sum(widths) + len(sep) * (len(widths) - 1)))
    for row in table:
        print(fmt.format(*row))
    print("=" * (sum(widths) + len(sep) * (len(widths) - 1)))


def main():
    parser = argparse.ArgumentParser(description="Validate schedule files")
    parser.add_argument("--dir", type=Path, help="Directory containing schedule files")
    parser.add_argument("--case", help="Case name (e.g. Conv_Case0)")
    parser.add_argument("--problem", type=int, default=1, help="Problem ID")
    parser.add_argument("--file", type=Path, help="Single schedule file to validate")
    parser.add_argument("--memory", type=Path, help="Path to memory.txt (P2/P3)")
    parser.add_argument("--spill", type=Path, help="Path to spill.txt (P2/P3)")
    args = parser.parse_args()

    summary: list[tuple[str, int, bool, dict[str, int]]] = []

    if args.file and args.case:
        errors, metrics = validate_schedule(
            args.case, args.problem, args.file, args.memory, args.spill,
        )
        ok = _print_result(str(args.file), errors, metrics)
        summary.append((args.case, args.problem, ok, metrics))
    elif args.dir:
        for schedule_file in sorted(args.dir.rglob("*_schedule.txt")):
            case, pid = _parse_schedule_path(schedule_file, args.problem)
            mem = _sibling_artifact(schedule_file, "memory") if pid >= 2 else None
            spl = _sibling_artifact(schedule_file, "spill") if pid >= 2 else None
            errors, metrics = validate_schedule(case, pid, schedule_file, mem, spl)
            ok = _print_result(str(schedule_file), errors, metrics)
            summary.append((case, pid, ok, metrics))
    else:
        parser.print_help()
        return

    _print_summary(summary)
    if any(not ok for _, _, ok, _ in summary):
        sys.exit(1)


if __name__ == "__main__":
    main()
