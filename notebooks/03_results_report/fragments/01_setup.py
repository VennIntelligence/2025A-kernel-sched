# %% [markdown]
# # Results Report
#
# This notebook is the narrative entry point for the paper's results. It ties
# the headline numbers and figures to the evidence layers — claims **C1/C2/C3**,
# criterion **D**, and method **M** — and states each conclusion precisely
# (no overclaiming).
#
# All numbers come from `results/paper/*.csv`; the paper figures (`e*`) are
# embedded from `output/02_paper_figures/`; two explanatory figures (`x2`, `x3`)
# are rendered inline from their CSVs and are **notebook-only — not paper
# figures**. Markdown is English; chart labels are English.

# %%
from pathlib import Path

import numpy as np
import pandas as pd
from IPython.display import Image, Markdown, display

from ks_core.plotting import (
    METHOD_PALETTE,
    add_reference_line,
    make_figure,
    savefig_academic,
    setup_academic_style,
)

PROJECT_ROOT = Path.cwd()
RESULTS = PROJECT_ROOT / "results" / "paper"
PAPER_FIGURES = PROJECT_ROOT / "output" / "02_paper_figures"
OUTPUT_DIR = PROJECT_ROOT / "output" / "03_results_report"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

setup_academic_style()
pd.set_option("display.max_columns", 80)
pd.set_option("display.width", 160)

CASE_ORDER = [
    "Conv_Case0",
    "Conv_Case1",
    "FlashAttention_Case0",
    "FlashAttention_Case1",
    "Matmul_Case0",
    "Matmul_Case1",
]

# Result tables (paper SSOT).
headline = pd.read_csv(RESULTS / "e1_headline.csv")
e2_cv = pd.read_csv(RESULTS / "e2_victim_cv.csv")
e2_order = pd.read_csv(RESULTS / "e2_victim_order.csv")
e6_corr = pd.read_csv(RESULTS / "e6_corr.csv")
e7 = pd.read_csv(RESULTS / "e7_misalign.csv")
e8 = pd.read_csv(RESULTS / "e8_prefetch.csv")
e9 = pd.read_csv(RESULTS / "e9_working_set.csv")
e10 = pd.read_csv(RESULTS / "e10_portfolio.csv")
e11_ablation = pd.read_csv(RESULTS / "e11_synth_ablation.csv")
e11_orders = pd.read_csv(RESULTS / "e11_synth_orders.csv")

# Problem-framing tables (read, not recomputed).
case_summary = pd.read_csv(RESULTS / "inv_case_summary.csv")
problem_overview = pd.read_csv(RESULTS / "prob_overview.csv")
capacities = pd.read_csv(RESULTS / "prob_capacities.csv")

# Explanatory (notebook-only) figure data.
x2_timeline = pd.read_csv(RESULTS / "x2_clean_dirty_timeline.csv")
x2_split = pd.read_csv(RESULTS / "x2_cost_split.csv")
x3_traj = pd.read_csv(RESULTS / "x3_portfolio_traj.csv", dtype={"iter": str})


def note(text: str) -> None:
    """Render a one-line takeaway callout."""
    display(Markdown(f"> **Takeaway.** {text}"))


def show_png(name: str, width: int = 900) -> None:
    """Embed a paper figure from output/02_paper_figures/."""
    path = PAPER_FIGURES / name
    if path.exists():
        display(Image(filename=str(path), width=width))
    else:
        display(Markdown(f"`Missing figure: {path}` — build 02_paper_figures first."))


def save_fig(fig, name):
    """Save an inline explanatory figure to output/03_results_report/."""
    savefig_academic(fig, OUTPUT_DIR / name)
    print(f"Saved: output/03_results_report/{name}")
    return fig


def ordered_cases(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["case"] = pd.Categorical(out["case"], categories=CASE_ORDER, ordered=True)
    return out.sort_values(["case"])
