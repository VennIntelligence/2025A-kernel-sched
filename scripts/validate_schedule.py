"""Validate schedule files — check constraint satisfaction."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ks_core.graph import load_json
from ks_core.io import get_project_root, read_schedule_txt


def validate_schedule(
    case_name: str, problem_id: int, schedule_path: Path
) -> list[str]:
    """Validate a schedule against the problem constraints.

    Returns a list of error messages (empty = valid).
    """
    errors: list[str] = []

    # Load instance
    root = get_project_root()
    json_path = root / "data" / "raw" / "json" / f"{case_name}.json"
    if not json_path.exists():
        return [f"Data file not found: {json_path}"]

    instance = load_json(json_path, problem_id=problem_id)
    order = read_schedule_txt(schedule_path)

    # 1. All nodes must appear exactly once
    node_ids = {n.id for n in instance.nodes}
    order_set = set(order)
    missing = node_ids - order_set
    extra = order_set - node_ids
    if missing:
        errors.append(f"Missing nodes: {sorted(missing)[:10]}... ({len(missing)} total)")
    if extra:
        errors.append(f"Unknown nodes: {sorted(extra)[:10]}... ({len(extra)} total)")
    if len(order) != len(order_set):
        errors.append(f"Duplicate nodes: {len(order)} entries but {len(order_set)} unique")

    # 2. Dependency order: src must come before dst
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


def main():
    parser = argparse.ArgumentParser(description="Validate schedule files")
    parser.add_argument(
        "--dir",
        type=Path,
        default=None,
        help="Directory containing schedule files to validate",
    )
    parser.add_argument("--case", help="Case name (e.g. Conv_Case0)")
    parser.add_argument("--problem", type=int, default=1, help="Problem ID")
    parser.add_argument("--file", type=Path, help="Single schedule file to validate")
    args = parser.parse_args()

    if args.file and args.case:
        errors = validate_schedule(args.case, args.problem, args.file)
        if errors:
            print(f"❌ {args.file}:")
            for e in errors:
                print(f"   {e}")
            sys.exit(1)
        else:
            print(f"✅ {args.file}: valid")
    elif args.dir:
        any_error = False
        for f in sorted(args.dir.rglob("*_schedule.txt")):
            # Try to extract case name from filename: P1_Conv_Case0_schedule.txt
            parts = f.stem.replace("_schedule", "").split("_", 1)
            if len(parts) >= 2 and parts[0].startswith("P"):
                pid = int(parts[0][1:])
                case = parts[1]
            else:
                print(f"⚠️  Skipping {f}: cannot parse case name")
                continue
            errors = validate_schedule(case, pid, f)
            if errors:
                any_error = True
                print(f"❌ {f.name}:")
                for e in errors:
                    print(f"   {e}")
            else:
                print(f"✅ {f.name}")
        if any_error:
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
