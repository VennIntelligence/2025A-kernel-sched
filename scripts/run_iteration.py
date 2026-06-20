"""Run one immutable AutoResearch iteration.

Process state (iterations, ledger, best_iter) lives under ``autoresearch/``;
the active solver slot is ``algorithms/ours/solve.py``. The search is complete
(iter038 promoted into ``ks_core.solver``); this runner is retained for
reproducibility.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from ks_core.io import get_project_root
from ks_core.metrics import load_metrics

SUITES: dict[str, dict[str, Any]] = {
    "p1_fast": {
        "cases": ["Conv_Case0", "FlashAttention_Case0", "Matmul_Case0"],
        "problems": [1],
    },
    "p1_full": {
        "cases": [
            "Conv_Case0",
            "Conv_Case1",
            "FlashAttention_Case0",
            "FlashAttention_Case1",
            "Matmul_Case0",
            "Matmul_Case1",
        ],
        "problems": [1],
    },
    "p2_fast": {
        "cases": ["Conv_Case0", "FlashAttention_Case0", "Matmul_Case0"],
        "problems": [1, 2],
    },
    "p2_full": {
        "cases": [
            "Conv_Case0",
            "Conv_Case1",
            "FlashAttention_Case0",
            "FlashAttention_Case1",
            "Matmul_Case0",
            "Matmul_Case1",
        ],
        "problems": [1, 2],
    },
    "p3_fast": {
        "cases": ["Conv_Case0", "FlashAttention_Case0", "Matmul_Case0"],
        "problems": [1, 2, 3],
    },
    "p3_full": {
        "cases": [
            "Conv_Case0",
            "Conv_Case1",
            "FlashAttention_Case0",
            "FlashAttention_Case1",
            "Matmul_Case0",
            "Matmul_Case1",
        ],
        "problems": [1, 2, 3],
    },
    "full": {
        "cases": [
            "Conv_Case0",
            "Conv_Case1",
            "FlashAttention_Case0",
            "FlashAttention_Case1",
            "Matmul_Case0",
            "Matmul_Case1",
        ],
        "problems": [1, 2, 3],
    },
    "regression_full": {
        "cases": [
            "Conv_Case0",
            "Conv_Case1",
            "FlashAttention_Case0",
            "FlashAttention_Case1",
            "Matmul_Case0",
            "Matmul_Case1",
        ],
        "problems": [1, 2, 3],
    },
}

LEDGER_COLUMNS = [
    "iter",
    "timestamp",
    "algorithm_desc",
    "case",
    "problem",
    "algorithm",
    "max_L1",
    "max_UB",
    "max_L0A_count",
    "max_L0B_count",
    "max_L0C_count",
    "spills",
    "extra",
    "time",
    "schedule_len",
    "valid",
    "violations",
]


def main() -> int:
    args = _parse_args()
    root = get_project_root()
    suite = SUITES[args.suite]
    iter_id = _format_iter(args.iter_id)
    slug = _slugify(args.desc)
    iter_name = f"iter{iter_id}_{slug}"

    process_dir = root / "autoresearch"
    method_dir = root / "algorithms" / "ours"
    iteration_dir = process_dir / "iterations" / iter_name
    candidate_solve = iteration_dir / "solve.py"
    active_solve = method_dir / "solve.py"
    result_dir = root / "results" / "autoresearch" / iter_name
    best_path = process_dir / "best_iter.txt"
    ledger_path = process_dir / "ledger.csv"

    if not candidate_solve.exists():
        raise FileNotFoundError(f"Missing candidate solver: {candidate_solve}")
    if result_dir.exists():
        raise FileExistsError(f"Result directory already exists: {result_dir}")
    if (iteration_dir / "status.json").exists() or (iteration_dir / "config.yaml").exists():
        raise FileExistsError(f"Iteration already has run metadata: {iteration_dir}")

    previous_best = best_path.read_text().strip() if best_path.exists() else ""
    timestamp = datetime.now(timezone.utc).isoformat()

    result_dir.mkdir(parents=True)
    config_path = iteration_dir / "config.yaml"
    _write_config(config_path, iter_name, suite, result_dir.relative_to(root))

    shutil.copy2(candidate_solve, active_solve)
    command = [
        "uv",
        "run",
        "python",
        "experiments/run_experiment.py",
        str(config_path.relative_to(root)),
    ]
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True)
    _write_run_log(result_dir / "run.log", command, completed)

    metrics_path = result_dir / "metrics.json"
    rows = load_metrics(metrics_path) if metrics_path.exists() else []
    if rows:
        _append_ledger(ledger_path, rows, iter_id, timestamp, slug)

    promoted, comparison = _promotion_decision(
        rows=rows,
        previous_best=previous_best,
        root=root,
        suite_name=args.suite,
        promote_mode=args.promote,
        run_succeeded=completed.returncode == 0,
    )
    baseline_comparison = _comparison_summary(
        rows,
        load_metrics(root / "results" / "exp001_baseline01" / "metrics.json"),
    )
    if promoted:
        shutil.copy2(candidate_solve, active_solve)
        best_path.write_text(f"{iter_name}\n")
    elif previous_best:
        best_solve = process_dir / "iterations" / previous_best / "solve.py"
        if best_solve.exists():
            shutil.copy2(best_solve, active_solve)

    status = {
        "iteration": iter_name,
        "suite": args.suite,
        "result_dir": str(result_dir.relative_to(root)),
        "returncode": completed.returncode,
        "promoted": promoted,
        "previous_best": previous_best,
        "baseline_comparison": baseline_comparison,
        "comparison": comparison,
    }
    (iteration_dir / "status.json").write_text(json.dumps(status, indent=2) + "\n")

    print(f"Iteration: {iter_name}")
    print(f"Suite: {args.suite}")
    print(f"Results: {result_dir.relative_to(root)}")
    print(f"Rows: {len(rows)}")
    print(f"Promoted: {promoted}")
    if comparison:
        print(f"Comparison: {comparison}")
    if baseline_comparison:
        print(f"Baseline: {baseline_comparison}")
    return completed.returncode


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one AutoResearch iteration")
    parser.add_argument("--iter", dest="iter_id", required=True, help="Iteration id, e.g. 002")
    parser.add_argument(
        "--desc",
        "--slug",
        dest="desc",
        required=True,
        help="Short iteration description",
    )
    parser.add_argument("--suite", choices=sorted(SUITES), default="p1_fast")
    parser.add_argument(
        "--promote",
        choices=["auto", "always", "never"],
        default="auto",
        help="Promotion policy after evaluation",
    )
    return parser.parse_args()


def _format_iter(value: str) -> str:
    return f"{int(value):03d}" if value.isdigit() else value


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    if not slug:
        raise ValueError("Iteration description must contain at least one alphanumeric character")
    return slug


def _write_config(
    config_path: Path,
    iter_name: str,
    suite: dict[str, Any],
    output_dir: Path,
) -> None:
    config = {
        "experiment": {
            "name": f"autoresearch_{iter_name}",
            "author": "autoresearch",
            "description": f"AutoResearch iteration {iter_name}",
        },
        "algorithm": {
            "name": "ours",
            "params": {},
        },
        "cases": suite["cases"],
        "problems": suite["problems"],
        "output": {
            "dir": str(output_dir),
            "save_schedules": True,
        },
    }
    with open(config_path, "w") as f:
        yaml.safe_dump(config, f, sort_keys=False)


def _write_run_log(
    path: Path,
    command: list[str],
    completed: subprocess.CompletedProcess[str],
) -> None:
    content = [
        "$ " + " ".join(command),
        f"returncode: {completed.returncode}",
        "",
        "## stdout",
        completed.stdout,
        "",
        "## stderr",
        completed.stderr,
    ]
    path.write_text("\n".join(content))


def _append_ledger(
    ledger_path: Path,
    rows: list[dict[str, Any]],
    iter_id: str,
    timestamp: str,
    algorithm_desc: str,
) -> None:
    write_header = not ledger_path.exists() or ledger_path.stat().st_size == 0
    with open(ledger_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LEDGER_COLUMNS, lineterminator="\n")
        if write_header:
            writer.writeheader()
        for row in rows:
            output = {column: row.get(column, "") for column in LEDGER_COLUMNS}
            output["iter"] = iter_id
            output["timestamp"] = timestamp
            output["algorithm_desc"] = algorithm_desc
            writer.writerow(output)


def _promotion_decision(
    rows: list[dict[str, Any]],
    previous_best: str,
    root: Path,
    suite_name: str,
    promote_mode: str,
    run_succeeded: bool,
) -> tuple[bool, dict[str, Any]]:
    valid = bool(rows) and run_succeeded and all(_as_bool(row.get("valid")) for row in rows)
    if promote_mode == "never":
        return False, {"reason": "promotion disabled", "valid": valid}
    if not valid:
        return False, {"reason": "candidate invalid or incomplete", "valid": valid}
    if promote_mode == "always":
        return True, {"reason": "forced promotion", "valid": valid}
    if not previous_best:
        return True, {"reason": "first valid autoresearch iteration", "valid": valid}
    if suite_name.endswith("_fast"):
        return False, {"reason": "fast suite cannot promote existing best", "valid": valid}

    best_rows = _load_best_rows(root, previous_best)
    if not best_rows:
        return True, {"reason": "previous best metrics unavailable", "valid": valid}

    wins, losses, ties = _compare_metric_rows(rows, best_rows)
    promoted = losses == 0 and wins > 0
    reason = (
        "candidate is no-worse and improves at least one row"
        if promoted
        else "candidate did not beat current best"
    )
    comparison = {"reason": reason, "valid": valid, "wins": wins, "losses": losses, "ties": ties}
    return promoted, comparison


def _load_best_rows(root: Path, previous_best: str) -> list[dict[str, Any]]:
    path = root / "results" / "autoresearch" / previous_best / "metrics.json"
    return load_metrics(path) if path.exists() else []


def _compare_metric_rows(
    candidate_rows: list[dict[str, Any]],
    best_rows: list[dict[str, Any]],
) -> tuple[int, int, int]:
    best_by_key = {(row.get("case"), int(row.get("problem", 0))): row for row in best_rows}
    wins = losses = ties = 0
    for row in candidate_rows:
        key = (row.get("case"), int(row.get("problem", 0)))
        best = best_by_key.get(key)
        if best is None:
            wins += 1
            continue
        candidate_score = _score(row)
        best_score = _score(best)
        if candidate_score < best_score:
            wins += 1
        elif candidate_score > best_score:
            losses += 1
        else:
            ties += 1
    return wins, losses, ties


def _comparison_summary(
    candidate_rows: list[dict[str, Any]],
    reference_rows: list[dict[str, Any]],
) -> dict[str, int]:
    if not candidate_rows or not reference_rows:
        return {}
    wins, losses, ties = _compare_metric_rows(candidate_rows, reference_rows)
    return {"wins": wins, "losses": losses, "ties": ties}


def _score(row: dict[str, Any]) -> tuple[int, ...]:
    problem = int(row.get("problem", 0))
    violations = int(row.get("violations", 0))
    if not _as_bool(row.get("valid", True)):
        violations = max(violations, 1)

    if problem == 1:
        keys = ("max_L1", "max_UB", "max_L0A_count", "max_L0B_count", "max_L0C_count", "time")
    elif problem == 2:
        keys = ("extra", "spills", "time", "max_L1", "max_UB")
    else:
        keys = ("time", "extra", "spills", "max_L1", "max_UB")
    return (violations, *(_as_int(row.get(key)) for key in keys))


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.lower() == "true"
    return bool(value)


def _as_int(value: Any) -> int:
    return int(value) if value not in (None, "") else 0


if __name__ == "__main__":
    sys.exit(main())
