"""DAG parsing utilities — load problem instances from JSON/CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from ks_core.types import Edge, Node, ProblemInstance


def load_json(path: Path, case_name: str | None = None, problem_id: int = 1) -> ProblemInstance:
    """Load a problem instance from the original JSON format.

    Args:
        path: Path to a JSON file (e.g. data/raw/json/Conv_Case0.json).
        case_name: Override case name. Defaults to filename stem.
        problem_id: Problem variant (1, 2, or 3).
    """
    if case_name is None:
        case_name = path.stem

    with open(path) as f:
        data = json.load(f)

    nodes: list[Node] = []
    for n in data.get("Nodes", []):
        nodes.append(
            Node(
                id=n["Id"],
                op=n.get("Op", ""),
                pipe=n.get("Pipe"),
                cycles=n.get("Cycles", 0),
                bufs=n.get("Bufs", []),
                buf_id=n.get("BufId"),
                size=n.get("Size", 0),
                mem_type=n.get("Type"),
            )
        )

    edges: list[Edge] = []
    for e in data.get("Edges", []):
        if isinstance(e, dict):
            edges.append(Edge(src=e["Src"], dst=e["Dst"], edge_type=e.get("Type", "data")))
        else:
            # Edge stored as [src, dst] list
            edges.append(Edge(src=e[0], dst=e[1], edge_type="data"))

    return ProblemInstance(
        case_name=case_name,
        problem_id=problem_id,
        nodes=nodes,
        edges=edges,
    )


def load_csv(
    nodes_path: Path,
    edges_path: Path,
    case_name: str | None = None,
    problem_id: int = 1,
) -> ProblemInstance:
    """Load a problem instance from CSV node/edge files.

    Args:
        nodes_path: Path to *_Nodes.csv
        edges_path: Path to *_Edges.csv
        case_name: Override case name.
        problem_id: Problem variant.
    """
    if case_name is None:
        # Extract from filename: Conv_Case0_Nodes.csv → Conv_Case0
        case_name = nodes_path.stem.replace("_Nodes", "")

    nodes: list[Node] = []
    with open(nodes_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            bufs_raw = row.get("Bufs", "")
            bufs = [int(b) for b in bufs_raw.split(";") if b.strip()] if bufs_raw else []
            nodes.append(
                Node(
                    id=int(row["Id"]),
                    op=row.get("Op", ""),
                    pipe=row.get("Pipe") or None,
                    cycles=int(row.get("Cycles", 0)),
                    bufs=bufs,
                    buf_id=int(row["BufId"]) if row.get("BufId") else None,
                    size=int(row.get("Size", 0)),
                    mem_type=row.get("Type") or None,
                )
            )

    edges: list[Edge] = []
    with open(edges_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            edges.append(
                Edge(
                    src=int(row["Src"]),
                    dst=int(row["Dst"]),
                    edge_type=row.get("Type", "data"),
                )
            )

    return ProblemInstance(
        case_name=case_name,
        problem_id=problem_id,
        nodes=nodes,
        edges=edges,
    )


def list_cases(data_dir: Path, fmt: str = "json") -> list[str]:
    """List available case names from a data directory.

    Args:
        data_dir: Path to data/raw/json or data/raw/csv.
        fmt: "json" or "csv".
    """
    if fmt == "json":
        return sorted(p.stem for p in data_dir.glob("*.json"))
    else:
        return sorted(
            p.stem.replace("_Nodes", "")
            for p in data_dir.glob("*_Nodes.csv")
        )
