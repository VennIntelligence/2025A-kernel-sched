"""Experiment runner — load config, run algorithm, save results."""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from ks_core.graph import load_json
from ks_core.io import get_project_root, save_result


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

    # Run for each case × problem
    for case_name in cases:
        json_path = root / "data" / "raw" / "json" / f"{case_name}.json"
        if not json_path.exists():
            print(f"⚠️  Skipping {case_name}: data file not found")
            continue

        for pid in problems:
            print(f"▶ Running {algo_config['name']} on {case_name} P{pid}...")
            instance = load_json(json_path, problem_id=pid)
            schedule = solve_fn(instance, algo_config.get("params", {}))

            if output_config.get("save_schedules", True):
                save_result(schedule, output_dir)

            print(f"  ✅ {case_name} P{pid}: {len(schedule.order)} steps")

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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run an experiment")
    parser.add_argument("config", type=Path, help="Path to experiment YAML config")
    args = parser.parse_args()

    run_experiment(args.config)
