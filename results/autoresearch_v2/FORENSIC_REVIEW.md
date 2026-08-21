# 审稿取证与文件定位（只读核验）

核验日期：2026-07-11。本取证任务未修改正式代码；本文件是唯一由本任务新增的报告。取证开始时 `src/ks_core/solver.py` 未修改，但报告完成时该文件已被并发任务改动；下述 solver 行号与结论均基于取证开始时读到的版本。

## 1. 文件定位结论

用户转述中声称存在的三个审稿产物，在整个 `/Users/ujs` 下搜索、当前仓库已跟踪文件及全部 Git 历史中均不存在：

- `/Users/ujs/mycode/kernal_scheduling/scratchpad/ADVERSARIAL_REVIEW.md`：不存在；当前仓库连 `scratchpad/` 目录也没有。
- `/Users/ujs/mycode/kernal_scheduling/scratchpad/e5_check/`：不存在。
- `/Users/ujs/mycode/kernal_scheduling/scratchpad/e5_check/alt2_overflow_decomposition.png`：不存在。

机器上唯一名为 `scratchpad` 的普通目录是：

- `/Users/ujs/mycode/thermal_lift/scratchpad/`，其中只有 `make_noise_goldens.py`，与本仓库无关。
- `/Users/ujs/mycode/thermal_lift/.claude/worktrees/agent-abd5a3f7eadc0805c/scratchpad/`，同样只有 `make_noise_goldens.py`。

实际相关文件如下：

- 英文算法：`/Users/ujs/mycode/kernal_scheduling/paper/src/en_conf/sections/algorithm.tex`
- 中文算法：`/Users/ujs/mycode/kernal_scheduling/paper/src/zh_conf/sections/algorithm.tex`
- 英文实验：`/Users/ujs/mycode/kernal_scheduling/paper/src/en_conf/sections/experiments.tex`
- 中文实验：`/Users/ujs/mycode/kernal_scheduling/paper/src/zh_conf/sections/experiments.tex`
- Notebook 中的 negative-example 原文：`/Users/ujs/mycode/kernal_scheduling/notebooks/02_paper_figures/fragments/06_e5_peak_residency.py:79`
- E5 数据生成器：`/Users/ujs/mycode/kernal_scheduling/scripts/paper/e5_residency.py`
- E5 两份数据：
  - `/Users/ujs/mycode/kernal_scheduling/results/paper/e5_residency_id_raw.csv`
  - `/Users/ujs/mycode/kernal_scheduling/results/paper/e5_residency_baseline.csv`
- E5 当前论文图：`/Users/ujs/mycode/kernal_scheduling/paper/assets/figures/e5_peak_residency.png`
- 概念图 e0：`/Users/ujs/mycode/kernal_scheduling/paper/assets/figures/e0_concept.pdf`
- 用户会话开始前已修改的网页文案：`/Users/ujs/mycode/kernal_scheduling/web/src/lib/i18n.ts`
- 当前 solver：`/Users/ujs/mycode/kernal_scheduling/src/ks_core/solver.py`
- victim/order 全表：`/Users/ujs/mycode/kernal_scheduling/results/paper/e2_victim_order.csv`
- 强 baseline 主表：`/Users/ujs/mycode/kernal_scheduling/results/paper/e12_baselines.csv`
- 外部 baseline01 指标：`/Users/ujs/mycode/kernal_scheduling/results/exp001_baseline01/metrics.json`

## 2. E5 数字复核

### 2.1 峰值与占比：用户转述正确

数据源直接给出：

- `id_raw` 峰值在 `pos=2226`：clean=2,304，dirty=12,288，总计=14,592（`e5_residency_id_raw.csv:2228`）。dirty 占比 `12288/14592 = 84.2105%`。
- `baseline` 峰值在 `pos=2285`：clean=576，dirty=6,912，总计=7,488（`e5_residency_baseline.csv:2287`）。dirty 占比 `6912/7488 = 92.3077%`。

因此 Notebook 的标签（`06_e5_peak_residency.py:15-16`）有两种不同口径：

- 按 dirty **绝对字节数**，`id_raw` 的 12,288 的确高于 baseline 的 6,912，`Dirty-heavy` 字面上勉强成立。
- 按论文反复声称的 clean/dirty **composition/fraction**，标签反了：baseline 更 dirty-heavy（92.3% > 84.2%）。

概念图承诺“similar capacity pressure”（`paper/src/en_conf/sections/introduction.tex:6-9`），E5 两序的峰值却相差 1.95 倍。全曲线累计 L1 overflow area 更相差 5.19 倍：

| order | peak | 全曲线 overflow area | max overflow |
|---|---:|---:|---:|
| id_raw | 14,592 | 5,046,535 | 10,496 |
| baseline | 7,488 | 971,486 | 3,392 |

所以 E5 不能在控制总压力后识别 composition 的因果作用。

### 2.2 转述中的 79.4% / 45.3% 可以复现，但 alt2 图片本身不存在

若逐时刻定义：

```text
overflow = max(live_total - 4096, 0)
clean_cover = min(overflow, live_clean)
forced_dirty = overflow - clean_cover
forced_dirty_share = sum(forced_dirty) / sum(overflow)
```

则全曲线结果恰为：

- id_raw：79.3539%
- baseline：45.2864%

这基本确定了转述中 `alt2` 数字的来源。注意 Notebook 实图只显示 `pos>=1650`（`06_e5_peak_residency.py:23,36`）；若只对显示窗口计算，数值是 82.2582% 和 45.5426%，不是 79.4% 和 45.3%。而且这个量是逻辑 live-set 的“潜在 clean cover”，不是 allocator 实际选出的 spill composition。

### 2.3 “溢出代价 212,956 vs 74,076”混用了 victim policy

`results/paper/e2_victim_order.csv` 给出：

- id_raw + 论文默认 `dist_size_cost` = 212,956（第 10 行）。
- baseline + 同一个 `dist_size_cost` = 88,768（第 18 行）。
- baseline + `cost_then_dist` 或 `cheap_first` = 74,076（第 19-20 行）。
- 外部 baseline01 自带完整 plan = 73,500（`results/exp001_baseline01/metrics.json:19-32`）。

因此 212,956 与 74,076 都是真实产物中的数，但不是“同一 victim policy、只换 order”的配对值。若 E5 要表达 same-engine/order-only 证据，应配对 212,956 vs 88,768；若每序各取 victim-policy oracle，必须明确写明并对两边都做同样搜索。

## 3. 论文主张与实现/数据的具体不一致

### A. 最严重：公开六例上的收益来自 spill volume，而不是 clean/dirty composition

由 evaluator 定义，令 `V = clean_bytes + dirty_bytes/2` 为实际被 spill 的无权重字节体积，则 `extra = V + dirty_volume`。用 `e12_baselines.csv` 的 P2 行比较 proposed portfolio 与最强 clean/dirty-blind `cp_free_first`：

| case | ours extra | blind extra | blind/ours extra | ours V | blind V | blind/ours V | ours/blind dirty-cost share |
|---|---:|---:|---:|---:|---:|---:|---:|
| Conv_Case0 | 88,044 | 212,956 | 2.4187 | 44,022 | 113,678 | 2.5823 | 100.0% / 93.2% |
| Conv_Case1 | 72,520 | 73,348 | 1.0114 | 69,616 | 70,434 | 1.0118 | 8.0% / 7.9% |
| FA_Case0 | 3,904 | 3,904 | 1.0000 | 1,952 | 1,952 | 1.0000 | 100% / 100% |
| FA_Case1 | 32,920 | 33,152 | 1.0070 | 20,684 | 20,800 | 1.0056 | 74.3% / 74.5% |
| Matmul_Case0 | 34,688 | 34,944 | 1.0074 | 34,688 | 34,944 | 1.0074 | 0% / 0% |
| Matmul_Case1 | 460,800 | 460,800 | 1.0000 | 460,800 | 460,800 | 1.0000 | 0% / 0% |

直接结论：

1. 五个 case 的收益在约 0--1.1%，两个完全持平。
2. 唯一大收益 Conv_Case0 中，ours 的实际 spill **反而 100% dirty**，blind 还有 clean spill；composition 对 ours 不利。extra 比值 2.42 倍完全由 spill volume 的 2.58 倍差异解释。
3. Matmul_Case0 两边 100% clean，不可能用 clean/dirty shaping 解释 0.7% 差异。
4. FA_Case0 两边 100% dirty且完全持平。

这与正文 “clean reserve is decisive”（`paper/src/en_conf/sections/experiments.tex:156-163`）以及补充材料把 Conv1/Matmul0 胜利归因于更多 clean reserve（`paper/src/en_supp/sections/solution_walkthrough.tex:149-167`；中文版 `zh_supp/...:68-72`）不一致。

另一个简单的量纲检查：若 spill volume 固定，clean/dirty 的单位代价只在 1--2 之间，纯 composition 最多带来 2 倍收益。论文的 2.4--26 倍主张不可能主要由这个 2 倍非对称单独导致，必然主要来自 spill 数量/体积差异或弱 baseline 的 liveness pathology。

### B. 三个候选序的生成没有使用 clean/dirty 状态

论文明确称候选序依赖 “buffer clean/dirty state, size, and cache capacity”（`paper/src/en_conf/sections/algorithm.tex:83-109`；中文版 `zh_conf/...:44-52`）。实现则为：

- 候选仅为 `capfit_id`, `p1`, `id_raw`（`src/ks_core/solver.py:103-108`）。
- `id_raw` 只分 FREE/op/ALLOC 三层并取最小 node id（`solver.py:111-156`）。
- `_memory_aware_order` 的普通 priority 使用 successor indegree、size、cache weight、remaining uses 和 node id（`solver.py:202-360`），没有查询 clean-buffer 集合。
- `copy_in_bufs` 直到 address/spill engine 才建立（`solver.py:438`），并用于 victim score（`solver.py:469-486`）。

不过转述中“cost-aware 唯一进入方法的是驱逐评分”也稍微过头：portfolio 的最终 key 使用 `_extra_traffic`，后者按 clean=1、dirty=2 计价（`solver.py:72,84-85,91-96`）。所以准确表述应是：**候选生成完全 cost-blind；cost awareness 只存在于 victim rule 和候选的事后 exact-cost 选优中。**

### C. 所谓提出的 `id_raw` 候选在六个公开 case 上与强 blind baseline 完全相同

逐 case 比较 `H.build_order(inst, "id_raw") == B.cp_free_first(inst)`，六个结果全部为 `True`（长度分别 2580、36086、1716、6952、4160、30976）。因此 portfolio 中的第三个“方法候选”实质上已经把强 blind baseline 原样包含进去；最终不劣具有 portfolio 单调性，不能作为 clean/dirty-aware ordering 的证据。

代码对应：`id_raw` 见 `solver.py:111-156`；`cp_free_first` 见 `scripts/paper/baselines.py:255-295`。

### D. 论文称 structure-agnostic / 不编码 operator motif，P1 实现却显式检查 D2S/transfer 模式

论文：`paper/src/en_conf/sections/algorithm.tex:85-87`。

代码：

- `solver.py:225-227` 仅在 cache types 恰为 `{L1,L0B}` 且存在 `D2S` 时开启特殊 tie-break。
- `solver.py:253-260` 显式识别 downstream `D2S`、`COPY_IN`、`MOVE` 并分组排序。

这不是 case-name hard-code，但确实是 operator/operation-specific motif，且正文把 pressure-aware order 简化成“按 successor indegree”并未披露这些分支。

### E. “overflow-area surrogate 用于实现/跨阶段选序”与代码不符

论文称实现使用 `Phi`，并称其为 P1/P2/P3 一致 scalar（`algorithm.tex:56-81`）。代码虽定义 `_overflow_traffic`（`solver.py:179-195`），全仓库对该函数没有任何调用；P2/P3 实际对每个候选完整运行 spill assignment 和 timing simulator，再按真实 `(extra, spills, time)` 或 `(time, extra, spills)` 选优（`solver.py:61-87`）。

此外论文报告的 global Spearman 0.958（`experiments.tex:220-230`）是把不同规模 case 混在一起。真正与“同一 case 内选序”相关的 per-case Phi-extra Spearman 只有 0.207--0.600，中位 0.448（`results/paper/e6_corr.csv:2-7`）；global 高相关主要受跨 case 尺度支配。

### F. “spill-inevitability certificate 是算法第一阶段的 linear-time diagnostic”并未实现，且当前实验是 post-hoc 候选统计

论文 method pipeline 把 diagnosis 写成第一阶段（`algorithm.tex:11-20`），但 `solve()` 里没有 certificate/diagnosis 分支（`solver.py:51-88`）。实际 E9 脚本只枚举 5 个固定序 + 8 个随机序（`scripts/paper/e9_working_set.py:20-22`），先用同一 heuristic engine 找候选中的最小 extra，再定义 10% near-opt subset（第 49-97 行）。

形式定义本身需要知道 `min E*(S)` 和 near-optimal schedule set（`paper/src/en_supp/sections/formal_reasoning.tex:59-69`）；这不是在未知最优调度上可直接线性时间求得的诊断。当前可诚实称为“给定有限候选集后的 O(N) post-hoc statistic”，不能称为对所有合理/近最优 schedule 的可计算 certificate，除非另给一个真正可计算的全局下界算法。

### G. prefetch 与 spill selection 并未解耦

正文写 “Reload timing does not change spill traffic”（`algorithm.tex:171-179`）。实现注释也说 P2 中 prefetch “can only increase” extra（`solver.py:62-65`）。数据却明确显示 window 会改变 spill 集和 extra：例如 `results/paper/e8_prefetch.csv:18-25` 中 Conv1/capfit 从 78,056 降到 77,820 后又升到 95,560；`e8_prefetch.csv:58-64` 中 FA1/p1 也先降后升。原因是提前 reload 虽不立即驱逐，却改变后续 residency 和 victim choice。

### H. E5 不是 proposed selected order 的正面 case

E5 画的是 `id_raw` 与外部 baseline 的 P1 order（`scripts/paper/e5_residency.py:13-16`），而 Conv_Case0 的 proposed P2 实际选择 `p1`，extra=88,044；`id_raw` extra=212,956。Notebook 自己明确称这是五个 order-level losses 之一和 negative example（`06_e5_peak_residency.py:84-94`），正文却在 mechanism 段将图作为正面论证的一环且不披露哪边是失利候选（`experiments.tex:170-192`）。补充材料同时承认外部 baseline01 在 Conv0 P2 为 73,500，优于 ours 88,044（`en_supp/sections/solution_walkthrough.tex:149-167,213-215`）。

### I. “best blind”转述表的 Conv0 行有内部口径问题

如果 blind 集合包含论文四个 comparator，则 Conv0 默认同引擎最小值是 `pressure_uniform=207,932`，不是 `cp_free_first=212,956`（`e12_baselines.csv:8-12`）。`207932/88044 = 2.3617`，这解释了转述的“2.36x”；而 `212956/88044 = 2.4187`。所以转述表把 212,956 和 2.36x 拼在同一行是不自洽的。

## 4. 核心科学问题

当前真正被数据支持的核心不是“clean/dirty-aware ordering”，而是：

> allocator-friendly 的 FREE-first / ALLOC-late 分层拓扑序和少量互补候选，能够大幅减少 spill volume；在强 baseline 已采用相同分层结构后，额外收益通常只有约 1%。

clean/dirty 的 2x 非对称当然真实，但它目前只被 synthetic matched ablation 证明为 metric 定义的直接后果，未被真实 case 证明是 proposed algorithm 胜利的因果机制。论文把三个层次混在一起了：

1. **存在性**：clean 与 dirty 单次 spill 成本差 2x（成立，几乎是定义）。
2. **机制机会**：在相同 overflow pressure 下，order 能否改变 evictable composition（E5 未控制 pressure；synthetic 可以说明存在）。
3. **算法贡献**：proposed order 是否因为显式 cost-aware 决策而赢强 baseline（当前候选生成不读 clean/dirty，真实六例数据否定）。

## 5. 可诚实调整的创新方向

### 方向 1（最稳妥）：改写为 spill-volume-first 的 allocator-aware scheduling portfolio

把主贡献改为 FREE-first/ALLOC-late 的 layered scheduling、multi-cache capacity gating、candidate portfolio + exact simulation，以及 P3 prefetch search。删除“候选生成显式 clean/dirty-aware”“Phi 实际选序”“linear-time pre-diagnostic”等未实现主张。优点是与代码/真实数据一致；缺点是理论和 novelty 需要重新建立，且需与更强的 memory-aware list schedulers 公平比较。

### 方向 2（更有潜力）：真正实现 cost-aware ordering，而非事后贴标签

在 ready-node priority 中显式使用每 cache 的 `live_clean/live_dirty`、新分配 buffer 的 clean/dirty 类别、下一次使用距离和预计释放字节。可先尝试 cost-weighted overflow surrogate：

```text
O_t = max(live_total_t - C, 0)
cheap_cover_t = min(O_t, evictable_clean_t)
forced_dirty_t = O_t - cheap_cover_t
A_cost = sum_t (cheap_cover_t + 2 * forced_dirty_t)
```

但必须与 total overflow/pressure 分开报告，并加入 next-use/pinning，避免把逻辑 clean volume误当成可驱逐对象。更可靠的实现路径是 beam search / rollout：同一搜索预算下，对 exact spill evaluator 做有限深度 lookahead，以 `extra = spill_volume + dirty_spill_volume` 为 reward；小图 CP-SAT oracle 用于训练/校准 priority。

必须做 2x2 因果消融：cost-aware vs cost-blind ordering × cost-aware vs far-only victim，并额外在 evaluator 中把所有成本强制设为 1。只有 `true-cost` 下出现、uniform-cost 下消失的增益才能归因于 composition。

### 方向 3（科学上很诚实）：把论文改成“cost awareness 何时值得”的边界/负结果论文

提出 `E = V + D` 分解（总 spill volume `V` + dirty spill volume `D`），定义 composition opportunity gap，并证明同 `V` 下 cost awareness 的最大收益不超过 2x。大规模扫容量、DAG family、clean fraction、reuse distance，展示强 liveness scheduler 后真实 benchmark 的 marginal composition value 很小、在哪些合成/真实 regime 才变大。这个方向与当前反例高度一致，也比继续维护 2.4--26x 叙事可信。

### 方向 4：若继续使用 overflow surrogate/certificate，先让它们成为真算法

- 用 `A_cost` 或 next-use-weighted forced-dirty area 做候选 pruning/ranking，报告每 case 的 top-k regret，而不是跨 case global Spearman。
- spill inevitability 要换成无需先知道 near-optimum 的可计算 lower bound（例如受 DAG precedence 约束的 weighted vertex-separation/pathwidth lower bound，或对小图 CP-SAT exact、对大图 relaxation bound），否则只称 post-hoc applicability analysis。

## 6. 建议下一轮实验的最低验收标准

1. 主要 baseline：external baseline01、cp_free/id_raw、以及相同 candidate/search budget 的 cost-blind beam；不要再把 pressure_uniform/G--Hsu 的 2.4--26x 作为 headline。
2. 每 case 同时报告 `spill volume V`、`dirty volume D`、`extra=V+D`、spill count、time。
3. 固定 pressure 的 matched-order pair；E5 不得用峰值差 2x 的两条曲线证明 composition 因果。
4. 使用至少几十个非合成/不同来源 DAG，并做 capacity sweep；六例只能作为 case study。
5. proposed method 必须在 external baseline01 上按 P2 extra 明确统计：当前是 2 胜、1 平、3 负（若按 lexicographic key，Matmul1 可算第三个 win，但 extra 本身持平）。
6. 所有 comparator 用相同 spill engine 参数；若各自做 victim/window oracle，则全部方法使用相同搜索预算并明确写出。
