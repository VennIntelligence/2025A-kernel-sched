"""Sweep prefetch windows for P3 selection/placement decoupling."""
from __future__ import annotations

import csv

from harness import CASES, ROOT, assign, build_order, extra_split, load_instance, total_time

ORDERS = ("capfit_id", "p1")
PREFETCH_WINDOWS = (0, 5, 10, 20, 40, 80, 120, 160)
VICTIM_POLICY = "dist_size_cost"
OUT = ROOT / "results" / "paper" / "e8_prefetch.csv"
COLUMNS = ("case", "order", "H", "extra", "time", "spills")


def improvement_cases(rows: list[dict[str, int | str]]) -> list[dict[str, int | str]]:
    improved = []
    for case in CASES:
        candidates = []
        for order in ORDERS:
            curve = [
                row for row in rows
                if row["case"] == case and row["order"] == order and row["time"] >= 0
            ]
            base = next((row for row in curve if row["H"] == 0), None)
            if base is None:
                continue
            better = [row for row in curve if row["H"] > 0 and row["time"] < base["time"]]
            if better:
                best = min(better, key=lambda row: row["time"])
                candidates.append(
                    {
                        "case": case,
                        "order": order,
                        "H": best["H"],
                        "time": best["time"],
                        "time0": base["time"],
                    }
                )
        if candidates:
            improved.append(min(candidates, key=lambda row: row["time"]))
    return improved


def extra_decreases(rows: list[dict[str, int | str]]) -> list[dict[str, int | str]]:
    decreases = []
    for case in CASES:
        for order in ORDERS:
            curve = sorted(
                (
                    row for row in rows
                    if row["case"] == case and row["order"] == order and row["extra"] >= 0
                ),
                key=lambda row: row["H"],
            )
            for prev, cur in zip(curve, curve[1:]):
                if cur["extra"] < prev["extra"]:
                    decreases.append(
                        {
                            "case": case,
                            "order": order,
                            "from_H": prev["H"],
                            "to_H": cur["H"],
                            "from_extra": prev["extra"],
                            "to_extra": cur["extra"],
                            "delta": cur["extra"] - prev["extra"],
                        }
                    )
    return decreases


def run_sweep() -> tuple[list[dict[str, int | str]], list[tuple[str, str, int, str]]]:
    rows = []
    failures = []
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()

        for case in CASES:
            inst = load_instance(case, problem_id=3)
            for order_name in ORDERS:
                base_order = build_order(inst, order_name, case=case)
                for window in PREFETCH_WINDOWS:
                    try:
                        order_with_spills, memory, spills = assign(
                            inst, list(base_order), VICTIM_POLICY, window
                        )
                        split = extra_split(spills, inst)
                        row = {
                            "case": case,
                            "order": order_name,
                            "H": window,
                            "extra": split["extra"],
                            "time": total_time(inst, order_with_spills, memory, spills),
                            "spills": split["spills"],
                        }
                    except RuntimeError as exc:
                        failures.append((case, order_name, window, str(exc)))
                        row = {
                            "case": case,
                            "order": order_name,
                            "H": window,
                            "extra": -1,
                            "time": -1,
                            "spills": -1,
                        }

                    rows.append(row)
                    writer.writerow(row)
                    f.flush()
                    print(
                        f"{case} {order_name} H={window} "
                        f"extra={row['extra']} time={row['time']} spills={row['spills']}",
                        flush=True,
                    )
    return rows, failures


def main() -> None:
    rows, failures = run_sweep()
    improved = improvement_cases(rows)
    decreases = extra_decreases(rows)

    assert len(rows) == len(CASES) * len(ORDERS) * len(PREFETCH_WINDOWS), len(rows)
    assert len(improved) >= 4, improved

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"rows={len(rows)} runtime_errors={len(failures)}")
    print(f"improved_cases={len(improved)} details={improved}")
    print(f"extra_decreases={len(decreases)} details={decreases}")
    if failures:
        print(f"runtime_error_details={failures}")


if __name__ == "__main__":
    main()
