"""Experiment runner — load config, run algorithm, save results."""

from __future__ import annotations

import importlib
import importlib.util
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from ks_core.graph import load_json
from ks_core.io import get_project_root, write_memory_txt, write_schedule_txt, write_spill_txt


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
        # Fallback: try importing from the filesystem directly
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

    # Save run metadata
    metadata = {
        "experiment": exp["name"],
        "algorithm": algo_config["name"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config_file": str(config_path),
        "git_hash": _get_git_hash(),
    }
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # Resolve algorithm
    solve_fn = resolve_algorithm(algo_config["name"])
    evaluator = _load_evaluator()

    # Run for each case × problem
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

            metrics = _compute_metrics(evaluator, instance, schedule, memory, spill_entries)
            _append_metrics(schedule, output_dir, metrics)

            max_l1 = metrics.get("max_L1", "?")
            max_ub = metrics.get("max_UB", "?")
            time_val = metrics.get("time", "?")
            print(
                f"  ✅ {case_name} P{pid}: {len(schedule.order)} steps, "
                f"max_L1={max_l1}, max_UB={max_ub}, time={time_val}"
            )

    print(f"\n📁 Results saved to: {output_dir}")


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


def _load_evaluator() -> Any | None:
    """Load the optional evaluator module when it is available."""
    try:
        return importlib.import_module("ks_core.evaluator")
    except ModuleNotFoundError as exc:
        if exc.name == "ks_core.evaluator":
            return None
        raise


def _unpack_solution(result: Any) -> tuple[Any, dict[int, int], list[tuple[int, int]]]:
    """Accept Schedule or (Schedule, memory, spill_entries) solver outputs."""
    if isinstance(result, tuple):
        schedule = result[0]
        memory = dict(result[1] or {}) if len(result) > 1 else {}
        spill_entries = _as_spill_entries(result[2] if len(result) > 2 else [])
        return schedule, memory, spill_entries

    memory = getattr(result, "memory", None) or getattr(result, "memory_layout", None) or {}
    spill_entries = (
        getattr(result, "spill_entries", None)
        or getattr(result, "spills", None)
        or []
    )
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


def _compute_metrics(
    evaluator: Any | None,
    instance: Any,
    schedule: Any,
    memory: dict[int, int],
    spill_entries: list[tuple[int, int]],
) -> dict[str, Any]:
    """Compute metrics from the optional evaluator functions."""
    metrics = dict(getattr(schedule, "metrics", {}) or {})
    metrics["schedule_len"] = len(schedule.order)
    metrics["spills"] = len(spill_entries)

    if evaluator is None:
        return metrics

    nodes_by_id = {node.id: node for node in instance.nodes}

    compute_max_vstay = getattr(evaluator, "compute_max_vstay", None)
    if callable(compute_max_vstay):
        original_order = [node_id for node_id in schedule.order if node_id in nodes_by_id]
        metrics.update(_prefix_max_metrics(compute_max_vstay(original_order, nodes_by_id)))

    compute_extra = getattr(evaluator, "compute_extra", None)
    if instance.problem_id >= 2 and callable(compute_extra):
        metrics["extra"] = compute_extra(spill_entries, nodes_by_id)

    compute_total_time = getattr(evaluator, "compute_total_time", None)
    if callable(compute_total_time):
        metrics["time"] = compute_total_time(
            schedule.order,
            nodes_by_id,
            instance.edges,
            memory=memory or None,
            spill_entries=spill_entries or None,
            num_original_nodes=len(instance.nodes),
        )

    return metrics


def _prefix_max_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    """Keep evaluator output compatible with existing max_* metric names."""
    return {
        key if key.startswith("max_") else f"max_{key}": value
        for key, value in metrics.items()
    }


def _append_metrics(schedule: Any, output_dir: Path, metrics: dict[str, Any]) -> None:
    """Append one experiment row to metrics.json."""
    metrics_path = output_dir / "metrics.json"
    existing: list[dict[str, Any]] = []
    if metrics_path.exists():
        with open(metrics_path) as f:
            data = json.load(f)
        existing = data if isinstance(data, list) else [data]

    existing.append(
        {
            "case": schedule.case_name,
            "problem": schedule.problem_id,
            "algorithm": schedule.algorithm,
            **metrics,
        }
    )
    with open(metrics_path, "w") as f:
        json.dump(existing, f, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run an experiment")
    parser.add_argument("config", type=Path, help="Path to experiment YAML config")
    args = parser.parse_args()

    run_experiment(args.config)
