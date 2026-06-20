"""Generate E2 victim-policy sensitivity data."""
from __future__ import annotations

import csv
import statistics
from collections import defaultdict

from harness import CASES, ROOT, assign, build_order, extra_split, load_instance

ORDERS = ["capfit_id", "p1", "id_raw", "min_id", "baseline"]
VICTIMS = ["dist_size_cost", "cost_then_dist", "cheap_first", "far_only"]

RESULTS = ROOT / "results" / "paper"
ORDER_PATH = RESULTS / "e2_victim_order.csv"
CV_PATH = RESULTS / "e2_victim_cv.csv"

ORDER_FIELDS = [
    "case",
    "order",
    "victim",
    "extra",
    "spills",
    "clean_bytes",
    "dirty_bytes",
    "clean_count",
    "dirty_count",
]
CV_FIELDS = ["case", "order", "cv", "extra_min", "extra_max"]


def failure_row(case: str, order: str, victim: str) -> dict:
    return {
        "case": case,
        "order": order,
        "victim": victim,
        "extra": -1,
        "spills": -1,
        "clean_bytes": -1,
        "dirty_bytes": -1,
        "clean_count": -1,
        "dirty_count": -1,
    }


def write_csv(path, fields, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows = []
    failures = []

    for case in CASES:
        print(f"[case] {case}", flush=True)
        inst = load_instance(case, 2)
        order_cache = {}

        for order in ORDERS:
            for victim in VICTIMS:
                try:
                    if order not in order_cache:
                        order_cache[order] = build_order(inst, order, case)
                    order_ids = order_cache[order]
                    _, _, spills = assign(inst, order_ids, victim, 0)
                    row = {"case": case, "order": order, "victim": victim}
                    row.update(extra_split(spills, inst))
                except RuntimeError as exc:
                    failures.append((case, order, victim, str(exc)))
                    print(f"[fail] {case} {order} {victim}: {exc}", flush=True)
                    row = failure_row(case, order, victim)
                rows.append(row)

    write_csv(ORDER_PATH, ORDER_FIELDS, rows)

    extras_by_key = defaultdict(list)
    for row in rows:
        extra = int(row["extra"])
        if extra >= 0:
            extras_by_key[(row["case"], row["order"])].append(extra)

    cv_rows = []
    for case in CASES:
        for order in ORDERS:
            extras = extras_by_key[(case, order)]
            if extras:
                mean = statistics.fmean(extras)
                cv = 0.0 if mean == 0 else statistics.pstdev(extras) / mean
                extra_min = min(extras)
                extra_max = max(extras)
            else:
                cv = -1.0
                extra_min = -1
                extra_max = -1
            cv_rows.append({
                "case": case,
                "order": order,
                "cv": cv,
                "extra_min": extra_min,
                "extra_max": extra_max,
            })

    write_csv(CV_PATH, CV_FIELDS, cv_rows)

    good = sum(float(row["cv"]) >= 0 and float(row["cv"]) < 0.01 for row in cv_rows)
    valid = sum(float(row["cv"]) >= 0 for row in cv_rows)
    print(f"[summary] rows={len(rows)} failures={len(failures)} cv_lt_0.01={good}/{valid}", flush=True)
    print(f"DONE T2: {ORDER_PATH} {CV_PATH}", flush=True)


if __name__ == "__main__":
    main()
