export type Language = 'zh' | 'en'

export type PageId = 'home' | 'problem'

export type Copy = {
  nav: {
    brand: string
    home: string
    problem: string
  }
  home: {
    title: string
    subtitle: string
    authors: string[]
    affiliations: string[]
    links: Array<{ label: string }>
    abstractTitle: string
    abstract: string
    teaserTitle: string
    teaserBody: string
    animationTitle: string
    animationBody: string
    openProblem: string
    bibtexTitle: string
    bibtex: string
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
    dataFormatTitle: string
    dataFormatBody: string
    dataFormatLink: string
  }
}

export const copy: Record<Language, Copy> = {
  zh: {
    nav: {
      brand: 'Kernel Scheduling',
      home: '首页',
      problem: '赛题动画',
    },
    home: {
      title: 'Kernel Scheduling for Neural Operator DAGs',
      subtitle: '通用神经网络处理器下的核内调度、缓存分配与流水执行优化',
      authors: ['高成志', '黄骏', '叶勤'],
      affiliations: ['东南大学', '文氏智能基金会', '2025A Kernel Scheduling Challenge'],
      links: [{ label: 'Paper' }, { label: 'Code' }, { label: 'Data' }, { label: 'Results' }],
      abstractTitle: 'Abstract',
      abstract:
        '本项目研究给定神经算子 computation DAG 时，如何在 dependency、cache capacity、physical offset、spill 和 multi-pipe exclusivity 约束下构造高质量调度。首页未来会展示我们的算法设计、benchmark 结果和论文结论；当前先保留标准 GitHub Pages 学术项目页结构。',
      teaserTitle: 'Algorithm and Results',
      teaserBody:
        '这里预留一张核心 teaser：可以展示 best schedule、maxV_stay、spill traffic、pipeline runtime，以及不同 case 的 benchmark 对比。',
      animationTitle: 'Problem Animation',
      animationBody:
        '赛题动画子页面解释 DAG topological scheduling、buffer residency、cache placement、spill segment 和 pipe timing。它是读者理解算法目标之前的背景页面。',
      openProblem: '查看赛题讲解动画',
      bibtexTitle: 'BibTeX',
      bibtex:
        '@misc{kernel_scheduling_2025,\n  title={Kernel Scheduling for Neural Operator DAGs},\n  author={Venn Intelligence Kernel Scheduling Team},\n  year={2025}\n}',
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
      dataFormatTitle: '数据格式与 Benchmark',
      dataFormatBody: '详细的赛题背景、算子计算图解析、评测数据集（Benchmark）及输入输出 JSON 格式说明，请参考我们的完整赛题文档。',
      dataFormatLink: '查看完整赛题文档',
    },
  },
  en: {
    nav: {
      brand: 'Kernel Scheduling',
      home: 'Home',
      problem: 'Problem Animation',
    },
    home: {
      title: 'Kernel Scheduling for Neural Operator DAGs',
      subtitle: 'In-core scheduling, cache placement, and pipelined execution for general neural processors',
      authors: ['Chengzhi Gao', 'Jun Huang', 'Qin Ye'],
      affiliations: ['Southeast University', 'Response by Vennai.org', '2025A Kernel Scheduling Challenge'],
      links: [{ label: 'Paper' }, { label: 'Code' }, { label: 'Data' }, { label: 'Results' }],
      abstractTitle: 'Abstract',
      abstract:
        'This project studies how to produce high-quality schedules for neural-operator computation DAGs under dependency, cache capacity, physical offset, spill, and multi-pipe exclusivity constraints. The home page will later present our algorithm design, benchmark results, and paper findings; for now it keeps the standard academic GitHub Pages project structure.',
      teaserTitle: 'Algorithm and Results',
      teaserBody:
        'This area is reserved for the main teaser: best schedules, maxV_stay, spill traffic, pipeline runtime, and benchmark comparisons across cases.',
      animationTitle: 'Problem Animation',
      animationBody:
        'The problem animation subpage explains DAG topological scheduling, buffer residency, cache placement, spill segments, and pipe timing before readers dive into the algorithm.',
      openProblem: 'Open problem animation',
      bibtexTitle: 'BibTeX',
      bibtex:
        '@misc{kernel_scheduling_2025,\n  title={Kernel Scheduling for Neural Operator DAGs},\n  author={Venn Intelligence Kernel Scheduling Team},\n  year={2025}\n}',
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
      dataFormatTitle: 'Data Format and Benchmark',
      dataFormatBody: 'For detailed problem background, operator DAG parsing, evaluation benchmark datasets, and JSON I/O format specifications, please refer to our complete problem documentation.',
      dataFormatLink: 'Read Problem Documentation',
    },
  },
}
