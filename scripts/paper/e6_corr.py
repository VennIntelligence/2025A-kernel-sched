from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results" / "paper"
IN = RESULTS / "e6_surrogate.csv"
OUT = RESULTS / "e6_corr.csv"


def corr_row(case: str, df: pd.DataFrame) -> dict[str, object]:
    corr = df[["phi", "peak_over", "extra_p2", "time_p3"]].corr(method="spearman")
    return {
        "case": case,
        "spearman_phi_extra": corr.loc["phi", "extra_p2"],
        "spearman_peak_extra": corr.loc["peak_over", "extra_p2"],
        "spearman_phi_time": corr.loc["phi", "time_p3"],
        "n": len(df),
    }


def main() -> None:
    df = pd.read_csv(IN)
    rows = [corr_row(case, group) for case, group in df.groupby("case", sort=True)]
    rows.append(corr_row("ALL", df))
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(out.to_string(index=False))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
