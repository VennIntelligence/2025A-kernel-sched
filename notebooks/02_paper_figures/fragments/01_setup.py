# %% [markdown]
# # Paper Figures
#
# This notebook is the single factory for every figure the paper includes
# (experiments **E1–E15**, mapped to claims C1/C2/C3, criterion D, and method M).
#
# All derived data is precomputed by `scripts/paper/*.py` into `results/paper/`;
# this notebook **only reads CSVs and renders** publication-grade figures — it
# never recomputes metrics. Every chart label is English. Figures are saved to
# `output/02_paper_figures/` and copied into `paper/assets/figures/` by
# `scripts/paper/sync_paper_artifacts.py`.
#
# Shared figure style and helpers live in `ks_core.plotting` (the single
# styling layer used by all notebooks).

# %%
from pathlib import Path

import pandas as pd
from IPython.display import display

from ks_core.plotting import (
    CASE_LABELS,
    CASE_ORDER,
    METHOD_PALETTE,
    ORDER_COLORS,
    ORDER_LABELS,
    add_reference_line,
    annotate_bars,
    case_label,
    compact_count,
    compact_ratio,
    get_method_style,
    grouped_offsets,
    make_figure,
    place_bar_legend,
    savefig_academic,
    setup_academic_style,
    style_bar_axes,
)

PROJECT_ROOT = Path.cwd()
RESULTS = PROJECT_ROOT / "results" / "paper"
OUTPUT_DIR = PROJECT_ROOT / "output" / "02_paper_figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
setup_academic_style()


def save_fig(fig, name):
    """Save a figure to output/02_paper_figures/ and report the path."""
    savefig_academic(fig, OUTPUT_DIR / name)
    print(f"Saved: output/02_paper_figures/{name}")
    return fig
