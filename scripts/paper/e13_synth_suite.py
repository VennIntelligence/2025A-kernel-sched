"""E13 -- synthetic DAG suite for scheduler generality."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

import baselines as B
import harness as H

from ks_core.evaluator import validate_memory, validate_spill
from ks_core.graph import load_json

ROOT = Path(__file__).resolve().parents[2]
SUITE_DIR = ROOT / "data" / "processed" / "synthetic" / "suite"
RESULTS = ROOT / "results" / "paper"
OUT_SUITE = RESULTS / "e13_suite.csv"
OUT_SUMMARY = RESULTS / "e13_summary.csv"
MANIFEST = SUITE_DIR / "manifest.csv"

TARGET_SUITE_SIZE = 36
RANDOM_K = 8
ORDER_NAMES = ("cp_list", "cp_free_first", "pressure_uniform", "goodman_hsu", "ours")
METRIC_FIELDS = [
    "inst_id",
    "regime",
    "order",
    "extra",
    "clean_bytes",
    "dirty_bytes",
    "spills",
    "time",
    "victim_policy",
    "prefetch_window",
    "assign_fallback",
    "time_source",
    "peak_L1",
    "peak_UB",
    "peak_L0A",
    "peak_L0B",
    "peak_L0C",
    "phi",
]
MANIFEST_FIELDS = [
    "inst_id",
    "seed",
    "target_cache",
    "n_nodes",
    "n_edges",
    "dirty_reserve",
    "min_peak_target_over_cap",
    "regime",
]
SUMMARY_FIELDS = [
    "comparator",
    "regime",
    "n_instances",
    "median_ours_over_comparator_extra",
    "q25_ours_over_comparator_extra",
    "q75_ours_over_comparator_extra",
    "ours_win_rate",
]


def _validate_instance(inst) -> list[str]:
    order = H.build_order(inst, "capfit_id")
    order_ws, memory, spills = H.assign(
        inst,
        order,
        victim_policy="dist_size_cost",
        prefetch_window=0,
    )
    nodes = {node.id: node for node in inst.nodes}
    errors = validate_memory(
        order_ws,
        nodes,
        memory,
        spill_entries=spills,
        num_original_nodes=len(inst.nodes),
    )
    errors += validate_spill(order_ws, nodes, inst.edges, spills, len(inst.nodes))
    return errors


def _scan_regime(inst, target_cache: str, seed: int) -> tuple[float, str]:
    candidates: list[list[int]] = [
        B.cp_list(inst),
        B.cp_free_first(inst),
        B.pressure_uniform(inst),
        B.goodman_hsu(inst),
    ]
    for name in B.BASE_CANDIDATES:
        candidates.append(H.build_order(inst, name))
    for offset in range(24):
        candidates.append(H.random_topo(inst, seed * 1000 + offset))

    min_peak = min(H.peak_working_set(order, inst).get(target_cache, 0) for order in candidates)
    ratio = min_peak / H.CAP[target_cache]
    regime = "capacity_bound" if ratio > 1.0 else "order_reachable"
    return ratio, regime


def _knobs(index: int, desired_regime: str) -> dict[str, Any]:
    target_cache = ("UB", "L0C", "L1")[index % 3]
    if desired_regime == "capacity_bound":
        n_reserve = 5 + (index % 3)
        n_acc = 3 + (index % 5)
    else:
        n_reserve = 4 + (index % 4)
        n_acc = 3 + (index % 6)
    return {
        "target_cache": target_cache,
        "regime": desired_regime,
        "n_reserve": n_reserve,
        "n_acc": n_acc,
        "dirty_reserve": bool((index // 2) % 2),
    }


def _generate_suite() -> list[dict[str, Any]]:
    SUITE_DIR.mkdir(parents=True, exist_ok=True)
    manifest_rows: list[dict[str, Any]] = []
    invalid = 0
    attempts = 0
    index = 0

    while len(manifest_rows) < TARGET_SUITE_SIZE and attempts < TARGET_SUITE_SIZE * 12:
        attempts += 1
        desired = "capacity_bound" if attempts % 2 else "order_reachable"
        seed = 7100 + attempts
        knobs = _knobs(attempts, desired)
        data = B.gen_instance(seed, knobs)
        tmp_path = SUITE_DIR / "_candidate.json"
        tmp_path.write_text(json.dumps(data), encoding="utf-8")
        inst = load_json(tmp_path, problem_id=2)
        errors = _validate_instance(inst)
        if errors:
            invalid += 1
            continue
        ratio, regime = _scan_regime(inst, knobs["target_cache"], seed)
        inst_id = f"synth_{index:03d}"
        out_path = SUITE_DIR / f"{inst_id}.json"
        out_path.write_text(json.dumps(data), encoding="utf-8")
        manifest_rows.append(
            {
                "inst_id": inst_id,
                "seed": seed,
                "target_cache": knobs["target_cache"],
                "n_nodes": len(data["Nodes"]),
                "n_edges": len(data["Edges"]),
                "dirty_reserve": knobs["dirty_reserve"],
                "min_peak_target_over_cap": f"{ratio:.8g}",
                "regime": regime,
            }
        )
        index += 1

    candidate = SUITE_DIR / "_candidate.json"
    if candidate.exists():
        candidate.unlink()

    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_FIELDS)
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(
        f"generated suite: valid={len(manifest_rows)} invalid_skipped={invalid} "
        f"attempts={attempts}"
    )
    return manifest_rows


def _order_for(inst, order_name: str) -> tuple[list[int], dict[str, Any] | None]:
    if order_name == "cp_list":
        return B.cp_list(inst), None
    if order_name == "cp_free_first":
        return B.cp_free_first(inst), None
    if order_name == "pressure_uniform":
        return B.pressure_uniform(inst), None
    if order_name == "goodman_hsu":
        return B.goodman_hsu(inst), None
    if order_name == "ours":
        selected = B.select_ours_order(inst)
        return selected["base_order"], selected
    if order_name.startswith("random:"):
        return H.random_topo(inst, int(order_name.split(":", 1)[1])), None
    raise ValueError(order_name)


def _measure(inst, inst_id: str, regime: str, order_name: str) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    order, selected = _order_for(inst, order_name)
    ok, reason = B.validate_topological_order(inst, order)
    if not ok:
        failures.append(f"{inst_id} {order_name}: invalid topo order: {reason}")

    if selected is None:
        initial_policy = "far_only" if order_name == "cp_list" else "dist_size_cost"
        initial_window = 80 if order_name == "cp_list" else 0
        order_ws, memory, spills, assign_meta = B.safe_assign(
            inst,
            order,
            victim_policy=initial_policy,
            prefetch_window=initial_window,
        )
        if order_name == "cp_list":
            failures.append(
                f"{inst_id} cp_list: assign_policy="
                f"{assign_meta['victim_policy']}/{assign_meta['prefetch_window']} "
                "for latency-only stress baseline"
            )
        elif order_name == "cp_free_first":
            failures.append(
                f"{inst_id} cp_free_first: assign_policy="
                f"{assign_meta['victim_policy']}/{assign_meta['prefetch_window']} "
                "allocator-friendly latency companion for cp_list"
            )
        if assign_meta["fallback"]:
            failures.append(
                f"{inst_id} {order_name}: initial assign failed; used "
                f"{assign_meta['victim_policy']}/{assign_meta['prefetch_window']} "
                f"after {assign_meta['errors']}"
            )
        split = H.extra_split(spills, inst)
        time, time_source = B.controlled_total_time(inst, order_ws, memory, spills)
        if time_source != "address":
            failures.append(
                f"{inst_id} {order_name}: time_source={time_source} "
                f"for {split['spills']} spills"
            )
    else:
        assign_meta = selected.get("assign_meta", {})
        if assign_meta.get("fallback"):
            failures.append(
                f"{inst_id} ours: initial assign failed; used "
                f"{assign_meta['victim_policy']}/{assign_meta['prefetch_window']} "
                f"after {assign_meta['errors']}"
            )
        split = selected["split"]
        time = selected["time"]
        time_source = selected.get("time_source", "address")
        if selected.get("time_source") != "address":
            failures.append(
                f"{inst_id} ours: time_source={selected.get('time_source')} "
                f"for {split['spills']} spills"
            )

    peak = H.peak_working_set(order, inst)
    return (
        {
            "inst_id": inst_id,
            "regime": regime,
            "order": order_name,
            "extra": split["extra"],
            "clean_bytes": split["clean_bytes"],
            "dirty_bytes": split["dirty_bytes"],
            "spills": split["spills"],
            "time": time,
            "victim_policy": assign_meta.get("victim_policy", ""),
            "prefetch_window": assign_meta.get("prefetch_window", ""),
            "assign_fallback": assign_meta.get("fallback", ""),
            "time_source": time_source,
            "peak_L1": peak.get("L1", 0),
            "peak_UB": peak.get("UB", 0),
            "peak_L0A": peak.get("L0A", 0),
            "peak_L0B": peak.get("L0B", 0),
            "peak_L0C": peak.get("L0C", 0),
            "phi": H.overflow_integral(order, inst),
        },
        failures,
    )


def _ratio(num: float, den: float) -> float:
    if den == 0:
        return 1.0 if num == 0 else float("inf")
    return num / den


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    sorted_values = sorted(values)
    pos = (len(sorted_values) - 1) * q
    low = math.floor(pos)
    high = math.ceil(pos)
    if low == high:
        return sorted_values[low]
    frac = pos - low
    return sorted_values[low] * (1.0 - frac) + sorted_values[high] * frac


def _summarize(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_inst_order = {(row["inst_id"], row["order"]): row for row in rows}
    inst_regime = {row["inst_id"]: row["regime"] for row in rows if row["order"] == "ours"}
    inst_ids = sorted(inst_regime)
    summary_rows: list[dict[str, Any]] = []
    for comparator in (
        "cp_list",
        "cp_free_first",
        "pressure_uniform",
        "goodman_hsu",
        "random_best",
    ):
        for regime in ("all", "capacity_bound", "order_reachable"):
            selected = [
                inst_id
                for inst_id in inst_ids
                if regime == "all" or inst_regime[inst_id] == regime
            ]
            ratios = []
            wins = 0
            for inst_id in selected:
                ours_extra = float(by_inst_order[(inst_id, "ours")]["extra"])
                if comparator == "random_best":
                    comp_extra = min(
                        float(by_inst_order[(inst_id, f"random:{seed}")]["extra"])
                        for seed in range(RANDOM_K)
                    )
                else:
                    comp_extra = float(by_inst_order[(inst_id, comparator)]["extra"])
                ratios.append(_ratio(ours_extra, comp_extra))
                if ours_extra < comp_extra:
                    wins += 1
            summary_rows.append(
                {
                    "comparator": comparator,
                    "regime": regime,
                    "n_instances": len(selected),
                    "median_ours_over_comparator_extra": f"{_percentile(ratios, 0.5):.8g}",
                    "q25_ours_over_comparator_extra": f"{_percentile(ratios, 0.25):.8g}",
                    "q75_ours_over_comparator_extra": f"{_percentile(ratios, 0.75):.8g}",
                    "ours_win_rate": f"{(wins / len(selected)) if selected else float('nan'):.8g}",
                }
            )
    return summary_rows


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    manifest_rows = _generate_suite()
    assertion_failures: list[str] = []

    if len(manifest_rows) < 30:
        assertion_failures.append(f"suite size {len(manifest_rows)} < 30")
    regimes = {row["regime"] for row in manifest_rows}
    if "capacity_bound" not in regimes or "order_reachable" not in regimes:
        assertion_failures.append(f"suite regimes missing, got {sorted(regimes)}")

    rows: list[dict[str, Any]] = []
    for item in manifest_rows:
        path = SUITE_DIR / f"{item['inst_id']}.json"
        inst = load_json(path, problem_id=2)
        for order_name in list(ORDER_NAMES) + [f"random:{seed}" for seed in range(RANDOM_K)]:
            row, failures = _measure(inst, item["inst_id"], item["regime"], order_name)
            rows.append(row)
            assertion_failures.extend(failures)

    with OUT_SUITE.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=METRIC_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    summary_rows = _summarize(rows)
    with OUT_SUMMARY.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(summary_rows)

    print("--- E13 summary (all regimes) ---")
    for row in summary_rows:
        if row["regime"] == "all":
            print(
                f"{row['comparator']}: median={row['median_ours_over_comparator_extra']} "
                f"q25={row['q25_ours_over_comparator_extra']} "
                f"q75={row['q75_ours_over_comparator_extra']} "
                f"win_rate={row['ours_win_rate']}"
            )

    hard_failures = []
    for failure in assertion_failures:
        if "assign_policy=" in failure:
            print(f"ASSIGN POLICY E13: {failure}")
        elif "initial assign failed" in failure:
            print(f"ASSIGN FALLBACK E13: {failure}")
        elif "time_source=" in failure:
            print(f"TIME FASTPATH E13: {failure}")
        else:
            hard_failures.append(failure)
            print(f"ASSERTION FAILED E13: {failure}")
    if hard_failures:
        raise SystemExit(1)

    print(
        f"DONE E13: {SUITE_DIR.relative_to(ROOT)}/ ({len(manifest_rows)} instances), "
        f"{OUT_SUITE.relative_to(ROOT)}, {OUT_SUMMARY.relative_to(ROOT)}"
    )


if __name__ == "__main__":
    main()
