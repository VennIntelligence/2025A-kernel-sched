"""E12 -- standard scheduling baselines for the six contest cases."""

from __future__ import annotations

import csv
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

import baselines as B
import harness as H

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "paper"
OUT_BASELINES = RESULTS / "e12_baselines.csv"
OUT_WINLOSS = RESULTS / "e12_winloss.csv"

ORDER_NAMES = (
    "cp_list",
    "cp_free_first",
    "pressure_uniform",
    "goodman_hsu",
    "ours",
    "baseline",
)
COMPARATORS = ("cp_list", "cp_free_first", "pressure_uniform", "goodman_hsu", "baseline")
ASSIGN_CACHE: dict[
    tuple[str, str, tuple[int, ...]],
    tuple[list[int], dict[int, int], list[tuple[int, int]], dict[str, Any]],
] = {}
METRIC_FIELDS = [
    "case",
    "problem",
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
WINLOSS_FIELDS = [
    "case",
    "problem",
    "comparator",
    "key_kind",
    "ours_key",
    "comparator_key",
    "result",
]


def _base_order(inst, case: str, order_name: str) -> tuple[list[int], dict[str, Any] | None]:
    if order_name == "cp_list":
        return B.cp_list(inst), None
    if order_name == "cp_free_first":
        return B.cp_free_first(inst), None
    if order_name == "pressure_uniform":
        return B.pressure_uniform(inst), None
    if order_name == "goodman_hsu":
        return B.goodman_hsu(inst), None
    if order_name == "baseline":
        return H.build_order(inst, "baseline", case), None
    if order_name == "ours":
        selected = B.select_ours_order(inst)
        return selected["base_order"], selected
    raise ValueError(order_name)


def _measure(inst, case: str, problem: int, order_name: str) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    order, selected = _base_order(inst, case, order_name)
    ok, reason = B.validate_topological_order(inst, order)
    if not ok:
        failures.append(f"{case} P{problem} {order_name}: invalid topo order: {reason}")

    fallback_notes: list[str] = []
    if selected is None:
        cache_key = (case, order_name, tuple(order))
        if cache_key in ASSIGN_CACHE:
            order_ws, memory, spills, assign_meta = ASSIGN_CACHE[cache_key]
        else:
            initial_policy = "far_only" if order_name == "cp_list" else "dist_size_cost"
            initial_window = 80 if order_name == "cp_list" else 0
            order_ws, memory, spills, assign_meta = B.safe_assign(
                inst,
                order,
                victim_policy=initial_policy,
                prefetch_window=initial_window,
            )
            ASSIGN_CACHE[cache_key] = (order_ws, memory, spills, assign_meta)
        if order_name == "cp_list":
            fallback_notes.append(
                f"{case} P{problem} cp_list: assign_policy="
                f"{assign_meta['victim_policy']}/{assign_meta['prefetch_window']} "
                "for latency-only stress baseline"
            )
        elif order_name == "cp_free_first":
            fallback_notes.append(
                f"{case} P{problem} cp_free_first: assign_policy="
                f"{assign_meta['victim_policy']}/{assign_meta['prefetch_window']} "
                "allocator-friendly latency companion for cp_list"
            )
        if assign_meta["fallback"]:
            fallback_notes.append(
                f"{case} P{problem} {order_name}: initial assign failed; "
                f"used {assign_meta['victim_policy']}/{assign_meta['prefetch_window']} "
                f"after {assign_meta['errors']}"
            )
        split = H.extra_split(spills, inst)
        time, time_source = B.controlled_total_time(inst, order_ws, memory, spills)
        if time_source != "address":
            fallback_notes.append(
                f"{case} P{problem} {order_name}: time_source={time_source} "
                f"for {split['spills']} spills"
            )
    else:
        assign_meta = selected.get("assign_meta", {})
        if assign_meta.get("fallback"):
            fallback_notes.append(
                f"{case} P{problem} ours: initial assign failed; used "
                f"{assign_meta['victim_policy']}/{assign_meta['prefetch_window']} "
                f"after {assign_meta['errors']}"
            )
        split = selected["split"]
        spills = selected["spills"]
        time = selected["time"]
        time_source = selected.get("time_source", "address")
        if selected.get("time_source") != "address":
            fallback_notes.append(
                f"{case} P{problem} ours: time_source={selected.get('time_source')} "
                f"for {split['spills']} spills"
            )
        _ = spills

    peak = H.peak_working_set(order, inst)
    row = {
        "case": case,
        "problem": problem,
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
    }
    return row, fallback_notes + failures


def _key(row: dict[str, Any]) -> tuple[tuple[Any, ...], str]:
    problem = int(row["problem"])
    if problem == 1:
        return (
            (
                int(row["peak_L1"]),
                int(row["peak_UB"]),
                int(row["peak_L0A"]),
                int(row["peak_L0B"]),
                int(row["peak_L0C"]),
                int(row["time"]),
            ),
            "p1_bytes_proxy",
        )
    if problem == 2:
        return (int(row["extra"]), int(row["spills"]), int(row["time"])), "p2_official"
    return (int(row["time"]), int(row["extra"]), int(row["spills"])), "p3_official"


def _ratio(num: float, den: float) -> float:
    if den == 0:
        return 1.0 if num == 0 else float("inf")
    return num / den


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    assertion_failures: list[str] = []

    for case in H.CASES:
        for problem in (1, 2, 3):
            inst = H.load_instance(case, problem)
            for order_name in ORDER_NAMES:
                print(f"E12 measure {case} P{problem} {order_name}", flush=True)
                row, failures = _measure(inst, case, problem, order_name)
                rows.append(row)
                assertion_failures.extend(failures)

    with OUT_BASELINES.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=METRIC_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    by_cell_order = {
        (row["case"], int(row["problem"]), row["order"]): row
        for row in rows
    }
    winloss_rows: list[dict[str, Any]] = []
    for case in H.CASES:
        for problem in (1, 2, 3):
            ours = by_cell_order[(case, problem, "ours")]
            ours_key, key_kind = _key(ours)
            for comparator in COMPARATORS:
                comp = by_cell_order[(case, problem, comparator)]
                comp_key, comp_kind = _key(comp)
                if comp_kind != key_kind:
                    assertion_failures.append(
                        f"{case} P{problem} {comparator}: key kind mismatch "
                        f"{key_kind} vs {comp_kind}"
                    )
                result = "WIN" if ours_key < comp_key else "LOSS" if ours_key > comp_key else "TIE"
                winloss_rows.append(
                    {
                        "case": case,
                        "problem": problem,
                        "comparator": comparator,
                        "key_kind": key_kind,
                        "ours_key": repr(ours_key),
                        "comparator_key": repr(comp_key),
                        "result": result,
                    }
                )

    with OUT_WINLOSS.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=WINLOSS_FIELDS)
        writer.writeheader()
        writer.writerows(winloss_rows)

    counts = Counter((row["comparator"], row["result"]) for row in winloss_rows)
    print("--- E12 win/loss counts ---")
    for comparator in COMPARATORS:
        print(
            f"{comparator}: WIN={counts[(comparator, 'WIN')]} "
            f"TIE={counts[(comparator, 'TIE')]} LOSS={counts[(comparator, 'LOSS')]}"
        )

    cp_extra_ratios = []
    cp_phi_ratios = []
    companion_extra_ratios = []
    cp_to_companion_ratios = []
    for case in H.CASES:
        ours = by_cell_order[(case, 2, "ours")]
        cp = by_cell_order[(case, 2, "cp_list")]
        companion = by_cell_order[(case, 2, "cp_free_first")]
        cp_extra_ratios.append(_ratio(float(cp["extra"]), float(ours["extra"])))
        cp_phi_ratios.append(_ratio(float(cp["phi"]), float(ours["phi"])))
        companion_extra_ratios.append(_ratio(float(companion["extra"]), float(ours["extra"])))
        cp_to_companion_ratios.append(_ratio(float(cp["extra"]), float(companion["extra"])))
    print(
        "cp_list / ours P2 median multiples: "
        f"extra={statistics.median(cp_extra_ratios):.6g} "
        f"phi={statistics.median(cp_phi_ratios):.6g}"
    )
    print(
        "cp_free_first / ours P2 median multiple: "
        f"extra={statistics.median(companion_extra_ratios):.6g}"
    )
    print(
        "cp_list / cp_free_first P2 median multiple: "
        f"extra={statistics.median(cp_to_companion_ratios):.6g}"
    )

    for failure in assertion_failures:
        if "assign_policy=" in failure:
            print(f"ASSIGN POLICY E12: {failure}")
        elif "initial assign failed" in failure:
            print(f"ASSIGN FALLBACK E12: {failure}")
        elif "time_source=" in failure:
            print(f"TIME FASTPATH E12: {failure}")
        else:
            print(f"ASSERTION FAILED E12: {failure}")

    print(
        "DONE E12: "
        f"{OUT_BASELINES.relative_to(ROOT)}, {OUT_WINLOSS.relative_to(ROOT)} "
        "(P1 key_kind=p1_bytes_proxy)"
    )


if __name__ == "__main__":
    main()
