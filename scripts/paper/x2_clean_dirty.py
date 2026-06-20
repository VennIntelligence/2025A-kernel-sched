"""Emit explanatory clean/dirty mechanism data for Conv_Case0.

Explanatory (notebook-only) figure **x2** — NOT a paper figure.  Illustrates
why dirty residency costs 2x: the L1 clean/dirty residency timeline (promoted
id_raw order) plus the spill-cost decomposition for the promoted vs baseline
order (dirty bytes counted twice: write-back + read-back).

Run::

    uv run python scripts/paper/x2_clean_dirty.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "paper"))
import harness  # noqa: E402

OUT = ROOT / "results" / "paper"
CASE = "Conv_Case0"


def main() -> None:
    inst = harness.load_instance(CASE, 2)

    # L1 clean/dirty residency timeline for the promoted order.
    order = harness.build_order(inst, "id_raw", case=CASE)
    tl = harness.live_clean_dirty_timeline(order, inst, "L1")
    pd.DataFrame(tl, columns=["pos", "live_clean", "live_dirty"]).to_csv(
        OUT / "x2_clean_dirty_timeline.csv", index=False
    )

    # Spill-cost decomposition: promoted vs baseline order.
    rows = []
    for name in ("id_raw", "baseline"):
        o = harness.build_order(inst, name, case=CASE)
        _, _, spills = harness.assign(inst, o)
        rows.append({"order": name, **harness.extra_split(spills, inst)})
    split = pd.DataFrame(rows)
    split.to_csv(OUT / "x2_cost_split.csv", index=False)

    print(f"x2: {CASE} timeline_steps={len(tl)}")
    print(split.to_string(index=False))
    for name in ("x2_clean_dirty_timeline.csv", "x2_cost_split.csv"):
        print(f"wrote results/paper/{name}")


if __name__ == "__main__":
    main()
