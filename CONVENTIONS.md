# Project Conventions

本文档定义了团队协作的核心约定。所有成员必须遵守。

> 如有新约定从其他仓库引入（如 CVPR 绘图标准），请放入 `conventions/` 目录并在此文档中添加链接。

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
| `notebooks/` | 可视化 & 分析 | 分析负责人 |
| `paper/` | 论文源文件 | 论文负责人 |
| `scripts/` | 工具脚本 | 全员 |
| `output/` | 最终提交物 | 提交前统一生成 |
| `conventions/` | 约定文档（绘图标准等） | 全员 |

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
- `exp010_rl_dqn_pretrain`

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

## 🎨 绘图约定

> 🔗 CVPR / 学术绘图标准请参见 [`conventions/`](conventions/) 目录中的具体文档。

### 基本要求

- 所有图片使用矢量格式（PDF / SVG）导出
- 字体大小 ≥ 8pt（打印后可读）
- 配色方案统一（推荐使用 seaborn 默认 palette 或自定义 palette）
- 图例 (legend) 不遮挡数据
- 坐标轴必须有标签和单位

### Notebook 导出

- 图片统一导出到 `paper/figures/`
- 命名格式：`fig_{section}_{description}.pdf`
- 示例：`fig_exp_benchmark_comparison.pdf`

---

## 🔗 外部约定文档

将从其他仓库引入的约定放在 `conventions/` 目录：

| 文件 | 说明 |
|------|------|
| `conventions/cvpr_figures.md` | CVPR 绘图标准 *(待添加)* |
| `conventions/latex_style.md` | LaTeX 排版约定 *(待添加)* |

---

## 🏷️ 依赖管理约定

- **共享依赖**：添加到根 `pyproject.toml` 的 `dependencies`
- **算法专属依赖**：添加到 `algorithms/<name>/pyproject.toml`
- **添加依赖后**：运行 `uv sync` 更新 lock file 并提交 `uv.lock`
- **严禁** `pip install` — 所有依赖通过 `uv` 管理
