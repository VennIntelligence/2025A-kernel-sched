# %% [markdown]
# # 03 — Schedule Gantt Chart
#
# **目标**: 将调度结果可视化为甘特图，展示 pipeline 时间线和资源利用情况。
#
# ---
#
# ### 运行环境
#
# ```bash
# cd kernel_scheduling
# uv sync
# uv run python scripts/build_notebook.py notebooks/03_schedule_gantt --execute
# ```

# %%
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from ks_core.plotting import setup_academic_style, make_figure, savefig_academic

PROJECT_ROOT = Path.cwd()
RESULTS_DIR = PROJECT_ROOT / "results"
OUTPUT_DIR = PROJECT_ROOT / "output" / "03_schedule_gantt"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

setup_academic_style()

print(f"✅ 项目根目录: {PROJECT_ROOT}")


def save_fig(fig, name):
    """Save and display a figure following project conventions."""
    savefig_academic(fig, OUTPUT_DIR / name)
    print(f"💾 已保存: output/03_schedule_gantt/{name}")
    return fig
