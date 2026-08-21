# Post-review AutoResearch v2

日期：2026-07-11

## 结论

原论文的主要问题不是 E5 一张图，而是把三件不同的事混成了一个因果故事：

1. clean/dirty 的单次 spill 成本确实是 `1x/2x`；
2. allocator-friendly order 能显著减少 spill volume；
3. proposed ordering 是否因为显式 clean/dirty 决策而赢强 baseline。

旧实现只证明了前两点，未证明第三点。六个公开 case 相对强 blind order 的收益几乎都可由
spill volume 解释；旧 Conv0 selected plan 甚至是 100% dirty spill。旧候选序生成也不读取
clean/dirty，cost awareness 只在 victim rule 和事后 exact-cost selection 中出现。

本轮得到的更可信方向是：

> locality-preserving dependency-frontier order + weighted residency-gap spill planning

其中 clean/dirty 是真实 objective 和 repair proposal 的一部分，而不再被描述成唯一机制。

## 审稿取证

- E5 `id_raw` 峰值为 `14592 = 2304 clean + 12288 dirty`，dirty share 84.2%。
- E5 baseline 峰值为 `7488 = 576 clean + 6912 dirty`，dirty share 92.3%。
- 因此 composition 标签反了，而且两条曲线 peak 相差 1.95x，不能作为 fixed-pressure 因果证据。
- `212956 vs 74076` 混用了 victim policy；同 `dist_size_cost` 应为 `212956 vs 88768`。
- `ADVERSARIAL_REVIEW.md`、`e5_check/` 和 `alt2_overflow_decomposition.png` 均未实际保存。

完整证据见 `results/autoresearch_v2/FORENSIC_REVIEW.md`。

## Scalable v2 solver

正式 `src/ks_core/solver.py` 新增：

1. `unlock_frontier`：优先完成可共同解锁 consumer 的 ready ALLOC predecessor group；
2. true best-fit：修复原 `_FreeSpace.find()` 实为 first-fit 的实现错误；
3. victim portfolio：保留 distance/cost Belady，并加入 clean-share/fragmentation-adaptive policy；
4. 对无可行 placement 的 policy/window member 跳过，最终仍以真实 P2/P3 key 选择。

### P2 对官方 baseline01

| case | old promoted | scalable v2 | official | 对 official |
|---|---:|---:|---:|---|
| Conv_Case0 | 88,044 | **66,828** | 73,500 | WIN |
| Conv_Case1 | **72,520** | 72,734 | 73,240 | WIN |
| FlashAttention_Case0 | 3,904 | **3,584** | 3,692 | WIN |
| FlashAttention_Case1 | 32,920 | **32,512** | 32,840 | WIN |
| Matmul_Case0 | 34,688 | **34,688** | 34,944 | WIN |
| Matmul_Case1 | 460,800 | **460,800** | 460,800 | extra/spills TIE，time WIN |

六个结果均通过 canonical evaluator，0 violations。机器可读结果见
`round10_final_p2.json`。该 JSON 是 metrics/validation ledger；对应的六套 production
schedule/memory/spill 文件没有一起保存在 `results/autoresearch_v2/`，所以独立复验需要重跑
deterministic solver，而不能只靠该目录回放 artifact。

这里的 5 WIN / 1 TIE 是相对 official，而不是相对上一版 solver。相对真实的
`iter038_id_raw_candidate`，scalable v2 是 3 WIN / 2 TIE / 1 LOSS；唯一回退是 Conv1
的 72,520 -> 72,734（+214）。因此不能把全部 public gain 描述成“新模块相对旧系统的提升”。

### P3

P3 time 相对 official 为 5 WIN / 1 LOSS。唯一失败是 Conv_Case1：
`1118687 vs 1073322`。固定 step-count prefetch window 可继续压低该值，但最优点不连续，
本轮没有把 case-specific window 塞入正式方法。

P2 与 P3 必须脱钩报告。同一 case 内，P3-selected artifact 在六例上都比 P2-selected
artifact 更快、但 traffic 更高；traffic/time 差分别为 Conv0 `+2884/-5400`、Conv1
`+8/-35985`、FA0 `+512/-8612`、FA1 `+1792/-11802`、MM0 `+256/-5560`、MM1
`+128/-11700`。这是 portfolio 内观察到的 trade-off，不是全局 Pareto 最优性证明。

## 六实例机制账本：`E = V + D`

对 production P2 与 matching official P2 的 spill artifact 做配对分解，定义正数为
`official - scalable v2`：

| case | volume reduction `delta V` | unbacked reduction `delta D` | traffic reduction `delta E` |
|---|---:|---:|---:|
| Conv0 | 2,832 | 3,840 | 6,672 |
| Conv1 | 677 | -171 | 506 |
| FA0 | 54 | 54 | 108 |
| FA1 | 164 | 164 | 328 |
| MM0 | 256 | 0 | 256 |
| MM1 | 0 | 0 | 0 |

每个 strict win 都伴随 `V` 下降；在 mixed regime 中，Conv0 和 FA1 的 `D` 也下降，Conv1
甚至以 `D` 上升 171 bytes 换取净胜。这支持“volume 是共同解释，composition 只在部分
case 可能贡献”的最窄主张。FA0 全部为 unbacked、两例 Matmul 全部为 backed，所以其中的
`delta D` 不能被解释为调度器主动改变了类别构成。即使在 mixed case，`delta V + delta D`
仍是 accounting decomposition，不是两个独立处理效应或因果识别。

## Round-7 component ablation 的边界

`round7_public_ablation.json` 是固定 `prefetch_window=0` 的 controlled traffic ablation，
其选择 key 只有 `(extra, spills)`，没有 P2 的 time tie-break。六个配置对应
`000, 010, 100, 001, 101, 111`（frontier / best-fit / adaptive），缺少 `011` 与 `110`，
所以不是完整 factorial design。`full` 也只是 adaptive + best-fit + H=0 的 selected
configuration，不是 canonical `solve` 的 order/policy/window portfolio。

此外，round-7 中名为 `iter038` 的行也是 H=0 controlled reference；Conv1 为 73,348，
而真实 promoted iter038 是 72,520。可以报告各条件值及 non-additivity，但不能把
`best-fit + frontier - reference - full` 的余项当作隔离后的 interaction：它同时混入
adaptive policy。也不能把 round-7 的 `full` 与最终 production artifact 视为同一工件；
它们只是在六例上恰好有相同的 traffic/spill split。

## 真正 cost-aware 的 order repair

研究脚本对合法 order 做 relocation，并只接受 `1x backed / 2x unbacked` traffic key
严格改善。但本轮没有形成一个统一算法、统一 proposal family 或统一预算的六实例实验：

| case | 起点 | 最好值 | 实际搜索范围 | 结论 |
|---|---:|---:|---|---|
| Conv0 | 66,828 | **65,532** | seed 0，10,000 次 stochastic single-node hill proposal | observed gain -1,296 |
| Conv1 | 72,734 | **70,940** | spill-targeted beam 10，2 rounds | observed gain -1,794 |
| FA0 | 3,584 | 3,584 | seed 0，2,000 次 stochastic proposal | no observed gain |
| FA1 | 32,512 | 32,512 | seed 0，2,000 次 stochastic proposal | no observed gain |
| MM0 | 34,688 | 34,688 | 未运行 repair search | not evaluated |
| MM1 | 460,800 | 460,800 | 未运行 repair search | not evaluated |

对最终 order 的事后检查表明，Conv0/Conv1 的改进都涉及前移 backed ALLOC/COPY_IN 相关
事件，并同时降低 `V` 与 `D`。这证明 cost semantics **能够**改变有利的 order；它不证明
统一 repair 方法在 2/6 case 有效，更不能把未搜索的 Matmul 记成 negative result。搜索阶段
使用内部 assigner 和 traffic key，当前目录也没有为六例各自保存完整的 canonical-evaluator
artifact，因此 repair 只能作为 exploratory mechanism evidence。

产物位于 `results/autoresearch_v2/agent_cost_order/`。

## Fixed-order exact spill/layout backend

`tmp/agent_direct_search.py` 把 fixed order 上每个 buffer 相邻 mandatory event 之间的 residency
gap 建成 optional interval：keep 一个 gap 的收益等于避免一次 canonical spill cost。CP-SAT
cumulative 选择 gap，连续地址打包再为 residency segment 求 offset，最后生成标准
schedule/memory/spill artifact 并调用 canonical evaluator。该模型只优化 traffic `E`；它没有
在 `E` 相同的解中继续最小化 spill count 与 time。因此下表中的 certificate 是
**fixed-order traffic-optimal**，不是完整 lexicographic P2-optimal。

| case / fixed order | emitted `E` | lower bound / known upper bound | machine status |
|---|---:|---:|---|
| Conv0 / unlock_frontier | **57,408** | LB 57,408 | gap OPTIMAL；packing OPTIMAL；valid；112 spills；0.88s |
| Conv0 / p1 | 81,504 | LB 81,504 | gap OPTIMAL；packing OPTIMAL；valid；328 spills；19.49s |
| FA0 / id_raw | **3,584** | LB 3,584 | gap OPTIMAL；packing GREEDY_VALID；valid；14 spills；2.17s |
| FA1 / capfit_id | 32,512 | LB 31,936 | gap FEASIBLE；packing OPTIMAL；valid；127 spills；123.96s |
| MM0 / capfit_id | 34,816 | LB 29,952；known legal UB 34,688 | gap FEASIBLE；packing GREEDY_VALID；valid；120.09s |
| Conv1 | -- | -- | cumulative/packing research run 未完成 |
| MM1 | -- | -- | not run |

当前可独立复验的 zero-gap traffic certificates 是 Conv0/unlock、Conv0/p1 和 FA0/id_raw。
Conv0 上同一 exact planner 仅替换 fixed order，traffic optimum 从 81,504 降至 57,408
（29.56%），直接隔离出该 case 的 order bottleneck；unlock order 上 exact traffic 又比
scalable heuristic 的 66,828 低 14.1%，相对 official 低 21.9%。

旧报告中的 “MM0 34,688 OPTIMAL” 已被 2026-07-11 的可复现补跑撤销。新 run 在 120s
只得到 34,816、lower bound 29,952；同时已有同一 fixed order 的合法 heuristic artifact
34,688，所以正确结论是 traffic optimum 位于 `[29,952, 34,688]`，而不是 34,688 已获证。

该 backend 适合作为 research oracle 或未来 guarded backend，不适合无条件用于大图。FA0
很快获证，但 FA1 与规模相近的 MM0 在约 120s 后仍有 gap，说明不能仅凭 node count 宣称
scaling threshold。未来集成必须有 timeout、packing/evaluator validation 和 heuristic
fallback。

## Robustness

### Capacity sweep

Conv0 在 evaluator 可行的 L1 容量 3072--16384 上，H=0 的四-order/two-policy slice 从未输
`cp_free_first` order comparator；2048/2560 下最大 mandatory pinned L1 operand set 为
3,072 bytes，因而不可行。该实验只扫一个 case 和一个 cache，并未运行完整 P2 window grid。
所谓 blind 只指 `cp_free_first` **order** 不读类别；其 best-fit allocator 和 victim-policy
selection 仍与 ours 共用、且包含 cost-aware policy。该结果只能作为 narrow stress boundary，
不能作为相对强 baseline 的泛化证据。完整数据见 `round8_capacity_sweep.json`。

### Synthetic suite

36 个已有 synthetic DAG 上：

- capacity-bound：相对 selected order-blind comparator 为 14 WIN / 4 TIE / 0 LOSS，median ratio 0.5；
- order-reachable：0 WIN / 18 TIE / 0 LOSS；
- 相对 iter038：36 TIE / 0 regression。

这些也是 H=0 内部 assigner 结果，不是逐例落盘并重新通过 canonical evaluator 的 production
artifacts。18 个 order-reachable case 的三方 traffic 全为 0；14 个对 blind 的 win 又全部由
旧 iter038 已经达到。它们只支持 non-regression：新 public-case 模块在该 suite 上是
0/36 新增提升，不能用来宣称额外泛化。

## 推荐论文方向

建议标题/主线改为：

> Joint Frontier Scheduling and Weighted Spill Planning for Multi-cache NPU Kernels

建议按强弱分层，而不是把全部结果并列为贡献：

1. **主贡献**：fixed-order weighted residency-gap traffic lower bound + concrete layout /
   evaluator certificate；Conv0 的两个 machine-certified order 还给出同-planner order
   bottleneck 对照。
2. **系统贡献**：dependency-frontier、best-fit、victim diversity 与 true-key production
   portfolio；公开 P2 对 official 为 5W/1T，但组件收益不均匀且对真实 predecessor 为
   3W/2T/1L。
3. **次贡献 / 审计方法**：`extra = spill volume + unbacked spill volume` 的配对分解、P2/P3
   分离和 evaluator applicability boundary。
4. **探索性结果**：非统一 cost-aware repair 在两个 Conv 上找到额外 gain；在形成统一算法和
   公平预算前，不能写成 scalable stage 或六实例贡献。
5. **负结果**：adaptive policy 单独可回退、round-7 非 factorial、synthetic 0/36 新增 gain、
   MM0/FA1 未获证、Conv1 packing 未完成、MM1 未运行。

不能再声称：三个候选序本身 clean/dirty-aware、Phi 实际参与选序、certificate 是 solve 的第一
阶段、victim rule 总是不重要，或 E5 控制了相同 pressure。

相关工作边界也必须正面处理：[COSMA](https://arxiv.org/abs/2311.18246) 已联合优化
operator schedule、memory allocation 和 tensor replacement；
[Checkmate](https://arxiv.org/abs/1910.02653) / [DTR](https://arxiv.org/abs/2006.09616)
已分别做 optimal/online tensor rematerialization。因此潜在新意只能
落在本项目更具体的 multi-cache micro-op DAG、非对称 backed/dirty spill cost、frontier repair、
以及可验证的 exact-to-heuristic bridge，而不能写成“首次联合调度与内存优化”。

## Evaluator 风险

1. clean/dirty 是静态标签；COPY_IN buffer 后续若被 op 写入，仍可能被错误按 clean 计价；
2. FREE 被当成 mandatory residency event，final use 后已 spill 的 buffer 仍须 reload 才能 FREE；
3. `compute_max_vstay` 是逻辑 ALLOC--FREE footprint，不是 P2 physical peak；
4. `node.bufs` 没有明确 read/write role，dirty state transition 尚无法严谨定义。

在重写 theorem 或大规模跑新结果前，应先修正/明确这些 evaluator semantics。
