"""E15 -- compact applicability figure for the conference drafts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ks_core.plotting import METHOD_PALETTE, make_figure, savefig_academic

ROOT = Path(__file__).resolve().parents[2]
SUMMARY = ROOT / "results" / "paper" / "e13_summary.csv"
OUT_DIR = ROOT / "output" / "02_paper_figures"
ASSET_DIR = ROOT / "paper" / "assets" / "figures"

COMPARATORS = [
    ("cp_list", "CP"),
    ("cp_free_first", "CP-free"),
    ("pressure_uniform", "Pressure"),
    ("goodman_hsu", "G-Hsu"),
    ("random_best", "Random"),
]

REGIMES = [
    ("capacity_bound", "Capacity-bound"),
    ("order_reachable", "Order-reachable"),
]


def main() -> None:
    df = pd.read_csv(SUMMARY)
    df = df[df["comparator"].isin([name for name, _ in COMPARATORS])]
    df = df[df["regime"].isin([name for name, _ in REGIMES])]

    fig, axes = make_figure("double_col", nrows=1, ncols=2, height=2.35)
    ax_win, ax_ratio = axes

    colors = [METHOD_PALETTE["primary"], METHOD_PALETTE["secondary"]]
    bar_w = 0.34
    x = list(range(len(COMPARATORS)))

    for offset, (regime, label) in zip([-bar_w / 2, bar_w / 2], REGIMES):
        subset = df[df["regime"] == regime].set_index("comparator")
        win = [subset.loc[name, "ours_win_rate"] * 100 for name, _ in COMPARATORS]
        ratio = [subset.loc[name, "median_ours_over_comparator_extra"] for name, _ in COMPARATORS]
        color = colors[0] if regime == "capacity_bound" else colors[1]
        ax_win.bar([i + offset for i in x], win, width=bar_w, label=label, color=color, edgecolor="black", linewidth=0.4)
        ax_ratio.bar([i + offset for i in x], ratio, width=bar_w, label=label, color=color, edgecolor="black", linewidth=0.4)

    tick_labels = [label for _, label in COMPARATORS]
    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(tick_labels, rotation=20, ha="right")
        ax.grid(axis="y", color="#cccccc", linewidth=0.5, alpha=0.45)
        ax.set_axisbelow(True)

    ax_win.set_title("(a) Win rate")
    ax_win.set_ylabel("Ours wins [%]")
    ax_win.set_ylim(0, 105)
    ax_win.set_yticks([0, 25, 50, 75, 100])

    ax_ratio.set_title("(b) Extra traffic ratio")
    ax_ratio.set_ylabel("Median ours / comparator")
    ax_ratio.set_ylim(0, 1.08)
    ax_ratio.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax_ratio.axhline(1.0, color="#555555", linestyle="--", linewidth=0.8)
    ax_ratio.text(4.46, 1.0, "tie", va="bottom", ha="right", color="#555555", fontsize=8)

    handles, labels = ax_win.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.05))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "e15_applicability.png"
    asset = ASSET_DIR / "e15_applicability.png"
    savefig_academic(fig, out)
    asset.write_bytes(out.read_bytes())
    print(f"wrote {out}")
    print(f"wrote {asset}")


if __name__ == "__main__":
    main()
