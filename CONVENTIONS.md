# Project Conventions

本文档定义了团队协作的核心约定。所有成员必须遵守。

> AI Agent 请同时参阅 [AGENTS.md](AGENTS.md) 获取完整操作规范。

---

## 📂 目录约定

| 目录 | 用途 | 谁写 |
|------|------|------|
| `data/raw/` | 原始数据，**只读** | 初始化时固定 |
| `data/processed/` | 预处理产物，可重新生成 | 脚本自动生成 |
| `src/ks_core/` | 共享核心库 | 全员共同维护 |
| `algorithms/<name>/` | 算法实现 | 算法负责人 |
| `experiments/configs/` | 实验配置 YAML | 实验执行者 |
| `results/<exp_name>/` | 实验输出 | 自动生成 |
| `notebooks/<name>/` | Notebook (fragment-based) | 分析负责人 |
| `output/<notebook_name>/` | Notebook 缓存产物 (CSV, PNG) | cache builder |
| `paper/` | 论文源文件 | 论文负责人 |
| `scripts/` | 工具脚本 | 全员 |
| `conventions/` | 约定文档（绘图标准等） | 全员 |
| `docs/` | 参考文档 | 全员 |

---

## 📓 Notebook 约定

### Fragment 构建系统

**绝不手动编辑 `.ipynb`** — 它是构建产物，被 `.gitignore` 忽略。

Notebook 源码在 `notebooks/<name>/fragments/` 下，使用 jupytext percent 格式：

```
notebooks/01_data_exploration/
├── fragments/
│   ├── manifest.txt          # 片段排列顺序
│   ├── 01_setup.py           # jupytext percent 格式
│   ├── 02_case_overview.py
│   └── ...
└── 01_data_exploration.ipynb  ← 构建产物
```

### 构建命令

```bash
# 单个 notebook
uv run python scripts/build_notebook.py notebooks/01_data_exploration --execute

# 一键构建所有 notebook
uv run python scripts/build_all_notebooks.py --execute
```

### 内容原则

- **Notebook 是「报告」，不是「脚本」**
- 通用逻辑提取到 `src/ks_core/`，notebook 只保留调用 + 展示 + 解读
- 每个图表/数值输出后紧跟 Markdown 解读（是什么 → 分布/模式 → 核心发现）
- 表格用 Markdown/HTML 表格，**不要渲染成图片**

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
- 可选：`tests/` 子目录放算法自测

---

## 📊 实验命名约定

```
exp{NNN}_{algorithm}_{variant}
```

示例：
- `exp001_baseline_gpt`
- `exp002_greedy_v1`
- `exp003_ilp_small_cases`

---

## 🎨 绘图约定

> 🔗 完整标准见 [`docs/plotting_standards.md`](docs/plotting_standards.md)

### 核心要求

- 使用 `ks_core.plotting` 模块的标准 API（`make_figure`, `savefig_academic`）
- 字体: serif (Times New Roman)，dpi ≥ 300，白色背景
- 所有轴标签和标题使用**英文**
- 配色使用 `METHOD_PALETTE` + `MARKER_CYCLE` + `LINESTYLE_CYCLE` 确保色盲安全
- 禁止 `"jet"` colormap，禁止 legend 覆盖数据

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
  infra   — 基础设施 (CI, Makefile, etc.)
```

示例：
```
[algo] greedy_v2: add lookahead window parameter
[exp] exp003: greedy_v2 vs baseline on all cases
[core] simulator: fix pipe conflict detection
[paper] add algorithm section first draft
```

---

## 🏷️ 依赖管理约定

- **共享依赖**：添加到根 `pyproject.toml` 的 `dependencies`
- **算法专属依赖**：添加到 `algorithms/<name>/pyproject.toml`
- **添加依赖后**：运行 `uv sync` 更新 lock file 并提交 `uv.lock`
- **严禁** `pip install` — 所有依赖通过 `uv` 管理
