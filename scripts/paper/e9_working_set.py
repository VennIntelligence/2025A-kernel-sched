from __future__ import annotations

import csv
from pathlib import Path

from harness import (
    CAP,
    CASES,
    assign,
    build_order,
    extra_split,
    live_clean_dirty_timeline,
    load_instance,
    peak_working_set,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "paper" / "e9_working_set.csv"
ORDERS = ["capfit_id", "p1", "id_raw", "min_id", "baseline"] + [
    f"random:{seed}" for seed in range(8)
]
FIELDNAMES = [
    "case",
    "cache",
    "capacity",
    "min_peak_all",
    "ratio_all",
    "min_peak_nearopt",
    "ratio_nearopt",
    "nearopt_order",
    "n_nearopt",
    "clean_frac_at_peak",
    "bound_class",
]


def clean_fraction_at_peak(record: dict, cache: str) -> float:
    timeline = live_clean_dirty_timeline(record["ids"], record["inst"], cache)
    _, live_clean, live_dirty = max(timeline, key=lambda row: row[1] + row[2])
    live_total = live_clean + live_dirty
    return live_clean / live_total if live_total else 0.0


def main() -> None:
    rows = []
    skipped = []

    for case in CASES:
        records = []
        for order_name in ORDERS:
            inst = load_instance(case, 2)
            try:
                ids = build_order(inst, order_name, case)
                peak = peak_working_set(ids, inst)
                _, _, spills = assign(inst, ids, "dist_size_cost", 0)
                extra = extra_split(spills, inst)["extra"]
            except RuntimeError as exc:
                skipped.append((case, order_name, str(exc)))
                print(f"SKIP {case} {order_name}: {exc}")
                continue
            records.append({
                "order": order_name,
                "inst": inst,
                "ids": ids,
                "peak": peak,
                "extra": extra,
            })

        if not records:
            raise RuntimeError(f"no successful orders for {case}")

        extra_min = min(record["extra"] for record in records)
        threshold = extra_min * 1.10
        near_opt = [record for record in records if record["extra"] <= threshold]
        order_rank = {name: index for index, name in enumerate(ORDERS)}

        for cache, capacity in CAP.items():
            min_peak_all = min(record["peak"].get(cache, 0) for record in records)
            best_near = min(
                near_opt,
                key=lambda record: (record["peak"].get(cache, 0), order_rank[record["order"]]),
            )
            min_peak_nearopt = best_near["peak"].get(cache, 0)
            ratio_nearopt = min_peak_nearopt / capacity
            rows.append({
                "case": case,
                "cache": cache,
                "capacity": capacity,
                "min_peak_all": min_peak_all,
                "ratio_all": min_peak_all / capacity,
                "min_peak_nearopt": min_peak_nearopt,
                "ratio_nearopt": ratio_nearopt,
                "nearopt_order": best_near["order"],
                "n_nearopt": len(near_opt),
                "clean_frac_at_peak": clean_fraction_at_peak(best_near, cache),
                "bound_class": "capacity_bound" if ratio_nearopt > 1.0 else "order_reachable",
            })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    assertion_failures = []
    m1_l1 = next(r for r in rows if r["case"] == "Matmul_Case1" and r["cache"] == "L1")
    if m1_l1["ratio_nearopt"] <= 1.0:
        assertion_failures.append(
            "Matmul_Case1,L1 ratio_nearopt expected > 1.0 "
            f"(approx 8.5, min_peak_nearopt approx 34816), got "
            f"ratio={m1_l1['ratio_nearopt']:.6g}, "
            f"min_peak_nearopt={m1_l1['min_peak_nearopt']}"
        )

    conv_over = [
        r for r in rows
        if r["case"].startswith("Conv") and r["ratio_nearopt"] > 1.0
    ]
    if not conv_over:
        assertion_failures.append("expected at least one Conv cache with ratio_nearopt > 1.0")

    print(f"wrote {OUT}")
    if skipped:
        print("skipped:")
        for case, order_name, reason in skipped:
            print(f"  {case} {order_name}: {reason}")
    else:
        print("skipped=[]")

    if assertion_failures:
        for failure in assertion_failures:
            print(f"ASSERTION FAILED T11: {failure}")
    else:
        print(
            "ASSERTION PASS T11: Matmul_Case1,L1 ratio_nearopt="
            f"{m1_l1['ratio_nearopt']:.6g}, min_peak_nearopt={m1_l1['min_peak_nearopt']}"
        )
        print(f"ASSERTION PASS T11: Conv ratio_nearopt > 1 count={len(conv_over)}")

    print(f"DONE T11: {OUT}")


if __name__ == "__main__":
    main()
