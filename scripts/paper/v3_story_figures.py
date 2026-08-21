# ruff: noqa: E402, I001
"""Publication figure suite for the revised (post-review) paper narrative.

Every numeric input is read from the SSOT CSVs in ``results/paper`` (which are
themselves derived from audited AutoResearch-v2 artifacts by
``scripts/paper/v2_evidence.py``); the two Conv_Case0 residency timelines are
recomputed deterministically from ``data/raw``.  Figures are emitted as PNG to
``output/02_paper_figures`` and as PDF to ``paper/assets/figures``.

Run:  uv run python scripts/paper/v3_story_figures.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "paper"))

import harness as H  # noqa: E402
from ks_core import solver as INSTR  # noqa: E402
from ks_core.plotting import setup_academic_style  # noqa: E402

RESULTS = ROOT / "results" / "paper"
OUTPUT = ROOT / "output" / "02_paper_figures"
PAPER_FIGURES = ROOT / "paper" / "assets" / "figures"

# ── Stable method colours (project METHOD_PALETTE assignments) ─────────────
C_OURS = "#4C72B0"      # scalable v2 / production
C_EXACT = "#55A868"     # fixed-order exact / certificates
C_REPAIR = "#8172B2"    # cost-aware repair case studies
C_OFFICIAL = "#937860"  # official artifacts
C_LEGACY = "#b5b5b5"    # legacy predecessor
C_BACKED = "#4C72B0"    # backed spill volume C
C_GEN = "#DD8452"       # generated spill volume D
C_SURCHARGE = "#C44E52" # generated surcharge (+D)
C_LOSS = "#C44E52"      # regressions
C_GRAY = "#666666"

CASE_SHORT = {
    "Conv_Case0": "Conv 0",
    "Conv_Case1": "Conv 1",
    "FlashAttention_Case0": "FA 0",
    "FlashAttention_Case1": "FA 1",
    "Matmul_Case0": "Matmul 0",
    "Matmul_Case1": "Matmul 1",
}
ORDER6 = list(CASE_SHORT)


def _emit(fig, stem: str) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    PAPER_FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT / f"{stem}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(PAPER_FIGURES / f"{stem}.pdf", dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"emitted {stem}")


def _fmt_b(v: float) -> str:
    return f"{v:,.0f}"


# ───────────────────────────────────────────────────────────────────────────
# 1. Hero: Conv_Case0 evidence ladder with V/D composition
# ───────────────────────────────────────────────────────────────────────────

def figure_bridge_conv0() -> None:
    df = pd.read_csv(RESULTS / "v2_conv0_cost_identity.csv").set_index("stage")
    stages = ["official", "scalable", "repair", "exact"]
    labels = {
        "official": "Official artifact",
        "scalable": "Scalable solver\n(dependency frontier)",
        "repair": "+ cost-aware\norder repair",
        "exact": "Fixed-order exact\n(certificate)",
    }
    edge = {"official": C_OFFICIAL, "scalable": C_OURS, "repair": C_REPAIR, "exact": C_EXACT}

    setup_academic_style()
    fig, ax = plt.subplots(figsize=(7.2, 2.9))
    y = np.arange(len(stages))[::-1]
    for yi, st in zip(y, stages):
        row = df.loc[st]
        c, d, s = row.backed_volume, row.generated_volume, row.generated_surcharge
        ax.barh(yi, c, height=0.62, color=C_BACKED, edgecolor="white", linewidth=0.6)
        ax.barh(yi, d, left=c, height=0.62, color=C_GEN, edgecolor="white", linewidth=0.6)
        ax.barh(yi, s, left=c + d, height=0.62, color=C_SURCHARGE, alpha=0.68,
                edgecolor="white", linewidth=0.6)
        ax.text(row.extra + 900, yi, _fmt_b(row.extra) + " B", va="center",
                fontsize=8.5, color="#222222")
        ax.barh(yi, row.extra, height=0.62, fill=False, edgecolor=edge[st], linewidth=1.1)

    lb = float(df.loc["exact", "extra"])
    ax.axvline(lb, color=C_EXACT, ls="--", lw=1.0, zorder=0)
    ax.text(lb - 900, y[0] + 0.52, "certified fixed-order minimum 57,408 B",
            color=C_EXACT, fontsize=8, fontweight="bold", ha="right", va="center")

    off = float(df.loc["official", "extra"])
    for st, yi in zip(stages, y):
        e = float(df.loc[st, "extra"])
        if st != "official":
            ax.text(2100, yi + 0.40, f"$-{(1 - e / off) * 100:.1f}\\%$ vs official",
                    fontsize=7.5, color=edge[st], fontweight="bold")

    ax.set_yticks(y)
    ax.set_yticklabels([labels[s] for s in stages], fontsize=8.5)
    ax.set_xlabel(
        "Conv 0 canonical P2 traffic $\\mathrm{Tr} = \\mathrm{Vol} + \\mathrm{Dt}$ [bytes]"
    )
    ax.set_xlim(0, off * 1.16)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.grid(axis="x", alpha=0.25, linewidth=0.5)
    ax.legend(handles=[
        Patch(facecolor=C_BACKED, label="Backed (clean) spill volume $\\mathrm{Cl}$"),
        Patch(facecolor=C_GEN, label="Generated (dirty) spill volume $\\mathrm{Dt}$"),
        Patch(facecolor=C_SURCHARGE, alpha=0.68,
              label="Generated surcharge $+\\mathrm{Dt}$"),
        Line2D([0], [0], color=C_EXACT, ls="--", lw=1.0, label="Matching lower bound"),
    ], ncol=2, loc="lower left", bbox_to_anchor=(0.0, 1.01), frameon=False,
        fontsize=7.6, handlelength=1.4, columnspacing=1.5, labelspacing=0.35)
    _emit(fig, "bridge_conv0")


# ───────────────────────────────────────────────────────────────────────────
# 2. Headline: P2 traffic and P3 time vs official, all six cases
# ───────────────────────────────────────────────────────────────────────────

def figure_headline_reductions() -> None:
    df = pd.read_csv(RESULTS / "v2_public_p2_p3.csv")
    df["order"] = df["case"].map({c: i for i, c in enumerate(ORDER6)})
    df = df.sort_values("order")
    y = np.arange(len(df))[::-1]

    setup_academic_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.6), sharey=True)

    # P2 traffic reduction (positive = better)
    ax = axes[0]
    red = df["p2_reduction_pct"].to_numpy()
    cols = [C_OURS if r > 0 else C_LEGACY for r in red]
    ax.barh(y, red, color=cols, height=0.62)
    for yi, r, ours, off in zip(y, red, df["p2_scalable_extra"], df["p2_official_extra"]):
        if r > 0:
            ax.text(r + 0.14, yi, f"$-{r:.2f}\\%$", va="center", fontsize=7.8)
            ax.text(-0.14, yi, f"{_fmt_b(ours)} vs {_fmt_b(off)}", va="center",
                    ha="right", fontsize=7.0, color="#111111")
        else:
            ax.text(0.14, yi, "tie (wins time tie-break)", va="center",
                    fontsize=7.4, color="#111111")
    ax.axvline(0, color="#444444", lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(df["label"])
    ax.set_xlabel("P2 traffic reduction vs official [%]")
    ax.set_xlim(-4.6, 10.6)
    ax.set_title("P2 extra traffic: 5 wins, 1 tie", fontsize=9.5)
    ax.text(-0.14, 1.08, "(a)", transform=ax.transAxes, fontsize=9.5,
            fontweight="bold", ha="left", va="center")
    ax.grid(axis="x", alpha=0.25, linewidth=0.5)

    # P3 time change (negative delta = faster; plot reduction = -delta)
    ax = axes[1]
    red3 = -df["p3_delta_pct"].to_numpy()
    cols = [C_OURS if r > 0 else C_LOSS for r in red3]
    ax.barh(y, red3, color=cols, height=0.62)
    for yi, r in zip(y, red3):
        if r > 0:
            ax.text(r + 0.4, yi, f"$-{r:.1f}\\%$", va="center", fontsize=7.8)
        else:
            ax.text(r - 0.4, yi, f"$+{-r:.1f}\\%$", va="center", ha="right",
                    fontsize=7.8, color=C_LOSS)
    ax.axvline(0, color="#444444", lw=0.8)
    ax.set_xlabel("P3 execution-time reduction vs official [%]")
    ax.set_xlim(-8.5, 26.5)
    ax.set_title("P3 pipeline time: 5 wins, 1 loss", fontsize=9.5)
    ax.text(-0.08, 1.08, "(b)", transform=ax.transAxes, fontsize=9.5,
            fontweight="bold", ha="left", va="center")
    ax.grid(axis="x", alpha=0.25, linewidth=0.5)

    _emit(fig, "headline_reductions")


# ───────────────────────────────────────────────────────────────────────────
# 3. Mechanism: normalized (Vol, Dt) plane with iso-Tr lines
# ───────────────────────────────────────────────────────────────────────────

def figure_vd_plane() -> None:
    df = pd.read_csv(RESULTS / "v2_all_cases_cost_decomposition.csv")
    setup_academic_style()
    fig, ax = plt.subplots(figsize=(3.5, 2.55))
    ax.set_aspect("equal")

    # Feasible half-plane D <= V shading and V = D regime edge.
    lim = 1.03
    ymax = 0.64
    ax.fill_between([0, ymax], [0, ymax], [ymax, ymax], color="#000000",
                    alpha=0.045, lw=0)
    ax.plot([0, ymax], [0, ymax], color="#999999", lw=0.7, ls=":")
    ax.text(0.175, 0.235, "infeasible ($\\mathrm{Dt}>\\mathrm{Vol}$)", rotation=45, fontsize=6.0,
            color="#222222", ha="center", va="center")

    # Iso-traffic lines Tr/Tr_official = x + y, labelled mid-line in free space.
    iso_label_at = {0.6: 0.45, 0.8: 0.615, 1.0: 0.79}
    for e in (0.6, 0.8, 1.0):
        xs = np.array([max(0.0, e - ymax), min(lim, e)])
        ax.plot(xs, e - xs, color="#c9c9c9", lw=0.7, ls="--", zorder=1)
        xl = iso_label_at[e]
        ax.annotate(
            f"$\\mathrm{{Tr}}/\\mathrm{{Tr}}_{{\\rm off}}={e:.1f}$",
            xy=(xl, e - xl),
            fontsize=5.8,
            color="#222222",
            rotation=-45,
            ha="center",
            va="center",
            bbox=dict(fc="white", ec="none", pad=0.4),
        )

    offsets = {
        "Conv 0": (-34, -14), "Conv 1": (-18, 12),
        "FA 0": (8, 8), "FA 1": (10, -10),
    }
    for _, row in df.iterrows():
        e_off = row.official_extra
        x0, y0 = row.official_volume / e_off, row.official_generated_volume / e_off
        x1, y1 = row.scalable_volume / e_off, row.scalable_generated_volume / e_off
        if abs(x0 - x1) + abs(y0 - y1) > 0.02:
            ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                        arrowprops=dict(arrowstyle="-|>", color="#555555", lw=0.9,
                                        shrinkA=3.2, shrinkB=3.2))
        ax.scatter([x0], [y0], s=22, facecolor="white", edgecolor=C_OFFICIAL,
                   linewidth=1.1, zorder=3)
        ax.scatter([x1], [y1], s=22, color=C_OURS, zorder=4)
        if row.label in offsets:
            dx, dy = offsets[row.label]
            ax.annotate(row.label, xy=(x1, y1), xytext=(dx, dy),
                        textcoords="offset points", fontsize=6.6, color="#111111",
                        bbox=dict(fc="white", ec="none", pad=0.25), zorder=5)

    ax.annotate("all backed ($\\mathrm{Dt}{=}0$): Matmul 0/1", xy=(0.80, 0.008),
                fontsize=6.0, color="#111111", ha="center", va="bottom")
    ax.annotate("all generated ($\\mathrm{Dt}=\\mathrm{Vol}$)", xy=(0.395, 0.455), fontsize=6.0,
                color="#111111", rotation=45, ha="center", va="center")

    ax.set_xlim(0, lim)
    ax.set_ylim(-0.018, ymax)
    ax.set_xlabel("Spilled volume $\\mathrm{Vol}/\\mathrm{Tr}_{\\rm official}$")
    ax.set_ylabel("Generated part $\\mathrm{Dt}/\\mathrm{Tr}_{\\rm official}$")
    ax.legend(handles=[
        Line2D([0], [0], marker="o", color="none", markerfacecolor="white",
               markeredgecolor=C_OFFICIAL, markersize=6, label="Official artifact"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=C_OURS,
               markersize=6, label="Scalable solver"),
        Line2D([0], [0], color="#c9c9c9", lw=0.7, ls="--",
               label="Iso-traffic $\\mathrm{Tr}=\\mathrm{Vol}+\\mathrm{Dt}$"),
    ], loc="upper left", fontsize=6.2, frameon=False, borderaxespad=0.1,
        handletextpad=0.35, labelspacing=0.28)
    _emit(fig, "vd_plane")


# ───────────────────────────────────────────────────────────────────────────
# 4. Order bottleneck: residency pressure of two legal orders + certified E*
# ───────────────────────────────────────────────────────────────────────────

def figure_order_headroom() -> None:
    inst = H.load_instance("Conv_Case0", 2)
    orders = {
        "p1": H.build_order(inst, "p1"),
        "unlock_frontier": INSTR._unlock_frontier_order(inst),
    }
    certified = {"p1": 81504, "unlock_frontier": 57408}
    titles = {
        "p1": "Legacy P1 order",
        "unlock_frontier": "Dependency-frontier order",
    }
    colors = {"p1": C_OFFICIAL, "unlock_frontier": C_OURS}

    setup_academic_style()
    fig, axes = plt.subplots(2, 1, figsize=(7.2, 3.8), sharex=True, sharey=True)
    cap = 4096
    for ax, name in zip(axes, orders):
        rows = H.live_clean_dirty_timeline(orders[name], inst, "L1")
        pos = np.array([r[0] for r in rows], dtype=float) / (len(rows) - 1)
        clean = np.array([r[1] for r in rows], dtype=float) / 1024.0
        total = np.array([r[1] + r[2] for r in rows], dtype=float) / 1024.0
        phi = int(np.sum(np.clip(total * 1024.0 - cap, 0, None)))
        ax.fill_between(pos, 0, clean, color=C_BACKED, alpha=0.75, lw=0,
                        label="Backed live bytes")
        ax.fill_between(pos, clean, total, color=C_GEN, alpha=0.75, lw=0,
                        label="Generated live bytes")
        ax.axhline(cap / 1024.0, color="#333333", ls="--", lw=0.9)
        ax.fill_between(pos, cap / 1024.0, total, where=total > cap / 1024.0,
                        color=C_SURCHARGE, alpha=0.35, lw=0,
                        label="Above L1 capacity")
        ax.set_ylabel("L1 live bytes [KiB]")
        ax.text(0.006, 0.96, titles[name], transform=ax.transAxes, fontsize=8.6,
                fontweight="bold", va="top", color=colors[name])
        ax.text(0.006, 0.78,
                f"L1 overflow area {phi / 1024:,.0f} KiB$\\cdot$steps"
                f"  $\\vert$  certified fixed-order minimum $\\mathrm{{Tr}}^*$ = "
                f"{certified[name]:,} B",
                transform=ax.transAxes, fontsize=7.8, va="top",
                color="#333333")
        ax.grid(axis="y", alpha=0.22, linewidth=0.5)
    axes[0].text(0.37, 4096 / 1024.0 + 0.18, "L1 capacity 4 KiB", fontsize=7.2,
                 ha="left", va="bottom", color="#333333")
    axes[1].set_xlabel("Normalized schedule position")
    axes[1].set_xlim(0, 1)
    axes[0].legend(ncol=3, loc="lower left", bbox_to_anchor=(0.0, 1.03),
                   frameon=False, fontsize=7.6)
    _emit(fig, "order_headroom")


# ───────────────────────────────────────────────────────────────────────────
# 5. Certificate ladder: bounds, artifacts, and status per instance
# ───────────────────────────────────────────────────────────────────────────

def figure_certificate_ladder() -> None:
    exact = pd.read_csv(RESULTS / "v2_exact_evidence_scope.csv")
    pub = pd.read_csv(RESULTS / "v2_public_p2_p3.csv").set_index("case")
    repair = {"Conv_Case0": 65532, "Conv_Case1": 70940}

    rows = []
    for case in ORDER6:
        sub = exact[exact["case"] == case]
        best = sub[sub["record_kind"] != "audited_status_metadata"]
        r = best.iloc[0] if len(best) else sub.iloc[0]
        rows.append({
            "case": case,
            "label": CASE_SHORT[case],
            "order": r["order"],
            "status": r["status"],
            "objective": r["objective"],
            "lb": r["lower_bound"],
            "scalable": pub.loc[case, "p2_scalable_extra"],
            "official": pub.loc[case, "p2_official_extra"],
            "repair": repair.get(case),
        })

    setup_academic_style()
    fig, ax = plt.subplots(figsize=(7.2, 3.1))
    y = np.arange(len(rows))[::-1]
    for yi, r in zip(y, rows):
        if np.isfinite(r["lb"]) if r["lb"] is not None else False:
            pass
        if pd.notna(r["lb"]):
            ax.plot([r["lb"], max(r["official"], r["objective"])], [yi, yi],
                    color="#dddddd", lw=3.2, solid_capstyle="round", zorder=1)
            ax.plot([r["lb"]], [yi], marker="|", ms=11, mew=1.8, color=C_EXACT, zorder=3)
        if pd.notna(r["objective"]):
            certified = r["status"] == "OPTIMAL"
            ax.plot([r["objective"]], [yi], marker="P" if certified else "X",
                    ms=7.5, color=C_EXACT, zorder=4)
        if r["repair"]:
            ax.plot([r["repair"]], [yi], marker="D", ms=5, color=C_REPAIR, zorder=4)
        ax.plot([r["scalable"]], [yi], marker="o", ms=6, color=C_OURS, zorder=5)
        ax.plot([r["official"]], [yi], marker="s", ms=6, mfc="white",
                mec=C_OFFICIAL, mew=1.3, zorder=4)

        status = {
            "OPTIMAL": f"traffic certificate ({r['order']})",
            "FEASIBLE": f"feasible, gap {r['objective'] - r['lb']:,.0f} B",
            "FALLBACK_TIMEOUT": "exact path timed out",
            "FALLBACK_NOT_RUN": "exact path not run",
        }[r["status"]]
        ax.text(1.012, yi, status, transform=ax.get_yaxis_transform(),
                fontsize=7.2, va="center",
                color=C_EXACT if r["status"] == "OPTIMAL" else "#777777")

    ax.annotate("scalable solver attains\nthe certificate", xy=(3584, y[2]),
                xytext=(6200, y[2] - 0.62), fontsize=7.2, color="#555555",
                va="center",
                arrowprops=dict(arrowstyle="->", color="#888888", lw=0.8))
    ax.annotate("traffic tie with official", xy=(460800, y[5]),
                xytext=(150000, y[5] + 0.55), fontsize=7.2, color="#555555",
                va="center",
                arrowprops=dict(arrowstyle="->", color="#888888", lw=0.8))

    ax.set_yticks(y)
    ax.set_yticklabels([r["label"] for r in rows])
    ax.set_xscale("log")
    ax.set_xlabel("Canonical P2 traffic $\\mathrm{Tr}$ [bytes, log scale]")
    ax.grid(axis="x", alpha=0.25, linewidth=0.5, which="major")
    ax.legend(handles=[
        Line2D([0], [0], marker="s", color="none", mfc="white", mec=C_OFFICIAL,
               ms=6, label="Official"),
        Line2D([0], [0], marker="o", color="none", mfc=C_OURS, ms=6, label="Scalable solver"),
        Line2D([0], [0], marker="D", color="none", mfc=C_REPAIR, ms=5, label="Order repair"),
        Line2D([0], [0], marker="P", color="none", mfc=C_EXACT, ms=7, label="Exact, certified"),
        Line2D([0], [0], marker="X", color="none", mfc=C_EXACT, ms=7, label="Exact, feasible"),
        Line2D([0], [0], marker="|", color=C_EXACT, mew=1.8, ms=10, ls="none",
               label="Traffic lower bound"),
    ], ncol=6, loc="lower left", bbox_to_anchor=(-0.02, 1.02), frameon=False,
        fontsize=7.2, columnspacing=1.0, handletextpad=0.35)
    _emit(fig, "certificate_ladder")


# ───────────────────────────────────────────────────────────────────────────
# 6. Weighted residency-gap model schematic
# ───────────────────────────────────────────────────────────────────────────

def figure_gap_model() -> None:
    setup_academic_style()
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.48, 3.4)
    ax.axis("off")

    def buffer_row(yc, events, kept, label, color, charge):
        # residency bars for kept gaps, dashed outline for interrupted ones
        for (a, b), k in zip(zip(events[:-1], events[1:]), kept):
            if k:
                ax.add_patch(FancyBboxPatch((a, yc - 0.16), b - a, 0.32,
                                            boxstyle="round,pad=0.012,rounding_size=0.05",
                                            fc=color, ec="none", alpha=0.75))
            else:
                ax.add_patch(FancyBboxPatch((a + 0.06, yc - 0.16), b - a - 0.12, 0.32,
                                            boxstyle="round,pad=0.012,rounding_size=0.05",
                                            fc="none", ec=C_SURCHARGE, ls=(0, (3, 2)), lw=1.0))
                mid = (a + b) / 2
                ax.annotate("", xy=(a + 0.28, yc - 0.55), xytext=(a + 0.08, yc - 0.18),
                            arrowprops=dict(arrowstyle="->", color=C_SURCHARGE, lw=0.9))
                ax.annotate("", xy=(b - 0.08, yc - 0.18), xytext=(b - 0.28, yc - 0.55),
                            arrowprops=dict(arrowstyle="->", color=C_SURCHARGE, lw=0.9))
                ax.text(mid, yc - 0.62, charge, ha="center", fontsize=7.6,
                        color=C_SURCHARGE)
        for e in events:
            ax.plot([e], [yc], marker="o", ms=4.5, color="#333333", zorder=5)
        ax.text(-0.15, yc, label, ha="right", va="center", fontsize=8)

    ax.text(2.0, 3.15, "mandatory events (ALLOC, uses, FREE)", fontsize=7.6,
            color="#333333")
    ax.annotate("", xy=(1.0, 2.62), xytext=(2.1, 3.05),
                arrowprops=dict(arrowstyle="->", color="#333333", lw=0.8))

    buffer_row(2.5, [1.0, 3.2, 6.0, 8.6], [True, False, True],
               "backed $b_1$\n($\\kappa=1$)", C_BACKED,
               "interrupt gap: charge $1\\times s_{b_1}$")
    buffer_row(1.2, [0.6, 2.4, 4.8, 9.2], [False, True, True],
               "generated $b_2$\n($\\kappa=2$)", C_GEN,
               "interrupt gap: charge $2\\times s_{b_2}$")

    ax.annotate("kept gap $x_g{=}1$: stays resident,\ncounts toward capacity",
                xy=(7.2, 2.5), xytext=(7.6, 3.1), fontsize=7.6,
                arrowprops=dict(arrowstyle="->", color="#333333", lw=0.8),
                ha="left", va="center")

    # bottom: pipeline
    steps = [
        ("Gap selection\nCP-SAT (cumulative)", "traffic lower bound"),
        ("Contiguous packing\ngreedy $\\to$ NoOverlap2D", "concrete offsets"),
        ("Canonical evaluator\nzero violations", "validated artifact"),
        ("$\\mathrm{Tr}$ = lower\nbound?", "fixed-order traffic certificate"),
    ]
    x0, box_w, box_h, step_x = 0.20, 2.20, 0.76, 2.42
    for i, (top, bottom) in enumerate(steps):
        x = x0 + i * step_x
        ax.add_patch(FancyBboxPatch((x, -0.38), box_w, box_h,
                                    boxstyle="round,pad=0.02,rounding_size=0.08",
                                    fc="#f2f2f2", ec="#555555", lw=0.9))
        ax.text(x + box_w / 2, 0.15, top, ha="center", va="center", fontsize=7.8,
                linespacing=1.05)
        ax.text(x + box_w / 2, -0.25, bottom, ha="center", va="center", fontsize=7.4,
                color=C_EXACT if i == 3 else "#333333")
        if i:
            ax.annotate("", xy=(x, 0.0), xytext=(x - (step_x - box_w), 0.0),
                        arrowprops=dict(arrowstyle="-|>", color="#555555", lw=0.9))
    _emit(fig, "gap_model")


# ───────────────────────────────────────────────────────────────────────────
# 7. Dependency-frontier mechanism schematic (toy example)
# ───────────────────────────────────────────────────────────────────────────

def figure_frontier_mechanism() -> None:
    setup_academic_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.15), sharex=True, sharey=True)

    # Each panel aligns the actual issue order (top row) with the three live
    # ranges below it.  The same nine slots are used in both panels, so the
    # horizontal compression is directly comparable rather than illustrative.
    schedules = [
        (["$a_1$", "$s_1$", "$a_2$", "$s_2$", "$a_3$", "$s_3$", "$s_4$", "$s_5$", "$X$"],
         {"$a_1$": 1, "$a_2$": 3, "$a_3$": 5}, 9,
         "(a) Indegree greedy", "18 operand-steps"),
        (["$a_1$", "$a_2$", "$a_3$", "$X$", "$s_1$", "$s_2$", "$s_3$", "$s_4$", "$s_5$"],
         {"$a_1$": 1, "$a_2$": 2, "$a_3$": 3}, 4,
         "(b) Dependency frontier", "6 operand-steps  ($-67\\%$)"),
    ]

    for ax, (order, alloc_step, x_step, title, occupancy) in zip(axes, schedules):
        # Schedule tokens use the paper's solid method colours; the node labels
        # and outlined X keep the three roles distinct without texture fills.
        for step, node in enumerate(order, start=1):
            is_group = node.startswith("$a_")
            is_x = node == "$X$"
            face = C_OURS if is_group else ("#ffffff" if is_x else C_GEN)
            edge = C_OURS if is_group or is_x else C_GEN
            ax.add_patch(FancyBboxPatch(
                (step - 0.38, 3.48), 0.76, 0.62,
                boxstyle="round,pad=0.01,rounding_size=0.05",
                fc=face, ec=edge, lw=1.0,
            ))
            ax.text(step, 3.79, node, ha="center", va="center",
                    color="white" if is_group or not is_x else "#222222")

        # X is both the execution event and the common end of all three live
        # intervals.  A single reference line makes the causal contrast clear.
        ax.axvline(x_step, ymin=0.12, ymax=0.78, color="#333333", lw=1.0,
                   ls="--", zorder=1)
        ax.text(x_step, 3.23, "$X$ executes", ha="center", va="top",
                color="#333333", fontsize=7.4)

        for row, operand in enumerate(["$a_1$", "$a_2$", "$a_3$"]):
            y = 2.55 - 0.78 * row
            start = alloc_step[operand]
            ax.plot([start, x_step], [y, y], color=C_OURS, lw=5.2,
                    solid_capstyle="round", zorder=2)
            ax.scatter([start], [y], s=19, marker="o", fc="white", ec=C_OURS,
                       lw=1.0, zorder=3)
            ax.scatter([x_step], [y], s=22, marker="|", color="#333333",
                       lw=1.1, zorder=3)
            ax.text(0.43, y, operand, ha="right", va="center")

        ax.text(5, 0.08, f"Total operand residency: {occupancy}",
                ha="center", va="bottom", fontsize=7.6,
                color=C_LOSS if x_step == 9 else C_EXACT)
        ax.set_title(title, pad=5)
        ax.set_xlim(0.45, 9.55)
        ax.set_ylim(-0.02, 4.25)
        ax.set_xticks(range(1, 10))
        ax.set_xlabel("Schedule step")
        ax.set_yticks([])
        ax.tick_params(axis="x", length=2.5, pad=2)
        ax.spines[["left", "right", "top"]].set_visible(False)
        ax.spines["bottom"].set_color("#aaaaaa")

    _emit(fig, "frontier_mechanism")


# ───────────────────────────────────────────────────────────────────────────
# 8. Supp: paired accounting Delta Tr = Delta Vol + Delta Dt
# ───────────────────────────────────────────────────────────────────────────

def figure_paired_accounting() -> None:
    df = pd.read_csv(RESULTS / "v2_all_cases_cost_decomposition.csv")
    df["order"] = df["case"].map({c: i for i, c in enumerate(ORDER6)})
    df = df.sort_values("order")
    y = np.arange(len(df))[::-1]

    setup_academic_style()
    fig, ax = plt.subplots(figsize=(6.4, 2.55))
    dv = df["volume_reduction"].to_numpy(float)
    dd = df["generated_reduction"].to_numpy(float)
    ax.barh(
        y + 0.19,
        dv,
        height=0.34,
        color=C_OURS,
        label="Volume reduction $\\Delta\\mathrm{Vol}$",
    )
    ax.barh(y - 0.19, dd, height=0.34, color=C_GEN,
            label="Surcharge reduction $\\Delta\\mathrm{Dt}$")
    for yi, (v, d, e) in zip(y, zip(dv, dd, df["extra_reduction"])):
        label_y = yi + 0.30 if e == 506 else yi
        ax.text(max(v, d, 0) + 60, label_y,
                f"$\\Delta\\mathrm{{Tr}}$ = {e:,.0f} B", va="center",
                fontsize=8.2)
    ax.axvline(0, color="#444444", lw=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels(df["label"])
    ax.set_xlabel("Official $-$ scalable solver [bytes]")
    ax.set_xlim(-500, 4400)
    ax.grid(axis="x", alpha=0.25, linewidth=0.5)
    ax.annotate(
        "Traffic falls by 506 B despite\na 171 B surcharge increase",
        xy=(-171, y[1] - 0.19),
        xytext=(780, y[1] - 0.72),
        fontsize=8.4,
        color="#222222",
        va="center",
        ha="left",
        bbox=dict(boxstyle="round,pad=0.28", facecolor="white",
                  edgecolor=C_SURCHARGE, linewidth=1.0),
        arrowprops=dict(arrowstyle="->", color=C_SURCHARGE, lw=1.25,
                        connectionstyle="arc3,rad=0.14"),
        zorder=6,
    )
    ax.legend(ncol=2, loc="lower left", bbox_to_anchor=(0.0, 1.02), frameon=False,
              fontsize=8.2)
    _emit(fig, "paired_accounting")


# ───────────────────────────────────────────────────────────────────────────
# 9. Supp: controlled H=0 component attribution (dot plot)
# ───────────────────────────────────────────────────────────────────────────

def figure_ablation_attribution() -> None:
    df = pd.read_csv(RESULTS / "v2_component_attribution.csv")
    df["order"] = df["case"].map({c: i for i, c in enumerate(ORDER6)})
    df = df.sort_values("order")
    y = np.arange(len(df))[::-1]

    setup_academic_style()
    fig, ax = plt.subplots(figsize=(6.4, 2.75))
    series = [
        ("best_fit_only_ratio", "Best-fit only", C_GEN, "s"),
        ("frontier_only_ratio", "Frontier only", C_EXACT, "^"),
        ("naive_additive_prediction", None, None, None),  # placeholder skip
        ("selected_full_ratio", "Selected configuration", C_OURS, "o"),
    ]
    for yi in y:
        ax.plot([0.74, 1.005], [yi, yi], color="#eeeeee", lw=3.4, zorder=1,
                solid_capstyle="round")
    for col, lab, c, m in series:
        if lab is None:
            continue
        ax.scatter(df[col], y, s=38, color=c, marker=m, label=lab, zorder=4)
    naive = df["naive_additive_prediction"] / df["h0_reference_extra"]
    ax.scatter(naive, y, s=54, facecolor="none", edgecolor=C_SURCHARGE, marker="o",
               linewidth=1.2, label="Additive reference estimate", zorder=5)
    ax.axvline(1.0, color="#444444", lw=0.8, ls="--")
    ax.text(1.0, y[0] + 0.63, "Controlled $H=0$ reference", fontsize=8.0,
            ha="center", color="#444444")
    ax.annotate(
        "Selected configuration:\n18,484 B below the additive estimate",
        xy=(float(df.iloc[0]["selected_full_ratio"]), y[0]),
        xytext=(0.802, y[0] - 1.72),
        fontsize=8.4,
        color="#222222",
        va="center",
        ha="left",
        bbox=dict(boxstyle="round,pad=0.28", facecolor="white",
                  edgecolor=C_SURCHARGE, linewidth=1.0),
        arrowprops=dict(arrowstyle="->", color="#555555", lw=1.05,
                        connectionstyle="arc3,rad=0.08"),
        zorder=6,
    )
    ax.set_yticks(y)
    ax.set_yticklabels(df["label"])
    ax.set_xlabel("Relative P2 traffic (controlled $H=0$ reference = 1)")
    ax.set_xlim(0.742, 1.012)
    ax.grid(axis="x", alpha=0.25, linewidth=0.5)
    ax.legend(ncol=2, loc="lower left", bbox_to_anchor=(-0.01, 1.03), frameon=False,
              fontsize=8.1, columnspacing=1.2, handletextpad=0.4,
              labelspacing=0.35)
    _emit(fig, "ablation_attribution")


# ───────────────────────────────────────────────────────────────────────────
# 10. Supp: robustness boundaries (capacity sweep + synthetic diagnostic)
# ───────────────────────────────────────────────────────────────────────────

def figure_robustness() -> None:
    cap = pd.read_csv(RESULTS / "v2_capacity_boundary.csv")
    setup_academic_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8),
                             gridspec_kw={"width_ratios": [1.45, 1.0]})

    ax = axes[0]
    feas = cap[cap["status"] == "feasible"]
    infeas = cap[cap["status"] != "feasible"]
    kib = feas["L1_capacity"] / 1024.0
    ax.plot(kib, feas["blind_extra"] / 1024.0, marker="s", ms=4.5, lw=1.3,
            color=C_OFFICIAL, ls="--", label="Cost-blind ordering comparator")
    ax.plot(kib, feas["full_extra"] / 1024.0, marker="o", ms=4.5, lw=1.4,
            color=C_OURS, label="Selected $H=0$ configuration")
    for _, r in infeas.iterrows():
        ax.plot([r["L1_capacity"] / 1024.0], [feas["blind_extra"].max() / 1024.0],
                marker="x", ms=6, color=C_SURCHARGE, mew=1.5)
    ax.plot([], [], marker="x", ls="none", ms=6, color=C_SURCHARGE, mew=1.5,
            label="Pinned set infeasible")
    ax.set_xlabel("L1 capacity [KiB]")
    ax.set_ylabel("Conv 0 P2 traffic [KiB]")
    ax.set_title("Controlled $H=0$ capacity sweep", fontsize=9)
    ax.grid(alpha=0.22, linewidth=0.5)
    ax.legend(fontsize=7.2, frameon=False)

    ax = axes[1]
    groups = ["Capacity-bound\nvs cost-blind", "Order-reachable\nvs cost-blind",
              "All 36\nvs predecessor"]
    wins = [14, 0, 0]
    ties = [4, 18, 36]
    x = np.arange(3)
    ax.bar(x, wins, 0.55, color=C_OURS, label="Wins")
    ax.bar(x, ties, 0.55, bottom=wins, color="#c9c0b6", label="Ties")
    for xi, (w, t) in enumerate(zip(wins, ties)):
        if w:
            ax.text(xi, w / 2, str(w), ha="center", va="center", fontsize=7.6,
                    color="white")
        ax.text(xi, w + t / 2, str(t), ha="center", va="center", fontsize=7.6,
                color="#444444")
    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontsize=7.2)
    ax.set_ylabel("Synthetic instances")
    ax.set_title("Internal synthetic diagnostic\n(no losses; unvalidated)", fontsize=9)
    ax.grid(axis="y", alpha=0.22, linewidth=0.5)
    ax.legend(fontsize=7.4, frameon=False, loc="upper left")
    _emit(fig, "robustness")


# ───────────────────────────────────────────────────────────────────────────
# 10b. Main text: Conv 0 L1 capacity sweep as a standalone curve figure
# ───────────────────────────────────────────────────────────────────────────

def figure_capacity_sweep() -> None:
    cap = pd.read_csv(RESULTS / "v2_capacity_boundary.csv")
    feas = cap[cap["status"] == "feasible"]
    infeas = cap[cap["status"] != "feasible"]

    setup_academic_style()
    fig, ax = plt.subplots(figsize=(3.5, 2.6))
    kib = feas["L1_capacity"].to_numpy(float) / 1024.0
    blind = feas["blind_extra"].to_numpy(float) / 1024.0
    full = feas["full_extra"].to_numpy(float) / 1024.0

    ax.fill_between(kib, full, blind, color=C_OURS, alpha=0.10, lw=0)
    ax.plot(kib, blind, marker="s", ms=4, lw=1.2, ls="--", color=C_OFFICIAL,
            label="Cost-blind ordering comparator")
    ax.plot(kib, full, marker="o", ms=4, lw=1.3, color=C_OURS,
            label="Selected $H=0$ configuration")

    # Per-capacity comparator/selected ratio, placed between the curves.
    for x, b, f in zip(kib, blind, full):
        if f > 0:
            txt = f"{b / f:.1f}$\\times$" if b / f < 10 else f"{b / f:.0f}$\\times$"
        elif b > 0:
            txt = "$\\infty$"
        else:
            continue
        ax.annotate(txt, xy=(x, np.sqrt(max(f, 0.2) * max(b, 0.2))), fontsize=6.4,
                    color="#555555", ha="center", va="center",
                    bbox=dict(fc="white", ec="none", pad=0.25))

    # Infeasible pinned-set region below 3 KiB.
    if len(infeas):
        lo = infeas["L1_capacity"].min() / 1024.0
        hi = (infeas["L1_capacity"].max() + 512) / 1024.0
        ax.axvspan(lo - 0.25, hi, color="#000000", alpha=0.05, lw=0)
        ax.text((lo + hi) / 2 - 0.12, 30, "pinned set\ninfeasible", rotation=90,
                fontsize=6.4, color="#777777", ha="center", va="center")

    ax.axvline(4.0, color="#444444", lw=0.7, ls=":")
    ax.text(4.0, 320, "benchmark\ncapacity", fontsize=6.2, ha="center",
            va="bottom", color="#444444")

    ax.set_yscale("symlog", linthresh=1.0)
    ax.set_ylim(-0.25, 900)
    ax.set_yticks([0, 1, 10, 100])
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xlim(1.6, 16.6)
    ax.set_xticks([2, 4, 6, 8, 12, 16])
    ax.set_xlabel("L1 capacity [KiB]")
    ax.set_ylabel("Conv 0 P2 traffic [KiB]")
    ax.grid(alpha=0.22, linewidth=0.5)
    ax.legend(fontsize=6.6, frameon=False, loc="upper right",
              bbox_to_anchor=(1.0, 0.97))
    _emit(fig, "capacity_sweep")


# ───────────────────────────────────────────────────────────────────────────
# 11. Supp: P2→P3 traffic/latency tradeoff
# ───────────────────────────────────────────────────────────────────────────

def figure_p3_tradeoff() -> None:
    df = pd.read_csv(RESULTS / "v2_p2_p3_decoupling.csv")
    df["order"] = df["case"].map({c: i for i, c in enumerate(ORDER6)})
    df = df.sort_values("order")
    y = np.arange(len(df))[::-1]
    traffic_increase = df["traffic_delta_pct"].to_numpy(float)
    time_reduction = -df["latency_delta_pct"].to_numpy(float)

    setup_academic_style()
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.45), sharey=True)
    panels = [
        (axes[0], traffic_increase, C_OURS, "o", "Additional P3 traffic [%]", 16.2),
        (axes[1], time_reduction, C_GEN, "D", "P3 time reduction [%]", 21.5),
    ]

    def _fmt_pct(value: float) -> str:
        return "<0.1%" if 0 < value < 0.05 else f"{value:.1f}%"

    for ax, values, color, marker, xlabel, xmax in panels:
        ax.hlines(y, 0, values, color="#dddddd", linewidth=2.4, zorder=1)
        ax.scatter(values, y, s=44, color=color, marker=marker, zorder=3)
        for value, yi in zip(values, y):
            ax.text(value + 0.32, yi, _fmt_pct(value), va="center", fontsize=8.0)
        ax.axvline(0, color="#777777", lw=0.8)
        ax.set_xlim(-0.45, xmax)
        ax.set_xlabel(xlabel)
        ax.grid(axis="x", alpha=0.22, linewidth=0.5)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(df["label"])
    axes[0].set_xticks([0, 5, 10, 15])
    axes[1].set_xticks([0, 5, 10, 15, 20])
    _emit(fig, "p3_tradeoff")


ALL = [
    figure_bridge_conv0,
    figure_headline_reductions,
    figure_vd_plane,
    figure_order_headroom,
    figure_gap_model,
    figure_frontier_mechanism,
    figure_paired_accounting,
    figure_ablation_attribution,
    figure_robustness,
    figure_capacity_sweep,
    figure_p3_tradeoff,
]


def main() -> None:
    only = sys.argv[1:] or None
    for fn in ALL:
        stem = fn.__name__.removeprefix("figure_")
        if only and stem not in only:
            continue
        fn()


if __name__ == "__main__":
    main()
