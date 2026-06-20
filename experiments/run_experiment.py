"""Experiment runner — load config, run algorithm, save results."""

from __future__ import annotations

import importlib
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from ks_core.graph import load_json
from ks_core.io import get_project_root, write_memory_txt, write_schedule_txt, write_spill_txt
from ks_core.metrics import evaluate
from ks_core.types import Schedule


def load_config(config_path: Path) -> dict:
    """Load a YAML experiment config."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def resolve_algorithm(algo_name: str):
    """Dynamically import the solve function from algorithms/<algo_name>/solve.py."""
    module_path = f"algorithms.{algo_name}.solve"
    try:
        mod = importlib.import_module(module_path)
    except ModuleNotFoundError:
        algo_dir = get_project_root() / "algorithms" / algo_name
        spec = importlib.util.spec_from_file_location(
            module_path, algo_dir / "solve.py"
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot find algorithm: {algo_name}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    return mod.solve


def run_experiment(config_path: Path) -> None:
    """Run a single experiment from a YAML config file."""
    config = load_config(config_path)
    exp = config["experiment"]
    algo_config = config["algorithm"]
    cases = config["cases"]
    problems = config.get("problems", [1])
    output_config = config.get("output", {})

    root = get_project_root()
    output_dir = root / output_config.get("dir", f"results/{exp['name']}")
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "experiment": exp["name"],
        "algorithm": algo_config["name"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config_file": str(config_path),
        "git_hash": _get_git_hash(),
    }
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    solve_fn = resolve_algorithm(algo_config["name"])
    invalid_runs = 0

    for case_name in cases:
        json_path = root / "data" / "raw" / "json" / f"{case_name}.json"
        if not json_path.exists():
            print(f"⚠️  Skipping {case_name}: data file not found")
            continue

        for pid in problems:
            print(f"▶ Running {algo_config['name']} on {case_name} P{pid}...")
            instance = load_json(json_path, problem_id=pid)
            schedule, memory, spill_entries = _unpack_solution(
                solve_fn(instance, algo_config.get("params", {}))
            )

            if output_config.get("save_schedules", True):
                write_schedule_txt(
                    schedule.order,
                    output_dir / "schedules" / f"P{pid}_{case_name}_schedule.txt",
                )

            if pid >= 2:
                write_memory_txt(
                    memory,
                    output_dir / "memory" / f"P{pid}_{case_name}_memory.txt",
                )
                write_spill_txt(
                    spill_entries,
                    output_dir / "spills" / f"P{pid}_{case_name}_spill.txt",
                )

            result = evaluate(
                instance,
                schedule.order,
                memory,
                spill_entries,
            )
            row = _build_metrics_row(schedule, result)
            _append_metrics(output_dir, row)

            status = "✅" if result.valid else "❌"
            if not result.valid:
                invalid_runs += 1
                for error in result.errors[:3]:
                    print(f"      {error}")
                if len(result.errors) > 3:
                    print(f"      ... and {len(result.errors) - 3} more errors")

            max_l1 = row.get("max_L1", "?")
            max_ub = row.get("max_UB", "?")
            time_val = row.get("time", "?")
            print(
                f"  {status} {case_name} P{pid}: {row['schedule_len']} steps, "
                f"max_L1={max_l1}, max_UB={max_ub}, time={time_val}, "
                f"valid={result.valid}"
            )

    print(f"\n📁 Results saved to: {output_dir}")
    if invalid_runs:
        print(f"⚠️  {invalid_runs} run(s) failed validation.")
        sys.exit(1)


def _get_git_hash() -> str:
    """Get current git commit hash, or 'unknown'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=get_project_root(),
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except FileNotFoundError:
        return "unknown"


def _unpack_solution(result: Any) -> tuple[Schedule, dict[int, int], list[tuple[int, int]]]:
    """Read the standard Schedule return shape required from every algorithm."""
    if not isinstance(result, Schedule):
        raise TypeError("Algorithm solve() must return ks_core.types.Schedule")

    memory = result.memory
    spill_entries = result.spill_entries
    return result, dict(memory), _as_spill_entries(spill_entries)


def _as_spill_entries(entries: Any) -> list[tuple[int, int]]:
    """Normalize spill entries to the text format shape: (BufId, NewOffset)."""
    normalized: list[tuple[int, int]] = []
    for entry in entries or []:
        if isinstance(entry, (tuple, list)) and len(entry) >= 2:
            normalized.append((int(entry[0]), int(entry[1])))
        elif hasattr(entry, "buf_id") and hasattr(entry, "new_offset"):
            normalized.append((int(entry.buf_id), int(entry.new_offset)))
    return normalized


def _build_metrics_row(schedule: Any, result: Any) -> dict[str, Any]:
    """Build one metrics.json row including validation status."""
    row = {
        "case": schedule.case_name,
        "problem": schedule.problem_id,
        "algorithm": schedule.algorithm,
        **result.metrics,
        "valid": result.valid,
        "violations": result.violations,
    }
    if result.errors:
        row["errors"] = result.errors[:10]
    return row


def _append_metrics(output_dir: Path, row: dict[str, Any]) -> None:
    """Append one experiment row to metrics.json."""
    metrics_path = output_dir / "metrics.json"
    existing: list[dict[str, Any]] = []
    if metrics_path.exists():
        with open(metrics_path) as f:
            data = json.load(f)
        existing = data if isinstance(data, list) else [data]

    existing.append(row)
    with open(metrics_path, "w") as f:
        json.dump(existing, f, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run an experiment")
    parser.add_argument("config", type=Path, help="Path to experiment YAML config")
    args = parser.parse_args()

    run_experiment(args.config)
