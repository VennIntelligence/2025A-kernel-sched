# Paper v2 Brief — Dependency-Frontier Scheduling with Asymmetric-Cost Spill Planning for NPU Kernels

> **Active handoff document / 当前有效论文交接稿（2026-07-12）**
>
> 旧版以 E5、2.4–26×、Φ surrogate 和“驱逐不重要”为核心的叙事已废弃。
> 数字硬约束见 [`results/autoresearch_v2/CLAIM_LEDGER.md`](../../results/autoresearch_v2/CLAIM_LEDGER.md)，
> 完整调查见
> [`results/autoresearch_v2/RESEARCH_REPORT.md`](../../results/autoresearch_v2/RESEARCH_REPORT.md)。

## 1. 一句话主线

> 对多 cache NPU 微操作 DAG，dependency-frontier scheduling 提供可扩展的结构性
> order；weighted fixed-order traffic planning 给出 lower bound 和可验证连续布局证书。
> Cost-aware order repair 仅为异构预算的探索证据，不是 production stage。未来若集成
> exact path，必须提供 timeout 与可验证 fallback。

这里的 backed 是 evaluator 的静态 COPY_IN 标签：换出后只计一次 reload；其他
generated/unbacked 缓冲计 write + reload。不要把它描述为已有 read/write 语义支持的动态
clean/dirty 状态机。

## 2. 方法层级必须分开

### 2.1 Scalable v2（正式默认）

`src/ks_core/solver.py`：

1. `unlock_frontier` 完成能共同解锁早期 consumer 的 ready ALLOC group；
2. true best-fit 物理放置；
3. distance/cost 与 backed-share/fragmentation-adaptive 两种 victim policy；
4. 对 order × policy × prefetch window 运行真实 assign/evaluate；
5. P2 按 `(extra, spills, time)`、P3 按 `(time, extra, spills)` 选优。

这是 scalable production path。它的新增排序信号是结构性的，不应包装成“所有候选序显式读取
backed/unbacked 信息”。

### 2.2 Fixed-order weighted traffic planner（研究 oracle，尚未集成）

`scripts/agent_direct_search.py` 把相邻 mandatory buffer event 之间的 residency gap 建成
optional interval：保留 gap 的收益等于避免一次真实 spill traffic。CP-SAT cumulative 选
gap，独立连续打包阶段先尝试 48 个 deterministic greedy layout，失败才调用
NoOverlap2D，最后生成并 canonical-validate artifact。FA0/MM0 为 `GREEDY_VALID`。

zero gap + validated packing 只证明该 fixed order 上的 minimum traffic `E`；模型没有继续
优化相同 `E` 下的 spill count/time，所以不能称完整 P2 optimal，也不是全局 order 最优。
当前 canonical `solve` 未集成 CP-SAT。

### 2.3 Cost-aware order repair（探索性原型）

`scripts/agent_cost_order_search.py` 中记录的不是统一六实例算法：Conv0 使用 seed 0、10,000 次
stochastic single-node hill proposal；Conv1 使用 beam 10、2 rounds 的 targeted search；
FA0/FA1 只做 2,000 次 probe 且无观察增益；MM0/MM1 未运行。该层只能作为 mechanism
exploration。

## 3. Headline 结果

### 3.1 P2 scalable v2 vs official

| Case | Scalable v2 | Official | 结论 |
| --- | ---: | ---: | :---: |
| Conv_Case0 | **66,828** | 73,500 | WIN |
| Conv_Case1 | **72,734** | 73,240 | WIN |
| FlashAttention_Case0 | **3,584** | 3,692 | WIN |
| FlashAttention_Case1 | **32,512** | 32,840 | WIN |
| Matmul_Case0 | **34,688** | 34,944 | WIN |
| Matmul_Case1 | **460,800** | **460,800** | TIE；time tie-break win |

正确摘要：**5 strict wins + 1 tie**；最大下降 9.08%，中位下降 0.866%。六行均
valid、0 violations。生产 P2 及其 `C/D/V` source-of-truth 是
`results/autoresearch_v2/round11_audited_p2.json`。

### 3.2 P3

P3 time 为 **5/6 wins**，中位下降 3.77%。Conv_Case1 回退 4.23%：
1,118,687 vs 1,073,322。禁止把 P3 official spill 数字混入 P2 表。

### 3.3 显式 cost-aware 证据

| Case | Structural scalable | Repair result | Search coverage |
| --- | ---: | ---: | --- |
| Conv0 | 66,828 | **65,532** | 10,000 stochastic proposals |
| Conv1 | 72,734 | **70,940** | targeted beam 10 × 2 rounds |
| FA0 / FA1 | 3,584 / 32,512 | unchanged | 2,000-proposal probes；no observed gain |
| MM0 / MM1 | 34,688 / 460,800 | baseline carry-forward | repair 未运行 |

### 3.4 Exact fixed-order 证据

| Case / order | Emitted `E` | Lower bound / known upper | 状态 |
| --- | ---: | ---: | --- |
| Conv0 / unlock_frontier | **57,408** | LB 57,408 | traffic certificate；112 spills |
| Conv0 / p1 | 81,504 | LB 81,504 | traffic certificate；328 spills |
| FA0 / id_raw | **3,584** | LB 3,584 | traffic certificate；14 spills |
| FA1 / capfit_id | 32,512 | LB 31,936 | machine FEASIBLE；gap 576 |
| MM0 / capfit_id | 34,816 | LB 29,952；legal UB 34,688 | machine FEASIBLE；旧 OPTIMAL 撤销 |

三个 certificate 都是 fixed-order traffic certificate。Conv0 在同一 planner 下仅换 order，
81,504 -> 57,408（-29.56%），是目前最干净的 order-bottleneck 证据。MM0 的 production
合法结果 34,688 比 CP incumbent 34,816 更好，因此正确 optimum 区间是
`[29,952, 34,688]`。

### 3.5 `E=V+D` 机制账本

round11 直接保存 production `C,D,V`。与 official P2 配对后，
`(delta V, delta D, delta E)` 为 Conv0 `(2832,3840,6672)`、Conv1
`(677,-171,506)`、FA0 `(54,54,108)`、FA1 `(164,164,328)`、MM0
`(256,0,256)`、MM1 `(0,0,0)`。所有 strict win 都降低 `V`；Conv1 即使 `D`
上升仍获胜。该分解是 accounting，不是独立因果效应。

## 4. 贡献表述

建议 conference 主贡献：

1. **Dependency-frontier scheduling.** 解释 successor-wait 式局部规则如何让单输入
   stream 长期饿死 multi-input consumer，并以结构性 group completion 修复。
2. **Weighted residency-gap planning.** 把 canonical `1x backed / 2x
   generated-unbacked` 成本直接放进 fixed-order optimization，并生成可验证连续布局。
3. **Exact-to-heuristic bridge.** 小图提供 lower bound / packing certificate；大图使用
   best-fit + victim portfolio，并以真实 key 选优。
4. **Exploratory cost-aware order repair.** 只写“异构搜索在两个 Conv 找到额外 gain”；
   FA probe 是 no-observed-gain，Matmul 未运行，不能包装成六实例算法。
5. **Applicability and semantic audit.** 报告 capacity sweep、synthetic non-regression，
   同时披露 evaluator 的静态 backed 标签、FREE residency、logical max_vstay 与缺少
   read/write roles。

不要把 `E=C+2D=V+D` 会计恒等式升级成“composition 是唯一/主要机制”的定理；机制图应同时
报告总 spill volume `V` 与 generated-or-unbacked volume `D`。

## 5. 新实验地图

| ID | 问题 | 数据源 | 公共结论 |
| --- | --- | --- | --- |
| V1 | Scalable P2 是否胜 official？ | `round11_audited_p2.json` | 5 strict + 1 tie；production C/D/V source |
| V2 | P3 time 是否稳健？ | `round6_formal_p3.json` | 5/6 wins；明确 Conv1 loss |
| V3 | 组件配置有何条件效应？ | `round7_public_ablation.json` | H=0、`(E,n)` only、非 factorial；不是 production full |
| V4 | cost-aware ordering 是否可能生效？ | `agent_cost_order/` | Conv 用不同搜索获益；FA 小 probe 无 gain；MM 未跑 |
| V5 | fixed order 离 minimum traffic 多远？ | `agent_direct/*_exact.json` | 三个 traffic certificates；FA1/MM0 feasible gap |
| V6 | 容量变化是否回退？ | `round8_capacity_sweep.json` | controlled H=0 Conv0/L1；comparator 仅 ordering cost-blind |
| V7 | 新组件是否跨 synthetic 泛化？ | `round9_synthetic_summary.json` | internal H=0；未落盘 canonical artifacts；36/36 tie iter038 |
| V8 | evaluator 结论依赖哪些语义？ | evaluator audit | 四项限制作为 threats-to-validity 主表 |

### 需要的新图/表

- **主表：** scalable P2 vs official 六行；可在相邻小表展示 repair 与 exact 层级。
- **方法图：** structural frontier → scalable placement/policy → optional repair / exact
  planner；明确 default 与 research-only 分支。
- **机制分解：** `E=V+D`，同时画 `V` 和 `D`，不用旧 E5 波浪图。
- **Conv0 平行分支：** production 66,828 分别连到 repair 65,532 与
  unlock-fixed-order certificate 57,408；不要画成 repair 后再运行 exact 的串行 pipeline。
- **同 planner/order 对照：** Conv0/p1 81,504 vs Conv0/unlock 57,408。
- **边界表：** scalable / repair / exact 的适用规模、optimality status 与 fallback。
- **P3 表：** 5 wins + Conv1 loss，禁止 universal headline。

## 6. 禁用旧主张

- 不使用 2.4–26× headline；
- 不使用旧 E5 fixed-pressure/composition 证据或 `Dirty-heavy` 标签；
- 不声称 Φ 被 production solver 使用；
- 不声称所有候选序 clean/dirty-aware；
- 不声称 victim rule 总是不重要；
- 不声称 72 个组合全胜或 universal dominance；
- 不声称 repair / exact backend 对所有 workload 都增益；
- 不声称 round7 是 factorial、其 `full` 是 production artifact，或其 H=0 `iter038`
  reference 是真实 promoted solver；
- 不声称 MM0 34,688 已获 exact certificate；
- 不把 fixed-order minimum traffic 写成完整 P2 optimal；
- 不声称首次联合 scheduling + memory optimization（COSMA 已在先）；
- 不混用 official P2 与 P3 artifact。

## 7. Related work 与边界

必须正面处理 COSMA、Checkmate、DTR、register-pressure-aware scheduling 与
rematerialization。潜在新意应限定为 multi-cache NPU micro-op DAG、静态 backed/unbacked
非对称代价、dependency-frontier scheduling，以及从 fixed-order traffic certificate 到
scalable heuristic 的桥接。

## 8. Sources of record

- [`results/autoresearch_v2/RESEARCH_REPORT.md`](../../results/autoresearch_v2/RESEARCH_REPORT.md)
- [`docs/research_summary.md`](../research_summary.md)
- [`results/autoresearch_v2/CLAIM_LEDGER.md`](../../results/autoresearch_v2/CLAIM_LEDGER.md)
- [`results/autoresearch_v2/round11_audited_p2.json`](../../results/autoresearch_v2/round11_audited_p2.json)
- [`results/autoresearch_v2/agent_cost_order/final_summary.json`](../../results/autoresearch_v2/agent_cost_order/final_summary.json)
- [`results/autoresearch_v2/agent_direct/REPORT.md`](../../results/autoresearch_v2/agent_direct/REPORT.md)
