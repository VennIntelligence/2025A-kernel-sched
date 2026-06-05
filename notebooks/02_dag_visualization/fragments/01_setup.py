# %% [markdown]
# # 02 — DAG Visualization
#
# **目标**: 可视化 kernel scheduling DAG 的拓扑结构，理解节点依赖关系和图的整体形态。
#
# ---
#
# ### 运行环境
#
# ```bash
# cd kernel_scheduling
# uv sync
# uv run python scripts/build_notebook.py notebooks/02_dag_visualization --execute
# ```

# %%
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

from ks_core.graph import load_json, list_cases
from ks_core.plotting import setup_academic_style, make_figure, savefig_academic

PROJECT_ROOT = Path.cwd()
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "json"
OUTPUT_DIR = PROJECT_ROOT / "output" / "02_dag_visualization"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

setup_academic_style()

cases = list_cases(DATA_DIR, fmt="json")
print(f"✅ 项目根目录: {PROJECT_ROOT}")
print(f"✅ 可用 cases: {cases}")


def save_fig(fig, name):
    """Save and display a figure following project conventions."""
    savefig_academic(fig, OUTPUT_DIR / name)
    print(f"💾 已保存: output/02_dag_visualization/{name}")
    return fig
