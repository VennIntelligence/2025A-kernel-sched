"""Emit problem-framing & benchmark-difficulty CSVs to results/paper/.

The benchmark numbers here are derived from the SAME source as the paper's
headline comparison — ``results/paper/e1_headline.csv`` (the ``base_*``
columns) — plus the inventory's op-node counts.  This replaces the old
``ks_core.data_utils`` live-recompute path in the notebooks, so the
problem-setup tables cannot drift from the headline results table.

Depends on: ``e1_headline.csv`` (run ``e1_headline.py`` first) and
``inv_case_summary.csv`` (run ``inv_inventory.py`` first).

Run::

    uv run python scripts/paper/prob_metrics.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ks_core.constants import CACHE_CAPACITIES
from ks_core.data_utils import problem_overview_table

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "paper"
HEADLINE = OUT / "e1_headline.csv"
CASE_SUMMARY = OUT / "inv_case_summary.csv"


def main() -> None:
    head = pd.read_csv(HEADLINE)
    summary = pd.read_csv(CASE_SUMMARY)

    # Baseline metrics, taken straight from the headline 'base_*' columns so
    # there is a single canonical source for the benchmark numbers.
    base = head.rename(
        columns={
            "base_max_L1": "max_L1",
            "base_max_UB": "max_UB",
            "base_spills": "spills",
            "base_extra": "extra",
            "base_time": "time",
        }
    )[["case", "problem", "max_L1", "max_UB", "spills", "extra", "time"]]

    # Static problem overview + hardware capacities.
    problem_overview_table().to_csv(OUT / "prob_overview.csv", index=False)
    cap = pd.DataFrame([{"cache": c, "capacity": v} for c, v in CACHE_CAPACITIES.items()])

    # P1 — peak residency and capacity pressure.
    p1 = base.query("problem == 1")[["case", "max_L1", "max_UB"]].copy()
    p1["L1_ratio"] = p1["max_L1"] / CACHE_CAPACITIES["L1"]
    p1["UB_ratio"] = p1["max_UB"] / CACHE_CAPACITIES["UB"]

    # P2 — spill traffic and density (op-node count comes from the inventory).
    op_nodes = summary.set_index("case")["op_nodes"]
    p2 = base.query("problem == 2")[["case", "spills", "extra"]].copy()
    p2["op_nodes"] = p2["case"].map(op_nodes)
    p2["spill_density"] = p2["spills"] / p2["op_nodes"]

    # P3 / time comparison — pivot baseline time per problem.
    t = base.pivot(index="case", columns="problem", values="time")
    t = t.rename(columns={1: "P1_time", 2: "P2_time", 3: "P3_time"})
    t["P2_P1_ratio"] = t["P2_time"] / t["P1_time"]
    t["P3_P1_ratio"] = t["P3_time"] / t["P1_time"]
    time_table = t.reset_index()

    # Difficulty — normalised cross-case pressure indicators (column max == 1).
    p3 = base.query("problem == 3")[["case", "time"]].rename(columns={"time": "P3_time"})
    diff = (
        p1[["case", "L1_ratio", "UB_ratio"]]
        .merge(p2[["case", "spills", "extra"]], on="case")
        .merge(p3, on="case")
        .rename(
            columns={
                "L1_ratio": "L1_over_capacity",
                "UB_ratio": "UB_over_capacity",
                "spills": "P2_spills",
                "extra": "P2_extra",
            }
        )
    )
    norm = diff.set_index("case")
    difficulty = (norm / norm.max()).fillna(0.0).reset_index()

    outputs = {
        "prob_baseline_metrics.csv": base,
        "prob_capacities.csv": cap,
        "prob_p1.csv": p1,
        "prob_p2.csv": p2,
        "prob_time.csv": time_table,
        "prob_difficulty.csv": difficulty,
    }
    for name, df in outputs.items():
        path = OUT / name
        df.to_csv(path, index=False)
        print(f"wrote {path.relative_to(ROOT)}  ({len(df)} rows)")


if __name__ == "__main__":
    main()
