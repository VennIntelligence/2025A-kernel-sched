from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.paper.harness import (  # noqa: E402
    CAP,
    CASES,
    assign,
    build_order,
    extra_split,
    load_instance,
    overflow_integral,
    peak_working_set,
    total_time,
)


RESULTS = ROOT / "results" / "paper"
OUT = RESULTS / "e6_surrogate.csv"
ORDERS = ["capfit_id", "p1", "id_raw", "min_id", "baseline"] + [
    f"random:{seed}" for seed in range(12)
]


def evaluate_order(case: str, order_name: str) -> dict[str, object]:
    inst = load_instance(case, 2)
    order = build_order(inst, order_name, case)
    peak = peak_working_set(order, inst)
    _, _, spills_p2 = assign(inst, order, prefetch_window=0)
    order_p3, memory_p3, spills_p3 = assign(inst, order, prefetch_window=40)

    return {
        "case": case,
        "order": order_name,
        "phi": overflow_integral(order, inst),
        "peak_over": sum(max(0, peak.get(cache, 0) - cap) for cache, cap in CAP.items()),
        "extra_p2": extra_split(spills_p2, inst)["extra"],
        "time_p3": total_time(inst, order_p3, memory_p3, spills_p3),
    }


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for case in CASES:
        for order_name in ORDERS:
            try:
                row = evaluate_order(case, order_name)
            except RuntimeError as exc:
                print(f"SKIP {case} {order_name}: {exc}")
                continue
            rows.append(row)
            print(
                f"{case} {order_name}: "
                f"phi={row['phi']:.3f} peak_over={row['peak_over']} "
                f"extra_p2={row['extra_p2']} time_p3={row['time_p3']}"
            )

    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["case", "order", "phi", "peak_over", "extra_p2", "time_p3"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
