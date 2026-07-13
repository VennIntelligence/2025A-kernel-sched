export type Language = 'zh' | 'en'

export type LinkKind = 'paper' | 'code' | 'data' | 'results'

export type ResourceLink = { label: string; kind: LinkKind; href: string }

export type StageCopy = { tab: string; title: string; detail: string }

export type FieldRow = { name: string; type: string; desc: string }

export type TransportLabels = {
  play: string
  pause: string
  restart: string
  prevStep: string
  nextStep: string
}

export type DataSectionCopy = {
  eyebrow: string
  title: string
  lead: string
  inputTitle: string
  inputLead: string
  nodeToggle: { cache: string; op: string }
  cacheFields: FieldRow[]
  opFields: FieldRow[]
  cacheExample: string
  opExample: string
  edgesTitle: string
  edgesType: string
  edgesDesc: string
  outputTitle: string
  outputLead: string
  files: Array<{ name: string; format: string; desc: string }>
  benchTitle: string
  benchLead: string
  benchCols: { task: string; nodes: string; edges: string; bufs: string; ops: string }
  capTitle: string
  capLead: string
  enumTitle: string
  enumLead: string
  enumGroups: { op: string; pipe: string; type: string }
  docTitle: string
  docBody: string
  docLink: string
  docHide: string
}

export type ProblemCopy = {
  eyebrow: string
  title: string
  lead: string
  figureKicker: string
  stageWord: string
  nextStage: string
  controls: TransportLabels
  legend: { cache: string; op: string; spill: string }
  stages: StageCopy[]
  problems: Array<{ label: string; title: string; formula: string; body: string }>
  data: DataSectionCopy
}

export type Copy = {
  nav: {
    brand: string
    overview: string
    problem: string
    method: string
    results: string
    cite: string
  }
  meta: {
    venue: string
    title: string
    authors: Array<{ name: string; email: string }>
    affiliation: string
    links: ResourceLink[]
    fig1Label: string
    fig1Caption: string
    fig2Label: string
    fig2Caption: string
  }
  abstract: { title: string; body: string }
  highlights: { title: string; items: Array<{ value: string; label: string }> }
  contributions: {
    title: string
    lead: string
    items: Array<{ tag: string; name: string; body: string }>
  }
  problem: ProblemCopy
  model: {
    eyebrow: string
    title: string
    lead: string
    figLabel: string
    figCaption: string
    backed: { term: string; body: string }
    unbacked: { term: string; body: string }
    asideTitle: string
    asideBody: string
    viewsTitle: string
    views: Array<{ tag: string; title: string; formula: string; body: string }>
  }
  method: {
    eyebrow: string
    title: string
    lead: string
    stagesTitle: string
    stages: Array<{ n: string; title: string; body: string }>
    pipelineLabel: string
    pipelineCaption: string
    exactLabel: string
    exactCaption: string
    ordersTitle: string
    orders: Array<{ tag: string; name: string; body: string }>
    victimTitle: string
    victimBody: string
  }
  theory: {
    eyebrow: string
    title: string
    lead: string
    wsLabel: string
    wsCaption: string
    items: Array<{ tag: string; name: string; statement: string; note: string }>
  }
  results: {
    eyebrow: string
    title: string
    lead: string
    headlineLabel: string
    headlineCaption: string
    mainTitle: string
    mainCaption: string
    mainCols: {
      instance: string
      official: string
      scalable: string
      outcome: string
    }
    lowerBetter: string
    win: string
    tie: string
    loss: string
    evidenceTitle: string
    evidenceCaption: string
    evidenceCols: { instance: string; repair: string; exact: string; status: string }
    evidenceStatus: {
      probe: string
      certificate: string
      timeout: string
      feasibleFa1: string
      feasibleMm0: string
      notRun: string
    }
    accountingTitle: string
    accountingBody: string
    accountingLabel: string
    accountingCaption: string
    robustnessTitle: string
    robustnessBody: string
    benchTitle: string
    benchCaption: string
    benchCols: { instance: string; opType: string; nodes: string; edges: string; buffers: string }
    p3Title: string
    p3Caption: string
    p3Cols: { instance: string; official: string; scalable: string; outcome: string }
    capTitle: string
    capBody: string
  }
  related: { title: string; body: string[] }
  conclusion: { title: string; body: string; futureTitle: string; future: string }
  cite: { title: string; lead: string; bibtex: string; copy: string; copied: string }
  footer: { tagline: string; note: string }
}

const REPO = 'https://github.com/VennIntelligence/2025A-kernel-sched'

export const copy: Record<Language, Copy> = {
  zh: {
    nav: {
      brand: 'Frontier Scheduling',
      overview: '概览',
      problem: '赛题图解',
      method: '方法',
      results: '实验',
      cite: '引用',
    },
    meta: {
      venue: '编译优化 · Exact-to-Heuristic Scheduling',
      title: '面向 NPU 核函数的依赖前沿调度与非对称代价溢出规划',
      authors: [
        { name: '高成志', email: 'contact@vennai.org' },
        { name: '黄骏', email: 'hj992881627@outlook.com' },
        { name: '叶勤', email: 'yq020319@163.com' },
      ],
      affiliation: '东南大学 · 文氏智能基金会',
      links: [
        { label: '论文', kind: 'paper', href: `${REPO}/blob/master/paper/dist/en_conf.pdf` },
        { label: '代码', kind: 'code', href: REPO },
        { label: '数据', kind: 'data', href: `${REPO}/tree/master/data` },
        { label: '结果', kind: 'results', href: `${REPO}/tree/master/results` },
      ],
      fig1Label: '研究主线',
      fig1Caption:
        'Conv0 的完整证据阶梯：production solver 相对官方工件降低 9.1%，探索性 order repair 再降低 1.9%，fixed-order planner 达到 57,408 字节下界并形成证书。',
      fig2Label: '方法层级',
      fig2Caption:
        '生产求解器、非统一 repair 个案与 fixed-order oracle 是三个不同层级；后两者不是默认 solve 的隐藏阶段。',
    },
    abstract: {
      title: '摘要',
      body:
        'NPU 核函数调度需联合选择微操作 DAG 的合法拓扑序、片上缓冲区连续地址和容量不足时的 spill 计划。本文构建以 dependency-frontier order 为核心的有界 production portfolio，并直接按 P2 流量或 P3 时间选择完整工件。对固定拓扑序，加权 residency-gap CP-SAT 给出流量下界；若连续打包后的合法工件达到该下界，即得到 fixed-order traffic certificate。六个公开 DAG 上，production solver 的 P2 为五胜一平，P3 时间为五快一慢。证据支持一条可审计的 exact-to-heuristic bridge，而不是普适的 clean/dirty 构成定律。',
    },
    highlights: {
      title: '核心结果',
      items: [
        { value: '5 胜 + 1 平', label: 'production solver 的 canonical P2 结果，全部 0 violations' },
        { value: '5 快 + 1 慢', label: 'P3 pipeline time；Conv1 回退 4.23%' },
        { value: '3 份证书', label: '覆盖两个公开实例的 fixed-order traffic optimum' },
      ],
    },
    contributions: {
      title: '三项贡献',
      lead: '把 production portfolio、固定序证书和审计式评价分层陈述，让每个结论都对应可复验 artifact。',
      items: [
        {
          tag: '贡献 1',
          name: 'Dependency-frontier 调度',
          body:
            '识别 successor-wait 规则会让单输入 stream 饿死多输入 consumer，并以 ready predecessor group completion 尽快解锁依赖前沿；该新信号不读取 case 名、算子 motif 或 buffer 类别。',
        },
        {
          tag: '贡献 2',
          name: '加权 residency-gap planning',
          body:
            '对固定序，把相邻 mandatory buffer event 之间的驻留 gap 作为 optional interval，以 evaluator 的真实 backed 1× / unbacked 2× 代价求解并生成连续物理布局。',
        },
        {
          tag: '贡献 3',
          name: 'Exact-to-heuristic bridge',
          body:
            '研究评估报告 fixed-order traffic lower bound 与 contiguous-packing certificate；production 在所有规模使用有界 portfolio，repair 个案、exact gap 和超时边界均单独披露。',
        },
      ],
    },
    problem: {
      eyebrow: '交互式赛题图解',
      title: '从 DAG 到缓存与流水线调度',
      lead:
        '输入是带缓存事件的计算 DAG，输出是合法拓扑调度、物理地址分配与必要的 spill，并在多流水线串行约束下评价总执行时间。下面用一个逻辑自洽的迷你实例走完全部五个阶段。',
      figureKicker: '交互图',
      stageWord: '阶段',
      nextStage: '下一阶段',
      controls: {
        play: '播放',
        pause: '暂停',
        restart: '重播',
        prevStep: '上一步',
        nextStep: '下一步',
      },
      legend: {
        cache: '缓存事件 ALLOC / FREE',
        op: '算子节点',
        spill: 'Spill 节点',
      },
      stages: [
        {
          tab: 'DAG',
          title: 'DAG 依赖结构',
          detail:
            '输入 DAG 由缓存事件（ALLOC/FREE）与多流水线算子组成：两次 MATMUL 复用同一个权重块 W（b0，COPY_IN 来源）。动画沿一个合法拓扑序逐节点点亮，角标数字即调度位置——这正是 Problem 1 要输出的 schedule。',
        },
        {
          tab: 'V_stay',
          title: 'Problem 1 · V_stay 前缀扫描',
          detail:
            '沿调度前缀扫描：ALLOC 计 +Size，FREE 计 −Size，算子贡献 0。该调度的 maxV_stay = 1024，恰好等于 UB 容量——从逻辑驻留看这是一个不需要 spill 的"完美"调度。',
        },
        {
          tab: 'Memory',
          title: 'Problem 2 · 物理放置与碎片化',
          detail:
            '把逻辑驻留落到物理地址区间后问题出现了：第 10 步要放置 X2（640），空闲总量 896 足够，但驻留在 [384, 512) 的 W 把空闲切成 384 + 512 两段，找不到 640 的连续洞——碎片化迫使 spill。这说明 maxV_stay ≤ 容量并不保证可放置。',
        },
        {
          tab: 'Spill',
          title: 'Problem 2 · Spill 重定位',
          detail:
            '插入 SPILL_OUT / SPILL_IN 对：W 暂存 DDR，X2 占据 [0, 640)，W 以 NewOffset = 640 重载回片上。W 带静态 COPY_IN-backed 标签，SPILL_OUT 为 0 cycle，额外 DDR 搬运量仅 Size = 128——这正是 Problem 2 的 artifact 计费。',
        },
        {
          tab: 'Pipeline',
          title: 'Problem 3 · 多流水线时序',
          detail:
            '同一 pipe 按调度序串行、不同 pipe 可并行；地址复用与 spill 引入新依赖（虚线）。SPILL_IN 在 MTE2 上排队，使 MATMUL₂ 直到 t=1366 才能发射，最终 T = max E(v) = 1766。Problem 3 要在不显著增加搬运量的前提下压缩 T。',
        },
      ],
      problems: [
        {
          label: 'Problem 1',
          title: '拓扑调度',
          formula: 'min maxV_stay',
          body: '输出所有原始节点的合法拓扑序，最小化调度前缀中的峰值逻辑驻留。',
        },
        {
          label: 'Problem 2',
          title: '地址分配与 Spill',
          formula: 'min Σ spill cost',
          body: '为 buffer 分配物理偏移，满足容量与不重叠约束；放不下时插入 spill，静态 COPY_IN-backed 标签计 Size，否则计 2×Size。',
        },
        {
          label: 'Problem 3',
          title: '流水线执行时间',
          formula: 'min T = max E(v)',
          body: '计入 spill 与地址复用依赖后，在同 pipe 串行约束下最小化总执行时间。',
        },
      ],
      data: {
        eyebrow: '数据格式与评测基准',
        title: '输入输出数据类型与评测算例',
        lead: '上面的动画用一个 17 节点的迷你实例讲清了流程。这里补充动画未展开的部分——真实的输入/输出数据结构、提交文件格式、硬件缓存容量，以及六个评测算例的规模。',
        inputTitle: '输入 · 计算 DAG',
        inputLead: '由两类节点与有向依赖边构成。切换标签查看两种节点各自的字段类型。',
        nodeToggle: { cache: '缓存节点', op: '算子节点' },
        cacheFields: [
          { name: 'Id', type: 'int', desc: '唯一节点编号' },
          { name: 'Op', type: 'ALLOC | FREE', desc: '缓存管理指令' },
          { name: 'BufId', type: 'int', desc: '缓冲区编号' },
          { name: 'Size', type: 'int', desc: '缓冲区大小（抽象单位）' },
          { name: 'Type', type: 'str', desc: '缓存类型 L1 / UB / L0*' },
        ],
        opFields: [
          { name: 'Id', type: 'int', desc: '唯一节点编号' },
          { name: 'Op', type: 'str', desc: '算子名，如 MATMUL' },
          { name: 'Pipe', type: 'str', desc: '执行流水线单元' },
          { name: 'Cycles', type: 'int', desc: '执行周期 10–3771' },
          { name: 'Bufs', type: 'list[int]', desc: '读写的缓冲区 id' },
        ],
        cacheExample: '{ "Id": 0, "Op": "ALLOC", "BufId": 0, "Size": 1, "Type": "UB" }',
        opExample: '{ "Id": 1, "Op": "COPY_IN", "Pipe": "MTE2", "Cycles": 15, "Bufs": [0] }',
        edgesTitle: '依赖边 Edges',
        edgesType: 'list[[int, int]]',
        edgesDesc: '有向依赖 [src, dst]，合法调度必须满足全部边。',
        outputTitle: '输出 · 调度 / 地址 / Spill',
        outputLead: '三个子问题分目录提交；Problem 2/3 还需地址与 spill 文件。',
        files: [
          { name: '<task>_schedule.txt', format: '每行一个节点 id', desc: 'P1 为全部原始节点；P2/P3 额外含插入的 SPILL_OUT / SPILL_IN' },
          { name: '<task>_memory.txt', format: 'BufId : Offset', desc: '每个缓冲区的初始物理偏移' },
          { name: '<task>_spill.txt', format: 'BufId : NewOffset', desc: '按顺序的 spill 重载偏移，无 spill 则为空' },
        ],
        benchTitle: '六个评测算例',
        benchLead: 'Case0 为小规模、Case1 规模陡增（最大 36k 节点 / 85k 边）。算法须随规模稳定，不能针对单个算例特调。',
        benchCols: { task: '算例', nodes: '节点', edges: '边', bufs: '缓冲区', ops: '算子节点' },
        capTitle: '硬件缓存容量',
        capLead: '五种片上缓存，容量相差达 16×：L1 最大、L0A / L0B 最小。',
        enumTitle: '取值枚举',
        enumLead: '求解器须按精确字符串解析（CUBE / VECTOR / MATMUL），不要盲目归一化。',
        enumGroups: { op: 'Op · 算子', pipe: 'Pipe · 流水线', type: 'Type · 缓存' },
        docTitle: '完整赛题文档',
        docBody: '以上图解已覆盖核心要点。如需完整背景、约束清单、spill 周期公式与数据 schema，可展开原始赛题文档作为参考。',
        docLink: '展开完整赛题文档',
        docHide: '收起赛题文档',
      },
    },
    model: {
      eyebrow: '问题模型',
      title: '静态 backed 标签与三个评价视角',
      lead:
        '输入是神经算子的微操作图 G。算子节点携带 pipe、cycles 与缓冲列表，缓存节点标记 ALLOC / FREE。每个逻辑缓冲 b 有大小 s_b 与缓存类型 τ(b)，调度 S 是全部节点的合法拓扑序。当前 evaluator 没有显式 read/write role，因此 COPY_IN membership 是静态 backed 标签，而不是动态更新的脏位。',
      figLabel: '图 2 · 微操作 DAG',
      figCaption:
        '微操作 DAG 中，粉色节点是 ALLOC / FREE，蓝色节点是计算或数据搬运。COPY_IN 标记的 backed 缓冲按一次 reload 计费；其他 generated-or-unbacked 缓冲按 write + reload 计费。',
      backed: {
        term: 'Backed（COPY_IN 标签）',
        body: 'evaluator 假定片外已有副本，spill 只计 reload：e_b = s_b。该标签在当前模型中不会随后续写入动态改变。',
      },
      unbacked: {
        term: 'Generated / unbacked',
        body: 'evaluator 按 write + reload 计费：e_b = 2s_b。由于缺少读写角色，这是一种 artifact 级分类。',
      },
      asideTitle: '目标恒等式，不是单一机制定理',
      asideBody:
        '若 backed 与 unbacked spill volume 分别为 C、D，则 E=C+2D=(C+D)+D=V+D。非对称代价确实进入目标；但总 spill volume V 与 unbacked volume D 都会改变，不能只凭峰值构成归因。',
      viewsTitle: '三个嵌套的评价视角',
      views: [
        {
          tag: 'P1',
          title: '峰值驻留',
          formula: 'min maxₜ Wᶜ(t)',
          body: '只看节点顺序，最小化每个缓存的峰值活跃驻留。',
        },
        {
          tag: 'P2',
          title: '溢出流量',
          formula: 'E(S) = Σ_b∈Spills e_b',
          body: '加入连续地址分配与 spill 插入，按静态 backed/unbacked 计费并最小化总额外搬运。',
        },
        {
          tag: 'P3',
          title: '流水线时间',
          formula: 'T = maxᵥ E(v)',
          body: '计入原始依赖、spill 依赖、地址复用与 pipe 串行约束，最小化最终完成时间。',
        },
      ],
    },
    method: {
      eyebrow: '方法',
      title: '结构前沿、真实代价选择与有界精确规划',
      lead:
        'Production solver 枚举四种合法拓扑序、best-fit 放置、两种 victim policy 与有限 reload window，并直接用 canonical P2/P3 key 选择完整工件。Dependency frontier 是新加入的结构序；repair 与 exact planner 只作为独立研究证据。',
      stagesTitle: '三个阶段',
      stages: [
        {
          n: '1',
          title: 'Dependency frontier',
          body:
            '当某个 consumer 的剩余 predecessor 全部是 ready ALLOC 时，完成这组分配并尽快执行 consumer，避免多输入节点被连续的单输入 transfer 长期饿死。',
        },
        {
          n: '2',
          title: 'Scalable placement 与 policy portfolio',
          body:
            '沿合法序执行 true best-fit；在容量或碎片压力下比较 distance/cost 与 backed-share/fragmentation-adaptive victim policy，并跳过无法生成合法 placement 的组合。',
        },
        {
          n: '3',
          title: '真实目标选择与 fallback',
          body:
            'P2 直接按 (extra, spills, time)，P3 按 (time, extra, spills) 选择。Fixed-order exact planner 目前是独立研究分支，尚未进入默认 solver；未来集成必须在超时或 packing 失败时回退 validated scalable portfolio。',
        },
      ],
      pipelineLabel: '方法总览',
      pipelineCaption:
        'Dependency frontier 将同一 consumer 的 ready operand 集中完成：示意例中的 operand residency 从 18 降至 6 operand-steps。该图解释结构机制，不是公开 benchmark 的数值结果。',
      exactLabel: '图 · Fixed-order certificate 链',
      exactCaption:
        'CP-SAT 先选择加权 residency gap 并给出流量下界，再做连续 offset 打包和 canonical validation；只有合法工件达到下界时才形成 fixed-order traffic certificate。',
      ordersTitle: '三个实现层级',
      orders: [
        {
          tag: '默认',
          name: 'Production portfolio',
          body: '四种结构序 + true best-fit + 两种 victim policy + canonical objective selection；六个 P2 artifact 全部有效。',
        },
        {
          tag: '证据',
          name: 'Cost-aware repair case studies',
          body: 'Conv0 与 Conv1 使用不同搜索程序和预算，只接受 asymmetric P2 cost 严格下降；它们是探索性 case study，不是一套统一的六例算法。',
        },
        {
          tag: 'Oracle',
          name: 'Fixed-order exact planner',
          body: 'CP-SAT 选择 weighted residency gap，独立的 NoOverlap2D 或 validated greedy packing 检查连续 offset，再做 canonical validation；只对 fixed order 给 traffic 证书。',
        },
      ],
      victimTitle: 'Cost awareness 的真实位置',
      victimBody:
        '新 dependency-frontier 信号是结构性的；静态 backed/generated 成本进入 victim score、真实流量计算和最终 P2 key。两个非统一 Conv repair 个案分别再降 1.94% / 2.47%，不能外推为统一六例算法。',
    },
    theory: {
      eyebrow: '可证明与可验证的边界',
      title: '从目标恒等式到 fixed-order certificate',
      lead: '只保留与实现和 artifact 一一对应的论断：一个会计恒等式、一个容量松弛下界、达到下界后的固定序证书，以及明确的全局最优边界。',
      wsLabel: '图 6 · Conv0 的逻辑 L1 驻留',
      wsCaption:
        'Conv0 的 dependency-frontier order 具有更大的逻辑 L1 overflow area，却把 certified fixed-order traffic 从 81,504 降至 57,408 字节；仅靠峰值或面积不能可靠排序。',
      items: [
        {
          tag: '恒等式',
          name: 'Extra 的 volume 分解',
          statement:
            '令 backed spill volume 为 Cl、generated spill volume 为 Dt，总 volume 为 Vol=Cl+Dt，则 Tr=Cl+2Dt=Vol+Dt。优化可减少总 spill volume、generated surcharge，或二者。',
          note: '这是 evaluator 的计费恒等式，不是 composition 主导性的因果证明。',
        },
        {
          tag: '证书',
          name: 'Fixed-order traffic certificate',
          statement:
            '对给定拓扑序，每个相邻 mandatory event gap 是带收益的 optional interval；cumulative lower bound 后另做连续 offset packing，并以 canonical evaluator 验证 artifact。',
          note: 'Conv0/frontier：objective = bound = 57,408；所选段可连续打包，0 violations。证书不优化 spill-count/time tie-break。',
        },
        {
          tag: '边界',
          name: 'Exact-to-heuristic 边界',
          statement:
            'Exact planner 当前仅作研究 oracle，scalable portfolio 始终是正式默认。未来若集成 exact path，timeout 或 packing 失败时必须使用经验证的 scalable fallback。',
          note: 'FA1 120s 后仍有 576-byte gap；Conv1 未在研究预算内完成 exact + packing。',
        },
      ],
    },
    results: {
      eyebrow: '实验',
      title: '生产结果与研究证据分层报告',
      lead:
        '公开 headline 只包含 canonical-valid 的 production artifact。Repair 与 fixed-order exact 另表报告：前者是非统一个案，后者只认证给定拓扑序下的最小 traffic，不能混入默认算法的胜负统计。',
      headlineLabel: '图 · 六个公开实例的 P2 / P3 主结果',
      headlineCaption:
        'P2 相对 official 为五次严格胜出、一次持平；P3 time 为五快一慢。Repair 与 fixed-order oracle 均未混入本图。',
      mainTitle: 'Canonical P2 extra traffic',
      mainCaption:
        'Production solver 对 official 为 5 次严格胜出、1 次持平，最大下降 9.08%，中位下降 0.866%；六个工件均为 0 violations。',
      mainCols: { instance: '算例', official: 'Official', scalable: 'Production', outcome: '结果' },
      lowerBetter: '越低越好',
      win: '胜',
      tie: '平',
      loss: '负',
      evidenceTitle: '有界研究证据：repair 与 fixed-order oracle',
      evidenceCaption:
        'Repair 使用非统一搜索程序和预算；Exact 仅优化 fixed-order traffic。破折号表示没有完成结果或未运行，不表示零 traffic。',
      evidenceCols: { instance: '算例', repair: 'Cost repair', exact: 'Fixed-order exact', status: '状态' },
      evidenceStatus: {
        probe: 'probe',
        certificate: 'Traffic certificate',
        timeout: 'Packing timeout',
        feasibleFa1: 'Feasible；LB 31,936',
        feasibleMm0: 'Feasible；LB 29,952',
        notRun: '未运行',
      },
      accountingTitle: 'Tr = Vol + Dt 的六例计账',
      accountingBody:
        '所有严格 P2 胜例都降低总 spill volume；但 generated surcharge Dt 的变化并不统一：Conv1 在 Dt 增加 171 字节时仍获胜，Matmul0 则在 Dt=0 的纯 backed 区域获胜。',
      accountingLabel: '图 · Public cases 的 Vol / Dt 平面',
      accountingCaption:
        '箭头从 official 指向 production artifact。六例覆盖 generated-only、mixed 与 backed-only 区域，因此不存在统一的类别构成解释。',
      robustnessTitle: 'Robustness 支持非回归，不支持新的泛化结论',
      robustnessBody:
        '最新 canonical synthetic re-evaluation 中，production portfolio 与其候选子集前代在 36/36 例持平，并对四个未直接包含的固定实现观察到零负；8 个 17 节点 oracle 例均达到自身所选固定序的 traffic optimum。这是非回归和小规模同序吻合证据，不是相对前代的新泛化。',
      benchTitle: '评测算例',
      benchCaption: '六个公开 NPU 核内调度实例，覆盖三大算子族；|V| 从约 1.7k 到 36k 节点。',
      benchCols: { instance: '算例', opType: '算子族', nodes: '|V|', edges: '|E|', buffers: '缓冲区' },
      p3Title: 'Canonical P3 pipeline time',
      p3Caption: 'Production solver 为 5/6 time wins，中位改善 3.77%。Conv1 回退 4.23%，明确保留为 loss；P3 extra 不能替代 P2 objective。',
      p3Cols: { instance: '算例', official: 'Official time', scalable: 'Production time', outcome: '结果' },
      capTitle: '缓存容量',
      capBody: '五种片上缓存（抽象单位）：L1 4096，UB 1024，L0A 256，L0B 256，L0C 512。',
    },
    related: {
      title: '相关工作中的定位',
      body: [
        '联合 scheduling 与 memory optimization 并非本文首创。COSMA 已用 ILP 联合优化 operator schedule、memory allocation 与 tensor replacement；因此本文不能声称“首次联合优化”。',
        'Goodman–Hsu、register-pressure-aware scheduling、Checkmate 与 DTR 分别覆盖调度/活跃区间耦合以及 optimal/online rematerialization。我们的具体问题更细：multi-cache NPU micro-op DAG、静态 backed/unbacked spill 计费、连续 offset 与 pipe timing。',
        '可辩护的新意是 dependency-frontier scheduling、weighted fixed-order residency planning 与连续布局验证的组合，以及从小图 traffic certificate 到大图 heuristic 的可审计桥接。',
      ],
    },
    conclusion: {
      title: '结论',
      body:
        '本文把 NPU kernel memory planning 拆成两个可审计的问题：哪种合法 order 暴露出可规划的 residency frontier，以及固定 order 下哪些 backed/generated gap 应保持驻留。Production portfolio 在公开 P2 上五胜一平、P3 上五快一慢；fixed-order planner 提供三份 traffic certificate。结果不是普适的 clean/dirty 调度原则，而是一条带明确失败边界的 exact-to-heuristic bridge。',
      futureTitle: '未来工作',
      future:
        '补充明确的 buffer 读写角色与动态 backing-state transition；集成带门槛的 exact backend；并在六个公开 case 之外的新 workload 分布上检验 frontier scheduling 与统一 repair 算法。',
    },
    cite: {
      title: '引用',
      lead: '若本工作对你有帮助，欢迎引用。',
      bibtex:
        '@inproceedings{gao2027frontier,\n  title     = {Dependency-Frontier Scheduling with Asymmetric-Cost Spill Planning for NPU Kernels},\n  author    = {Gao, Chengzhi and Huang, Jun and Ye, Qin},\n  booktitle = {Proc. 2027 IEEE/ACM Int. Symp. on Code Generation and Optimization (CGO)},\n  year      = {2027}\n}',
      copy: '复制',
      copied: '已复制',
    },
    footer: {
      tagline: 'Dependency-frontier scheduling · Weighted spill planning',
      note: '页面 headline 取自 canonical production artifacts；repair、fixed-order oracle 与 synthetic boundary 均按证据范围单独报告。',
    },
  },

  en: {
    nav: {
      brand: 'Frontier Scheduling',
      overview: 'Overview',
      problem: 'Problem',
      method: 'Method',
      results: 'Results',
      cite: 'Cite',
    },
    meta: {
      venue: 'Compiler Optimization · Exact-to-Heuristic Scheduling',
      title: 'Dependency-Frontier Scheduling with Asymmetric-Cost Spill Planning for NPU Kernels',
      authors: [
        { name: 'Chengzhi Gao', email: 'contact@vennai.org' },
        { name: 'Jun Huang', email: 'hj992881627@outlook.com' },
        { name: 'Qin Ye', email: 'yq020319@163.com' },
      ],
      affiliation: 'Southeast University · Venn Intelligence Foundation',
      links: [
        { label: 'Paper', kind: 'paper', href: `${REPO}/blob/master/paper/dist/en_conf.pdf` },
        { label: 'Code', kind: 'code', href: REPO },
        { label: 'Data', kind: 'data', href: `${REPO}/tree/master/data` },
        { label: 'Results', kind: 'results', href: `${REPO}/tree/master/results` },
      ],
      fig1Label: 'Research thesis',
      fig1Caption:
        'The full Conv0 evidence ladder: production improves the official artifact by 9.1%, exploratory order repair adds 1.9%, and the fixed-order planner reaches its 57,408-byte lower bound.',
      fig2Label: 'Method layers',
      fig2Caption:
        'The production solver, nonuniform repair studies, and fixed-order oracle are distinct evidence layers; the latter two are not hidden stages of default solve.',
    },
    abstract: {
      title: 'Abstract',
      body:
        'NPU kernel scheduling jointly chooses a legal micro-operation order, contiguous on-chip addresses, and a spill plan under capacity. We build a bounded production portfolio around dependency-frontier ordering and select complete artifacts directly by the P2 traffic or P3 time objective. For a fixed topological order, a weighted residency-gap CP-SAT model supplies a traffic lower bound; a valid contiguous artifact that attains it becomes a fixed-order traffic certificate. On six public DAGs, production records five P2 wins and one tie, and five P3 time wins with one loss. The evidence supports an auditable exact-to-heuristic bridge rather than a universal clean/dirty composition law.',
    },
    highlights: {
      title: 'Headline results',
      items: [
        { value: '5 wins + 1 tie', label: 'canonical P2 outcome for the production solver; zero violations' },
        { value: '5 faster + 1 slower', label: 'P3 pipeline time; Conv1 regresses by 4.23%' },
        { value: '3 certificates', label: 'fixed-order traffic optima across two public instances' },
      ],
    },
    contributions: {
      title: 'Three contributions',
      lead: 'We separate the production portfolio, fixed-order certificates, and audit-oriented evaluation so every statement maps to a validated artifact.',
      items: [
        {
          tag: 'Contribution 1',
          name: 'Dependency-frontier scheduling',
          body:
            'We identify how successor-wait rules can starve multi-input consumers behind one-input streams, then unlock the dependency frontier through ready-predecessor group completion without case names, operator motifs, or buffer classes.',
        },
        {
          tag: 'Contribution 2',
          name: 'Weighted residency-gap planning',
          body:
            'For a fixed order, gaps between mandatory buffer events become optional intervals weighted by the evaluator’s backed 1× versus unbacked 2× spill cost, followed by concrete contiguous packing.',
        },
        {
          tag: 'Contribution 3',
          name: 'Exact-to-heuristic bridge',
          body:
            'Research evaluation reports fixed-order traffic bounds and contiguous-packing certificates; production uses a bounded portfolio at every size, while repair studies, nonzero gaps, and timeouts remain separate evidence.',
        },
      ],
    },
    problem: {
      eyebrow: 'Interactive Problem Explainer',
      title: 'From DAG to cache and pipeline scheduling',
      lead:
        'The input is a computation DAG with cache events; the output is a valid topological schedule, physical address assignment, and any required spills, evaluated under serial-per-pipe timing. One self-consistent miniature instance drives all five stages below.',
      figureKicker: 'Interactive figure',
      stageWord: 'Stage',
      nextStage: 'Next stage',
      controls: {
        play: 'Play',
        pause: 'Pause',
        restart: 'Restart',
        prevStep: 'Previous step',
        nextStep: 'Next step',
      },
      legend: {
        cache: 'cache event (ALLOC / FREE)',
        op: 'operation node',
        spill: 'spill node',
      },
      stages: [
        {
          tab: 'DAG',
          title: 'DAG dependency structure',
          detail:
            'The input DAG mixes cache events (ALLOC/FREE) with multi-pipe operations: two MATMUL tiles share one weight buffer W (b0, COPY_IN origin). The animation lights nodes up along one valid topological order; the badge is the schedule position — exactly the output of Problem 1.',
        },
        {
          tab: 'V_stay',
          title: 'Problem 1 · V_stay prefix scan',
          detail:
            'Scan the schedule prefix: ALLOC adds Size, FREE subtracts it, operations contribute 0. This schedule reaches maxV_stay = 1024, exactly the UB capacity — logically a "perfect" schedule that should need no spill.',
        },
        {
          tab: 'Memory',
          title: 'Problem 2 · placement and fragmentation',
          detail:
            'Mapping logical residency onto physical address intervals exposes the catch: at step 10, X2 (640) must be placed. Total free space is 896, but W resident at [384, 512) splits it into 384 + 512 — no contiguous 640-unit hole exists. Fragmentation forces a spill even though maxV_stay ≤ capacity.',
        },
        {
          tab: 'Spill',
          title: 'Problem 2 · spill relocation',
          detail:
            'A SPILL_OUT / SPILL_IN pair is inserted: W parks in DDR, X2 takes [0, 640), and W reloads at NewOffset = 640. W carries the static COPY_IN-backed label, so SPILL_OUT costs 0 cycles and extra DDR traffic is Size = 128 under the artifact metric.',
        },
        {
          tab: 'Pipeline',
          title: 'Problem 3 · multi-pipe timing',
          detail:
            'Each pipe runs serially in schedule order while different pipes overlap; address reuse and spills add new dependencies (dashed). SPILL_IN queues on MTE2, delaying MATMUL₂ until t = 1366, giving T = max E(v) = 1766. Problem 3 minimizes T without materially increasing traffic.',
        },
      ],
      problems: [
        {
          label: 'Problem 1',
          title: 'Topological schedule',
          formula: 'min maxV_stay',
          body: 'Output every original node in a valid topological order, minimizing peak logical residency over schedule prefixes.',
        },
        {
          label: 'Problem 2',
          title: 'Cache address & spill',
          formula: 'min Σ spill cost',
          body: 'Assign physical offsets under capacity and non-overlap constraints; insert spills when placement fails—Size for the static COPY_IN-backed class, 2×Size otherwise.',
        },
        {
          label: 'Problem 3',
          title: 'Pipelined runtime',
          formula: 'min T = max E(v)',
          body: 'With spill and address-reuse dependencies added, minimize the makespan under serial-per-pipe execution.',
        },
      ],
      data: {
        eyebrow: 'Data format & benchmark',
        title: 'I/O data types and benchmark cases',
        lead: 'The animation above used one 17-node miniature instance to convey the flow. This part fills in what it left out — the real input/output data structures, the submission file formats, the hardware cache capacities, and the scale of the six benchmark cases.',
        inputTitle: 'Input · computation DAG',
        inputLead: 'Two node kinds plus directed dependency edges. Toggle to inspect the field types of each node kind.',
        nodeToggle: { cache: 'Cache node', op: 'Operation node' },
        cacheFields: [
          { name: 'Id', type: 'int', desc: 'Unique node id' },
          { name: 'Op', type: 'ALLOC | FREE', desc: 'Cache-management directive' },
          { name: 'BufId', type: 'int', desc: 'Buffer id' },
          { name: 'Size', type: 'int', desc: 'Buffer size (abstract units)' },
          { name: 'Type', type: 'str', desc: 'Cache type L1 / UB / L0*' },
        ],
        opFields: [
          { name: 'Id', type: 'int', desc: 'Unique node id' },
          { name: 'Op', type: 'str', desc: 'Operator name, e.g. MATMUL' },
          { name: 'Pipe', type: 'str', desc: 'Execution pipe unit' },
          { name: 'Cycles', type: 'int', desc: 'Latency 10–3771' },
          { name: 'Bufs', type: 'list[int]', desc: 'Buffer ids read/written' },
        ],
        cacheExample: '{ "Id": 0, "Op": "ALLOC", "BufId": 0, "Size": 1, "Type": "UB" }',
        opExample: '{ "Id": 1, "Op": "COPY_IN", "Pipe": "MTE2", "Cycles": 15, "Bufs": [0] }',
        edgesTitle: 'Dependency edges',
        edgesType: 'list[[int, int]]',
        edgesDesc: 'Directed dependency [src, dst]; a valid schedule must respect every edge.',
        outputTitle: 'Output · schedule / address / spill',
        outputLead: 'Submitted per subproblem; Problem 2/3 also need address and spill files.',
        files: [
          { name: '<task>_schedule.txt', format: 'one node id per line', desc: 'P1: all original nodes. P2/P3 also include inserted SPILL_OUT / SPILL_IN' },
          { name: '<task>_memory.txt', format: 'BufId : Offset', desc: 'Initial physical offset of each buffer' },
          { name: '<task>_spill.txt', format: 'BufId : NewOffset', desc: 'Reload offset per spill in order; empty if no spills' },
        ],
        benchTitle: 'Six benchmark cases',
        benchLead: 'Case0 is small; Case1 jumps sharply (up to 36k nodes / 85k edges). A solver must stay stable across scale rather than over-fit one case.',
        benchCols: { task: 'Case', nodes: 'Nodes', edges: 'Edges', bufs: 'Buffers', ops: 'Op nodes' },
        capTitle: 'Hardware cache capacities',
        capLead: 'Five on-chip caches spanning a 16× capacity range: L1 the largest, L0A / L0B the smallest.',
        enumTitle: 'Value enums',
        enumLead: 'Solvers must parse exact strings (CUBE / VECTOR / MATMUL) rather than normalize blindly.',
        enumGroups: { op: 'Op · operator', pipe: 'Pipe · unit', type: 'Type · cache' },
        docTitle: 'Full problem document',
        docBody: 'The figures above cover the essentials. For the full background, the constraint list, spill-cycle formulas, and the data schema, expand the original problem document for reference.',
        docLink: 'Expand the problem document',
        docHide: 'Collapse the problem document',
      },
    },
    model: {
      eyebrow: 'Problem model',
      title: 'Static backing labels and three evaluation views',
      lead:
        'The input is a neural-operator micro-operation graph G. Operation nodes carry a pipe, latency, and buffer list; cache nodes mark ALLOC and FREE. Each logical buffer b has size s_b and cache type τ(b), and S is a legal topological order. The evaluator has no explicit read/write roles, so COPY_IN membership is a static backing label rather than a dynamically updated dirty bit.',
      figLabel: 'Figure 2 · Micro-operation DAG',
      figCaption:
        'In this micro-operation DAG, pink nodes are ALLOC/FREE and blue nodes are compute or transfer operations. COPY_IN-backed buffers are charged one reload; other generated-or-unbacked buffers are charged write plus reload.',
      backed: {
        term: 'Backed (COPY_IN label)',
        body: 'The evaluator assumes an off-chip copy and charges reload only: e_b = s_b. This static label does not change after a possible later write.',
      },
      unbacked: {
        term: 'Generated / unbacked',
        body: 'The evaluator charges write plus reload: e_b = 2s_b. Without explicit access roles, this is an artifact-level classification.',
      },
      asideTitle: 'An objective identity, not a single-mechanism theorem',
      asideBody:
        'If backed and unbacked spill volumes are C and D, then E=C+2D=(C+D)+D=V+D. Asymmetric cost is real, but both total spill volume V and unbacked volume D can change; peak composition alone does not establish causality.',
      viewsTitle: 'Three nested evaluation views',
      views: [
        {
          tag: 'P1',
          title: 'Peak residency',
          formula: 'min maxₜ Wᶜ(t)',
          body: 'Considers only node order; minimizes per-cache peak live residency.',
        },
        {
          tag: 'P2',
          title: 'Spill traffic',
          formula: 'E(S) = Σ_b∈Spills e_b',
          body: 'Adds contiguous address assignment and spill insertion, charging the static backed/unbacked classes and minimizing total extra traffic.',
        },
        {
          tag: 'P3',
          title: 'Pipelined time',
          formula: 'T = maxᵥ E(v)',
          body: 'Accounts for original, spill, address-reuse, and serial-per-pipe constraints to minimize makespan.',
        },
      ],
    },
    method: {
      eyebrow: 'Method',
      title: 'Structural frontiers, true-cost selection, and bounded exact planning',
      lead:
        'Production enumerates four legal topological orders, best-fit placement, two victim policies, and a bounded reload-window set, then selects complete artifacts by the canonical P2/P3 key. Dependency frontier is the new structural order; repair and exact planning remain separate research evidence.',
      stagesTitle: 'Three stages',
      stages: [
        {
          n: '1',
          title: 'Dependency frontier',
          body:
            'When a consumer’s remaining predecessors are all ready allocations, complete the group and run the consumer promptly so a multi-input node is not starved behind one-input transfers.',
        },
        {
          n: '2',
          title: 'Scalable placement and policy portfolio',
          body:
            'Run true best-fit placement and compare distance/cost with backed-share/fragmentation-adaptive victim policies. Portfolio members that cannot produce a legal placement are discarded.',
        },
        {
          n: '3',
          title: 'True-objective selection and fallback',
          body:
            'P2 selects (extra, spills, time); P3 selects (time, extra, spills). The fixed-order exact planner is currently a separate research branch, not part of the default solver; any future integration needs a validated scalable fallback.',
        },
      ],
      pipelineLabel: 'Method overview',
      pipelineCaption:
        'Dependency frontier completes one consumer’s ready operands together: in this schematic, total operand residency falls from 18 to 6 operand-steps. The figure explains the mechanism; it is not a public benchmark result.',
      exactLabel: 'Figure · Fixed-order certificate chain',
      exactCaption:
        'CP-SAT selects weighted residency gaps and supplies a traffic lower bound; contiguous offset packing and canonical validation must then produce a valid artifact that reaches the bound.',
      ordersTitle: 'Three implementation layers',
      orders: [
        {
          tag: 'Default',
          name: 'Production portfolio',
          body: 'Four structural orders + true best-fit + two victim policies + canonical objective selection; all six P2 artifacts validate.',
        },
        {
          tag: 'Evidence',
          name: 'Cost-aware repair case studies',
          body: 'Conv0 and Conv1 use different search procedures and budgets, accepting only strict asymmetric-P2 improvements. They are exploratory case studies, not one uniform six-case algorithm.',
        },
        {
          tag: 'Oracle',
          name: 'Fixed-order exact planner',
          body: 'CP-SAT chooses weighted residency gaps; a separate NoOverlap2D or validated-greedy step checks contiguous offsets before canonical validation. Certificates cover fixed-order traffic only.',
        },
      ],
      victimTitle: 'Where cost awareness actually enters',
      victimBody:
        'The new dependency-frontier signal is structural. Static backed/generated cost enters victim scores, true traffic computation, and the final P2 key. Two nonuniform Conv repair studies lower traffic by another 1.94% / 2.47%; they are not one six-case algorithm.',
    },
    theory: {
      eyebrow: 'Provable and verifiable boundaries',
      title: 'From an objective identity to a fixed-order certificate',
      lead: 'The account keeps only statements that map directly to implementation and artifacts: an accounting identity, a capacity-relaxation lower bound, a fixed-order certificate, and a clear global-optimality boundary.',
      wsLabel: 'Figure 6 · Logical L1 residency on Conv0',
      wsCaption:
        'Conv0 dependency frontier has a larger logical L1 overflow area yet lowers certified fixed-order traffic from 81,504 to 57,408 bytes; peak or area alone cannot rank orders reliably.',
      items: [
        {
          tag: 'Identity',
          name: 'Volume decomposition of extra',
          statement:
            'Let backed spill volume be Cl and generated spill volume be Dt, with Vol=Cl+Dt. Then Tr=Cl+2Dt=Vol+Dt: optimization may reduce total spill volume, the generated surcharge, or both.',
          note: 'This is an evaluator accounting identity, not causal proof that composition dominates.',
        },
        {
          tag: 'Certificate',
          name: 'Fixed-order traffic certificate',
          statement:
            'For a given topological order, every mandatory-event gap is a weighted optional interval. A cumulative traffic bound is followed by separate contiguous packing and canonical artifact validation.',
          note: 'Conv0/frontier: objective = bound = 57,408; selected segments pack and validate with zero violations. The certificate does not optimize spill-count/time tie-breaks.',
        },
        {
          tag: 'Boundary',
          name: 'Exact-to-heuristic boundary',
          statement:
            'The exact planner is currently a research oracle, while the scalable portfolio remains the production default. Any future integration must use a validated scalable fallback after timeout or packing failure.',
          note: 'FA1 retains a 576-byte gap after 120 s; Conv1 did not finish exact selection plus packing.',
        },
      ],
    },
    results: {
      eyebrow: 'Experiments',
      title: 'Production results and bounded research evidence',
      lead:
        'Public headlines contain canonical-valid production artifacts only. Repair and fixed-order exact results appear separately: repair is nonuniform case-study evidence, while exact values certify traffic only under one given order.',
      headlineLabel: 'Figure · Public P2 and P3 headline results',
      headlineCaption:
        'P2 records five strict wins and one tie against official artifacts; P3 time records five wins and one loss. Repair and the fixed-order oracle are excluded.',
      mainTitle: 'Canonical P2 extra traffic',
      mainCaption:
        'Production records five strict wins and one tie against official artifacts, with a maximum reduction of 9.08% and median reduction of 0.866%; every row has zero violations.',
      mainCols: { instance: 'Instance', official: 'Official', scalable: 'Production', outcome: 'Result' },
      lowerBetter: 'lower is better',
      win: 'win',
      tie: 'tie',
      loss: 'loss',
      evidenceTitle: 'Bounded research evidence: repair and fixed-order oracle',
      evidenceCaption:
        'Repair uses nonuniform search procedures and budgets; Exact optimizes fixed-order traffic only. A dash means no completed result or not run, never zero traffic.',
      evidenceCols: { instance: 'Instance', repair: 'Cost repair', exact: 'Fixed-order exact', status: 'Status' },
      evidenceStatus: {
        probe: 'probe',
        certificate: 'Traffic certificate',
        timeout: 'Packing timeout',
        feasibleFa1: 'Feasible; LB 31,936',
        feasibleMm0: 'Feasible; LB 29,952',
        notRun: 'Not run',
      },
      accountingTitle: 'Six-case accounting under Tr = Vol + Dt',
      accountingBody:
        'Every strict P2 win reduces total spill volume, but the generated surcharge Dt does not move uniformly: Conv1 wins while Dt increases by 171 bytes, and Matmul0 wins in the Dt=0 backed-only regime.',
      accountingLabel: 'Figure · Public cases on the Vol / Dt plane',
      accountingCaption:
        'Arrows run from official to production artifacts. The cases span generated-only, mixed, and backed-only regimes, so no single composition story explains the results.',
      robustnessTitle: 'Robustness supports non-regression, not new generalization',
      robustnessBody:
        'In the latest canonical synthetic re-evaluation, production ties its predecessor candidate subset on all 36 cases and records no losses against four nonincluded fixed implementations; all eight 17-node oracle cases attain the traffic optimum under their own selected order. This is non-regression and small-scale same-order agreement, not new generalization over the predecessor.',
      benchTitle: 'Benchmark instances',
      benchCaption: 'Six public NPU intra-kernel scheduling instances across three operator families; |V| from about 1.7k to 36k nodes.',
      benchCols: { instance: 'Instance', opType: 'Op. type', nodes: '|V|', edges: '|E|', buffers: 'Buffers' },
      p3Title: 'Canonical P3 pipeline time',
      p3Caption: 'Production wins five of six time comparisons, with a median 3.77% improvement. Conv1 regresses by 4.23% and remains an explicit loss; P3 extra is not the P2 objective.',
      p3Cols: { instance: 'Instance', official: 'Official time', scalable: 'Production time', outcome: 'Result' },
      capTitle: 'Cache capacities',
      capBody: 'Five on-chip caches (abstract units): L1 4096, UB 1024, L0A 256, L0B 256, L0C 512.',
    },
    related: {
      title: 'Positioning in related work',
      body: [
        'Joint scheduling and memory optimization is not new: COSMA already combines operator scheduling, memory allocation, and tensor replacement in an ILP. We do not claim to be the first joint optimizer.',
        'Goodman–Hsu and register-pressure-aware scheduling connect order with live ranges, while Checkmate and DTR cover optimal and online rematerialization. Our setting is narrower: multi-cache NPU micro-operation DAGs, static backed/unbacked spill charging, contiguous offsets, and pipeline timing.',
        'The defensible contribution is the combination of dependency-frontier scheduling, weighted fixed-order residency planning, and contiguous-layout validation, plus an auditable bridge from traffic certificates to a scalable heuristic.',
      ],
    },
    conclusion: {
      title: 'Conclusion',
      body:
        'This work separates NPU kernel memory planning into two auditable questions: which legal order exposes a tractable residency frontier, and which backed or generated gaps should remain resident under that order. Production records five P2 wins and one tie and five P3 time wins with one loss; the fixed-order planner supplies three traffic certificates. The result is not a universal clean/dirty scheduling principle, but an exact-to-heuristic bridge with explicit failure boundaries.',
      futureTitle: 'Future work',
      future:
        'Add explicit buffer read/write roles and dynamic backing-state transitions; integrate a guarded exact backend; and test frontier scheduling plus a uniform repair algorithm on new workload distributions.',
    },
    cite: {
      title: 'Cite',
      lead: 'If you build on this work, please cite the paper.',
      bibtex:
        '@inproceedings{gao2027frontier,\n  title     = {Dependency-Frontier Scheduling with Asymmetric-Cost Spill Planning for NPU Kernels},\n  author    = {Gao, Chengzhi and Huang, Jun and Ye, Qin},\n  booktitle = {Proc. 2027 IEEE/ACM Int. Symp. on Code Generation and Optimization (CGO)},\n  year      = {2027}\n}',
      copy: 'Copy',
      copied: 'Copied',
    },
    footer: {
      tagline: 'Dependency-frontier scheduling · Weighted spill planning',
      note: 'Public headlines come from canonical production artifacts; repair, fixed-order oracle, and synthetic boundaries are reported at their actual evidence scope.',
    },
  },
}
