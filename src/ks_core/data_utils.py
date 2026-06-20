"""Notebook-facing data inventory and benchmark utilities."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

import networkx as nx
import pandas as pd

from ks_core.constants import CACHE_CAPACITIES
from ks_core.graph import load_csv, load_json, list_cases
from ks_core.types import Node, ProblemInstance


# Backward-compatible alias; the single source of truth lives in ks_core.constants.
CACHE_CAPACITY = CACHE_CAPACITIES
CACHE_OPS = {"ALLOC", "FREE"}


def load_all_cases(data_dir: Path, fmt: str = "json") -> dict[str, ProblemInstance]:
    """Load all cases from a raw data directory."""
    base_dir = _format_dir(Path(data_dir), fmt)
    cases = list_cases(base_dir, fmt)
    if fmt == "json":
        return {case: load_json(base_dir / f"{case}.json", case) for case in cases}
    return {
        case: load_csv(base_dir / f"{case}_Nodes.csv", base_dir / f"{case}_Edges.csv", case)
        for case in cases
    }


def case_summary_table(instances: dict[str, ProblemInstance]) -> pd.DataFrame:
    """Build the six-case scale overview table."""
    rows = []
    for case, instance in sorted(instances.items()):
        alloc_nodes = [n for n in instance.nodes if n.op == "ALLOC"]
        op_nodes = _op_nodes(instance)
        rows.append(
            {
                "case": case,
                "kernel": case.split("_Case")[0],
                "scale": "small" if case.endswith("Case0") else "large",
                "total_nodes": len(instance.nodes),
                "total_edges": len(instance.edges),
                "op_nodes": len(op_nodes),
                "alloc_nodes": len(alloc_nodes),
                "unique_buffers": len({n.buf_id for n in alloc_nodes}),
                "total_buf_size": sum(n.size for n in alloc_nodes),
                "num_pipes_used": len({n.pipe for n in op_nodes if n.pipe}),
                "num_mem_types": len({n.mem_type for n in alloc_nodes if n.mem_type}),
            }
        )
    return pd.DataFrame(rows)


def validate_data_integrity(instance: ProblemInstance) -> list[str]:
    """Validate one raw case and return human-readable issue messages."""
    issues: list[str] = []
    node_ids = [n.id for n in instance.nodes]
    node_id_set = set(node_ids)
    expected = set(range(len(instance.nodes)))
    if node_id_set != expected or len(node_ids) != len(node_id_set):
        issues.append("Node IDs are not contiguous unique values 0..N-1")

    alloc_by_buf = Counter(n.buf_id for n in instance.nodes if n.op == "ALLOC")
    free_by_buf = Counter(n.buf_id for n in instance.nodes if n.op == "FREE")
    for buf_id in sorted(set(alloc_by_buf) | set(free_by_buf)):
        if alloc_by_buf[buf_id] != 1 or free_by_buf[buf_id] != 1:
            issues.append(f"BufId {buf_id} has {alloc_by_buf[buf_id]} ALLOC and {free_by_buf[buf_id]} FREE")

    bad_edges = [(e.src, e.dst) for e in instance.edges if e.src not in node_id_set or e.dst not in node_id_set]
    if bad_edges:
        issues.append(f"{len(bad_edges)} edges reference missing node IDs")
    if any(e.src == e.dst for e in instance.edges):
        issues.append("Self-loop edges exist")

    graph = _graph(instance)
    if not nx.is_directed_acyclic_graph(graph):
        issues.append("Graph is not a DAG")

    nodes_by_id = {n.id: n for n in instance.nodes}
    bad_roots = [n for n in graph.nodes if graph.in_degree(n) == 0 and nodes_by_id[n].op != "ALLOC"]
    bad_leaves = [n for n in graph.nodes if graph.out_degree(n) == 0 and nodes_by_id[n].op != "FREE"]
    if bad_roots:
        issues.append(f"{len(bad_roots)} roots are not ALLOC nodes")
    if bad_leaves:
        issues.append(f"{len(bad_leaves)} leaves are not FREE nodes")

    missing_op = [n.id for n in _op_nodes(instance) if not n.pipe or n.cycles <= 0 or not n.bufs]
    missing_cache = [
        n.id for n in instance.nodes if n.op in CACHE_OPS and (n.buf_id is None or n.size <= 0 or not n.mem_type)
    ]
    if missing_op:
        issues.append(f"{len(missing_op)} op nodes miss Pipe/Cycles/Bufs")
    if missing_cache:
        issues.append(f"{len(missing_cache)} cache nodes miss BufId/Size/Type")
    return issues


def compare_json_csv(json_dir: Path, csv_dir: Path) -> pd.DataFrame:
    """Compare per-case JSON and CSV parsing results."""
    json_cases = load_all_cases(json_dir, "json")
    csv_cases = load_all_cases(csv_dir, "csv")
    rows = []
    for case in sorted(set(json_cases) | set(csv_cases)):
        json_instance = json_cases.get(case)
        csv_instance = csv_cases.get(case)
        rows.append(
            {
                "case": case,
                "nodes_match": bool(json_instance and csv_instance and _node_records(json_instance) == _node_records(csv_instance)),
                "edges_match": bool(json_instance and csv_instance and _edge_records(json_instance) == _edge_records(csv_instance)),
            }
        )
    return pd.DataFrame(rows)


def file_inventory_table(raw_dir: Path) -> pd.DataFrame:
    """List raw JSON and CSV files with sizes."""
    rows = []
    for fmt in ("json", "csv"):
        for path in sorted((Path(raw_dir) / fmt).glob("*")):
            rows.append({"format": fmt.upper(), "file": path.name, "size_bytes": path.stat().st_size})
    return pd.DataFrame(rows)


def file_inventory_counts(raw_dir: Path) -> dict[str, int]:
    """Count raw files by format."""
    raw_dir = Path(raw_dir)
    return {"json": len(list((raw_dir / "json").glob("*.json"))), "csv": len(list((raw_dir / "csv").glob("*.csv")))}


def markdown_table(df: pd.DataFrame) -> str:
    """Render a small DataFrame as a GitHub-style markdown table."""
    columns = [str(column) for column in df.columns]
    rows = [["" if pd.isna(value) else str(value) for value in row] for row in df.to_numpy()]
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def field_completeness_table(instances: dict[str, ProblemInstance]) -> pd.DataFrame:
    """Summarize required node-field completeness by case."""
    rows = []
    for case, instance in sorted(instances.items()):
        ops = _op_nodes(instance)
        caches = [n for n in instance.nodes if n.op in CACHE_OPS]
        rows.append(
            {
                "case": case,
                "op_nodes": len(ops),
                "op_nodes_with_pipe": sum(bool(n.pipe) for n in ops),
                "op_nodes_with_cycles": sum(n.cycles > 0 for n in ops),
                "op_nodes_with_bufs": sum(bool(n.bufs) for n in ops),
                "cache_nodes": len(caches),
                "cache_nodes_with_bufid": sum(n.buf_id is not None for n in caches),
                "cache_nodes_with_size": sum(n.size > 0 for n in caches),
                "cache_nodes_with_type": sum(bool(n.mem_type) for n in caches),
            }
        )
    return pd.DataFrame(rows)


def op_type_distribution(instances: dict[str, ProblemInstance]) -> pd.DataFrame:
    """Count operation types by case, excluding ALLOC/FREE."""
    return _count_table(instances, lambda n: n.op if n.op not in CACHE_OPS else None)


def pipe_distribution(instances: dict[str, ProblemInstance]) -> pd.DataFrame:
    """Count pipeline usage by case."""
    return _count_table(instances, lambda n: n.pipe if n.op not in CACHE_OPS else None)


def cache_layer_table(instances: dict[str, ProblemInstance]) -> pd.DataFrame:
    """Summarize allocated buffers by memory type."""
    rows = []
    for case, instance in sorted(instances.items()):
        for mem_type, nodes in _group_allocs(instance).items():
            sizes = [n.size for n in nodes]
            rows.append(
                {
                    "case": case,
                    "mem_type": mem_type,
                    "buffer_count": len(nodes),
                    "total_size": sum(sizes),
                    "max_buffer_size": max(sizes),
                }
            )
    return pd.DataFrame(rows).sort_values(["case", "mem_type"]).reset_index(drop=True)


def edge_validation_table(instances: dict[str, ProblemInstance]) -> pd.DataFrame:
    """Validate edge references, self-loops, and isolated nodes."""
    rows = []
    for case, instance in sorted(instances.items()):
        node_ids = {n.id for n in instance.nodes}
        referenced = {v for e in instance.edges for v in (e.src, e.dst)}
        rows.append(
            {
                "case": case,
                "self_loops": sum(e.src == e.dst for e in instance.edges),
                "missing_node_refs": sum(e.src not in node_ids or e.dst not in node_ids for e in instance.edges),
                "isolated_nodes": len(node_ids - referenced),
            }
        )
    return pd.DataFrame(rows)


def buffer_consistency_table(instances: dict[str, ProblemInstance]) -> pd.DataFrame:
    """Validate buffer allocation/free and operation references."""
    rows = []
    for case, instance in sorted(instances.items()):
        alloc = Counter(n.buf_id for n in instance.nodes if n.op == "ALLOC")
        free = Counter(n.buf_id for n in instance.nodes if n.op == "FREE")
        allocated = set(alloc)
        referenced = {buf_id for n in _op_nodes(instance) for buf_id in n.bufs}
        rows.append(
            {
                "case": case,
                "buffers": len(allocated),
                "bad_alloc_counts": sum(count != 1 for count in alloc.values()),
                "bad_free_counts": sum(free[buf_id] != 1 for buf_id in allocated),
                "op_refs_without_alloc": len(referenced - allocated),
                "passed": all(count == 1 for count in alloc.values())
                and all(free[buf_id] == 1 for buf_id in allocated)
                and not (referenced - allocated),
            }
        )
    return pd.DataFrame(rows)


def dag_topology_table(instances: dict[str, ProblemInstance]) -> pd.DataFrame:
    """Summarize DAG-level topology validity."""
    rows = []
    for case, instance in sorted(instances.items()):
        graph = _graph(instance)
        nodes_by_id = {n.id: n for n in instance.nodes}
        is_dag = nx.is_directed_acyclic_graph(graph)
        generations = sum(1 for _ in nx.topological_generations(graph)) if is_dag else None
        rows.append(
            {
                "case": case,
                "is_dag": is_dag,
                "weak_components": nx.number_weakly_connected_components(graph),
                "root_nodes": sum(graph.in_degree(n) == 0 for n in graph.nodes),
                "roots_all_alloc": all(nodes_by_id[n].op == "ALLOC" for n in graph.nodes if graph.in_degree(n) == 0),
                "leaf_nodes": sum(graph.out_degree(n) == 0 for n in graph.nodes),
                "leaves_all_free": all(nodes_by_id[n].op == "FREE" for n in graph.nodes if graph.out_degree(n) == 0),
                "topological_generations": generations,
            }
        )
    return pd.DataFrame(rows)


def integrity_summary_table(instances: dict[str, ProblemInstance]) -> pd.DataFrame:
    """Run full integrity validation across all cases."""
    rows = []
    for case, instance in sorted(instances.items()):
        issues = validate_data_integrity(instance)
        rows.append({"case": case, "passed": not issues, "issues": "; ".join(issues) if issues else "None"})
    return pd.DataFrame(rows)


def problem_overview_table() -> pd.DataFrame:
    """Build the structured P1/P2/P3 comparison table."""
    return pd.DataFrame(
        [
            {
                "problem": "Problem 1",
                "optimization_target": "Minimize peak resident cache demand for a valid topological schedule",
                "output_files": "<task>_schedule.txt",
                "metric_formula": "max prefix V_stay over ALLOC/FREE size deltas",
                "direction": "minimize maxV_stay",
            },
            {
                "problem": "Problem 2",
                "optimization_target": "Assign cache offsets and spills under capacity constraints",
                "output_files": "<task>_schedule.txt, <task>_memory.txt, <task>_spill.txt",
                "metric_formula": "sum spill cost: Size or 2*Size depending on COPY_IN usage",
                "direction": "minimize extra DDR traffic",
            },
            {
                "problem": "Problem 3",
                "optimization_target": "Reduce pipelined execution time with spill and reuse dependencies",
                "output_files": "<task>_schedule.txt, <task>_memory.txt, <task>_spill.txt",
                "metric_formula": "T = max E(v) under DAG, same-pipe, spill, and reuse constraints",
                "direction": "minimize total time",
            },
        ]
    )


def hardware_capacity_table() -> pd.DataFrame:
    """Return hardware cache capacities."""
    return pd.DataFrame([{"cache": cache, "capacity": capacity} for cache, capacity in CACHE_CAPACITY.items()])


def load_baseline_metrics(project_root: Path) -> pd.DataFrame:
    """Load baseline metrics from the legacy or current repository location."""
    paths = [
        Path(project_root) / "algorithms" / "baseline_gpt" / "metrics.json",
        Path(project_root) / "algorithms" / "baseline" / "metrics.json",
        Path(project_root) / "results" / "exp001_baseline01" / "metrics.json",
    ]
    metrics_path = next((path for path in paths if path.exists()), None)
    if metrics_path is None:
        raise FileNotFoundError("No baseline metrics.json found")
    with open(metrics_path) as f:
        rows = json.load(f)
    df = pd.DataFrame(rows).sort_values(["case", "problem"]).reset_index(drop=True)
    df.attrs["source_path"] = str(metrics_path)
    return df


def p1_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    """Return Problem 1 metrics with capacity ratios."""
    df = metrics.query("problem == 1").copy()
    df["L1_ratio"] = df["max_L1"] / CACHE_CAPACITY["L1"]
    df["UB_ratio"] = df["max_UB"] / CACHE_CAPACITY["UB"]
    return df


def p2_metrics(metrics: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    """Return Problem 2 metrics with spill density."""
    op_nodes = summary.set_index("case")["op_nodes"]
    df = metrics.query("problem == 2").copy()
    df["op_nodes"] = df["case"].map(op_nodes)
    df["spill_density"] = df["spills"] / df["op_nodes"]
    return df


def time_comparison_table(metrics: pd.DataFrame) -> pd.DataFrame:
    """Pivot execution time by problem and compute ratios."""
    pivot = metrics.pivot(index="case", columns="problem", values="time").rename(columns={1: "P1_time", 2: "P2_time", 3: "P3_time"})
    pivot["P2_P1_ratio"] = pivot["P2_time"] / pivot["P1_time"]
    pivot["P3_P1_ratio"] = pivot["P3_time"] / pivot["P1_time"]
    return pivot.reset_index()


def difficulty_table(metrics: pd.DataFrame) -> pd.DataFrame:
    """Build normalized cross-case difficulty indicators."""
    p1 = p1_metrics(metrics).set_index("case")
    p2 = metrics.query("problem == 2").set_index("case")
    p3 = metrics.query("problem == 3").set_index("case")
    df = pd.DataFrame(
        {
            "L1_over_capacity": p1["L1_ratio"],
            "UB_over_capacity": p1["UB_ratio"],
            "P2_spills": p2["spills"],
            "P2_extra": p2["extra"],
            "P3_time": p3["time"],
        }
    )
    return (df / df.max()).fillna(0).reset_index()


def _format_dir(data_dir: Path, fmt: str) -> Path:
    if fmt not in {"json", "csv"}:
        raise ValueError(f"Unsupported format: {fmt}")
    return data_dir / fmt if (data_dir / fmt).is_dir() else data_dir


def _op_nodes(instance: ProblemInstance) -> list[Node]:
    return [n for n in instance.nodes if n.op not in CACHE_OPS]


def _group_allocs(instance: ProblemInstance) -> dict[str, list[Node]]:
    groups: dict[str, list[Node]] = {}
    for node in instance.nodes:
        if node.op == "ALLOC" and node.mem_type:
            groups.setdefault(node.mem_type, []).append(node)
    return groups


def _count_table(instances: dict[str, ProblemInstance], key_fn) -> pd.DataFrame:
    rows = []
    for case, instance in sorted(instances.items()):
        counts = Counter(filter(None, (key_fn(node) for node in instance.nodes)))
        rows.extend({"case": case, "category": key, "count": value} for key, value in sorted(counts.items()))
    return pd.DataFrame(rows)


def _graph(instance: ProblemInstance) -> nx.DiGraph:
    graph = nx.DiGraph()
    graph.add_nodes_from(n.id for n in instance.nodes)
    graph.add_edges_from((e.src, e.dst) for e in instance.edges)
    return graph


def _node_records(instance: ProblemInstance) -> list[dict]:
    return [asdict(node) for node in sorted(instance.nodes, key=lambda n: n.id)]


def _edge_records(instance: ProblemInstance) -> list[tuple[int, int]]:
    return sorted((edge.src, edge.dst) for edge in instance.edges)
