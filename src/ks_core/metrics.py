"""Unified metrics computation and comparison utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ks_core.evaluator import (
    compute_extra,
    compute_max_vstay,
    compute_total_time,
    validate_memory,
    validate_spill,
)
from ks_core.types import EvaluationResult, Metrics, ProblemInstance

# Canonical metric keys used in metrics.json, metrics.csv, and experiment outputs.
CANONICAL_METRIC_KEYS = (
    "max_L1",
    "max_UB",
    "max_L0A_count",
    "max_L0B_count",
    "max_L0C_count",
    "spills",
    "extra",
    "time",
    "schedule_len",
)


def evaluate(
    instance: ProblemInstance,
    order: list[int],
    memory: dict[int, int] | None = None,
    spill_entries: list[tuple[int, int]] | None = None,
) -> EvaluationResult:
    """Validate a solution and compute canonical metrics."""
    errors = collect_validation_errors(instance, order, memory, spill_entries)
    metrics = compute_solution_metrics(instance, order, memory, spill_entries)
    return EvaluationResult(
        valid=not errors,
        errors=errors,
        metrics=metrics,
        violations=len(errors),
    )


def collect_validation_errors(
    instance: ProblemInstance,
    order: list[int],
    memory: dict[int, int] | None = None,
    spill_entries: list[tuple[int, int]] | None = None,
) -> list[str]:
    """Run all applicable validation checks for a problem variant."""
    nodes = {node.id: node for node in instance.nodes}
    spill_entries = spill_entries or []
    num_original = len(instance.nodes)

    if instance.problem_id >= 2:
        errors = validate_spill(
            order,
            nodes,
            instance.edges,
            spill_entries,
            num_original,
        )
        errors.extend(
            validate_memory(
                order,
                nodes,
                memory if memory is not None else {},
                spill_entries=spill_entries,
                num_original_nodes=num_original,
            )
        )
    else:
        errors = _validate_original_schedule(
            order,
            instance,
            allow_extra=False,
        )
    return errors


def compute_solution_metrics(
    instance: ProblemInstance,
    order: list[int],
    memory: dict[int, int] | None = None,
    spill_entries: list[tuple[int, int]] | None = None,
) -> dict[str, int]:
    """Compute canonical metrics for a schedule (independent of validity)."""
    nodes = {node.id: node for node in instance.nodes}
    spill_entries = spill_entries or []
    num_original = len(instance.nodes)
    use_spill = instance.problem_id >= 2

    return {
        **compute_max_vstay(order, nodes),
        "spills": len(spill_entries),
        "extra": compute_extra(spill_entries, nodes) if use_spill else 0,
        "time": compute_total_time(
            order,
            nodes,
            instance.edges,
            memory=memory if use_spill else None,
            spill_entries=spill_entries if use_spill else None,
            num_original_nodes=num_original,
        ),
        "schedule_len": len(order),
    }


def evaluation_to_metrics(result: EvaluationResult) -> Metrics:
    """Convert an :class:`EvaluationResult` to the summary :class:`Metrics` dataclass."""
    return metrics_dict_to_dataclass(result.metrics, violations=result.violations)


def metrics_dict_to_dataclass(
    metrics: dict[str, Any],
    violations: int = 0,
) -> Metrics:
    """Map canonical metric dict keys to :class:`Metrics` fields."""
    return Metrics(
        total_time=int(metrics.get("time", 0)),
        num_spills=int(metrics.get("spills", 0)),
        extra_memory=int(metrics.get("extra", 0)),
        violations=violations,
        schedule_length=int(metrics.get("schedule_len", 0)),
    )


def load_metrics(path: Path) -> list[dict[str, Any]]:
    """Load metrics from a JSON results file, always returning a list of rows."""
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return [data]


def save_metrics(metrics: Metrics, path: Path) -> None:
    """Save summary metrics to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "time": metrics.total_time,
        "spills": metrics.num_spills,
        "extra": metrics.extra_memory,
        "violations": metrics.violations,
        "schedule_len": metrics.schedule_length,
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def compare_experiments(result_dirs: list[Path]) -> list[dict[str, Any]]:
    """Compare metrics across experiment directories.

    Each row in every ``metrics.json`` list becomes one comparison entry.
    """
    rows: list[dict[str, Any]] = []
    for result_dir in result_dirs:
        metrics_path = result_dir / "metrics.json"
        if not metrics_path.exists():
            continue
        for entry in load_metrics(metrics_path):
            row = dict(entry)
            row["experiment"] = result_dir.name
            rows.append(row)
    return rows


def _validate_original_schedule(
    order: list[int],
    instance: ProblemInstance,
    allow_extra: bool,
) -> list[str]:
    """Validate schedule coverage, uniqueness, and original DAG dependencies."""
    errors: list[str] = []
    node_ids = {node.id for node in instance.nodes}
    order_set = set(order)

    missing = node_ids - order_set
    extra = order_set - node_ids
    if missing:
        errors.append(f"Missing nodes: {sorted(missing)[:10]} ({len(missing)} total)")
    if extra and not allow_extra:
        errors.append(f"Unknown nodes: {sorted(extra)[:10]} ({len(extra)} total)")
    if len(order) != len(order_set):
        errors.append(f"Duplicate nodes: {len(order)} entries but {len(order_set)} unique")

    position = {node_id: index for index, node_id in enumerate(order)}
    dep_violations = 0
    for edge in instance.edges:
        src_pos = position.get(edge.src)
        dst_pos = position.get(edge.dst)
        if src_pos is not None and dst_pos is not None and src_pos >= dst_pos:
            dep_violations += 1
            if dep_violations <= 5:
                errors.append(
                    f"Dependency violation: node {edge.src} (pos {src_pos}) "
                    f"must come before node {edge.dst} (pos {dst_pos})"
                )
    if dep_violations > 5:
        errors.append(f"{dep_violations - 5} more dependency violations")
    return errors
