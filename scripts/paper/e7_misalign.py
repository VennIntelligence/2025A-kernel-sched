"""Build the E7 objective-misalignment residency table."""

from __future__ import annotations

import csv
from pathlib import Path

from harness import CAP, CASES, build_order, load_instance, overflow_integral
from ks_core.evaluator import compute_max_vstay
from ks_core.types import Node

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "paper" / "e7_misalign.csv"
COLUMNS = (
    "case",
    "order_kind",
    "max_L1",
    "max_UB",
    "max_L0A_count",
    "max_L0B_count",
    "max_L0C_count",
    "worst_over_ratio",
)
PRESSURE_CAPACITY = {
    "max_L1": CAP["L1"],
    "max_UB": CAP["UB"],
    "max_L0A_count": CAP["L0A"],
    "max_L0B_count": CAP["L0B"],
    "max_L0C_count": CAP["L0C"],
}


def main() -> None:
    rows = []
    for case in CASES:
        inst = load_instance(case, 1)
        nodes = {node.id: node for node in inst.nodes}
        candidate_orders = {
            name: build_order(inst, name, case)
            for name in ("capfit_id", "id_raw")
        }
        phi_best_name = min(
            candidate_orders,
            key=lambda name: overflow_integral(candidate_orders[name], inst),
        )

        rows.append(make_row(case, "p1", build_order(inst, "p1", case), nodes))
        rows.append(make_row(case, "phi_best", candidate_orders[phi_best_name], nodes))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    p1_rows = [row for row in rows if row["order_kind"] == "p1"]
    paired = {
        row["case"]: row
        for row in rows
        if row["order_kind"] == "phi_best"
    }
    pressure_reductions = [
        row["worst_over_ratio"] / paired[row["case"]]["worst_over_ratio"]
        for row in p1_rows
    ]
    assert max(row["max_UB"] for row in p1_rows) > 10 * CAP["UB"]
    assert max(pressure_reductions) > 1.5
    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(
        "max_p1_UB="
        f"{max(row['max_UB'] for row in p1_rows)} "
        "best_pressure_reduction_ratio="
        f"{max(pressure_reductions):.2f}"
    )


def make_row(case: str, order_kind: str, order: list[int], nodes: dict[int, Node]) -> dict:
    metrics = compute_max_vstay(order, nodes)
    return {
        "case": case,
        "order_kind": order_kind,
        **metrics,
        "worst_over_ratio": max(
            metrics[key] / capacity
            for key, capacity in PRESSURE_CAPACITY.items()
        ),
    }


if __name__ == "__main__":
    main()
