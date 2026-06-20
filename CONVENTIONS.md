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

**Problem 2/3** 还需返回内存分配与 spill 决策，支持两种形式：

```python
# 形式 A：三元组（推荐）
def solve(instance: ProblemInstance, config: dict) -> tuple[Schedule, dict[int, int], list[tuple[int, int]]]:
    schedule = Schedule(...)
    memory = {buf_id: offset, ...}      # BufId → physical offset
    spill_entries = [(buf_id, new_offset), ...]  # 有序，可重复 BufId
    return schedule, memory, spill_entries

# 形式 B：Schedule 上挂属性（memory / memory_layout, spill_entries / spills）
```

- 算法目录必须包含 `pyproject.toml`（UV workspace member）
- 算法目录必须包含 `README.md`（说明算法思路）
- 可选：`tests/` 子目录放算法自测

---

## 📏 Metrics 评测约定

所有算法输出的评分 **必须** 通过 `ks_core.metrics.evaluate()` 统一计算，禁止各算法自行实现指标逻辑。

### 统一入口

```python
from ks_core.metrics import evaluate

result = evaluate(instance, order, memory=None, spill_entries=None)
# result.valid      — 是否通过全部合法性校验
# result.errors     — 违规详情（空列表 = 合法）
# result.metrics    — 标准指标字典
# result.violations — len(result.errors)
```

### Canonical 指标字段（`metrics.json` / `metrics.csv`）

| 字段 | 含义 | P1 | P2 | P3 |
|------|------|----|----|-----|
| `max_L1` | L1 峰值驻留 (bytes) | ✓ | ✓ | ✓ |
| `max_UB` | UB 峰值驻留 | ✓ | ✓ | ✓ |
| `max_L0A_count` | L0A 峰值并发 buffer 数 | ✓ | ✓ | ✓ |
| `max_L0B_count` | L0B 峰值并发 buffer 数 | ✓ | ✓ | ✓ |
| `max_L0C_count` | L0C 峰值并发 buffer 数 | ✓ | ✓ | ✓ |
| `time` | 流水线总执行 cycles | ✓ | ✓ | ✓ |
| `spills` | spill 次数 | — | ✓ | ✓ |
| `extra` | 额外 DDR 流量 (bytes) | — | ✓ | ✓ |
| `schedule_len` | schedule 节点总数 | ✓ | ✓ | ✓ |
| `valid` | 合法性（实验输出专用） | ✓ | ✓ | ✓ |
| `violations` | 违规条数（实验输出专用） | ✓ | ✓ | ✓ |

`Metrics` dataclass（`total_time`, `num_spills`, …）是摘要视图，字段名映射见 `metrics_dict_to_dataclass()`。

### 工具链

```bash
# 对任意 schedule 文件验算
uv run python scripts/validate_schedule.py --case Conv_Case0 --problem 2 \
    --file path/to/schedule.txt --memory path/to/memory.txt --spill path/to/spill.txt

# 金标准回归（18 点 baseline 对照）
uv run python scripts/eval_baseline.py

# 实验跑完后自动 evaluate；若有 invalid 解则 exit 1
make run CONFIG=experiments/configs/exp00X.yaml
```

---

## 📊 实验命名约定

```
exp{NNN}_{algorithm}_{variant}
```

示例：
- `exp001_baseline01`
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
