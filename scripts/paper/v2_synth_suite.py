"""v2 synthetic evidence -- production solver on the internal synthetic sets.

Runs the promoted production solver (``algorithms.ours.solve``) on the three
internal synthetic benchmark sets and validates every artifact with the
canonical evaluator:

- the 36-instance generality suite (``data/processed/synthetic/suite``),
- the 8-instance CP-SAT oracle set (``data/processed/synthetic/oracle``),
- the clean/dirty reserve pair (``data/processed/synthetic``).

Unlike round9 (which compared the H=0 internal assigner and did not persist
canonical artifacts), every row here is a full portfolio run whose schedule,
memory map, and spill table pass ``ks_core.metrics.evaluate`` with zero
violations.  Existing instances are reused verbatim; nothing is regenerated.

Outputs (results/paper):
- ``v2_synth_suite.csv``   per-instance, per-solver metrics on the 36 suite
- ``v2_synth_summary.csv`` win/tie/loss and ratio summary vs each comparator
- ``v2_synth_oracle.csv``  fixed-order CP-SAT optimum on the solver's own order
- ``v2_synth_pair.csv``    clean/dirty reserve pair
"""

from __future__ import annotations

import csv
import math
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import baselines as B
import harness as H
from e14_ilp_oracle import _solve_m2_fixed

from algorithms.ours.solve import solve
from ks_core.graph import load_json
from ks_core.metrics import evaluate

SUITE_DIR = ROOT / "data" / "processed" / "synthetic" / "suite"
ORACLE_DIR = ROOT / "data" / "processed" / "synthetic" / "oracle"
PAIR_DIR = ROOT / "data" / "processed" / "synthetic"
RESULTS = ROOT / "results" / "paper"

OUT_SUITE = RESULTS / "v2_synth_suite.csv"
OUT_SUMMARY = RESULTS / "v2_synth_summary.csv"
OUT_ORACLE = RESULTS / "v2_synth_oracle.csv"
OUT_PAIR = RESULTS / "v2_synth_pair.csv"

RANDOM_K = 8
COMPARATORS = (
    "prev_portfolio",
    "cp_list",
    "cp_free_first",
    "pressure_uniform",
    "goodman_hsu",
    "random_best",
)

SUITE_FIELDS = [
    "inst_id",
    "regime",
    "target_cache",
    "n_nodes",
    "solver",
    "extra",
    "backed_volume",
    "generated_volume",
    "spill_volume",
    "spills",
    "valid",
    "violations",
    "wall_seconds",
]
SUMMARY_FIELDS = [
    "comparator",
    "regime",
    "n_instances",
    "v2_wins",
    "ties",
    "v2_losses",
    "median_v2_over_comparator_extra",
]
ORACLE_FIELDS = [
    "inst_id",
    "n_nodes",
    "bound_cache",
    "v2_extra",
    "v2_valid",
    "fixed_opt_status",
    "fixed_opt_extra",
    "fixed_opt_bound",
    "v2_over_fixed_opt",
]
PAIR_FIELDS = [
    "instance",
    "solver",
    "extra",
    "backed_volume",
    "generated_volume",
    "spills",
    "valid",
    "violations",
]


def _split_volumes(spills, inst) -> dict[str, int]:
    split = H.extra_split(spills, inst)
    backed = int(split["clean_bytes"])
    generated = int(split["dirty_bytes"]) // 2
    return {
        "extra": int(split["extra"]),
        "backed_volume": backed,
        "generated_volume": generated,
        "spill_volume": backed + generated,
        "spills": int(split["spills"]),
    }


def _run_v2(inst) -> dict[str, Any]:
    started = time.perf_counter()
    schedule = solve(inst, {})
    elapsed = time.perf_counter() - started
    result = evaluate(inst, schedule.order, schedule.memory, schedule.spill_entries)
    row = _split_volumes(schedule.spill_entries, inst)
    row.update(
        {
            "valid": result.valid,
            "violations": result.violations,
            "wall_seconds": f"{elapsed:.4g}",
            "base_order": [nid for nid in schedule.order if nid < len(inst.nodes)],
        }
    )
    return row


def _run_prev_portfolio(inst) -> dict[str, Any]:
    selected = B.select_ours_order(inst)
    result = evaluate(
        inst, selected["order_with_spills"], selected["memory"], selected["spills"]
    )
    row = _split_volumes(selected["spills"], inst)
    row.update({"valid": result.valid, "violations": result.violations, "wall_seconds": ""})
    return row


def _run_baseline(inst, order_name: str) -> dict[str, Any]:
    if order_name == "cp_list":
        order = B.cp_list(inst)
        policy, window = "far_only", 80
    elif order_name == "cp_free_first":
        order = B.cp_free_first(inst)
        policy, window = "dist_size_cost", 0
    elif order_name == "pressure_uniform":
        order = B.pressure_uniform(inst)
        policy, window = "dist_size_cost", 0
    elif order_name == "goodman_hsu":
        order = B.goodman_hsu(inst)
        policy, window = "dist_size_cost", 0
    elif order_name.startswith("random:"):
        order = H.random_topo(inst, int(order_name.split(":", 1)[1]))
        policy, window = "dist_size_cost", 0
    else:
        raise ValueError(order_name)
    order_ws, memory, spills, _meta = B.safe_assign(
        inst, order, victim_policy=policy, prefetch_window=window
    )
    result = evaluate(inst, order_ws, memory, spills)
    row = _split_volumes(spills, inst)
    row.update({"valid": result.valid, "violations": result.violations, "wall_seconds": ""})
    return row


def _median(values: list[float]) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    mid = (len(ordered) - 1) / 2
    low, high = math.floor(mid), math.ceil(mid)
    return (ordered[low] + ordered[high]) / 2


def _ratio(num: float, den: float) -> float:
    if den == 0:
        return 1.0 if num == 0 else float("inf")
    return num / den


def _read_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def run_suite() -> list[str]:
    failures: list[str] = []
    manifest = _read_manifest(SUITE_DIR / "manifest.csv")
    rows: list[dict[str, Any]] = []
    extras: dict[tuple[str, str], float] = {}

    for item in manifest:
        inst_id = item["inst_id"]
        inst = load_json(SUITE_DIR / f"{inst_id}.json", problem_id=2)
        meta = {
            "inst_id": inst_id,
            "regime": item["regime"],
            "target_cache": item["target_cache"],
            "n_nodes": len(inst.nodes),
        }

        measured: dict[str, dict[str, Any]] = {"v2": _run_v2(inst)}
        measured["v2"].pop("base_order")
        measured["prev_portfolio"] = _run_prev_portfolio(inst)
        for name in ("cp_list", "cp_free_first", "pressure_uniform", "goodman_hsu"):
            measured[name] = _run_baseline(inst, name)
        random_rows = [
            _run_baseline(inst, f"random:{seed}") for seed in range(RANDOM_K)
        ]
        measured["random_best"] = min(random_rows, key=lambda row: row["extra"])

        for solver_name, row in measured.items():
            if not row["valid"]:
                failures.append(f"{inst_id} {solver_name}: canonical validation failed")
            rows.append({**meta, "solver": solver_name, **row})
            extras[(inst_id, solver_name)] = float(row["extra"])
        print(
            f"v2-synth {inst_id}: v2={measured['v2']['extra']} "
            f"prev={measured['prev_portfolio']['extra']} "
            f"best_baseline="
            f"{min(measured[name]['extra'] for name in COMPARATORS[1:-1])}",
            flush=True,
        )

    with OUT_SUITE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUITE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    inst_regime = {item["inst_id"]: item["regime"] for item in manifest}
    summary_rows: list[dict[str, Any]] = []
    for comparator in COMPARATORS:
        for regime in ("all", "capacity_bound", "order_reachable"):
            selected = [
                inst_id
                for inst_id in inst_regime
                if regime == "all" or inst_regime[inst_id] == regime
            ]
            wins = ties = losses = 0
            ratios: list[float] = []
            for inst_id in selected:
                ours = extras[(inst_id, "v2")]
                comp = extras[(inst_id, comparator)]
                ratios.append(_ratio(ours, comp))
                if ours < comp:
                    wins += 1
                elif ours == comp:
                    ties += 1
                else:
                    losses += 1
            summary_rows.append(
                {
                    "comparator": comparator,
                    "regime": regime,
                    "n_instances": len(selected),
                    "v2_wins": wins,
                    "ties": ties,
                    "v2_losses": losses,
                    "median_v2_over_comparator_extra": f"{_median(ratios):.8g}",
                }
            )

    with OUT_SUMMARY.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(summary_rows)

    print("--- v2 synth suite summary (all) ---")
    for row in summary_rows:
        if row["regime"] == "all":
            print(
                f"{row['comparator']}: W/T/L={row['v2_wins']}/{row['ties']}/"
                f"{row['v2_losses']} median_ratio="
                f"{row['median_v2_over_comparator_extra']}"
            )
    return failures


def run_oracle() -> list[str]:
    failures: list[str] = []
    manifest = _read_manifest(ORACLE_DIR / "manifest.csv")
    rows: list[dict[str, Any]] = []
    for item in manifest:
        inst_id = item["inst_id"]
        inst = load_json(ORACLE_DIR / f"{inst_id}.json", problem_id=2)
        v2 = _run_v2(inst)
        if not v2["valid"]:
            failures.append(f"{inst_id} v2: canonical validation failed")
        fixed = _solve_m2_fixed(inst, v2["base_order"])
        if fixed["status"] not in ("OPTIMAL", "FEASIBLE"):
            failures.append(f"{inst_id}: fixed-order CP-SAT status {fixed['status']}")
        fixed_extra = fixed["objective"]
        if (
            fixed["status"] == "OPTIMAL"
            and fixed_extra is not None
            and v2["extra"] < fixed_extra
        ):
            failures.append(
                f"{inst_id}: v2 extra {v2['extra']} below fixed-order optimum {fixed_extra}"
            )
        rows.append(
            {
                "inst_id": inst_id,
                "n_nodes": len(inst.nodes),
                "bound_cache": item["bound_cache"],
                "v2_extra": v2["extra"],
                "v2_valid": v2["valid"],
                "fixed_opt_status": fixed["status"],
                "fixed_opt_extra": "" if fixed_extra is None else fixed_extra,
                "fixed_opt_bound": (
                    "" if fixed["best_bound"] is None else fixed["best_bound"]
                ),
                "v2_over_fixed_opt": (
                    ""
                    if not fixed_extra
                    else f"{v2['extra'] / fixed_extra:.8g}"
                ),
            }
        )
        print(
            f"v2-oracle {inst_id}: v2={v2['extra']} fixed_opt={fixed_extra} "
            f"({fixed['status']})",
            flush=True,
        )

    with OUT_ORACLE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ORACLE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return failures


def run_pair() -> list[str]:
    failures: list[str] = []
    rows: list[dict[str, Any]] = []
    for reserve in ("clean", "dirty"):
        path = PAIR_DIR / f"Synthetic_Case0_{reserve}.json"
        inst = load_json(path, problem_id=2)
        for solver_name in ("v2", "prev_portfolio"):
            row = _run_v2(inst) if solver_name == "v2" else _run_prev_portfolio(inst)
            row.pop("base_order", None)
            if not row["valid"]:
                failures.append(f"{reserve} {solver_name}: canonical validation failed")
            rows.append(
                {
                    "instance": reserve,
                    "solver": solver_name,
                    "extra": row["extra"],
                    "backed_volume": row["backed_volume"],
                    "generated_volume": row["generated_volume"],
                    "spills": row["spills"],
                    "valid": row["valid"],
                    "violations": row["violations"],
                }
            )
            print(f"v2-pair {reserve} {solver_name}: extra={row['extra']}", flush=True)

    with OUT_PAIR.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PAIR_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return failures


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    failures = run_suite() + run_oracle() + run_pair()
    for failure in failures:
        print(f"ASSERTION FAILED v2-synth: {failure}")
    if failures:
        raise SystemExit(1)
    print(
        "DONE v2-synth: "
        f"{OUT_SUITE.relative_to(ROOT)}, {OUT_SUMMARY.relative_to(ROOT)}, "
        f"{OUT_ORACLE.relative_to(ROOT)}, {OUT_PAIR.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
