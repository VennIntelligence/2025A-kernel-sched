# Agent Research Log — 统一 P1/P2/P3 求解

> **Historical log / 历史日志**
>
> This file is an append-only forensic record of AutoResearch attempts. It
> contains failed hypotheses, intermediate conclusions, and statements that were
> later corrected by subsequent experiments. Do not use it as the source of
> truth for the final algorithm or paper claims.
>
> 最终结论请优先阅读 [`docs/research_summary.md`](research_summary.md) 和
> [`docs/paper/01_thesis_and_experiments.md`](paper/01_thesis_and_experiments.md)。

> 追加型日志:记录一次性解决三个问题的思考过程、阶段结果与教训。
> 时间:2026-06-11。起点:iter032 仍停留在 P1 (32 轮),P2/P3 从未开始。

---

## 0. 问题诊断(为什么之前 32 轮跑偏)

1. **指标过拟合**:P1 词典序得分以 max_L1 为首,导致 GPT 不停地以 UB/L0 残留爆炸的代价换微小的 L1 改善。例如 FA_Case1 max_UB 被推到 33010(UB 容量只有 1024),P2 spill 必然爆炸。
2. **没有全局视野**:P2/P3 的真实代价是 *容量超出量*(L1 4096、UB 1024、L0A/B 256、L0C 512),P1 的词典序与之背离。32 轮的努力对 P2/P3 几乎无积累。
3. **结构特调**:iter031 用了 D2S/CONV 特定门控,泛化性差,这正是数据集局限的体现。

## 1. 总体方案(iter033/034)

- **P1**:保留已晋升的 iter031 调度器(保证 P1 各行打平不丢分)。
- **P2/P3**:
  1. 生成多候选拓扑序:`capfit_id`(按节点 id 块状串行 + 容量节流)、`capfit`(容量节流 + successor_wait 优先)、`p1`(iter031 序);
  2. 对每个候选真实模拟地址分配 + spill,选 extra 最小者;
  3. 地址分配:首适配(低地址压实);溢出时按 Belady(下一次使用最远)+ 成本加权(COPY_IN 缓冲 extra=Size 减半)挑驱逐对象;reload 懒插入(下次使用前才 SPILL_IN);被 pin 的碎片用"原地搬迁"(spill+立即 reload)兜底。

## 2. 阶段结果(p3_fast,候选 vs baseline)

| 案例 | 指标 | iter034 | baseline |
|---|---|---|---|
| Conv_Case0 P2 | extra | 88044 | 73500 |
| Conv_Case0 P3 | time | 615694 | 535312 |
| FA_Case0 P2 | extra | 4444 | 3692 |
| FA_Case0 P3 | time | 53393 | 46761 |
| Matmul_Case0 P2 | extra | **34688** | 34944 |
| Matmul_Case0 P3 | time | **192380** | 194331 |

全部 valid=0 violations。Matmul 已双双小胜;FA 接近;Conv 仍差。

## 3. 关键教训(实验记录)

1. **dataclass + spec_from_file_location 崩溃**:模块未注册 sys.modules 时 `@dataclass` 解析字符串注解报 NoneType;改普通类即可。
2. **capfit 强制溢出选"最小尺寸"是错的**:大 L1 反复被迫提早打开(M0 L1 16384)。改成"最先解锁工作的链"(successor_wait)后 M0 L1 回到 9216。
3. **capfit_id 是最大单项收益**:id 顺序 = 数据原生块顺序(块状串行),配容量节流后 L0 残留 1~3、L1≈baseline,M0 extra 34688 首次胜 baseline。结构无关、不挑 kernel,正是"全局解"应有的形态。
4. **驱逐距离量化(q=128~8192)更差**,纯 Belady 距离 + 成本加权已接近局部最优;Conv 的差距不在驱逐策略,在 schedule 本身(大 tile 生命周期)。
5. **Conv 被 spill 的全是非 COPY_IN 输出 tile(成本 2×Size)**,baseline 多 spill 便宜 COPY_IN 权重;说明序上 COPY_IN 缓冲驻留窗口太短,后续可在 ALLOC 优先级上保留预载缓冲驻留。

## 4. iter034 full 套件结果(已晋升,18/18 valid)

首次产出全部 P2/P3 行。vs baseline:8 胜 10 负(此前为 0 行可比)。

- 胜:全部 P1、Matmul0 P2/P3、Conv1 P3(extra 78056 < 86690)。
- 负:Conv0/Conv1/FA0/FA1 P2 extra 差 6%~20%;P3 time 普遍输(P3 直接复用 P2 解,无任何时间优化)。
- M1 P2 extra=460800 恰等于 baseline:全部为 COPY_IN 廉价 spill,本质是逐块重载 B 矩阵,只有 zigzag 序能砍半,候选序里没有该形态。

## 5. iter035:P3 解耦 + SPILL_IN 预取

实验记录(p3_fast):

- 失败尝试:pipe 轮换 tie-break 对时间零影响(ready_ops 竞争极少,释放优先级主导)。
- **关键发现:P3 的时间损失主要在 reload 阻塞** —— 懒插入把 SPILL_IN 放在用户前一步,用户必须等 `2*Size+150` 周期。
- **预取窗口**:用户还有 ≤H 步才用到、且当前 cache 有空闲就提前 reload(不驱逐别人)。H=5/40 效果按案例不同,作为 P3 搜索维度;P2 不预取(预取轻微增加 extra)。
- 效果:Conv0 P3 time 615694 → 553280;FA0 53393 → 47608(基线 46761);M0 已胜。

P3 与 P2 解耦:P2 按 (extra, spills) 选;P3 按 (time, extra) 选,候选 = {capfit_id, p1} × H∈{0,5,40}。

## 6. 残余差距与定位(p3_fast 后)

| 行 | 差距 | 根因 |
|---|---|---|
| Conv0 P2 extra +20% | spill 选不到便宜 COPY_IN 缓冲(已被 FREE),序级问题 | tile 生命周期 |
| Conv0 P3 time +3.4% | 同上 (spill 字节多) | |
| FA0 P3 time +1.8% | 同上,接近 | |
| M1 P2 extra =baseline | B 矩阵每块全部重载,需 zigzag 序砍半 | 候选序无该形态 |

zigzag 需结构特定生成器,与"全局解"取向冲突,先记录不强求。

## 7. iter035/036 full 结果(均晋升)

- iter035:P3 解耦 + 预取窗口候选 → vs baseline 10 胜 8 负(P1 6/6 胜,FA1/M1 P3 翻盘)。
- iter036:P2 也纳入时间 tiebreak 与预取候选 → **11 胜 7 负**(M1 P2 翻盘:extra/spills 持平,time 1793377 < 1800218)。
- 收尾扫了驱逐评分 4 变体(dist、dist/cost、dist*size、dist*size/cost):差异 < 1%,确认剩余差距非驱逐策略所致。

## 8. 终态结论

| | P1 | P2 | P3 |
|---|---|---|---|
| Conv0 | 胜 | 负 (extra +20%) | 负 (time +3.4%) |
| Conv1 | 胜 | 负 (extra +6%) | 负 (time +14%) |
| FA0 | 胜 | 负 (extra +20%) | 负 (time +1.8%) |
| FA1 | 胜 | 负 (extra +0.2%) | 胜 |
| M0 | 胜 | 胜 | 胜 |
| M1 | 胜 | 胜 | 胜 |

从 0 行 P2/P3 可比 → 18/18 全部 valid、11/18 胜过出题方 baseline,P1 全胜保留。
剩余皆为序级差距,核心方向已在 lessons.md 注明:
1. Conv:让大 COPY_IN 缓冲驻留至 spill 高峰窗口,把 2×Size spill 替换为半价 COPY_IN spill;
2. Matmul1:zigzag 块遍历砍半 B 矩阵重载(extra 460800 → ~230400 量级)。

## 9. 第二轮复盘(iter037/038, 2026-06-11)

### 诊断(在 iter036 基础上重新定位)
- **驱逐策略已到顶**:对 4 种 victim 评分(dist、dist/cost、cost-first、far-only)在我方候选序上做对照,extra 差异 < 1%,常常完全相同。确认剩余差距不在 spill 引擎评分。
- **用我方引擎跑 baseline 自己的序**:Conv0 P2=87088、Conv1 P2=72520(胜)、M0/M1 P3 反超。说明我方 spill 引擎本身没问题,**差距=候选序**。baseline 序的关键性质:把廉价 COPY_IN 缓冲驻留到 L1 溢出窗口期间,从而能半价驱逐。
- **Matmul1 的 460800 基本是下界**:实测 capfit_id 下同时存活的 COPY_IN tile 峰值=272(M1)/72(M0),而 L1 仅容 32 个 128-tile,工作集 16+16 远超容量;zigzag 只改遍历方向、改不了工作集大小,因此**砍半不可达**(此前 lesson 过于乐观,已修正)。

### iter037: P3 预取窗口网格扩展(已晋升)
- 假设:P2 目标是 extra(预取只会增 extra,窄网格足够);P3 目标是 time(reload 隐藏是主杠杆,值得宽网格)。
- 改动:按 problem_id 分流,P3 窗口 {0,5,40} → {0,5,40,80,120}。纯加法、选 min,零回归。
- 结果:vs iter036 3 胜 0 负;**FA0 P3 46761→46167 翻盘胜 baseline**(12/18)。FA1 P3、M0 P3 同步改善。

### iter038: id_raw 候选序(已晋升)
- 关键发现:把"纯节点 id 表序(FREE>op>ALLOC,无容量节流)"加为第 3 个候选序,即能复刻 baseline 的廉价驻留性质。
- 改动:`_candidate_orders` 增加 `_id_raw_order`;选 min,零回归。用现有 dist victim 即可,无需 cost victim。
- 结果:vs iter037 7 胜 0 负;**Conv1 P2 77820→72520 翻盘胜 baseline**(13/18)。同时 FA0 P2 4444→3904、Conv1 P3 +14.6%→+3.6%、FA1 P3 180364、M0 P3 186820、M1 P3 1771132 全部改善。

### 终态(iter038,13/18 胜 baseline)
| | P1 | P2 | P3 |
|---|---|---|---|
| Conv0 | 胜 | 负 (+20%) | 负 (+3.4%) |
| Conv1 | 胜 | **胜** | 负 (+3.6%) |
| FA0 | 胜 | 负 (+5.7%) | **胜** |
| FA1 | 胜 | 负 (+0.2%) | 胜 |
| M0 | 胜 | 胜 | 胜 |
| M1 | 胜 | 胜 | 胜 |

剩余 5 负全部 = 序级差距,需复刻 baseline 在"确切溢出窗口保留廉价缓冲"的交织方式。已验证 DFS、延迟释放、operand-locality/zigzag 重排都无法泛化地生成该序(或更差),故记录不强求。安全的单调式扩候选思路(加序/加窗口、取 min)已被榨干。

## 10. 论文交接(2026-06-11)

把以上发现提炼为论文主线 + 实验矩阵,并把确定性数据/图表生成拆给 Codex:
- `docs/paper/01_thesis_and_experiments.md`:主线(Spill-Cost-Aware Liveness Shaping;clean/dirty 页类比)、
  贡献 C1/C2/C3 + 判据 D + 方法 M、实验矩阵 E1–E10、Solution of Record 快照(iter038)。
- `docs/paper/02_codex_playbook.md`:Codex 体力任务 T0–T10(仪器化求解器副本 + harness + 每实验数据 CSV + notebook 图表 `PF01_paper_figures`)。
数据回流后由主模型 + human 解读、落盘完整论文(含 supplementary)。
