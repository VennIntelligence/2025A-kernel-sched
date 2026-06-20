from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.paper.harness import build_order, live_clean_dirty_timeline, load_instance


CASE = "Conv_Case0"
PROBLEM_ID = 2
ORDERS = ("id_raw", "baseline")
OUT_DIR = ROOT / "results" / "paper"


def write_residency(order_name: str) -> Path:
    inst = load_instance(CASE, PROBLEM_ID)
    order = build_order(inst, order_name, CASE)
    rows = [
        {
            "pos": pos,
            "live_clean": live_clean,
            "live_dirty": live_dirty,
            "live_total": live_clean + live_dirty,
        }
        for pos, live_clean, live_dirty in live_clean_dirty_timeline(order, inst, "L1")
    ]
    assert len(rows) == len(order), (order_name, len(rows), len(order))
    assert all(r["live_total"] == r["live_clean"] + r["live_dirty"] for r in rows), order_name

    path = OUT_DIR / f"e5_residency_{order_name}.csv"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=("pos", "live_clean", "live_dirty", "live_total"))
        writer.writeheader()
        writer.writerows(rows)
    return path


def main() -> None:
    paths = [write_residency(order_name) for order_name in ORDERS]
    for path in paths:
        print(path.relative_to(ROOT))
    print("DONE T5: " + ", ".join(str(path.relative_to(ROOT)) for path in paths))


if __name__ == "__main__":
    main()
