from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.paper.harness import assign, build_order, extra_split, load_instance


EXPECTED = {
    ("Conv_Case0", "p1"): 88044,
    ("Matmul_Case0", "capfit_id"): 34688,
    ("FlashAttention_Case0", "capfit_id"): 4444,
}


def main() -> None:
    for (case, order_name), expected in EXPECTED.items():
        inst = load_instance(case, 2)
        order = build_order(inst, order_name, case)
        _, _, spills = assign(inst, order, "dist_size_cost", 0)
        extra = extra_split(spills, inst)["extra"]
        assert extra == expected, (case, order_name, extra, expected)
        print(f"{case} {order_name}: extra={extra}")
    print("DONE T0 verify")


if __name__ == "__main__":
    main()
