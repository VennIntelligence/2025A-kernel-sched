"""Generate public-case ablations, a capacity sweep, and synthetic checks."""

from __future__ import annotations

import csv
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src"), str(ROOT / "scripts" / "paper")]

import baselines as B  # noqa: E402
import harness as H  # noqa: E402

from ks_core import solver as S  # noqa: E402
from ks_core.constants import CACHE_CAPACITIES  # noqa: E402
from ks_core.graph import load_json  # noqa: E402

OUT = ROOT / "results" / "autoresearch_v2"
BEST_FIT = S._FreeSpace.find


def first_fit(space, size: int) -> int | None:
    for offset, free_size in sorted(space.free):
        if free_size >= size:
            return offset
    return None


def orders(inst, include_unlock: bool) -> list[tuple[str, list[int]]]:
    rows = [
        ("capfit_id", S._memory_aware_order(inst, "capfit_id")),
        ("p1", S._memory_aware_order(inst, "p1")),
        ("id_raw", S._id_raw_order(inst)),
    ]
    if include_unlock:
        rows.insert(0, ("unlock_frontier", S._unlock_frontier_order(inst)))
    return rows


def select(inst, candidate_orders, policy: str, placement: str) -> dict:
    S._FreeSpace.find = first_fit if placement == "first_fit" else BEST_FIT
    best = None
    for name, order in candidate_orders:
        try:
            _order_ws, _memory, spills = S._assign_memory_with_spills(
                inst,
                order,
                prefetch_window=0,
                victim_policy=policy,
            )
        except RuntimeError:
            continue
        split = H.extra_split(spills, inst)
        key = (split["extra"], split["spills"])
        record = {
            "extra": split["extra"],
            "spills": split["spills"],
            "clean_bytes": split["clean_bytes"],
            "dirty_bytes": split["dirty_bytes"],
            "order": name,
            "policy": policy,
            "placement": placement,
        }
        if best is None or key < (best["extra"], best["spills"]):
            best = record
    if best is None:
        raise RuntimeError("no feasible ablation candidate")
    return best


def public_ablation() -> list[dict]:
    schemes = [
        ("iter038", False, "dist_size_cost", "first_fit"),
        ("best_fit_only", False, "dist_size_cost", "best_fit"),
        ("unlock_only", True, "dist_size_cost", "first_fit"),
        ("adaptive_only", False, "share_adaptive_25", "first_fit"),
        ("unlock_adaptive", True, "share_adaptive_25", "first_fit"),
        ("full", True, "share_adaptive_25", "best_fit"),
    ]
    rows = []
    for case in H.CASES:
        inst = H.load_instance(case, 2)
        old_orders = orders(inst, False)
        new_orders = orders(inst, True)
        for scheme, use_unlock, policy, placement in schemes:
            chosen = select(
                inst,
                new_orders if use_unlock else old_orders,
                policy,
                placement,
            )
            rows.append({"case": case, "scheme": scheme, **chosen})
            print("ABLATE", rows[-1], flush=True)
    return rows


def capacity_sweep() -> list[dict]:
    original_l1 = CACHE_CAPACITIES["L1"]
    rows = []
    try:
        for capacity in (2048, 2560, 3072, 3584, 4096, 6144, 8192, 12288, 16384):
            CACHE_CAPACITIES["L1"] = capacity
            inst = H.load_instance("Conv_Case0", 2)
            candidates = orders(inst, True)
            full_options = []
            for policy in ("share_adaptive_25", "dist_size_cost"):
                try:
                    full_options.append(select(inst, candidates, policy, "best_fit"))
                except RuntimeError:
                    pass
            blind_options = []
            for policy in ("share_adaptive_25", "dist_size_cost"):
                try:
                    blind_options.append(
                        select(
                            inst,
                            [("cp_free_first", B.cp_free_first(inst))],
                            policy,
                            "best_fit",
                        )
                    )
                except RuntimeError:
                    pass
            full = min(full_options, key=lambda row: row["extra"]) if full_options else None
            blind = min(blind_options, key=lambda row: row["extra"]) if blind_options else None
            row = {
                "case": "Conv_Case0",
                "L1_capacity": capacity,
                "status": "feasible" if full is not None else "infeasible_pinned_working_set",
                "full_extra": full["extra"] if full else None,
                "full_order": full["order"] if full else None,
                "blind_extra": blind["extra"] if blind else None,
                "blind_over_full": (
                    blind["extra"] / full["extra"]
                    if full and blind and full["extra"] > 0
                    else None
                ),
            }
            rows.append(row)
            print("CAPACITY", row, flush=True)
    finally:
        CACHE_CAPACITIES["L1"] = original_l1
        S._FreeSpace.find = BEST_FIT
    return rows


def synthetic_check() -> tuple[list[dict], list[dict]]:
    manifest_path = ROOT / "data" / "processed" / "synthetic" / "suite" / "manifest.csv"
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        manifest = list(csv.DictReader(handle))
    rows = []
    for item in manifest:
        inst = load_json(
            manifest_path.parent / f"{item['inst_id']}.json",
            problem_id=2,
        )
        old = select(inst, orders(inst, False), "dist_size_cost", "first_fit")
        full = min(
            (
                select(inst, orders(inst, True), policy, "best_fit")
                for policy in ("dist_size_cost", "share_adaptive_25")
            ),
            key=lambda row: (row["extra"], row["spills"]),
        )
        blind_order = [("cp_free_first", B.cp_free_first(inst))]
        blind_candidates = [
            select(inst, blind_order, policy, placement)
            for policy in ("dist_size_cost", "share_adaptive_25")
            for placement in ("first_fit", "best_fit")
        ]
        blind = min(blind_candidates, key=lambda row: (row["extra"], row["spills"]))
        row = {
            "inst_id": item["inst_id"],
            "regime": item["regime"],
            "target_cache": item["target_cache"],
            "full_extra": full["extra"],
            "iter038_extra": old["extra"],
            "blind_extra": blind["extra"],
            "full_order": full["order"],
            "delta_full_vs_iter038": full["extra"] - old["extra"],
            "result": (
                "WIN"
                if full["extra"] < blind["extra"]
                else "LOSS"
                if full["extra"] > blind["extra"]
                else "TIE"
            ),
        }
        rows.append(row)
        print("SYNTH", row, flush=True)

    summary = []
    for regime in ("all", "capacity_bound", "order_reachable"):
        group = rows if regime == "all" else [row for row in rows if row["regime"] == regime]
        ratios = [
            row["full_extra"] / row["blind_extra"]
            for row in group
            if row["blind_extra"] > 0
        ]
        summary.append(
            {
                "regime": regime,
                "n": len(group),
                "wins": sum(row["result"] == "WIN" for row in group),
                "ties": sum(row["result"] == "TIE" for row in group),
                "losses": sum(row["result"] == "LOSS" for row in group),
                "improved_vs_iter038": sum(
                    row["delta_full_vs_iter038"] < 0 for row in group
                ),
                "tied_vs_iter038": sum(
                    row["delta_full_vs_iter038"] == 0 for row in group
                ),
                "regressed_vs_iter038": sum(
                    row["delta_full_vs_iter038"] > 0 for row in group
                ),
                "median_full_over_blind": statistics.median(ratios) if ratios else None,
            }
        )
    return rows, summary


def write_json(name: str, value) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, indent=2), encoding="utf-8")


def main() -> None:
    public = public_ablation()
    write_json("round7_public_ablation.json", public)
    capacity = capacity_sweep()
    write_json("round8_capacity_sweep.json", capacity)
    synthetic, summary = synthetic_check()
    write_json("round9_synthetic.json", synthetic)
    write_json("round9_synthetic_summary.json", summary)
    print("SUMMARY", summary, flush=True)


if __name__ == "__main__":
    main()
