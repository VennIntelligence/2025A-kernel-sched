# AGENTS.md — AI Agent 操作规范

> 本文档是 AI 编程助手在此项目中工作时必须遵守的规则。
> 人类用户请阅读 [README.md](README.md)。

---

## 📂 项目结构

```
kernel_scheduling/
├── data/raw/                  原始数据 (JSON/CSV DAG)，只读
├── data/processed/            预处理产物，可重新生成
├── src/ks_core/               共享核心库
│   ├── graph.py               DAG 解析
│   ├── io.py                  数据 I/O
│   ├── types.py               类型定义 (ProblemInstance, Schedule)
│   ├── metrics.py             评估指标
│   ├── plotting.py            CVPR 学术绘图标准
│   └── notebook_cache.py      Notebook 缓存基础设施
├── algorithms/<name>/         算法实现 (各自独立 pyproject.toml)
├── experiments/               实验配置 (YAML) 与运行器
├── results/<exp_name>/        实验输出产物
├── notebooks/<name>/          Notebook (fragment-based)
│   └── fragments/             .py 片段 + manifest.txt
├── output/<notebook_name>/    Notebook 缓存产物 (CSV, PNG)
├── paper/                     论文源文件
├── scripts/                   工具脚本
├── conventions/               约定文档
└── docs/                      参考文档
```

---

## 📓 Notebook 规范

### Fragment 构建系统

**绝不手动编辑 `.ipynb`** — 它是构建产物。

每个 notebook 的源码在 `notebooks/<name>/fragments/` 下：

```
notebooks/01_data_exploration/
├── fragments/
│   ├── manifest.txt          # 片段排列顺序
│   ├── 01_setup.py           # jupytext percent 格式
│   ├── 02_case_overview.py
│   └── ...
└── 01_data_exploration.ipynb  ← 构建产物，.gitignore 忽略
```

### 片段格式

每个 `.py` 文件使用 jupytext percent 格式的 cell 标记：

```python
# %% [markdown]
# ## 标题
# 说明文字

# %%
import numpy as np
# ... code ...
```

### 构建命令

```bash
# 单个 notebook — 仅构建（拼接片段 → .ipynb，不执行）
uv run python scripts/build_notebook.py notebooks/01_data_exploration

# 单个 notebook — 构建 + 执行（推荐）
uv run python scripts/build_notebook.py notebooks/01_data_exploration --execute

# 一键构建所有 notebook
uv run python scripts/build_all_notebooks.py --execute
```

**必须使用 `--execute`**: 构建后的 notebook 应该是**完全执行好的状态** —
用户打开即可看到全部文字输出和图片。

### Notebook 内容展示原则

**Notebook 是「报告」，不是「脚本」。**

1. **以数据和核心发现为中心**
   - 每个分析片段开头用 Markdown cell 说明**目的和结论**
   - Cell 输出应该是图表、关键指标、或简洁的汇总信息
   - 不要在 Notebook 里堆砌数据清洗/IO/解析的裸代码

2. **隐藏实现细节，只露调用层**
   - 数据加载、解析、转换等通用逻辑应提取到 `src/ks_core/` 中
   - Notebook cell 只保留**一行调用 + 结果展示**
   - 目标：片段 `.py` 尽量 < 30 行，大部分是 Markdown + 调用 + 绘图

3. **图片与表格各司其职**
   - 空间分布、时间趋势、DAG 结构等视觉证据优先使用图片
   - 决策表、方法对照表用 Markdown/HTML 表格，**不要把表格渲染成图片**

4. **图片显示：一图只显示一次**
   - 正确模式 — `save_fig` 标准实现:
     ```python
     def save_fig(fig, name):
         savefig_academic(fig, OUTPUT_DIR / name)  # 默认 close=True
         print(f"💾 已保存: output/{name}")
         return fig  # 已关闭但 _repr_png_() 仍可用
     ```
   - **三个禁止**: ① 绝不传 `close=False`；② 绝不在 `save_fig` 后调 `plt.show()`；③ viz 函数内绝不调 `plt.show()`

5. **每个数据输出必须附带解读**
   - 每个图表、表格、关键指标输出后，**紧跟一个 Markdown cell** 说明：
     1. **这张图/表是什么** — 展示了什么数据
     2. **数据分布/模式** — 读者应注意的特征
     3. **核心发现** — 1–2 句话总结关键结论

### 操作规则

1. **新增分析** → 在 `fragments/` 内新建 `NN_name.py`，更新 `manifest.txt`
2. **修改分析** → 编辑 `fragments/` 内对应 `.py` 片段，重新构建
3. **绝不手动编辑 `.ipynb`**

---

## 🎨 绘图规范

**完整标准见 `docs/plotting_standards.md`**，以下是必须遵守的核心规则：

### 强制使用标准 API

```python
from ks_core.plotting import setup_academic_style, make_figure, savefig_academic

fig, ax = make_figure("double_col")   # 标准尺寸 + 自动 setup_academic_style()
# ... 绑定数据 ...
savefig_academic(fig, "output/xxx.png")  # dpi=300 + close=True
```

### 禁止项

- ❌ `font.family: sans-serif / Arial` → ✅ serif / Times New Roman
- ❌ 在函数里写 `fontsize=12` → ✅ 统一由 rcParams 控制
- ❌ `savefig(dpi=180)` → ✅ `savefig(dpi=300)`
- ❌ 轴标签写中文 → ✅ 图表内容全英文
- ❌ `plt.show()` 在脚本里 → ✅ 只 `savefig` + `plt.close`
- ❌ legend 覆盖数据 → ✅ legend 放图外或空白角落
- ❌ `"jet"` colormap → ✅ `"viridis"` / `"inferno"`
- ❌ 只用颜色区分 → ✅ 同时用 marker + linestyle

---

## 🧪 算法接口约定

每个算法 **必须** 暴露以下接口：

```python
# algorithms/<name>/solve.py
from ks_core.types import ProblemInstance, Schedule

def solve(instance: ProblemInstance, config: dict) -> Schedule:
    ...
```

- 算法目录必须包含 `pyproject.toml`（UV workspace member）
- 算法目录必须包含 `README.md`（说明算法思路）

---

## 📊 实验命名约定

```
exp{NNN}_{algorithm}_{variant}
```

示例：`exp001_baseline_gpt`, `exp002_greedy_v1`

---

## 🔧 依赖管理

- **共享依赖**: 添加到根 `pyproject.toml`
- **算法专属依赖**: 添加到 `algorithms/<name>/pyproject.toml`
- **添加依赖后**: 运行 `uv sync` 更新 lock file
- **严禁** `pip install` — 所有依赖通过 `uv` 管理

---

## 📝 Git 提交约定

```
[scope] 简要描述

scope 可选值:
  algo    — 算法代码
  core    — ks_core 核心库
  exp     — 实验配置/运行
  data    — 数据处理
  paper   — 论文
  script  — 工具脚本
  nb      — notebook
  infra   — 基础设施
```
