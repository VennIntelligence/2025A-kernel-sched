export type Language = 'zh' | 'en'

export type PageId = 'home' | 'problem'

export type Copy = {
  nav: {
    brand: string
    home: string
    problem: string
    language: string
  }
  home: {
    eyebrow: string
    title: string
    lead: string
    placeholderTitle: string
    placeholderBody: string
    openProblem: string
    cards: Array<{ label: string; title: string; body: string }>
  }
  problem: {
    eyebrow: string
    title: string
    lead: string
    animationStage: string
    nextStage: string
    scheduleCursor: string
    summaryTitle: string
    exportTitle: string
    exportBody: string
    stages: Array<{ title: string; detail: string }>
    problems: Array<{ label: string; title: string; body: string }>
  }
}

export const copy: Record<Language, Copy> = {
  zh: {
    nav: {
      brand: 'Kernel Scheduling',
      home: '首页',
      problem: '赛题动画',
      language: 'EN',
    },
    home: {
      eyebrow: 'Kernel Scheduling Research Site',
      title: '算法与结果展示页',
      lead:
        '这里未来会突出我们的调度算法、实验结果、关键指标和论文结论。当前先保留清晰占位，避免在算法内容未定时写死错误叙事。',
      placeholderTitle: '算法与结果占位',
      placeholderBody:
        '后续可以在这里接入 best schedule、peak residency、spill traffic、runtime、benchmark 对比和论文图表。',
      openProblem: '查看赛题讲解动画',
      cards: [
        {
          label: 'Algorithm',
          title: '调度策略',
          body: '预留算法原理、启发式设计、消融实验入口。',
        },
        {
          label: 'Result',
          title: '实验结果',
          body: '预留 maxV_stay、spill cost、pipeline runtime 等核心结果。',
        },
        {
          label: 'Paper',
          title: '论文材料',
          body: '预留论文摘要、图表、复现实验和下载入口。',
        },
      ],
    },
    problem: {
      eyebrow: '赛题问题精确可视化',
      title: '从 DAG 到 cache 与 pipe 调度',
      lead:
        '这个子页面专注解释赛题本身：输入是带 cache event 的 computation DAG，输出是合法 schedule、memory offset 和必要 spill，并在多 pipe 约束下评价执行时间。',
      animationStage: '动画阶段',
      nextStage: '下一阶段',
      scheduleCursor: 'Schedule cursor',
      summaryTitle: '三问目标',
      exportTitle: '静态导出',
      exportBody: 'Vite build 后可直接发布 dist/。',
      stages: [
        {
          title: 'DAG dependency',
          detail: '节点只能生成合法 topological order；边同时表达计算依赖和 buffer 生命周期约束。',
        },
        {
          title: 'Problem 1: maxV_stay',
          detail: '沿 schedule 前缀扫描：ALLOC 增加 Size，FREE 减少 Size，operation 对驻留量贡献 0。',
        },
        {
          title: 'Problem 2: cache offset',
          detail: '同一 cache type 中，同时 resident 的 buffer 必须占用不重叠的 [Offset, Offset+Size-1]。',
        },
        {
          title: 'Problem 2/3: spill segment',
          detail: 'SPILL_OUT / SPILL_IN 移动的是 physical residency，logical BufId 不变。',
        },
        {
          title: 'Problem 3: pipe timing',
          detail: '同一 pipe 按 schedule order 串行，不同 pipe 可并行，但仍要等待 predecessor 完成。',
        },
      ],
      problems: [
        {
          label: 'Problem 1',
          title: 'Topological schedule',
          body: '输出所有原始 node id 的合法顺序，最小化 schedule 前缀中的 maxV_stay。',
        },
        {
          label: 'Problem 2',
          title: 'Cache address and spill',
          body: '为 buffer 分配 physical offset，满足 capacity / non-overlap，必要时输出 spill list。',
        },
        {
          label: 'Problem 3',
          title: 'Pipelined runtime',
          body: '加入 spill 和 address reuse dependency 后，在多 pipe 串行约束下最小化 T=max E(v)。',
        },
      ],
    },
  },
  en: {
    nav: {
      brand: 'Kernel Scheduling',
      home: 'Home',
      problem: 'Problem Animation',
      language: '中文',
    },
    home: {
      eyebrow: 'Kernel Scheduling Research Site',
      title: 'Algorithm and Result Showcase',
      lead:
        'This home page will foreground our scheduling algorithm, experimental results, key metrics, and paper findings. It is intentionally a placeholder until the result narrative is fixed.',
      placeholderTitle: 'Algorithm and result placeholder',
      placeholderBody:
        'This area can later host best schedules, peak residency, spill traffic, runtime, benchmark comparisons, and paper figures.',
      openProblem: 'Open problem animation',
      cards: [
        {
          label: 'Algorithm',
          title: 'Scheduling policy',
          body: 'Reserved for algorithm principles, heuristics, and ablation links.',
        },
        {
          label: 'Result',
          title: 'Experiment results',
          body: 'Reserved for maxV_stay, spill cost, pipeline runtime, and related metrics.',
        },
        {
          label: 'Paper',
          title: 'Paper assets',
          body: 'Reserved for abstract, figures, reproducibility notes, and downloads.',
        },
      ],
    },
    problem: {
      eyebrow: 'Precise Problem Visualization',
      title: 'From DAG to cache and pipe scheduling',
      lead:
        'This subpage explains the contest problem itself: the input is a computation DAG with cache events, and the output is a valid schedule, memory offsets, optional spills, and a multi-pipe runtime evaluation.',
      animationStage: 'Animation stage',
      nextStage: 'Next stage',
      scheduleCursor: 'Schedule cursor',
      summaryTitle: 'Three objectives',
      exportTitle: 'Static export',
      exportBody: 'After Vite build, the dist/ directory can be published directly.',
      stages: [
        {
          title: 'DAG dependency',
          detail:
            'Nodes can only form a valid topological order; edges encode both computation dependencies and buffer lifetime constraints.',
        },
        {
          title: 'Problem 1: maxV_stay',
          detail:
            'Scan schedule prefixes: ALLOC adds Size, FREE subtracts Size, and operation nodes contribute 0 to residency.',
        },
        {
          title: 'Problem 2: cache offset',
          detail:
            'Within the same cache type, simultaneously resident buffers must occupy non-overlapping [Offset, Offset+Size-1] intervals.',
        },
        {
          title: 'Problem 2/3: spill segment',
          detail:
            'SPILL_OUT and SPILL_IN move physical residency; the logical BufId remains the same buffer identity.',
        },
        {
          title: 'Problem 3: pipe timing',
          detail:
            'The same pipe executes serially in schedule order; different pipes may overlap but still wait for predecessors.',
        },
      ],
      problems: [
        {
          label: 'Problem 1',
          title: 'Topological schedule',
          body: 'Output every original node id in a valid order and minimize maxV_stay over schedule prefixes.',
        },
        {
          label: 'Problem 2',
          title: 'Cache address and spill',
          body: 'Assign physical offsets for buffers while satisfying capacity and non-overlap; emit spills when needed.',
        },
        {
          label: 'Problem 3',
          title: 'Pipelined runtime',
          body: 'After spills and address-reuse dependencies, minimize T=max E(v) under serial same-pipe execution.',
        },
      ],
    },
  },
}
