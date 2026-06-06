"""Validate schedule files — check constraint satisfaction and compute metrics."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ks_core.evaluator import (
    compute_extra,
    compute_max_vstay,
    compute_total_time,
    validate_memory,
    validate_spill,
)
from ks_core.graph import load_json
from ks_core.io import get_project_root, read_memory_txt, read_schedule_txt, read_spill_txt


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
    errors: list[str] = []

    root = get_project_root()
    json_path = root / "data" / "raw" / "json" / f"{case_name}.json"
    if not json_path.exists():
        return [f"Data file not found: {json_path}"], {}

    instance = load_json(json_path, problem_id=problem_id)
    order = read_schedule_txt(schedule_path)
    nodes = {node.id: node for node in instance.nodes}
    spills = read_spill_txt(spill_path) if spill_path else []

    errors.extend(_validate_original_schedule(order, instance, allow_extra=problem_id >= 2))

    if problem_id >= 2 and spill_path:
        errors.extend(
            validate_spill(order, nodes, instance.edges, spills, len(instance.nodes))
        )

    memory = None
    if memory_path:
        memory = read_memory_txt(memory_path)
        errors.extend(
            validate_memory(
                order, nodes, memory,
                spill_entries=spills, num_original_nodes=len(instance.nodes),
            )
        )

    # Metrics — always compute vstay and time
    metrics = compute_max_vstay(order, nodes)
    metrics["total_time"] = compute_total_time(order, nodes, instance.edges)

    if memory_path and spill_path:
        metrics["extra"] = compute_extra(spills, nodes)
        metrics["total_time_p2"] = compute_total_time(
            order, nodes, instance.edges,
            memory=memory, spill_entries=spills, num_original_nodes=len(instance.nodes),
        )

    return errors, metrics


def _validate_original_schedule(order: list[int], instance, allow_extra: bool) -> list[str]:
    errors: list[str] = []
    node_ids = {n.id for n in instance.nodes}
    order_set = set(order)
    missing = node_ids - order_set
    extra = order_set - node_ids
    if missing:
        errors.append(f"Missing nodes: {sorted(missing)[:10]}... ({len(missing)} total)")
    if extra and not allow_extra:
        errors.append(f"Unknown nodes: {sorted(extra)[:10]}... ({len(extra)} total)")
    if len(order) != len(order_set):
        errors.append(f"Duplicate nodes: {len(order)} entries but {len(order_set)} unique")

    position = {nid: i for i, nid in enumerate(order)}
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
        errors.append(f"... and {dep_violations - 5} more dependency violations")

    return errors


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
    candidate = schedule_path.with_name(
        schedule_path.name.replace("_schedule.txt", f"_{suffix}.txt")
    )
    return candidate if candidate.exists() else None


def _print_summary(rows: list[tuple[str, int, bool, dict[str, int]]]) -> None:
    if not rows:
        return
    # Collect all metric keys in stable order
    all_keys: list[str] = []
    for *_, m in rows:
        for k in m:
            if k not in all_keys:
                all_keys.append(k)

    headers = ["case", "P", "status"] + all_keys
    table: list[list[str]] = []
    for case, pid, ok, m in rows:
        table.append([case, str(pid), "OK" if ok else "FAIL"] + [str(m.get(k, "")) for k in all_keys])

    widths = [max(len(h), *(len(r[i]) for r in table)) for i, h in enumerate(headers)]
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
        for f in sorted(args.dir.rglob("*_schedule.txt")):
            case, pid = _parse_schedule_path(f, args.problem)
            mem = _sibling_artifact(f, "memory") if pid >= 2 else None
            spl = _sibling_artifact(f, "spill") if pid >= 2 else None
            errors, metrics = validate_schedule(case, pid, f, mem, spl)
            ok = _print_result(str(f), errors, metrics)
            summary.append((case, pid, ok, metrics))
    else:
        parser.print_help()
        return

    _print_summary(summary)
    if any(not ok for _, _, ok, _ in summary):
        sys.exit(1)


if __name__ == "__main__":
    main()
