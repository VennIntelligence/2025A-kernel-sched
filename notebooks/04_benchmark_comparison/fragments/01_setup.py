# %% [markdown]
# # 04 — Benchmark Comparison
#
# **目标**: 跨算法 benchmark 对比，评估不同调度策略的性能。
#
# ---
#
# ### 运行环境
#
# ```bash
# cd kernel_scheduling
# uv sync
# uv run python scripts/build_notebook.py notebooks/04_benchmark_comparison --execute
# ```

# %%
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from ks_core.plotting import (
    setup_academic_style,
    make_figure,
    savefig_academic,
    get_method_style,
)

PROJECT_ROOT = Path.cwd()
RESULTS_DIR = PROJECT_ROOT / "results"
OUTPUT_DIR = PROJECT_ROOT / "output" / "04_benchmark_comparison"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

setup_academic_style()

print(f"✅ 项目根目录: {PROJECT_ROOT}")


def save_fig(fig, name):
    """Save and display a figure following project conventions."""
    savefig_academic(fig, OUTPUT_DIR / name)
    print(f"💾 已保存: output/04_benchmark_comparison/{name}")
    return fig
