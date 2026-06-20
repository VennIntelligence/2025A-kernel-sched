# %% [markdown]
# # Data & Problem
#
# This notebook establishes the empirical ground for the paper in two parts:
#
# 1. **Data inventory & validation** — a full census of the six benchmark
#    instances and the integrity checks that justify trusting them.
# 2. **Problem framing** — the three sub-problems (P1 peak residency, P2 spill
#    traffic, P3 time), the hardware capacities, and the baseline difficulty.
#
# All numbers are precomputed by `scripts/paper/inv_inventory.py` and
# `scripts/paper/prob_metrics.py` into `results/paper/`; this notebook **only
# reads CSVs** and renders. The benchmark scale table and the cache-capacity
# table here are the same data the paper reports as its benchmark and capacity
# tables. Figures use the shared `ks_core.plotting` style.

# %%
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from IPython.display import display

from ks_core.plotting import (
    CASE_LABELS,
    CASE_ORDER,
    COLORMAPS,
    METHOD_COLOR_LIST,
    METHOD_PALETTE,
    add_reference_line,
    annotate_bars,
    case_label,
    compact_count,
    grouped_offsets,
    make_figure,
    place_bar_legend,
    savefig_academic,
    setup_academic_style,
    style_bar_axes,
)

PROJECT_ROOT = Path.cwd()
RESULTS = PROJECT_ROOT / "results" / "paper"
OUTPUT_DIR = PROJECT_ROOT / "output" / "01_data_and_problem"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
setup_academic_style()


def read(name):
    """Read a precomputed CSV from results/paper/."""
    return pd.read_csv(RESULTS / name)


def order_cases(df, col="case"):
    """Sort a per-case table into the canonical benchmark order."""
    df = df.copy()
    df[col] = pd.Categorical(df[col], categories=CASE_ORDER, ordered=True)
    return df.sort_values(col).reset_index(drop=True)


def save_fig(fig, name):
    """Save a figure to output/01_data_and_problem/ and report the path."""
    savefig_academic(fig, OUTPUT_DIR / name)
    print(f"Saved: output/01_data_and_problem/{name}")
    return fig
