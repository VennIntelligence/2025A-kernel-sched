"""Emit data-inventory & validation CSVs to results/paper/.

Single source of truth for the *structural* facts about the benchmark
instances (file census, node/edge counts, op/pipe/cache distributions,
integrity checks).  The 01_data_and_problem notebook only *reads* these
CSVs — it never recomputes them, so notebook output cannot drift from the
canonical numbers.

Run::

    uv run python scripts/paper/inv_inventory.py
"""

from __future__ import annotations

from pathlib import Path

from ks_core import data_utils as du

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "results" / "paper"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    instances = du.load_all_cases(RAW, "json")

    tables = {
        "inv_file_inventory.csv": du.file_inventory_table(RAW),
        "inv_case_summary.csv": du.case_summary_table(instances),
        "inv_json_csv_consistency.csv": du.compare_json_csv(RAW / "json", RAW / "csv"),
        "inv_field_completeness.csv": du.field_completeness_table(instances),
        "inv_op_distribution.csv": du.op_type_distribution(instances),
        "inv_pipe_distribution.csv": du.pipe_distribution(instances),
        "inv_cache_layer.csv": du.cache_layer_table(instances),
        "inv_edge_validation.csv": du.edge_validation_table(instances),
        "inv_buffer_consistency.csv": du.buffer_consistency_table(instances),
        "inv_dag_topology.csv": du.dag_topology_table(instances),
        "inv_integrity_summary.csv": du.integrity_summary_table(instances),
    }

    for name, df in tables.items():
        path = OUT / name
        df.to_csv(path, index=False)
        print(f"wrote {path.relative_to(ROOT)}  ({len(df)} rows)")


if __name__ == "__main__":
    main()
