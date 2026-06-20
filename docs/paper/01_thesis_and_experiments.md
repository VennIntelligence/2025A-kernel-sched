# Paper Brief — Spill-Cost-Aware Liveness Shaping for NPU Tensor Scheduling

> 本文档是论文的科学交接稿(human-facing)。它锁定主线、固化"赛题解法 + 最后一轮实验结果"作为上下文,
> 并给出后续要做的实验/验证矩阵。配套的 `02_codex_playbook.md` 把其中的**确定性体力活**拆给 Codex 执行,
> 产出数据与 notebook 图表;最后我们用这些数据回来落盘完整论文(含大量 supplementary)。

---

## 0. Solution of Record(冻结的上下文,勿改)

本节是"最后一轮实验结果 + 赛题解法"的快照。后续所有实验都以它为参照点。

### 0.1 最终求解器架构(promoted = `iter038_id_raw_candidate`)

- 活动解:`src/ks_core/solver.py`(方法入口 `algorithms/ours/solve.py`,= `autoresearch/iterations/iter038_id_raw_candidate/solve.py`),`autoresearch/best_iter.txt` 指向它。
- **P1(只要节点序,最小化峰值驻留)**:复用 iter031 的 memory-aware list scheduler
  = `_memory_aware_order(instance, variant="p1")`。D2S 门控 + transfer-feed ALLOC 优先。
- **P2/P3(地址分配 + spill)**:**候选序组合 + 真代价选优**:
  1. 候选序 `_candidate_orders` = {`capfit_id`(原始 id 块序 + 容量节流)、`p1`、`id_raw`(纯 id 表序,FREE>op>ALLOC,无节流)}。
  2. 预取窗口 grid:P2 = {0,5,40};P3 = {0,5,40,80,120}(`solve()` 按 `problem_id` 分流)。
  3. 地址分配:best-fit 空闲区间;溢出时按 **clean/dirty 代价加权的 Belady**(下一次使用最远 × size / 换出成本)选驱逐对象;
     reload 懒插入;被 pin 的碎片用"原地搬迁"(spill+立即 reload)兜底。
  4. 选择:对每个 (case, problem),按官方词典键取 min —— P2 用 `(extra, spills, time)`,P3 用 `(time, extra, spills)`。
- **关键不变量**:候选是"取 min"的组合,**加候选/加窗口只会改善或持平,绝不回退**(monotone)。这是我们能安全迭代的根本原因。

### 0.2 最终指标(iter038,18/18 valid,13/18 胜过出题方 baseline01)

| case | P1 (max_L1, time) | P2 (extra, spills, time) | P3 (time) | vs baseline |
|---|---|---|---|---|
| Conv_Case0 | 6912, 394430 | 88044, 339, 615694 | 553280 | P1✓ P2✗(+20%) P3✗(+3.4%) |
| Conv_Case1 | 13786, 650044 | **72520**, 1963, … | 1111778 | P1✓ **P2✓** P3✗(+3.6%) |
| FlashAttention_Case0 | 256, 31063 | 3904, 31, … | **46167** | P1✓ P2✗(+5.7%) **P3✓** |
| FlashAttention_Case1 | 256, 112458 | 32920, 229, … | **180364** | P1✓ P2✗(+0.2%) **P3✓** |
| Matmul_Case0 | 128, 82308 | **34688**, 271, … | **186820** | P1✓ **P2✓ P3✓** |
| Matmul_Case1 | 128, 629076 | **460800**, 3600, 1783145 | **1771132** | P1✓ **P2✓**(time tiebreak) **P3✓** |

- baseline 参照:`results/exp001_baseline01/metrics.json`(18 行)。
- 改进轨迹(ledger):iter034 8胜 → iter035 10胜 → iter036 11胜 → iter037 12胜(P3 预取网格) → iter038 13胜(id_raw 候选)。
- 剩余 5 个负全部是**序级差距**:需要复刻 baseline "在确切溢出窗口保留廉价缓冲"的交织;已验证 DFS / 延迟释放 / locality-zigzag 重排都无法泛化做到。

### 0.3 已确证的核心事实(实验支撑,勿重复劳动)

1. **驱逐策略不敏感**:在我方候选序上,4 种 victim 评分(dist、dist·size/cost、cost-first、far-only)的 extra 差异 <1%,常完全相同。
2. **序才是杠杆**:同一引擎下不同序,Conv0 P2 extra 在 73.5k–121k 间摆动(20%+);把 baseline 自己的序喂进我方引擎 ≈ 复现 baseline 代价。
3. **clean/dirty 成本非对称**:COPY_IN 缓冲 `SPILL_OUT cycles=0`、extra 计 `Size`(干净页,DDR 有备份);其它缓冲计 `2·Size`(脏页,需写回)。
4. **溢出 ≠ 峰值**:官方 P1 词典序可造出 `max_UB=33010`(容量仅 1024),P1 赢但 P2 必爆。容量溢出积分才与下游代价一致。
5. **工作集下界**:Matmul1 在最优候选序下 L1 同时存活仍达 272 个 128-tile(容量仅容 32),∴ 其 460800 extra 接近**容量受限下界**,zigzag 改不动(纠正了早期乐观假设)。

---

## 1. 主线(选定:会议长度,1 条故事线)

> **Thesis**:在换出代价非对称的多级 cache 上,*调度序*应当主动"塑形 liveness",
> 让**廉价可换出(clean)缓冲在容量溢出峰值处保持常驻**,形成一个"廉价驱逐储备池";
> 换出策略本身是次要的。我们用一个**容量溢出积分**作为跨阶段(P1→P2→P3)的统一代理目标来操作它,
> 并给出一个**工作集下界判据**来界定"何时重排有用 / 何时是容量受限、徒劳"。

**统一类比(论文的理论锚点)**:COPY_IN 缓冲 = OS 的*干净页*(换出免写回,题目 `SPILL_OUT=0` 正是此意),
其它缓冲 = *脏页*(换出要 2× 写回)。于是 NPU 张量调度 ≡ **一个脏/干净页感知的页面置换问题,
但"工作集成分"由调度器主动控制**。据我们所知,NPU 调度文献未把"调度序"显式当作"控制脏/干净驻留比例"的手段。

### 贡献清单(conference 体量:3 主 + 1 判据 + 1 方法学)

- **C1(核心)· Spill-Cost-Aware Liveness Shaping**:以 clean/dirty 换出代价梯度为信号,
  调度时保留廉价储备、尽早消解高代价脏缓冲。论证"驱逐策略是 red herring,序才是杠杆"。
- **C2 · Capacity-Overflow Integral 代理目标**:用 \(\Phi(S)=\sum_{t}\sum_{c}\max(0,\ \mathrm{live}_c(t)-\mathrm{Cap}_c)/\mathrm{Cap}_c\)
  取代"逐 cache 峰值词典序",作为能同时预测 P2 流量与 P3 时间的单一量。给出"峰值最优 ≠ 下游最优"的错配案例。
- **C3 · Spill Selection/Placement 解耦**:同一 spill 集合,其*时间放置*可独立优化 ——
  P2 选"换谁"以最小化流量,P3 把 SPILL_IN 预取进空闲 cache(不额外驱逐)以隐藏重载阻塞。
- **D · 重排徒劳性判据**:\(O(N)\) 预分析比较"最小同时存活工作集 vs 容量",
  把"该不该做结构特化重排"变成一个可检验的 bound(对应 reviewer 关心的 generality/limits)。
- **M · Portfolio + 真代价单调选择**:少量结构多样的*通用*序 + 按 \(\Phi\)/官方键模拟选优;
  "加候选取 min ⇒ 永不回退"给出一个安全的改进循环(由 C2 让选择变便宜来支撑,避免落成纯 algorithm-selection)。

> 反过度特化承诺:C1/C2/D 的所有信号都只依赖"缓冲是否可重物化 / 写回成本 / 容量",**不含任何 Conv/Matmul/FA motif 判断**。

---

## 2. 实验 / 验证矩阵(E1–E10)

每个实验标注:**支撑哪个贡献 / 假设 / 产出(图表)/ 证实或证伪的判据**。
实验脚本见 `scripts/paper/e*.py`。数据落 `results/paper/`,图落 `output/02_paper_figures/`。

| ID | 支撑 | 假设 (H) | 产出 | 证实判据 |
|---|---|---|---|---|
| **E1** | 全局 | 我方解 18/18 valid 且 13/18 胜 baseline | Table 1(headline 18 行) | 复现 §0.2 |
| **E2** | C1 | 驱逐策略对 extra 影响 <1%(序固定) | Table 2 + 分组柱状(变异系数) | 每个 (case,order) 上 5 种 victim 的 CV<1% |
| **E3** | C1 | 序对 extra 影响 ≫ 驱逐策略(同引擎) | Fig(orders×cases extra 柱状) | 至少 1 case 序间摆动 >10× victim 摆动 |
| **E4** | C1 | 我方序 spill 偏脏页;baseline 序偏干净页 | Fig(clean/dirty 堆叠柱,我方 vs baseline) | Conv 上 baseline clean 字节占比显著高于我方 |
| **E5** | C1(money fig) | 溢出峰值处我方序少 clean 常驻,baseline 多 | Fig(Conv0 L1 clean/dirty 驻留随调度位置 + 容量线) | 峰值窗口 clean 常驻字节:baseline ≫ 我方 |
| **E6** | C2 | \(\Phi\) 与下游 extra/time 强相关;逐 cache 峰值弱相关 | Fig(散点 \(\Phi\)↔extra、peak↔extra)+ 相关系数表 | Spearman(\(\Phi\),extra) 明显高于 Spearman(peak,extra) |
| **E7** | C2 | P1 词典序最优解对 P2 不可行(峰值爆容量) | Table(P1-lex-best vs \(\Phi\)-best 的 max_UB/max_L1) | 存在 case 上 P1-lex-best 的某 cache 峰值 ≫ 容量 |
| **E8** | C3 | extra 随预取窗口近似单调↑,time 有极小值 | Fig(双面板 time(H)、extra(H)) | 每 case 存在 H*>0 使 time(H*)<time(0) 且 extra 增幅可控 |
| **E9** | D | 存在 (case,cache) 容量受限(工作集≫容量)使重排徒劳 | Table + 柱状(min 工作集 / 容量) | Matmul1 L1 工作集/容量 ≫1;Conv L1 接近 1(序可救) |
| **E10** | M | 候选组合单调改善胜场 | Table/阶梯图(iter034→038 胜场) | 胜场单调不降:8→10→11→12→13 |

### 论文章节 ↔ 实验映射

- **Intro / Motivation**:E7(错配)+ §0.3 事实 1–2。
- **Method · C2 surrogate**:E6。
- **Method · C1 liveness shaping**:E2 + E3 + E4 + E5(E5 为主图)。
- **Method · C3 decoupling**:E8。
- **Analysis · limits/generality (D)**:E9。
- **Results**:E1 + E10。
- **Supplementary**:每个 E 的全 case 细表、所有 victim/order/window 的原始 CSV、复现脚本。

---

## 3. 诚实定位(避免审稿被打)

- *Register-pressure-aware scheduling / integrated prepass*(Goodman&Hsu 等)已耦合调度与分配。
  **我们的新意 = clean/dirty 非对称代价 + "把可重物化缓冲作为优先换出储备保留" 这个具体信号**,而非又一个联合 ILP。
- *Rematerialization / activation checkpointing* 已知。**我们不决定"是否重算",而是"调度保留可重算缓冲以便半价换出"**。
- *Portfolio / algorithm selection* 已知 ⇒ M 单独太薄,必须由 C2(便宜代理)托起,否则即"方法拼合"。
- 6 个 sample case 是验证集,**禁止 motif 硬编码**;所有结论需用"结构无关信号"复述(E2–E9 已满足)。

## 4. 后续我方(human + 主模型)要做的判断题(非 Codex)

1. 选 C1 作为唯一卖点,还是 C1+C2 双卖点(取决于 E6 相关性强度)。
2. C3 是独立 section 还是并入 C1 的"placement"小节。
3. D 是否值得升格为独立"when-to-stop"小节(取决于 E9 是否还有 Conv 之外的容量受限例证)。
4. 是否需要再补 1 个非样本 DAG(合成 matmul/conv,不同 tile 尺寸)来回应 generality —— 这步若要做,再单独立任务。
