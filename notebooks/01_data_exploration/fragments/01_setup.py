# %% [markdown]
# # 01 — Data Exploration
#
# **目标**: 探索 kernel scheduling DAG 数据的结构和统计特征。
#
# 本 Notebook 回答以下问题：
# - 6 个 case 的规模（节点数、边数、计算节点数、内存分配数）
# - 各 case 的操作类型分布
# - 数据质量确认（是否所有 case 都能正确解析）
#
# ---
#
# ### 运行环境
#
# ```bash
# cd kernel_scheduling
# uv sync
#
# # 构建 + 执行本 notebook：
# uv run python scripts/build_notebook.py notebooks/01_data_exploration --execute
# ```

# %%
from pathlib import Path

import pandas as pd

from ks_core.graph import load_json, list_cases
from ks_core.plotting import setup_academic_style

PROJECT_ROOT = Path.cwd()
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "json"

setup_academic_style()

cases = list_cases(DATA_DIR, fmt="json")
print(f"✅ 项目根目录: {PROJECT_ROOT}")
print(f"✅ 数据目录: {DATA_DIR}")
print(f"✅ 可用 cases: {cases}")
