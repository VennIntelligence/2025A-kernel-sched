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

export type ResidencyCopy = {
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
    clean: { term: string; body: string }
    dirty: { term: string; body: string }
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
    ordersTitle: string
    orders: Array<{ tag: string; name: string; body: string }>
    victimTitle: string
    victimBody: string
    residency: ResidencyCopy
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
    mainTitle: string
    mainCaption: string
    mainCols: { instance: string; cpList: string; pressure: string; gHsu: string; cpFree: string; ours: string }
    lowerBetter: string
    baselinesLabel: string
    baselinesCaption: string
    applicTitle: string
    applicBody: string
    applicLabel: string
    applicCaption: string
    ablationTitle: string
    ablationBody: string
    benchTitle: string
    benchCaption: string
    benchCols: { instance: string; opType: string; nodes: string; edges: string; buffers: string }
    runtimeTitle: string
    runtimeCaption: string
    runtimeCols: { instance: string; p1: string; p2: string; p3: string }
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
      brand: 'Liveness Shaping',
      overview: '概览',
      problem: '赛题图解',
      method: '方法',
      results: '实验',
      cite: '引用',
    },
    meta: {
      venue: '编译优化 · 投稿 CGO ’27',
      title: '调度序驱动的驻留构成优化：面向 NPU 的溢出代价感知方法',
      authors: [
        { name: '高成志', email: 'contact@vennai.org' },
        { name: '黄骏', email: 'hj992881627@outlook.com' },
        { name: '叶勤', email: 'yq020319@163.com' },
      ],
      affiliation: '东南大学 · 文氏智能',
      links: [
        { label: '论文', kind: 'paper', href: `${REPO}/blob/master/paper/dist/en_conf.pdf` },
        { label: '代码', kind: 'code', href: REPO },
        { label: '数据', kind: 'data', href: `${REPO}/tree/master/data` },
        { label: '结果', kind: 'results', href: `${REPO}/tree/master/results` },
      ],
      fig1Label: '图 1 · 概念图',
      fig1Caption:
        '溢出代价感知的活跃度塑形。两个容量压力相近的合法调度，会向驱逐过程暴露出不同的 clean/dirty 构成。当 clean 缓冲在高压窗口保持常驻时，同等大小的换出可避免写回，从而降低额外搬运。',
      fig2Label: '方法总览',
      fig2Caption:
        '优化框架的三个阶段：(1) 判定溢出是否不可避免，决定是否需要优化；(2) 通过活跃度塑形生成三条互补的候选拓扑序；(3) 沿每条序执行地址分配与 spill 插入，再以字典序键在候选序与预取窗口之间择优。',
    },
    abstract: {
      title: '摘要',
      body:
        '深度学习编译器在将算子编译为核函数时，会产生由微操作、短生命周期张量和异构流水线组成的有向无环图。由于片上缓存容量有限，不同的合法调度顺序会导致差异巨大的内存峰值和数据溢出流量。本文揭示了现有调度算法常忽略的一个结构性非对称特征：从主存读入且已有备份的“干净”数据在被驱逐时无需写回，而计算产生的“脏”数据则必须写回，两者的溢出代价截然不同。基于此，本文提出一种溢出代价感知的活跃度（liveness）塑形方法，通过主动调整容量受限时干净与脏数据的驻留比例，优先驱逐低代价数据，从而保留片上缓存储备。理论上，本文给出单侧的溢出必然性证书，用于判定溢出在近最优调度中是否不可避免，并建立了溢出面积与额外访存流量之间的有条件常数近似关系。基于公开 NPU 风格调度实例、合成分布、小图 oracle 与受控消融的实验表明，clean/dirty 无感的内存压力调度器在容量受限区域会多付 2.4–26× 的 P2 溢出流量。',
    },
    highlights: {
      title: '核心结果',
      items: [
        { value: '2.4–26×', label: 'clean/dirty 无感调度器多付的 P2 溢出流量（中位约 11×）' },
        { value: '2×', label: 'clean 与 dirty 换出代价的精确差距' },
        { value: '4 个层级', label: '公开基准 · 合成分布 · 小图 oracle · 受控消融' },
      ],
    },
    contributions: {
      title: '三项贡献',
      lead: '从一个被现有调度器忽略的结构性非对称出发，给出可诊断、可解释、可泛化的方法与理论。',
      items: [
        {
          tag: '贡献 1',
          name: '溢出代价感知的活跃度塑形',
          body:
            '为 NPU 核内 DAG 形式化“活跃度塑形”：通过改变合法拓扑序控制溢出窗口内的 clean/dirty 驻留构成，在容量紧张时保留低成本的可换出储备。',
        },
        {
          tag: '贡献 2',
          name: '溢出区间的理论刻画',
          body:
            '溢出必然性证书给出单侧、线性时间的诊断，识别任何近最优调度都无法避免溢出的情形；Belady-margin 稳定性说明调度序而非驱逐规则是主要优化自由度；溢出面积定理在有界缺席时长下把廉价代理与最优溢出流量以常数因子相连。',
        },
        {
          tag: '贡献 3',
          name: '四层级系统实验',
          body:
            '在公开 NPU 基准、合成 DAG 分布、小图 oracle 与受控消融四个层级上验证：收益恰好集中在定理判定为容量受限的区域，而 clean/dirty 无感的压力调度器要多付 2.4–26× 的溢出流量。',
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
    model: {
      eyebrow: '问题模型',
      title: '干净 / 脏缓冲，与三个嵌套视角',
      lead:
        '输入是神经算子的微操作图 G。节点分两类：算子节点执行计算或数据搬运，携带执行单元、时延与读写缓冲集；缓存管理节点标记缓冲生命周期的起止。每个逻辑缓冲 b 有大小 s_b、缓存类型 τ(b) 与容量 Cap_c。调度 S 是全部节点的一个合法拓扑序。',
      figLabel: '图 2 · 微操作 DAG',
      figCaption:
        '一个微操作 DAG。粉色节点是缓存管理事件（分配/释放），蓝色节点是算子。缓冲 b₀ 由片外读入、已有备份，故为 clean（κ=1）；b₁ 由计算产生，故为 dirty（κ=2）。',
      clean: {
        term: 'Clean 缓冲',
        body: '由从片外读数据的算子写入，片外已有备份；换出时无需写回，仅产生重载代价 e_b = s_b。',
      },
      dirty: {
        term: 'Dirty 缓冲',
        body: '由计算产生；若后续仍被使用，换出需先写回再重载，额外流量 e_b = 2 s_b。',
      },
      asideTitle: '相同容量，2× 代价',
      asideBody:
        'clean 与 dirty 缓冲占用相同的片上空间，溢出代价却相差 2×。因此，让溢出窗口内保留更多 clean 储备的调度序，可同时改善驻留、流量与时序。这一非对称是本文方法的核心建模特征。',
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
          body: '加入物理地址分配与 spill 插入，最小化总额外搬运。本文以 P2 为主视角，它直接度量活跃度塑形所针对的溢出代价。',
        },
        {
          tag: 'P3',
          title: '流水线时间',
          formula: 'T = maxᵥ E(v)',
          body: '在固定序下，计入依赖与流水线约束模拟最早完成时间。三个视角共享同一套 clean/dirty 非对称流量模型。',
        },
      ],
    },
    method: {
      eyebrow: '方法',
      title: '优化调度序，而非驱逐规则',
      lead:
        '已有调度器把溢出当作容量超限后的局部后果，在固定序上套一个驱逐规则。我们的实验表明这是错误的主自由度：在固定序上，四种 Belady 式驱逐变体的额外流量通常相差不超过 4%，而不同的合法序可摆动一个数量级以上。因此本方法转而优化调度序，塑形溢出窗口内的 clean/dirty 构成。',
      stagesTitle: '三个阶段',
      stages: [
        {
          n: '1',
          title: '溢出诊断',
          body:
            '判定给定 DAG 与容量下溢出是否不可避免。若不可避免，目标便从“消除溢出”转为“降低其代价”，溢出面积 Φ 成为廉价的跨阶段代理。',
        },
        {
          n: '2',
          title: '候选序生成与地址分配',
          body:
            '生成三条互补的拓扑序，沿每条序执行 best-fit 放置与代价感知的 spill 插入（见地址分配算法）。',
        },
        {
          n: '3',
          title: '择优',
          body:
            '模拟候选序 × 预取窗口的笛卡尔积，按真实字典序键择优：P2 用 (E, n, T)，P3 用 (T, E, n)。加入新候选只会改善或持平所选目标，永不回退。',
        },
      ],
      pipelineLabel: '方法总览',
      pipelineCaption:
        '三阶段流水线：先判定溢出必然性，再围绕溢出面积生成与筛选候选，最后在真实官方键上择优。',
      ordersTitle: '三条互补的候选拓扑序',
      orders: [
        {
          tag: '序 1',
          name: '压力感知序',
          body: '分配节点按后继入度排序：入度越小，消费者越快就绪，故可把分配延迟到接近使用处。',
        },
        {
          tag: '序 2',
          name: '容量节流序',
          body: '在压力感知序上加入容量门控：会超出缓存容量的分配被推迟，直到无法再延；容量权重按 1/Cap_c 归一化以平衡不同稀缺度的缓存。',
        },
        {
          tag: '序 3',
          name: 'ID 储备序',
          body: '在三类节点内取最小编号、不做容量节流。它是方法的候选而非外部基线：用于保留稳定的输入缓冲顺序，让 clean 的 COPY_IN 缓冲贯穿计算窗口常驻，在溢出区留下廉价储备。',
        },
      ],
      victimTitle: '序主导，驱逐规则次要',
      victimBody:
        '给定一条序，引擎按 argmaxᵦ d(b)·s_b/e_b 选择驱逐对象——即 clean 取 d(b)、dirty 取 d(b)/2——因此在 next-use 距离相近时偏好廉价的 clean 换出。由 Belady-margin 命题，当 next-use 距离占主导时所有此类规则选同一组驱逐对象：固定序上四种驱逐变体仅相差 ≤4%，而不同合法序可让额外流量摆动 10× 以上。',
      residency: {
        kicker: 'E5 · E6 容量溢出积分',
        title: 'Φ：把“溢出面积”当作代理目标',
        idRaw: 'id_raw（我们）',
        baseline: 'baseline',
        capacity: '容量 4096',
        phi: 'Φ 溢出面积',
        clean: 'clean 驻留',
        dirty: 'dirty 驻留',
        cleanAtPeak: '峰值处 clean 储备',
        caption:
          'Conv_Case0 的 L1 逻辑驻留沿调度序展开：超过容量线的阴影面积即容量溢出积分 Φ。我们的 id_raw 序在溢出峰值处保留了更多 clean 缓冲（廉价可驱逐），baseline 则几乎全是 dirty。切换两条曲线对比峰值处的 clean 储备。',
        surrogateNote: 'Φ ↔ extra 的 Spearman = 0.958，与 peak ↔ extra（0.955）几乎等价——Φ 是廉价而可靠的代理信号。',
      },
    },
    theory: {
      eyebrow: '理论',
      title: '方法在何处生效',
      lead: '三条结果界定了本方法的适用区间，并解释了“驱逐规则不敏感、调度序高度敏感”的实验现象。证明见补充材料。',
      wsLabel: '图 5 · 工作集下界',
      wsCaption:
        '每个 (算例, 缓存) 在近最优 extra 子集上的工作集 / 容量比。比值 > 1 意味着即便最优重排也放不下、溢出不可避免。红色的 Matmul_Case1 / L1 高达 8.5，在近最优口径下远超容量——正是溢出必然性证书（定理 1）的实证。',
      items: [
        {
          tag: '定理 1',
          name: '溢出必然性证书',
          statement:
            '若近最优序集合上的工作集下界 W̲ᶜ_ε 仍超过容量 Cap_c，则其中每个调度都必须在缓存 c 上溢出，且 extra(P) ≥ maxₜ(Wᶜ(t) − Cap_c)₊。这是一个单侧、线性时间的诊断：它确认溢出何时不可避免，从而标出“必须优化代价构成”的区域。',
          note: '在全部小图 CP-SAT oracle 上成立。',
        },
        {
          tag: '命题 1',
          name: 'Belady-margin 稳定性',
          statement:
            '对代价因子比 ρ = g_max/g_min ≤ 2 的距离主导评分规则：若所选驱逐者中最小的 next-use 距离大于 ρ 倍的非驱逐者最大距离，则所有此类规则选出相同的驱逐集合——这解释了为何调度序而非驱逐调参才是主要自由度。',
          note: '固定序驱逐 CV：Matmul/FA 上 ≈ 0，Conv 上 ≤ 4%。',
        },
        {
          tag: '定理 2',
          name: '溢出面积的有条件近似',
          statement:
            '在缺席时长有界时，溢出面积 A(S) 双边界定最优溢出流量：(1/L)·A(S) ≤ E⋆(S) ≤ (2λ/ℓ)·A(S)。这为 O(N) 的代理 Φ 在容量受限区域给出了一致的跨阶段依据。',
          note: '实测 E⋆/A ∈ [0.56, 1.13]；Spearman(Φ, extra)=0.958 vs peak 0.955。',
        },
      ],
    },
    results: {
      eyebrow: '实验',
      title: '四个层级的证据',
      lead:
        '实验检验本文的核心论断：当容量溢出不可避免时，调度序能否通过改变峰值窗口内的 clean/dirty 构成降低真实溢出代价。关键是“同引擎口径”——每个对照与本方法共享同一套 best-fit 地址分配与 spill 引擎，只替换输入拓扑序，从而把流量差异干净地归因于序如何塑形驻留构成。',
      mainTitle: '共享 spill 引擎下的 P2 溢出流量 E(S)',
      mainCaption:
        '越低越好，每行最优值加粗。clean/dirty 无感的压力序与 Goodman–Hsu 序在每个算例上都多付 2.4–26×（中位约 11×）；纯关键路径序更远，达 8–54×。在全部 6 算例 × 3 视角 × 4 对照（72 个组合）中，我们的序在每一个上都不劣。',
      mainCols: { instance: '算例', cpList: 'CP list', pressure: 'Pressure', gHsu: 'G–Hsu', cpFree: 'CP-free', ours: 'Ours' },
      lowerBetter: '越低越好',
      baselinesLabel: '图 3 · 标准调度器对比',
      baselinesCaption:
        '对数坐标下的标准调度器 P2 溢出流量对比。所有序共享同一套地址分配与 spill 引擎，只改变拓扑序。',
      applicTitle: '方法的适用边界',
      applicBody:
        '在一个合成 DAG 分布上，证书判定为容量受限的区域里，本方法对关键路径序与随机序 100% 取胜、对更强的 free-first 对照 77.8% 取胜，中位 2× 优势；而在“序可达”实例中，好的序本就能避免溢出，系统性优势随之消失（对 free-first 为 0%）。方法的有效性与证书的前提条件高度吻合。',
      applicLabel: '图 4 · 合成区间上的适用性',
      applicCaption:
        '不同合成区间上的适用性。左：本方法对各对照的胜率。右：额外流量中位比（ours/对照，越低越好），虚线为持平线。',
      ablationTitle: '受控 clean / dirty 消融',
      ablationBody:
        '合成 GEMM 核固定相同的 DAG 结构、spill 次数与峰值，只改变峰值窗口内储备的类型：clean 储备产生 1,536 单位额外流量，dirty 储备 3,072——恰好 2×。进一步的序扫描显示，额外流量随峰值处 clean 占比上升而单调下降。',
      benchTitle: '评测算例',
      benchCaption: '六个公开 NPU 核内调度实例，覆盖三大算子族；|V| 从约 1.7k 到 36k 节点。',
      benchCols: { instance: '算例', opType: '算子族', nodes: '|V|', edges: '|E|', buffers: '缓冲区' },
      runtimeTitle: '求解器运行时间',
      runtimeCaption:
        '墙钟秒数，三次重复取中位。P1 在每个实例上均于 0.2 s 内完成；P2/P3 随规模增长，最大算例 P3 约 73 s。',
      runtimeCols: { instance: '算例', p1: 'P1 (s)', p2: 'P2 (s)', p3: 'P3 (s)' },
      capTitle: '缓存容量',
      capBody: '五种片上缓存（抽象单位）：L1 4096，UB 1024，L0A 256，L0B 256，L0C 512。',
    },
    related: {
      title: '相关工作中的定位',
      body: [
        '调度与内存优化的联合优化由来已久。COSMA 等工作以 ILP 联合优化算子调度、内存分配与张量替换，求解的是图级放置与替换问题。NPU 核内 scratchpad 调度的粒度细得多：clean/dirty 状态引入 2× 的溢出代价非对称，调度序不仅决定活跃峰值，更决定暴露给驱逐的缓冲的代价构成。',
        '编译器后端早已认识到调度与活跃区间的耦合：Goodman–Hsu 式集成预调度、寄存器压力感知调度，以及“clean 值可免写回换出”的替换启发式。“调度影响活跃度”与“clean 驱逐更便宜”各自并不新；新的自由度在于请求序本身可被改变——编译器可主动塑形活跃区间重叠与 clean/dirty 构成，而不只是为固定流选择驱逐者。',
        '重物化、激活检查点与免溢出编译从另一方向缓解内存压力，与本方法互补。在大规模核内调度中，容量约束常使部分溢出不可避免；此时可重载的输入缓冲构成天然的 clean 储备，核心问题便是调度序如何降低不可避免换出的写回代价。',
      ],
    },
    conclusion: {
      title: '结论',
      body:
        'clean 与 dirty 溢出代价之间 2× 的非对称，意味着调度序不仅控制活跃峰值，还控制容量压力窗口内可供驱逐的缓冲的代价构成。当溢出不可避免时，保留更多廉价可换出的 clean 储备能显著降低真实片外流量。围绕这一发现，溢出必然性证书、有条件溢出面积近似与 Belady-margin 稳定性三条结果，共同解释了“驱逐规则不敏感、调度序高度敏感”的实验规律。',
      futureTitle: '未来工作',
      future:
        '将活跃度塑形扩展到多核调度与跨核缓存一致性；支持含动态控制流（分支、循环）的图；以及在更深的存储层次中建模跨级溢出级联。',
    },
    cite: {
      title: '引用',
      lead: '若本工作对你有帮助，欢迎引用。',
      bibtex:
        '@inproceedings{gao2027liveness,\n  title     = {Spill-Cost-Aware Liveness Shaping for NPU Intra-Kernel Scheduling},\n  author    = {Gao, Chengzhi and Huang, Jun and Ye, Qin},\n  booktitle = {Proc. 2027 IEEE/ACM Int. Symp. on Code Generation and Optimization (CGO)},\n  year      = {2027}\n}',
      copy: '复制',
      copied: '已复制',
    },
    footer: {
      tagline: '调度序驱动的驻留构成优化 · 面向 NPU 的溢出代价感知方法',
      note: '页面的图表与数字均取自本仓库的论文源文件与结果 CSV。',
    },
  },

  en: {
    nav: {
      brand: 'Liveness Shaping',
      overview: 'Overview',
      problem: 'Problem',
      method: 'Method',
      results: 'Results',
      cite: 'Cite',
    },
    meta: {
      venue: 'Compiler Optimization · CGO ’27 submission',
      title: 'Spill-Cost-Aware Liveness Shaping for NPU Intra-Kernel Scheduling',
      authors: [
        { name: 'Chengzhi Gao', email: 'contact@vennai.org' },
        { name: 'Jun Huang', email: 'hj992881627@outlook.com' },
        { name: 'Qin Ye', email: 'yq020319@163.com' },
      ],
      affiliation: 'Southeast University · Venn Intelligence',
      links: [
        { label: 'Paper', kind: 'paper', href: `${REPO}/blob/master/paper/dist/en_conf.pdf` },
        { label: 'Code', kind: 'code', href: REPO },
        { label: 'Data', kind: 'data', href: `${REPO}/tree/master/data` },
        { label: 'Results', kind: 'results', href: `${REPO}/tree/master/results` },
      ],
      fig1Label: 'Figure 1 · Concept',
      fig1Caption:
        'Spill-cost-aware liveness shaping. Two legal schedules can have similar capacity pressure while exposing different clean/dirty compositions to the eviction process. Keeping clean buffers resident in high-pressure windows provides low-cost eviction reserve and reduces off-chip traffic.',
      fig2Label: 'Method overview',
      fig2Caption:
        'The optimization framework has three stages: (1) inevitable-spill determination decides whether optimization is needed; (2) three complementary candidate topological orders are generated via liveness shaping; (3) address assignment and spill insertion run along each order, followed by lexicographic-key selection across candidate orders and prefetch windows.',
    },
    abstract: {
      title: 'Abstract',
      body:
        'Deep-learning compilers lower neural operators into kernel-level DAGs whose nodes mix micro-operations, short-lived tensors, and heterogeneous execution pipes. Under tight on-chip cache capacity, two legal topological orders can have similar peak pressure yet induce very different off-chip spill traffic. This paper identifies a structural asymmetry that standard schedulers often miss: clean buffers loaded from off chip already have a backing copy and need not be written back when evicted, whereas dirty buffers produced by computation must be written before they are later reloaded. The two classes consume identical on-chip capacity but differ by a factor of two in spill cost. We introduce spill-cost-aware liveness shaping, which changes the legal schedule order to control the clean/dirty composition exposed inside capacity-pressure windows, keeping low-cost clean bytes available as eviction reserve. We prove a one-sided certificate for spill inevitability, give a linear-time overflow-area surrogate with a conditional constant-factor connection to optimal spill traffic, and explain why schedule order dominates victim-rule tuning. Experiments on public NPU-style instances, synthetic DAG distributions, small-graph oracles, and controlled ablations show that clean/dirty-blind pressure schedulers can pay 2.4–26× more P2 spill traffic in capacity-bound regimes.',
    },
    highlights: {
      title: 'Headline results',
      items: [
        { value: '2.4–26×', label: 'extra P2 spill traffic paid by clean/dirty-blind schedulers (median ~11×)' },
        { value: '2×', label: 'exact clean-vs-dirty eviction-cost gap' },
        { value: '4 layers', label: 'public benchmarks · synthetic · oracle · ablation' },
      ],
    },
    contributions: {
      title: 'Three contributions',
      lead: 'From a structural asymmetry that existing schedulers overlook, to a diagnosable, interpretable, and generalizable method with theory.',
      items: [
        {
          tag: 'Contribution 1',
          name: 'Spill-cost-aware liveness shaping',
          body:
            'We formulate liveness shaping for NPU intra-kernel DAGs: change the legal schedule order to control the clean/dirty residency composition in overflow windows, preserving low-cost eviction reserve when capacity is tight.',
        },
        {
          tag: 'Contribution 2',
          name: 'Theory of the regime',
          body:
            'A spill-inevitability certificate gives a one-sided, linear-time diagnostic for cases no near-optimal schedule can avoid spilling; a Belady-margin stability result shows schedule order, not the victim rule, is the main degree of freedom; an overflow-area theorem ties a cheap surrogate to optimal spill traffic within constant factors under bounded absence durations.',
        },
        {
          tag: 'Contribution 3',
          name: 'Four-level evaluation',
          body:
            'Across public NPU benchmarks, synthetic DAG distributions, small-graph oracles, and controlled ablations: benefits concentrate exactly in regions the certificate marks capacity-bound, where clean/dirty-blind pressure schedulers pay 2.4–26× more spill traffic.',
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
    model: {
      eyebrow: 'Problem model',
      title: 'Clean and dirty buffers, three nested views',
      lead:
        'The input is a micro-operation graph G for a neural operator. Its nodes have two types: operation nodes execute computation or data movement and carry execution units, latencies, and read/write buffer sets; cache-management nodes mark the beginning and end of buffer lifetimes. Each logical buffer b has a size s_b, a cache type τ(b), and a capacity Cap_c. A schedule S is a topological order of all required nodes.',
      figLabel: 'Figure 2 · Micro-operation DAG',
      figCaption:
        'A micro-operation DAG. Pink nodes are cache-management events (allocation/free); blue nodes are operations. Buffer b₀ is loaded from off-chip memory and already has a backing copy, so it is clean (κ=1); b₁ is produced by computation, so it is dirty (κ=2).',
      clean: {
        term: 'Clean buffer',
        body: 'Written by an operation that reads from off-chip memory; off-chip already holds a backing copy, so eviction needs no write-back and costs only a reload e_b = s_b.',
      },
      dirty: {
        term: 'Dirty buffer',
        body: 'Produced by computation; if used again, eviction requires a write-back and a later reload, for extra traffic e_b = 2 s_b.',
      },
      asideTitle: 'Identical capacity, 2× cost',
      asideBody:
        'Clean and dirty buffers occupy identical on-chip space, yet their spill costs differ by 2×. So an order that keeps more clean reserve in overflow windows can improve residency, traffic, and timing at once. This asymmetry is the core modeling feature of our method.',
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
          body: 'Adds physical address assignment and spill insertion; minimizes total extra traffic. We take P2 as the primary view — it directly measures the spill cost liveness shaping targets.',
        },
        {
          tag: 'P3',
          title: 'Pipelined time',
          formula: 'T = maxᵥ E(v)',
          body: 'Simulates earliest completion under dependency and pipe constraints for a fixed order. All three views share one asymmetric clean/dirty traffic model.',
        },
      ],
    },
    method: {
      eyebrow: 'Method',
      title: 'Optimize the schedule order, not the victim rule',
      lead:
        'Existing schedulers treat spills as a local consequence after capacity is exceeded, then apply a victim rule to a fixed order. Our experiments show this is the wrong primary degree of freedom: on a fixed order, four Belady-style victim variants usually differ by at most 4% in extra traffic, whereas legal schedule orders can vary by more than an order of magnitude. Our method therefore optimizes schedule order to shape the clean/dirty composition of overflow windows.',
      stagesTitle: 'Three stages',
      stages: [
        {
          n: '1',
          title: 'Spill diagnosis',
          body:
            'Decide whether spills are unavoidable for the given DAG and capacity. If they are, the objective shifts from eliminating spills to lowering their cost, and overflow area Φ becomes a cheap cross-stage surrogate.',
        },
        {
          n: '2',
          title: 'Candidate orders & assignment',
          body:
            'Produce three complementary topological orders, then run best-fit placement with cost-aware spill insertion along each order (see the assignment algorithm).',
        },
        {
          n: '3',
          title: 'Selection',
          body:
            'Simulate the Cartesian product of candidate orders and prefetch windows; pick the best by the true lexicographic key — (E, n, T) for P2, (T, E, n) for P3. Adding a candidate can only improve or tie the selected objective.',
        },
      ],
      pipelineLabel: 'Method overview',
      pipelineCaption:
        'A three-stage pipeline: determine spill inevitability, generate and filter candidates around overflow area, then select on the true official key.',
      ordersTitle: 'Three complementary candidate orders',
      orders: [
        {
          tag: 'Order 1',
          name: 'Pressure-aware',
          body: 'Allocation nodes are ranked by successor indegree; a smaller indegree means consumers become ready soon, so the allocation can be delayed until close to use.',
        },
        {
          tag: 'Order 2',
          name: 'Capacity-throttled',
          body: 'The pressure-aware order plus capacity gating: an allocation that would exceed cache capacity is skipped until no further delay is possible; capacity weights are normalized by 1/Cap_c to balance caches of different scarcity.',
        },
        {
          tag: 'Order 3',
          name: 'ID-reserve',
          body: 'Minimum-identifier order with no throttling — a method candidate, not an external baseline: it preserves the stable input-buffer order that keeps clean COPY_IN buffers resident through compute windows, leaving cheap eviction reserve in overflow regions.',
        },
      ],
      victimTitle: 'Order dominates the victim rule',
      victimBody:
        'Given an order, the engine picks the victim by argmaxᵦ d(b)·s_b/e_b — i.e. d(b) for clean buffers, d(b)/2 for dirty — so it prefers cheap clean evictions when next-use distances are comparable. By the Belady-margin result, when next-use distance dominates, all such rules select the same victims: on a fixed order four variants differ by ≤4%, while legal orders swing extra traffic by more than 10×.',
      residency: {
        kicker: 'E5 · E6 capacity-overflow integral',
        title: 'Φ: treating the “overflow area” as a surrogate',
        idRaw: 'id_raw (ours)',
        baseline: 'baseline',
        capacity: 'capacity 4096',
        phi: 'Φ overflow area',
        clean: 'clean residency',
        dirty: 'dirty residency',
        cleanAtPeak: 'clean reserve at peak',
        caption:
          'L1 logical residency for Conv_Case0 unrolled along the schedule: the shaded area above the capacity line is the capacity-overflow integral Φ. Our id_raw order keeps more clean buffers (cheaply evictable) resident at the overflow peak, while the baseline is almost all dirty. Toggle the two curves to compare the clean reserve at the peak.',
        surrogateNote: 'Spearman(Φ, extra) = 0.958, nearly identical to Spearman(peak, extra) = 0.955 — Φ is a cheap, reliable surrogate.',
      },
    },
    theory: {
      eyebrow: 'Theory',
      title: 'Where the method applies',
      lead: 'Three results delimit the regime and explain the empirical pattern of an insensitive victim rule alongside a highly sensitive schedule order. Proofs are in the supplementary material.',
      wsLabel: 'Figure 5 · Working-set bound',
      wsCaption:
        'The near-optimal working-set / capacity ratio per (case, cache), computed over the near-optimal extra subset. A ratio > 1 means even an optimal reorder cannot fit — spills are unavoidable. Matmul_Case1 / L1 (red) reaches 8.5, far above capacity — an empirical instance of the spill-inevitability certificate (Theorem 1).',
      items: [
        {
          tag: 'Theorem 1',
          name: 'Spill-inevitability certificate',
          statement:
            'If the near-optimal working-set lower bound W̲ᶜ_ε still exceeds capacity Cap_c, then every schedule in that near-optimal set must spill on cache c, and extra(P) ≥ maxₜ(Wᶜ(t) − Cap_c)₊. A one-sided, linear-time diagnostic: it confirms when spills are unavoidable, marking the regime where the cost composition must be optimized.',
          note: 'Holds on every small CP-SAT oracle graph.',
        },
        {
          tag: 'Proposition 1',
          name: 'Belady-margin stability',
          statement:
            'For distance-dominant scoring rules with cost-factor ratio ρ = g_max/g_min ≤ 2: if the smallest next-use distance among selected victims exceeds ρ times the largest distance among non-victims, all such rules select the same victim set — explaining why schedule order, not victim tuning, is the main lever.',
          note: 'Fixed-order victim CV ≈ 0 on Matmul/FA, ≤ 4% on Conv.',
        },
        {
          tag: 'Theorem 2',
          name: 'Conditional overflow-area approximation',
          statement:
            'Under bounded absence durations, the overflow area A(S) brackets optimal spill traffic: (1/L)·A(S) ≤ E⋆(S) ≤ (2λ/ℓ)·A(S). This gives the O(N) surrogate Φ a consistent cross-stage justification in capacity-bound regimes.',
          note: 'Empirically E⋆/A ∈ [0.56, 1.13]; Spearman(Φ, extra) = 0.958 vs peak 0.955.',
        },
      ],
    },
    results: {
      eyebrow: 'Experiments',
      title: 'Evidence at four levels',
      lead:
        'The experiments test the central claim: when capacity overflow is unavoidable, can schedule order reduce real spill cost by changing the clean/dirty composition inside peak-pressure windows? The common thread is a same-engine caliber — every comparator and our method share one best-fit address-assignment and spill engine, swapping only the input topological order, so traffic differences attribute cleanly to how order shapes residency.',
      mainTitle: 'P2 spill traffic E(S) under a shared spill engine',
      mainCaption:
        'Lower is better; the best value in each row is bold. Clean/dirty-blind pressure and Goodman–Hsu orders pay 2.4–26× more (median ~11×); pure critical-path is 8–54× away. Across all 6 cases × 3 views × 4 comparators (72 combinations), our order is lower or equal in every one.',
      mainCols: { instance: 'Instance', cpList: 'CP list', pressure: 'Pressure', gHsu: 'G–Hsu', cpFree: 'CP-free', ours: 'Ours' },
      lowerBetter: 'lower is better',
      baselinesLabel: 'Figure 3 · Standard scheduler comparison',
      baselinesCaption:
        'Standard scheduler comparison for P2 spill traffic on a log scale. All orders use the same address-assignment and spill engine; only the topological order changes.',
      applicTitle: 'Where the benefit applies',
      applicBody:
        'On a synthetic DAG distribution, in regions the certificate marks capacity-bound our method wins 100% against critical-path and random orders and 77.8% against the strong free-first companion, with a median 2× advantage. In order-reachable instances a good order avoids spills outright and the systematic advantage disappears (0% vs free-first). Effectiveness tracks the certificate’s precondition closely.',
      applicLabel: 'Figure 4 · Applicability across synthetic regimes',
      applicCaption:
        'Applicability across synthetic regimes. Left: win rate of our method against each comparator. Right: median extra-traffic ratio (ours/comparator; lower is better), with the dashed line marking parity.',
      ablationTitle: 'Controlled clean / dirty ablation',
      ablationBody:
        'Synthetic GEMM kernels fix the same DAG structure, spill count, and peak, changing only the reserve type inside the peak window. Clean reserve incurs 1,536 units of extra traffic, dirty reserve 3,072 — exactly 2×. A schedule sweep shows extra traffic decreasing monotonically as the clean fraction at the peak rises.',
      benchTitle: 'Benchmark instances',
      benchCaption: 'Six public NPU intra-kernel scheduling instances across three operator families; |V| from about 1.7k to 36k nodes.',
      benchCols: { instance: 'Instance', opType: 'Op. type', nodes: '|V|', edges: '|E|', buffers: 'Buffers' },
      runtimeTitle: 'Solver runtime',
      runtimeCaption:
        'Wall-clock seconds, median of three repetitions. P1 finishes within 0.2 s on every instance; P2/P3 grow with size, reaching about 73 s for P3 on the largest case.',
      runtimeCols: { instance: 'Instance', p1: 'P1 (s)', p2: 'P2 (s)', p3: 'P3 (s)' },
      capTitle: 'Cache capacities',
      capBody: 'Five on-chip caches (abstract units): L1 4096, UB 1024, L0A 256, L0B 256, L0C 512.',
    },
    related: {
      title: 'Positioning in related work',
      body: [
        'Joint scheduling and memory optimization has a long history. Work such as COSMA optimizes operator schedule, memory allocation, and tensor replacement together with an ILP, solving a graph-level placement and replacement problem. NPU intra-kernel scratchpad scheduling operates at a far finer micro-operation granularity, where clean and dirty states introduce a 2× spill-cost asymmetry and order determines not only the live-byte peak but the cost composition of the buffers exposed to eviction.',
        'Compiler back ends have long coupled scheduling with live ranges — Goodman–Hsu integrated prepass scheduling, register-pressure-aware schedulers, and clean-value-cheap replacement heuristics. “Schedule affects liveness” and “clean victims are cheaper” are each known in isolation; the new freedom here is that the request order itself can be changed, so a compiler can actively shape live-range overlap and clean/dirty composition rather than only choose victims for a fixed stream.',
        'Rematerialization, activation checkpointing, and spill-free compilation attack memory pressure from a different direction and are complementary. In large kernel-level NPU schedules, capacity often makes some spills unavoidable; reloadable input buffers then form a natural clean reserve, and the central question becomes how schedule order reduces the write-back cost of unavoidable evictions.',
      ],
    },
    conclusion: {
      title: 'Conclusion',
      body:
        'The 2× asymmetry between clean and dirty spill costs means schedule order controls not only peak live bytes, but the cost composition of the buffers available for eviction in capacity-pressure windows. When spills are unavoidable, keeping more cheaply evictable clean reserve substantially reduces real off-chip traffic. Around this finding, a spill-inevitability certificate, a conditional overflow-area approximation, and a Belady-margin stability result together explain the empirical pattern of an insensitive victim rule alongside a highly sensitive schedule order.',
      futureTitle: 'Future work',
      future:
        'Extending liveness shaping to multi-core scheduling and cross-core cache coherence; supporting graphs with dynamic control flow such as branches and loops; and modeling cross-level spill cascades in deeper memory hierarchies.',
    },
    cite: {
      title: 'Cite',
      lead: 'If you build on this work, please cite the paper.',
      bibtex:
        '@inproceedings{gao2027liveness,\n  title     = {Spill-Cost-Aware Liveness Shaping for NPU Intra-Kernel Scheduling},\n  author    = {Gao, Chengzhi and Huang, Jun and Ye, Qin},\n  booktitle = {Proc. 2027 IEEE/ACM Int. Symp. on Code Generation and Optimization (CGO)},\n  year      = {2027}\n}',
      copy: 'Copy',
      copied: 'Copied',
    },
    footer: {
      tagline: 'Spill-Cost-Aware Liveness Shaping · NPU Intra-Kernel Scheduling',
      note: 'All figures and numbers on this page are drawn from the paper sources and result CSVs in this repository.',
    },
  },
}
