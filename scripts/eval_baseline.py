"""Evaluate baseline outputs against the recorded metrics.csv values."""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

from ks_core.evaluator import (
    compute_extra,
    compute_max_vstay,
    compute_total_time,
    validate_memory,
    validate_spill,
)
from ks_core.graph import load_json
from ks_core.io import get_project_root, read_memory_txt, read_schedule_txt, read_spill_txt

METRIC_COLUMNS = (
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


def main() -> None:
    root = get_project_root()
    baseline_dir = root / "algorithms" / "baseline_gpt"
    with open(baseline_dir / "metrics.csv") as f:
        rows = list(csv.DictReader(f))
    failures: list[str] = []

    print("problem case                      metric          computed      expected")
    print("------- ------------------------- --------------- ------------- -------------")

    for row in rows:
        computed, errors = evaluate_row(root, baseline_dir, row)
        failures.extend(f"{row['problem']} {row['case']}: {error}" for error in errors)

        for column in METRIC_COLUMNS:
            expected = int(row[column])
            actual = computed[column]
            status = "OK" if actual == expected else "FAIL"
            if actual != expected:
                failures.append(
                    f"{row['problem']} {row['case']} {column}: "
                    f"computed {actual}, expected {expected}"
                )
            print(
                f"{row['problem']:<7} {row['case']:<25} {column:<15} "
                f"{actual:<13} {expected:<13} {status}"
            )

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"  {failure}")
        sys.exit(1)

    print(f"\nAll baseline metrics matched for {len(rows)} rows.")


def evaluate_row(
    root: Path,
    baseline_dir: Path,
    row: dict[str, str],
) -> tuple[dict[str, int], list[str]]:
    problem_id = int(row["problem"][1:])
    case_name = row["case"]
    instance = load_json(
        root / "data" / "raw" / "json" / f"{case_name}.json",
        problem_id=problem_id,
    )
    nodes = {node.id: node for node in instance.nodes}
    artifact_dir = baseline_dir / f"Problem{problem_id}"
    order = read_schedule_txt(artifact_dir / f"{case_name}_schedule.txt")

    memory: dict[int, int] | None = None
    spill_entries: list[tuple[int, int]] = []
    errors = _validate_original_order(order, instance.nodes, instance.edges)

    if problem_id >= 2:
        memory = read_memory_txt(artifact_dir / f"{case_name}_memory.txt")
        spill_entries = read_spill_txt(artifact_dir / f"{case_name}_spill.txt")
        errors.extend(
            validate_memory(
                order,
                nodes,
                memory,
                spill_entries=spill_entries,
                num_original_nodes=len(instance.nodes),
            )
        )
        errors.extend(
            validate_spill(order, nodes, instance.edges, spill_entries, len(instance.nodes))
        )

    computed: dict[str, int] = {
        **compute_max_vstay(order, nodes),
        "spills": len(spill_entries),
        "extra": compute_extra(spill_entries, nodes) if problem_id >= 2 else 0,
        "time": compute_total_time(
            order,
            nodes,
            instance.edges,
            memory=memory,
            spill_entries=spill_entries,
            num_original_nodes=len(instance.nodes),
        ),
        "schedule_len": len(order),
    }
    return computed, errors


def _validate_original_order(order: list[int], nodes: list[Any], edges: list[Any]) -> list[str]:
    node_ids = {node.id for node in nodes}
    order_set = set(order)
    errors: list[str] = []
    missing = node_ids - order_set
    if missing:
        errors.append(f"Missing original nodes: {sorted(missing)[:10]} ({len(missing)} total)")
    original_order = [node_id for node_id in order if node_id in node_ids]
    if len(original_order) != len(set(original_order)):
        errors.append("Duplicate original nodes in schedule")

    position = {node_id: pos for pos, node_id in enumerate(order)}
    violations = 0
    for edge in edges:
        if position.get(edge.src, -1) >= position.get(edge.dst, -1):
            violations += 1
            if violations <= 5:
                errors.append(f"Dependency violation: {edge.src} must precede {edge.dst}")
    if violations > 5:
        errors.append(f"{violations - 5} more dependency violations")
    return errors


if __name__ == "__main__":
    main()
