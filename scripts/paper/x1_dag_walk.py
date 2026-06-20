"""Emit explanatory DAG + schedule-walk data for one real benchmark case.

Explanatory (notebook-only) figure **x1** — NOT a paper figure.  Provides the
node/edge tables and the per-step on-chip occupancy for Conv_Case0 under the
promoted id_raw order, so the 01_data_and_problem notebook can draw a readable
subgraph of a high-pressure window alongside the full-schedule occupancy curve.

Run::

    uv run python scripts/paper/x1_dag_walk.py
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

import networkx as nx
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "paper"))
import harness  # noqa: E402

OUT = ROOT / "results" / "paper"
CASE = "Conv_Case0"
ORDER = "id_raw"


def main() -> None:
    inst = harness.load_instance(CASE, 2)
    order = harness.build_order(inst, ORDER, case=CASE)
    nodes = {n.id: n for n in inst.nodes}

    # Topological generations give a layered x-position for a readable layout.
    g = nx.DiGraph()
    g.add_nodes_from(nodes)
    g.add_edges_from((e.src, e.dst) for e in inst.edges)
    gen_of: dict[int, int] = {}
    for gi, layer in enumerate(nx.topological_generations(g)):
        for nid in layer:
            gen_of[nid] = gi
    pos_of = {nid: i for i, nid in enumerate(order)}

    node_rows = [
        {
            "id": n.id,
            "op": n.op,
            "pipe": n.pipe or "",
            "mem_type": n.mem_type or "",
            "size": n.size,
            "buf_id": n.buf_id if n.buf_id is not None else -1,
            "gen": gen_of.get(n.id, -1),
            "sched_pos": pos_of.get(n.id, -1),
        }
        for n in inst.nodes
    ]
    pd.DataFrame(node_rows).to_csv(OUT / "x1_dag_nodes.csv", index=False)
    pd.DataFrame([{"src": e.src, "dst": e.dst} for e in inst.edges]).to_csv(
        OUT / "x1_dag_edges.csv", index=False
    )

    # Per-step on-chip occupancy (residency) along the schedule.
    cur: dict[str, int] = defaultdict(int)
    occ_rows = []
    for pos, nid in enumerate(order):
        n = nodes[nid]
        if n.mem_type is not None:
            if n.op == "ALLOC":
                cur[n.mem_type] += n.size
            elif n.op == "FREE":
                cur[n.mem_type] -= n.size
        occ_rows.append({"pos": pos, "L1": cur["L1"], "UB": cur["UB"]})
    pd.DataFrame(occ_rows).to_csv(OUT / "x1_dag_occupancy.csv", index=False)

    print(f"x1: {CASE}/{ORDER} nodes={len(node_rows)} edges={len(inst.edges)} steps={len(occ_rows)}")
    for name in ("x1_dag_nodes.csv", "x1_dag_edges.csv", "x1_dag_occupancy.csv"):
        print(f"wrote results/paper/{name}")


if __name__ == "__main__":
    main()
