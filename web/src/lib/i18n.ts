export type Language = 'zh' | 'en'

export type PageId = 'home' | 'problem'

export type LinkKind = 'paper' | 'code' | 'data' | 'results'

export type StageCopy = { tab: string; title: string; detail: string }

export type FieldRow = { name: string; type: string; desc: string }

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

export type Copy = {
  nav: {
    brand: string
    home: string
    problem: string
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
    controls: {
      play: string
      pause: string
      restart: string
      prevStep: string
      nextStep: string
    }
    legend: { cache: string; op: string; spill: string }
    stages: StageCopy[]
    problems: Array<{ label: string; title: string; formula: string; body: string }>
    data: DataSectionCopy
  }
}

export const copy: Record<Language, Copy> = {
  zh: {
    nav: {
      brand: 'Kernel Scheduling',
      home: '首页',
      problem: '赛题图解',
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
        '本项目研究给定神经算子计算 DAG 时，如何在依赖、缓存容量、物理地址、spill 与多流水线互斥约束下构造高质量调度。我们将问题分解为三个递进目标：最小化峰值驻留 maxV_stay、最小化 spill 额外搬运量、最小化流水线总执行时间 T = max E(v)。本页后续将呈现算法设计、benchmark 结果与论文结论。',
      teaserCaption: '调度 → 物理放置 → 多流水线执行：一个实例贯穿三个子问题。',
      animationTitle: '赛题图解',
      animationBody:
        '交互式五阶段图解用同一个迷你实例讲清赛题全貌：DAG 拓扑结构、V_stay 前缀扫描、物理地址碎片化、spill 重定位、以及多流水线时序评价。',
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
  },
  en: {
    nav: {
      brand: 'Kernel Scheduling',
      home: 'Home',
      problem: 'Problem Explainer',
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
        'This project studies how to construct high-quality schedules for neural-operator computation DAGs under dependency, cache-capacity, physical-address, spill, and multi-pipe exclusivity constraints. The task decomposes into three progressive objectives: minimize peak residency maxV_stay, minimize spill-induced extra DDR traffic, and minimize the pipelined makespan T = max E(v). Algorithm design, benchmark results, and paper findings will be presented here.',
      teaserCaption: 'Schedule → physical placement → pipelined execution: one instance, three subproblems.',
      animationTitle: 'Problem Explainer',
      animationBody:
        'An interactive five-stage figure walks one self-consistent miniature instance through the whole problem: DAG topology, the V_stay prefix scan, address fragmentation, spill relocation, and multi-pipe timing.',
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
  },
}
