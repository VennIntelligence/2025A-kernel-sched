# 🧠 Kernel Scheduling — AutoResearch

> 2025A 通用神经网络处理器下的核内调度问题  
> Multi-algorithm, multi-round optimization research framework

---

## Quick Start

```bash
# 1. Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone & setup
cd kernel_scheduling
make setup          # or: uv sync --all-extras

# 3. Run an experiment
make run CONFIG=experiments/configs/exp001_baseline_gpt.yaml

# 4. Validate results
make validate

# 5. Compare experiments
make compare

# 6. Launch notebooks
make notebook
```

---

## 📁 Project Structure

```
kernel_scheduling/
├── data/                   Raw & processed data
│   ├── raw/json/           Original JSON (DAG nodes + edges)
│   └── raw/csv/            Original CSV format
├── docs/                   Problem statement & references
├── src/ks_core/            Shared core library
├── algorithms/             Algorithm implementations
│   └── baseline_gpt/      GPT first-round baseline
├── experiments/            Experiment configs & runner
├── results/                Experiment outputs
├── notebooks/              Visualization & analysis
├── paper/                  Paper source files
├── scripts/                Utility scripts
├── conventions/            Team conventions & style guides
└── output/                 Final submission artifacts
```

→ Full structure details: see [CONVENTIONS.md](CONVENTIONS.md)

---

## 📖 Key Documents

| Document | Description |
|----------|-------------|
| [CONVENTIONS.md](CONVENTIONS.md) | 团队协作约定（目录、接口、命名、Git、绘图） |
| [docs/problem.md](docs/problem.md) | 赛题描述（Markdown 权威版本） |
| [algorithms/baseline_gpt/README.md](algorithms/baseline_gpt/README.md) | Baseline 算法说明 & benchmark 数据 |

---

## 🧪 How to Add a New Algorithm

```bash
# 1. Create algorithm directory
mkdir -p algorithms/my_algo

# 2. Create required files
cat > algorithms/my_algo/pyproject.toml << 'EOF'
[project]
name = "ks-my-algo"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["ks-core"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
EOF

# 3. Implement solve.py with the standard interface
cat > algorithms/my_algo/solve.py << 'EOF'
from ks_core.types import ProblemInstance, Schedule

def solve(instance: ProblemInstance, config: dict) -> Schedule:
    # Your algorithm here
    order = [n.id for n in instance.nodes]  # placeholder
    return Schedule(
        case_name=instance.case_name,
        problem_id=instance.problem_id,
        algorithm="my_algo",
        order=order,
    )
EOF

# 4. Sync dependencies
uv sync

# 5. Create experiment config
cp experiments/configs/exp001_baseline_gpt.yaml \
   experiments/configs/exp002_my_algo.yaml
# Edit the config to use your algorithm name

# 6. Run
make run CONFIG=experiments/configs/exp002_my_algo.yaml
```

---

## 🔬 How to Run Experiments

### Single experiment

```bash
uv run python experiments/run_experiment.py experiments/configs/exp001_baseline_gpt.yaml
```

### Experiment config format

```yaml
experiment:
  name: "exp002_greedy_v1"
  author: "alice"
  description: "Greedy with topological sort"

algorithm:
  name: "greedy_v1"
  params:
    eviction_policy: "belady_cost"

cases: [Conv_Case0, Conv_Case1, ...]
problems: [1, 2, 3]

output:
  dir: "results/exp002_greedy_v1"
  save_schedules: true
```

### Compare all results

```bash
make compare
# or
uv run python scripts/compare_results.py
```

---

## 📊 Notebooks

| Notebook | Purpose |
|----------|---------|
| `01_data_exploration.ipynb` | 数据结构探索、DAG 统计 |
| `02_dag_visualization.ipynb` | DAG 拓扑可视化 |
| `03_schedule_gantt.ipynb` | 调度甘特图（pipeline 时间线） |
| `04_benchmark_comparison.ipynb` | 跨算法 benchmark 对比 |

```bash
make notebook   # Launch Jupyter Lab
```

---

## 📝 Paper

Paper source files are in [`paper/`](paper/). Build with:

```bash
cd paper && ./build.sh
```

Figures are auto-exported from notebooks to `paper/figures/`.

---

## 🔧 Available Commands

```bash
make help       # Show all commands
make setup      # First-time setup
make sync       # Sync dependencies
make lint       # Run linter
make test       # Run tests
make run        # Run experiment (CONFIG=...)
make validate   # Validate schedules
make compare    # Compare results
make notebook   # Launch Jupyter
make clean      # Clean generated files
```

---

## 📐 Conventions

See [CONVENTIONS.md](CONVENTIONS.md) for full team conventions, including:
- Algorithm interface contract
- Experiment naming scheme
- Git commit format
- Plotting standards

Additional style guides in [`conventions/`](conventions/):
- CVPR figure standards *(to be added)*
- LaTeX style guide *(to be added)*

---

## 🗂️ Data Overview

6 cases across 3 kernel types:

| Kernel | Case 0 (Nodes) | Case 1 (Nodes) |
|--------|----------------|----------------|
| Conv | 2,580 | 36,086 |
| FlashAttention | 1,716 | 6,952 |
| Matmul | 4,160 | 30,976 |

3 problem variants:
- **P1**: Instruction scheduling (minimize total time, no spill)
- **P2**: Scheduling + memory management (allow spill/reload)
- **P3**: Optimized scheduling + memory (minimize combined cost)
