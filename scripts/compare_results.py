"""Compare results across experiments — generate leaderboard."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ks_core.io import get_project_root
from ks_core.metrics import compare_experiments


def build_leaderboard(results_dir: Path) -> list[dict]:
    """Scan all experiment directories and build a comparison table."""
    exp_dirs = [path for path in sorted(results_dir.iterdir()) if path.is_dir()]
    return compare_experiments(exp_dirs)


def main():
    parser = argparse.ArgumentParser(description="Compare experiment results")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=None,
        help="Results directory (default: <root>/results)",
    )
    parser.add_argument("--output", type=Path, help="Output leaderboard JSON")
    args = parser.parse_args()

    root = get_project_root()
    results_dir = args.results_dir or root / "results"
    leaderboard = build_leaderboard(results_dir)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(leaderboard, f, indent=2)
        print(f"📊 Leaderboard saved to {args.output} ({len(leaderboard)} entries)")
    else:
        try:
            import pandas as pd

            df = pd.DataFrame(leaderboard)
            if "valid" in df.columns:
                df = df[df["valid"].fillna(True)]
            print(df.to_string(index=False))
        except ImportError:
            print(json.dumps(leaderboard, indent=2))


if __name__ == "__main__":
    main()
