export type Language = 'zh' | 'en'

export type LinkKind = 'paper' | 'code' | 'data' | 'results'

export type StageCopy = { tab: string; title: string; detail: string }

export type FieldRow = { name: string; type: string; desc: string }

export type ScoreItem = { value: string; label: string }

export type ContribCard = { tag: string; name: string; body: string }

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

export type MethodCopy = {
  eyebrow: string
  title: string
  lead: string
  pipeline: { kicker: string; title: string; steps: string[]; caption: string }
  orderVictim: {
    kicker: string
    title: string
    caseLabel: string
    orderLabel: string
    victimLabel: string
    extraLabel: string
    cvLabel: string
    swingLabel: string
    caption: string
    note: string
  }
  residency: {
    kicker: string
    title: string
    idRaw: string
    baseline: string
    capacity: string
    phi: string
    clean: string
    dirty: string
    cleanAtPeak: string
    caption: string
    surrogateNote: string
  }
  cleanDirty: {
    kicker: string
    title: string
    clean: string
    dirty: string
    perSpill: string
    caption: string
    note: string
  }
}

export type ResultsCopy = {
  eyebrow: string
  title: string
  lead: string
  wall: {
    kicker: string
    title: string
    legendWin: string
    legendLoss: string
    pickHint: string
    ours: string
    base: string
    metricPeak: string
    metricExtra: string
    metricTime: string
    delta: string
    caption: string
  }
  portfolio: {
    kicker: string
    title: string
    wins: string
    losses: string
    iterLabel: string
    caption: string
    controls: TransportLabels
  }
  workingSet: {
    kicker: string
    title: string
    capacityBound: string
    orderReachable: string
    ratioAxis: string
    caption: string
    note: string
  }
}

export type Copy = {
  nav: {
    brand: string
    home: string
    problem: string
    method: string
    results: string
  }
  home: {
    eyebrow: string
    title: string
    subtitle: string
    authors: string[]
    affiliations: string[]
    links: Array<{ label: string; kind: LinkKind }>
    abstractTitle: string
    abstract: string
    teaserCaption: string
    scoresTitle: string
    scores: ScoreItem[]
    contribTitle: string
    contribLead: string
    contributions: ContribCard[]
    animationTitle: string
    animationBody: string
    openProblem: string
    bibtexTitle: string
    bibtex: string
    copyBibtex: string
    copied: string
  }
  problem: {
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
  method: MethodCopy
  results: ResultsCopy
}

export const copy: Record<Language, Copy> = {
  zh: {
    nav: {
      brand: 'Kernel Scheduling',
      home: '首页',
      problem: '赛题图解',
      method: '方法图解',
      results: '结果图解',
    },
    home: {
      eyebrow: '2025A Kernel Scheduling Challenge',
      title: 'Kernel Scheduling for Neural Operator DAGs',
      subtitle: '通用神经网络处理器下的核内调度、缓存分配与多流水线执行优化',
      authors: ['高成志', '黄骏', '叶勤'],
      affiliations: ['东南大学', '文氏智能基金会'],
      links: [
        { label: 'Paper', kind: 'paper' },
        { label: 'Code', kind: 'code' },
        { label: 'Data', kind: 'data' },
        { label: 'Results', kind: 'results' },
      ],
      abstractTitle: 'Abstract',
      abstract:
        '本项目研究给定神经算子计算 DAG 时，如何在依赖、缓存容量、物理地址、spill 与多流水线互斥约束下构造高质量调度。核心发现是：在 clean/dirty 换出代价非对称的多级缓存上，决定 spill 代价的是调度序本身——它塑形 liveness，让廉价的 clean 缓冲在容量溢出峰值处常驻；而具体的驱逐策略只是次要因素。我们用容量溢出积分 Φ 作为 P1→P2→P3 的统一代理目标，用工作集下界判据界定重排何时徒劳，并以候选序组合（portfolio）按真实官方键择优。在 6 算例 × 3 子问题共 18 个评测点上全部合法，13 项优于 baseline，P1 全胜。',
      teaserCaption: '调度 → 物理放置 → 多流水线执行：一个实例贯穿三个子问题。',
      scoresTitle: '核心成绩',
      scores: [
        { value: '18 / 18', label: '全部合法 valid' },
        { value: '13 / 18', label: '优于 baseline' },
        { value: '6 / 6', label: 'Problem 1 全胜' },
      ],
      contribTitle: '五个核心贡献',
      contribLead: '从一个反直觉的观察出发，到一套可解释、可泛化的求解框架。',
      contributions: [
        { tag: 'C1', name: 'Spill 代价感知的 Liveness 塑形', body: '调度序主动让 clean 缓冲在溢出窗口常驻，形成"廉价驱逐储备"，从源头压低 spill 代价。' },
        { tag: 'C2', name: '容量溢出积分 Φ', body: 'Φ = Σ(live−Cap)₊ 作为 P1→P2→P3 的统一代理目标，与真实 extra 几乎等价相关。' },
        { tag: 'C3', name: 'Selection / Placement 解耦', body: '"驱逐选谁"与"SPILL_IN 预取窗口"互相独立，可分别优化 extra 与 time。' },
        { tag: 'D', name: 'Spill 不可避免性判据', body: '近最优序集合上工作集下界仍 > 容量时，spill 不可避免，重排徒劳——给出停止信号。' },
        { tag: 'M', name: 'Portfolio + 真代价择优', body: '多候选序 × 预取窗口网格，按官方字典序键取最优，加候选永不回退。' },
      ],
      animationTitle: '从这里开始',
      animationBody:
        '三个互相衔接的交互页：赛题图解用一个迷你实例讲清问题全貌；方法图解展示"序主导、驱逐次要"等核心机制；结果图解呈现 18 个评测点的真实战绩。',
      openProblem: '打开交互式赛题图解',
      bibtexTitle: 'BibTeX',
      bibtex:
        '@misc{kernel_scheduling_2025,\n  title  = {Kernel Scheduling for Neural Operator DAGs},\n  author = {Venn Intelligence Kernel Scheduling Team},\n  year   = {2025}\n}',
      copyBibtex: '复制',
      copied: '已复制',
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
            '插入 SPILL_OUT / SPILL_IN 对：W 暂存 DDR，X2 占据 [0, 640)，W 以 NewOffset = 640 重载回片上。因为 W 源自 COPY_IN，SPILL_OUT 为 0 cycle，额外 DDR 搬运量仅 Size = 128——这正是 Problem 2 的代价度量。',
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
          body: '为 buffer 分配物理偏移，满足容量与不重叠约束；放不下时插入 spill，COPY_IN 来源代价 Size，否则 2×Size。',
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
    method: {
      eyebrow: '交互式方法图解',
      title: '为什么是"序"决定了一切',
      lead:
        '同一个 spill 预算下，换驱逐策略几乎不动，换调度序却能让代价摆动一个数量级。本页用三组真实实验数据，拆解我们方法的三块基石：序主导、容量溢出积分 Φ、以及 clean/dirty 非对称代价。',
      pipeline: {
        kicker: '求解流程',
        title: 'Portfolio 求解器一览',
        steps: [
          'P1 内存感知 list scheduler',
          '生成多条候选序 p1 / capfit / id_raw',
          '按 Φ 溢出积分择序（非 P1 字典序）',
          'best-fit 放置 + cost-加权 Belady 驱逐',
          'P3 预取窗口网格 → 按官方键取最优',
        ],
        caption:
          '五步流水线：先得到强 P1 序，再围绕容量溢出积分生成与筛选候选，最后在真实官方键上择优。加入新候选永不让成绩回退。',
      },
      orderVictim: {
        kicker: 'E2 · E3 核心反直觉点',
        title: '序主导，驱逐策略次要',
        caseLabel: '算例',
        orderLabel: '候选序',
        victimLabel: '驱逐策略',
        extraLabel: 'extra（额外 DDR 搬运）',
        cvLabel: '驱逐策略变异系数',
        swingLabel: '跨序摆动',
        caption:
          '固定一条候选序、轮换四种驱逐策略：extra 几乎不变（变异系数常为 0）。但换一条候选序，extra 立刻摆动数倍乃至 10× 以上。结论：先把序选对，远比纠结驱逐谁更重要。',
        note: '换驱逐策略：CV ≈ 0% · 换序：extra 摆动可达 10×+',
      },
      residency: {
        kicker: 'E5 · E6 容量溢出积分',
        title: 'Φ：把"溢出面积"当作代理目标',
        idRaw: 'id_raw（我们）',
        baseline: 'baseline',
        capacity: '容量 4096',
        phi: 'Φ 溢出面积',
        clean: 'clean 驻留',
        dirty: 'dirty 驻留',
        cleanAtPeak: '峰值处 clean 储备',
        caption:
          'Conv_Case0 的 L1 逻辑驻留沿调度序展开：超过容量线的阴影面积即容量溢出积分 Φ。我们的 id_raw 序在溢出峰值处保留了更多 clean 缓冲（廉价可驱逐），baseline 则几乎全是 dirty。切换两条曲线对比峰值处的 clean 储备。',
        surrogateNote: 'Φ ↔ extra 的 Spearman = 0.96，与 peak ↔ extra（0.95）几乎等价——Φ 是廉价而可靠的代理信号。',
      },
      cleanDirty: {
        kicker: 'E11 合成消融',
        title: 'clean / dirty：整 2× 的代价差',
        clean: 'clean 储备',
        dirty: 'dirty 储备',
        perSpill: '每次 spill 代价',
        caption:
          '在合成的 capacity-bound 核上，固定相同的候选序与相同的 spill 次数（3 次），只改变溢出峰值处常驻的是 clean 还是 dirty 缓冲：clean 储备的 extra 为 1536，dirty 储备为 3072。',
        note: 'clean 源（COPY_IN）每次 spill 代价 = Size；dirty = 2×Size，恰好 2 倍。',
      },
    },
    results: {
      eyebrow: '交互式结果图解',
      title: '18 个评测点上的真实战绩',
      lead:
        '6 个算例 × 3 个子问题 = 18 个评测点，全部合法。下面的战绩墙、迭代轨迹与工作集下界，均取自论文实验的真实数字。点击战绩墙的格子查看逐项对比。',
      wall: {
        kicker: 'E1 主线对比',
        title: '战绩墙：我们 vs baseline',
        legendWin: '优于 baseline',
        legendLoss: '不及 baseline',
        pickHint: '点击任一格子查看 ours vs baseline 明细',
        ours: '我们',
        base: 'baseline',
        metricPeak: 'P1 峰值 max_L1',
        metricExtra: 'P2 extra',
        metricTime: 'P3 time',
        delta: '相对变化',
        caption:
          '横向为三个子问题，纵向为六个算例。绿格表示该评测点优于 baseline。13 胜 5 负，P1 全胜——剩余 5 负全在 P2/P3 的序级细节，源于 baseline 在溢出窗口偶然保留了更多 clean 储备。',
      },
      portfolio: {
        kicker: 'E10 迭代轨迹',
        title: 'Portfolio：胜场单调上升',
        wins: '胜',
        losses: '负',
        iterLabel: '迭代',
        caption:
          '每次只向 portfolio 加入一条新候选序并按真实官方键择优，胜场从 8 单调升到 13。播放查看 iter034 → iter038 的演进——加候选永不让成绩回退。',
        controls: {
          play: '播放',
          pause: '暂停',
          restart: '重播',
          prevStep: '上一步',
          nextStep: '下一步',
        },
      },
      workingSet: {
        kicker: 'D 不可避免性判据',
        title: '工作集下界：何时 spill 不可避免',
        capacityBound: '容量受限（spill 不可避免）',
        orderReachable: '序可达（重排有效）',
        ratioAxis: '近最优工作集下界 / 容量',
        caption:
          '对每个 (算例, 缓存)，计算近最优序集合上的工作集峰值下界与容量之比。比值 > 1 意味着即便最优重排也放不下，spill 不可避免、纠结排序徒劳；此时应转而优化 spill 结构本身。',
        note: 'Matmul_Case1 / L1 比值高达 8.5：强容量受限，extra 已逼近下界。',
      },
    },
  },
  en: {
    nav: {
      brand: 'Kernel Scheduling',
      home: 'Home',
      problem: 'Problem',
      method: 'Method',
      results: 'Results',
    },
    home: {
      eyebrow: '2025A Kernel Scheduling Challenge',
      title: 'Kernel Scheduling for Neural Operator DAGs',
      subtitle: 'In-core scheduling, cache placement, and pipelined execution for general neural processors',
      authors: ['Chengzhi Gao', 'Jun Huang', 'Qin Ye'],
      affiliations: ['Southeast University', 'Venn Intelligence Foundation'],
      links: [
        { label: 'Paper', kind: 'paper' },
        { label: 'Code', kind: 'code' },
        { label: 'Data', kind: 'data' },
        { label: 'Results', kind: 'results' },
      ],
      abstractTitle: 'Abstract',
      abstract:
        'This project studies how to construct high-quality schedules for neural-operator computation DAGs under dependency, cache-capacity, physical-address, spill, and multi-pipe exclusivity constraints. The central finding: on multi-level caches with asymmetric clean/dirty eviction costs, the schedule order itself governs spill cost — it shapes liveness so that cheap clean buffers stay resident across capacity-overflow peaks, while the specific eviction policy is secondary. We use a capacity-overflow integral Φ as a unified surrogate across P1→P2→P3, a working-set lower-bound certificate to tell when reordering is futile, and a portfolio of candidate orders selected by the true official key. Across 6 cases × 3 subproblems (18 points) every result is valid, 13 beat the baseline, and P1 wins all six.',
      teaserCaption: 'Schedule → physical placement → pipelined execution: one instance, three subproblems.',
      scoresTitle: 'Headline results',
      scores: [
        { value: '18 / 18', label: 'valid solutions' },
        { value: '13 / 18', label: 'beat baseline' },
        { value: '6 / 6', label: 'Problem 1 wins' },
      ],
      contribTitle: 'Five core contributions',
      contribLead: 'From one counter-intuitive observation to an interpretable, generalizable solver.',
      contributions: [
        { tag: 'C1', name: 'Spill-cost-aware liveness shaping', body: 'The schedule order keeps clean buffers resident across overflow windows — a cheap eviction reserve that lowers spill cost at the source.' },
        { tag: 'C2', name: 'Capacity-overflow integral Φ', body: 'Φ = Σ(live−Cap)₊ is a unified surrogate across P1→P2→P3, almost equivalent in correlation to true extra.' },
        { tag: 'C3', name: 'Selection / placement decoupling', body: 'Which buffer to evict and the SPILL_IN prefetch window are independent — optimize extra and time separately.' },
        { tag: 'D', name: 'Spill inevitability certificate', body: 'When the near-optimal working-set lower bound still exceeds capacity, spills are unavoidable and reordering is futile — a stop signal.' },
        { tag: 'M', name: 'Portfolio + true-cost selection', body: 'Multiple candidate orders × a prefetch-window grid, picked by the official lexicographic key; adding a candidate never regresses.' },
      ],
      animationTitle: 'Start here',
      animationBody:
        'Three connected interactive pages: the Problem explainer walks one miniature instance through the whole task; the Method explainer dissects mechanisms like "order dominates, eviction is secondary"; the Results explainer shows the real scoreboard over 18 evaluation points.',
      openProblem: 'Open the interactive explainer',
      bibtexTitle: 'BibTeX',
      bibtex:
        '@misc{kernel_scheduling_2025,\n  title  = {Kernel Scheduling for Neural Operator DAGs},\n  author = {Venn Intelligence Kernel Scheduling Team},\n  year   = {2025}\n}',
      copyBibtex: 'Copy',
      copied: 'Copied',
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
            'A SPILL_OUT / SPILL_IN pair is inserted: W parks in DDR, X2 takes [0, 640), and W reloads at NewOffset = 640. Since W originates from a COPY_IN, SPILL_OUT costs 0 cycles and the extra DDR traffic is only Size = 128 — precisely the Problem 2 cost metric.',
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
          body: 'Assign physical offsets under capacity and non-overlap constraints; insert spills when placement fails — cost Size for COPY_IN-origin buffers, 2×Size otherwise.',
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
    method: {
      eyebrow: 'Interactive Method Explainer',
      title: 'Why the schedule order decides everything',
      lead:
        'Under the same spill budget, swapping the eviction policy barely moves the cost, yet swapping the schedule order swings it by an order of magnitude. This page dissects the three pillars of our method with real experimental data: order dominance, the capacity-overflow integral Φ, and asymmetric clean/dirty cost.',
      pipeline: {
        kicker: 'Solver flow',
        title: 'The portfolio solver at a glance',
        steps: [
          'P1 memory-aware list scheduler',
          'Generate candidate orders p1 / capfit / id_raw',
          'Select by Φ overflow integral (not the P1 key)',
          'Best-fit placement + cost-weighted Belady eviction',
          'P3 prefetch-window grid → pick by official key',
        ],
        caption:
          'A five-stage pipeline: obtain a strong P1 order, generate and filter candidates around the capacity-overflow integral, then pick the best on the true official key. Adding candidates never regresses the score.',
      },
      orderVictim: {
        kicker: 'E2 · E3 the counter-intuitive core',
        title: 'Order dominates, eviction is secondary',
        caseLabel: 'Case',
        orderLabel: 'Candidate order',
        victimLabel: 'Eviction policy',
        extraLabel: 'extra (extra DDR traffic)',
        cvLabel: 'eviction-policy CV',
        swingLabel: 'across-order swing',
        caption:
          'Fix one candidate order and cycle through four eviction policies: extra barely changes (CV is often 0). Switch the candidate order and extra immediately swings several-fold, often 10×+. Getting the order right matters far more than which buffer to evict.',
        note: 'Switch eviction: CV ≈ 0% · Switch order: extra swings up to 10×+',
      },
      residency: {
        kicker: 'E5 · E6 capacity-overflow integral',
        title: 'Φ: treating the "overflow area" as a surrogate',
        idRaw: 'id_raw (ours)',
        baseline: 'baseline',
        capacity: 'capacity 4096',
        phi: 'Φ overflow area',
        clean: 'clean residency',
        dirty: 'dirty residency',
        cleanAtPeak: 'clean reserve at peak',
        caption:
          'L1 logical residency for Conv_Case0 unrolled along the schedule: the shaded area above the capacity line is the capacity-overflow integral Φ. Our id_raw order keeps more clean buffers (cheaply evictable) resident at the overflow peak, while the baseline is almost all dirty. Toggle the two curves to compare the clean reserve at the peak.',
        surrogateNote: 'Spearman(Φ, extra) = 0.96, nearly identical to Spearman(peak, extra) = 0.95 — Φ is a cheap, reliable surrogate.',
      },
      cleanDirty: {
        kicker: 'E11 synthetic ablation',
        title: 'clean / dirty: an exact 2× cost gap',
        clean: 'clean reserve',
        dirty: 'dirty reserve',
        perSpill: 'cost per spill',
        caption:
          'On a synthetic capacity-bound kernel, with the candidate order fixed and the same spill count (3), we only change whether the buffers resident at the overflow peak are clean or dirty: the clean reserve yields extra = 1536, the dirty reserve 3072.',
        note: 'A clean (COPY_IN) buffer costs Size per spill; a dirty one costs 2×Size — exactly double.',
      },
    },
    results: {
      eyebrow: 'Interactive Results Explainer',
      title: 'The real scoreboard over 18 points',
      lead:
        '6 cases × 3 subproblems = 18 evaluation points, all valid. The scoreboard, iteration trajectory, and working-set bounds below all come from the real paper figures. Click a cell on the scoreboard for a per-metric comparison.',
      wall: {
        kicker: 'E1 headline comparison',
        title: 'Scoreboard: ours vs baseline',
        legendWin: 'beats baseline',
        legendLoss: 'below baseline',
        pickHint: 'Click any cell for the ours vs baseline detail',
        ours: 'ours',
        base: 'baseline',
        metricPeak: 'P1 peak max_L1',
        metricExtra: 'P2 extra',
        metricTime: 'P3 time',
        delta: 'relative change',
        caption:
          'Columns are the three subproblems, rows are the six cases. Green means that point beats the baseline. 13 wins, 5 losses, P1 swept — the remaining 5 losses are all order-level details in P2/P3, where the baseline happened to keep more clean reserve in the overflow window.',
      },
      portfolio: {
        kicker: 'E10 iteration trajectory',
        title: 'Portfolio: wins climb monotonically',
        wins: 'wins',
        losses: 'losses',
        iterLabel: 'iteration',
        caption:
          'Each step adds one new candidate order to the portfolio and picks by the true official key; wins rise monotonically from 8 to 13. Play through iter034 → iter038 — adding a candidate never regresses the score.',
        controls: {
          play: 'Play',
          pause: 'Pause',
          restart: 'Restart',
          prevStep: 'Previous step',
          nextStep: 'Next step',
        },
      },
      workingSet: {
        kicker: 'D inevitability certificate',
        title: 'Working-set bound: when spills are unavoidable',
        capacityBound: 'capacity-bound (spill unavoidable)',
        orderReachable: 'order-reachable (reordering helps)',
        ratioAxis: 'near-optimal working-set bound / capacity',
        caption:
          'For each (case, cache) we compute the ratio of the near-optimal working-set peak lower bound to capacity. A ratio > 1 means even an optimal reorder cannot fit — spills are unavoidable and chasing order is futile; one should instead optimize the spill structure itself.',
        note: 'Matmul_Case1 / L1 reaches 8.5: strongly capacity-bound, with extra already near the lower bound.',
      },
    },
  },
}
