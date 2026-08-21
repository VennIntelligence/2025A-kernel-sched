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
├── paper/                     论文源文件
├── scripts/                   工具脚本 (含可复现的验证/研究驱动脚本)
├── tmp/                       即用即丢的一次性 Python 脚本，不承载可复现材料
└── docs/                      参考文档
```

---

## 🧹 临时脚本

- 即用即丢的一次性 Python 脚本统一放在 `tmp/` 下
- 不要把临时验证、探索、批处理脚本散落到项目正式目录
- 任何论文/文档引用的、需要长期可复现的脚本必须放入 `scripts/`，不得留在 `tmp/`

---

## 🎨 绘图规范

**完整标准见 `docs/plotting_standards.md`**，以下是必须遵守的核心规则：

### 强制使用标准 API

```python
from ks_core.plotting import setup_academic_style, make_figure, savefig_academic

fig, ax = make_figure("double_col")   # 标准尺寸 + 自动 setup_academic_style()
# ... 绑定数据 ...
savefig_academic(fig, "paper/assets/figures/xxx.png")  # dpi=300 + close=True
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

示例：`exp001_baseline01`, `exp002_greedy_v1`

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
