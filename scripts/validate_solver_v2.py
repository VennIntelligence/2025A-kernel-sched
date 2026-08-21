"""Validate the research solver against official and strong P2 baselines."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "paper"))

import harness as H  # noqa: E402

from algorithms.ours.solve import solve  # noqa: E402
from ks_core.metrics import evaluate  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--problems", type=int, nargs="+", default=[2])
    parser.add_argument("--cases", nargs="*", default=H.CASES)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "autoresearch_v2" / "formal_validation.json",
    )
    args = parser.parse_args()

    official_rows = json.loads(
        (ROOT / "results" / "exp001_baseline01" / "metrics.json").read_text()
    )
    official = {
        (row["case"], int(row["problem"])): row
        for row in official_rows
    }
    paper_rows = []
    paper_path = ROOT / "results" / "paper" / "e12_baselines.csv"
    if paper_path.exists():
        import csv

        with paper_path.open(newline="", encoding="utf-8") as handle:
            paper_rows = list(csv.DictReader(handle))
    strong = {
        (row["case"], int(row["problem"])): row
        for row in paper_rows
        if row["order"] == "cp_free_first"
    }

    rows = []
    for case in args.cases:
        for problem in args.problems:
            print(f"[solve] {case} P{problem}", flush=True)
            inst = H.load_instance(case, problem)
            started = time.perf_counter()
            schedule = solve(inst, {})
            result = evaluate(inst, schedule.order, schedule.memory, schedule.spill_entries)
            split = H.extra_split(schedule.spill_entries, inst)
            backed_volume = int(split["clean_bytes"])
            generated_volume = int(split["dirty_bytes"] // 2)
            elapsed = time.perf_counter() - started
            base = official[(case, problem)]
            row = {
                "case": case,
                "problem": problem,
                **result.metrics,
                "valid": result.valid,
                "violations": result.violations,
                "backed_volume": backed_volume,
                "generated_volume": generated_volume,
                "spill_volume": backed_volume + generated_volume,
                "wall_seconds": elapsed,
                "official_extra": int(base["extra"]),
                "official_time": int(base["time"]),
                "extra_delta_vs_official": result.metrics["extra"] - int(base["extra"]),
                "time_delta_vs_official": result.metrics["time"] - int(base["time"]),
            }
            # The strong-order table is a P2 spill-engine comparison.  Its
            # extra-traffic fields are not meaningful for P1, whose output has
            # no spills and whose objective is logical lifetime pressure.
            if problem >= 2 and (case, problem) in strong:
                row["strong_blind_extra"] = int(strong[(case, problem)]["extra"])
                row["extra_delta_vs_strong_blind"] = (
                    result.metrics["extra"] - row["strong_blind_extra"]
                )
            rows.append(row)
            print(json.dumps(row, sort_keys=True), flush=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    if not all(row["valid"] for row in rows):
        raise SystemExit("invalid result found")


if __name__ == "__main__":
    main()
