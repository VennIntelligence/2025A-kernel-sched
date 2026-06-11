/**
 * One self-consistent miniature instance that drives every stage of the
 * explainer figure.
 *
 * Story: two MATMUL tiles share one weight buffer W (COPY_IN origin).
 * The chosen schedule reaches maxV_stay = 1024 = UB capacity (logically
 * perfect), yet physical placement still fails: when X2 (640) must be
 * allocated, free space totals 896 but is fragmented by the resident W
 * into 384 + 512 — no contiguous hole. W is spilled to DDR and reloaded
 * at NewOffset 640. Because W originates from a COPY_IN, the extra DDR
 * traffic is only Size = 128 and SPILL_OUT costs 0 cycles.
 *
 * All derived quantities (V_stay series, pipeline start/end times) are
 * computed from the node/dependency lists below, never hand-written.
 */

export type StageId = 'dag' | 'schedule' | 'memory' | 'spill' | 'pipeline'
export type NodeKind = 'cache' | 'op' | 'spill'
export type Pipe = 'MTE2' | 'MTE3' | 'CUBE'
export type BufId = 'b0' | 'b1' | 'b2' | 'b3' | 'b4'

export const UB_CAPACITY = 1024

/* Okabe–Ito colorblind-safe palette */
export const PIPE_COLOR: Record<Pipe, string> = {
  MTE2: '#0072B2',
  MTE3: '#E69F00',
  CUBE: '#CC79A7',
}

export const KIND_COLOR: Record<NodeKind, string> = {
  cache: '#009E73',
  op: '#0072B2',
  spill: '#D55E00',
}

export type BufferInfo = {
  id: BufId
  tag: string
  size: number
  color: string
  /** initial physical offset in UB */
  offset: number
  /** reload offset after SPILL_IN (only b0) */
  reloadOffset?: number
}

export const BUFFERS: Record<BufId, BufferInfo> = {
  b0: { id: 'b0', tag: 'W', size: 128, color: '#56B4E9', offset: 384, reloadOffset: 640 },
  b1: { id: 'b1', tag: 'X1', size: 384, color: '#0072B2', offset: 0 },
  b2: { id: 'b2', tag: 'Y1', size: 384, color: '#CC79A7', offset: 512 },
  b3: { id: 'b3', tag: 'X2', size: 640, color: '#E69F00', offset: 0 },
  b4: { id: 'b4', tag: 'Y2', size: 256, color: '#009E73', offset: 768 },
}

export type SchedNode = {
  id: string
  op: string
  kind: NodeKind
  /** buffer touched by a cache/spill node */
  buf?: BufId
  /** short human tag shown on the strip (X1, W, Y1 = W·X1 …) */
  tag: string
  /** +Size for ALLOC, −Size for FREE, 0 otherwise */
  delta: number
  pipe?: Pipe
  cycles?: number
}

const cacheNode = (id: string, op: 'ALLOC' | 'FREE', buf: BufId): SchedNode => ({
  id,
  op,
  kind: 'cache',
  buf,
  tag: `${buf}·${BUFFERS[buf].size}`,
  delta: (op === 'ALLOC' ? 1 : -1) * BUFFERS[buf].size,
})

const opNode = (id: string, op: string, tag: string, pipe: Pipe, cycles: number): SchedNode => ({
  id,
  op,
  kind: 'op',
  tag,
  delta: 0,
  pipe,
  cycles,
})

const spillNode = (id: string, op: 'SPILL_OUT' | 'SPILL_IN', buf: BufId, pipe: Pipe, cycles: number): SchedNode => ({
  id,
  op,
  kind: 'spill',
  buf,
  tag: buf,
  delta: 0,
  pipe,
  cycles,
})

/** Problem-1 schedule: the 17 original nodes in chosen topological order. */
export const NODES_17: SchedNode[] = [
  cacheNode('AL_b1', 'ALLOC', 'b1'),
  opNode('CI_X1', 'COPY_IN', 'X1', 'MTE2', 180),
  cacheNode('AL_b0', 'ALLOC', 'b0'),
  opNode('CI_W', 'COPY_IN', 'W', 'MTE2', 80),
  cacheNode('AL_b2', 'ALLOC', 'b2'),
  opNode('MM1', 'MATMUL', 'Y1', 'CUBE', 240),
  cacheNode('FR_b1', 'FREE', 'b1'),
  opNode('CO_Y1', 'COPY_OUT', 'Y1', 'MTE3', 160),
  cacheNode('FR_b2', 'FREE', 'b2'),
  cacheNode('AL_b3', 'ALLOC', 'b3'),
  opNode('CI_X2', 'COPY_IN', 'X2', 'MTE2', 300),
  cacheNode('AL_b4', 'ALLOC', 'b4'),
  opNode('MM2', 'MATMUL', 'Y2', 'CUBE', 240),
  cacheNode('FR_b3', 'FREE', 'b3'),
  opNode('CO_Y2', 'COPY_OUT', 'Y2', 'MTE3', 160),
  cacheNode('FR_b4', 'FREE', 'b4'),
  cacheNode('FR_b0', 'FREE', 'b0'),
]

/**
 * Problem-2/3 schedule: spill pair inserted.
 * SPILL_OUT b0 costs 0 cycles (COPY_IN origin); SPILL_IN = 2·128+150 = 406.
 */
export const NODES_19: SchedNode[] = (() => {
  const byId = new Map(NODES_17.map((n) => [n.id, n]))
  const pick = (id: string) => byId.get(id)!
  return [
    pick('AL_b1'),
    pick('CI_X1'),
    pick('AL_b0'),
    pick('CI_W'),
    pick('AL_b2'),
    pick('MM1'),
    pick('FR_b1'),
    pick('CO_Y1'),
    pick('FR_b2'),
    spillNode('SO_b0', 'SPILL_OUT', 'b0', 'MTE3', 0),
    pick('AL_b3'),
    pick('CI_X2'),
    spillNode('SI_b0', 'SPILL_IN', 'b0', 'MTE2', 2 * BUFFERS.b0.size + 150),
    pick('AL_b4'),
    pick('MM2'),
    pick('FR_b3'),
    pick('CO_Y2'),
    pick('FR_b4'),
    pick('FR_b0'),
  ]
})()

export type DepKind = 'data' | 'spill' | 'reuse'
export type Dep = { from: string; to: string; kind: DepKind }

const dep = (from: string, to: string, kind: DepKind = 'data'): Dep => ({ from, to, kind })

/** Original DAG edges (ALLOC → producer, producer → consumers, consumers → FREE). */
export const EDGES_17: Dep[] = [
  dep('AL_b1', 'CI_X1'),
  dep('AL_b0', 'CI_W'),
  dep('AL_b2', 'MM1'),
  dep('CI_X1', 'MM1'),
  dep('CI_W', 'MM1'),
  dep('MM1', 'FR_b1'),
  dep('MM1', 'CO_Y1'),
  dep('CO_Y1', 'FR_b2'),
  dep('MM1', 'FR_b0'),
  dep('AL_b3', 'CI_X2'),
  dep('AL_b4', 'MM2'),
  dep('CI_X2', 'MM2'),
  dep('CI_W', 'MM2'),
  dep('MM2', 'FR_b3'),
  dep('MM2', 'CO_Y2'),
  dep('CO_Y2', 'FR_b4'),
  dep('MM2', 'FR_b0'),
]

/**
 * Problem-3 dependency set = original edges + spill chain + address-reuse
 * dependencies implied by the physical placement:
 *   b3 [0,640)  overlaps b1 [0,384), b0 [384,512), b2 [512,640)
 *   b0 reload [640,768) and b4 [768,1024) both reuse b2's old [512,896)
 */
export const DEPS_19: Dep[] = [
  ...EDGES_17,
  dep('AL_b0', 'SO_b0', 'spill'),
  dep('SO_b0', 'SI_b0', 'spill'),
  dep('SI_b0', 'FR_b0', 'spill'),
  dep('CI_W', 'SO_b0', 'spill'),
  dep('MM1', 'SO_b0', 'spill'),
  dep('SI_b0', 'MM2', 'spill'),
  dep('FR_b1', 'AL_b3', 'reuse'),
  dep('SO_b0', 'AL_b3', 'reuse'),
  dep('FR_b2', 'AL_b3', 'reuse'),
  dep('FR_b2', 'SI_b0', 'reuse'),
  dep('FR_b2', 'AL_b4', 'reuse'),
]

/** Prefix V_stay series: vstay[k] = residency after the k-th node (vstay[0] = 0). */
export function computeVstay(nodes: SchedNode[]): number[] {
  const series = [0]
  let acc = 0
  for (const node of nodes) {
    acc += node.delta
    series.push(acc)
  }
  return series
}

export const VSTAY_17 = computeVstay(NODES_17)
export const MAX_VSTAY = Math.max(...VSTAY_17)

export type GanttBar = {
  id: string
  pipe: Pipe
  start: number
  end: number
  label: string
  kind: NodeKind
}

export type NodeTiming = { start: number; end: number }

/**
 * Problem-3 timing rules: S(v) ≥ E(u) for every predecessor, the same pipe
 * runs serially in schedule order, cache nodes take 0 cycles.
 */
function computeTimeline(nodes: SchedNode[], deps: Dep[]) {
  const endOf = new Map<string, number>()
  const timing = new Map<string, NodeTiming>()
  const lastPipeEnd = new Map<Pipe, number>()
  const bars: GanttBar[] = []

  for (const node of nodes) {
    let start = 0
    for (const d of deps) {
      if (d.to === node.id) start = Math.max(start, endOf.get(d.from) ?? 0)
    }
    if (node.pipe) start = Math.max(start, lastPipeEnd.get(node.pipe) ?? 0)
    const end = start + (node.cycles ?? 0)
    endOf.set(node.id, end)
    timing.set(node.id, { start, end })
    if (node.pipe) {
      lastPipeEnd.set(node.pipe, end)
      bars.push({ id: node.id, pipe: node.pipe, start, end, label: node.op === 'MATMUL' ? `MATMUL ${node.tag}` : `${node.op} ${node.tag}`, kind: node.kind })
    }
  }

  const makespan = Math.max(...[...endOf.values()])
  return { bars, timing, makespan }
}

export const TIMELINE = computeTimeline(NODES_19, DEPS_19)
export const PIPES: Pipe[] = ['MTE2', 'CUBE', 'MTE3']

/** Physical residency segment on the address × schedule-step plane. */
export type MemSegment = {
  buf: BufId
  /** [allocStep, freeStep] in 1-indexed schedule positions */
  fromStep: number
  toStep: number
  offset: number
}

const stepOf = (nodes: SchedNode[], id: string) => nodes.findIndex((n) => n.id === id) + 1

/** Stage-3 layout (17 nodes, no spill): placement of b3 fails at step 10. */
export const MEM_SEGMENTS_17: MemSegment[] = [
  { buf: 'b1', fromStep: stepOf(NODES_17, 'AL_b1'), toStep: stepOf(NODES_17, 'FR_b1'), offset: BUFFERS.b1.offset },
  { buf: 'b0', fromStep: stepOf(NODES_17, 'AL_b0'), toStep: stepOf(NODES_17, 'FR_b0'), offset: BUFFERS.b0.offset },
  { buf: 'b2', fromStep: stepOf(NODES_17, 'AL_b2'), toStep: stepOf(NODES_17, 'FR_b2'), offset: BUFFERS.b2.offset },
]

/** Step at which ALLOC b3 cannot be placed (the fragmentation punchline). */
export const MEM_FAIL_STEP = stepOf(NODES_17, 'AL_b3')

/** Stage-4 layout (19 nodes, with spill): b0 lives in two physical segments. */
export const MEM_SEGMENTS_19: MemSegment[] = [
  { buf: 'b1', fromStep: stepOf(NODES_19, 'AL_b1'), toStep: stepOf(NODES_19, 'FR_b1'), offset: BUFFERS.b1.offset },
  { buf: 'b0', fromStep: stepOf(NODES_19, 'AL_b0'), toStep: stepOf(NODES_19, 'SO_b0'), offset: BUFFERS.b0.offset },
  { buf: 'b2', fromStep: stepOf(NODES_19, 'AL_b2'), toStep: stepOf(NODES_19, 'FR_b2'), offset: BUFFERS.b2.offset },
  { buf: 'b3', fromStep: stepOf(NODES_19, 'AL_b3'), toStep: stepOf(NODES_19, 'FR_b3'), offset: BUFFERS.b3.offset },
  { buf: 'b0', fromStep: stepOf(NODES_19, 'SI_b0'), toStep: stepOf(NODES_19, 'FR_b0'), offset: BUFFERS.b0.reloadOffset! },
  { buf: 'b4', fromStep: stepOf(NODES_19, 'AL_b4'), toStep: stepOf(NODES_19, 'FR_b4'), offset: BUFFERS.b4.offset },
]

export const SPILL_OUT_STEP = stepOf(NODES_19, 'SO_b0')
export const SPILL_IN_STEP = stepOf(NODES_19, 'SI_b0')

export const stages: Array<{ id: StageId }> = [
  { id: 'dag' },
  { id: 'schedule' },
  { id: 'memory' },
  { id: 'spill' },
  { id: 'pipeline' },
]

export const stageOrder: StageId[] = stages.map((s) => s.id)

/** Node list whose order the strip / cursor walks for a given stage. */
export function stageNodes(stage: StageId): SchedNode[] {
  return stage === 'spill' || stage === 'pipeline' ? NODES_19 : NODES_17
}

/** Memory stage deliberately stops at the placement failure. */
export function stageMaxStep(stage: StageId): number {
  if (stage === 'memory') return MEM_FAIL_STEP
  return stageNodes(stage).length
}

/* ---------------------------------------------------------------- */
/* DAG layout: hand-tuned layered positions on a 960 × 470 canvas.  */
/* ---------------------------------------------------------------- */

export const DAG_VIEW = { w: 960, h: 470 }

export const DAG_POS: Record<string, { x: number; y: number }> = {
  AL_b1: { x: 78, y: 64 },
  CI_X1: { x: 224, y: 64 },
  AL_b2: { x: 224, y: 148 },
  MM1: { x: 394, y: 106 },
  FR_b1: { x: 560, y: 56 },
  CO_Y1: { x: 560, y: 140 },
  FR_b2: { x: 722, y: 140 },
  AL_b0: { x: 78, y: 236 },
  CI_W: { x: 224, y: 236 },
  FR_b0: { x: 884, y: 236 },
  AL_b3: { x: 78, y: 332 },
  CI_X2: { x: 224, y: 332 },
  AL_b4: { x: 224, y: 414 },
  MM2: { x: 394, y: 374 },
  FR_b3: { x: 560, y: 422 },
  CO_Y2: { x: 560, y: 338 },
  FR_b4: { x: 722, y: 338 },
}

/** Sub-label shown on the second line of a DAG node. */
export function dagSubLabel(node: SchedNode): string {
  if (node.kind === 'cache') {
    const buf = BUFFERS[node.buf!]
    return `${buf.id} (${buf.tag}) · ${buf.size}`
  }
  if (node.op === 'MATMUL') {
    return node.tag === 'Y1' ? 'Y1 ← W·X1' : 'Y2 ← W·X2'
  }
  return `${node.tag} · ${node.cycles}c`
}
