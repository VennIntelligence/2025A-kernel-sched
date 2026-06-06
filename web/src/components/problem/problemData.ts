export type StageId = 'dag' | 'schedule' | 'memory' | 'spill' | 'pipeline'

export type NodeKind = 'cache' | 'op' | 'spill'

export type GraphNode = {
  id: string
  label: string
  kind: NodeKind
  x: number
  y: number
  pipe?: string
}

export type ScheduleStep = {
  nodeId: string
  delta: number
  label: string
}

export const stages: Array<{ id: StageId; label: string }> = [
  { id: 'dag', label: 'DAG' },
  { id: 'schedule', label: 'Schedule' },
  { id: 'memory', label: 'Memory' },
  { id: 'spill', label: 'Spill' },
  { id: 'pipeline', label: 'Pipeline' },
]

export const graphNodes: GraphNode[] = [
  { id: 'a0', label: 'ALLOC b0', kind: 'cache', x: 80, y: 96 },
  { id: 'a1', label: 'ALLOC b1', kind: 'cache', x: 80, y: 210 },
  { id: 'copy', label: 'COPY_IN', kind: 'op', pipe: 'MTE2', x: 245, y: 96 },
  { id: 'move', label: 'MOVE', kind: 'op', pipe: 'MTE1', x: 245, y: 210 },
  { id: 'matmul', label: 'MATMUL', kind: 'op', pipe: 'CUBE', x: 420, y: 154 },
  { id: 'spillOut', label: 'SPILL_OUT', kind: 'spill', pipe: 'MTE3', x: 585, y: 88 },
  { id: 'spillIn', label: 'SPILL_IN', kind: 'spill', pipe: 'MTE2', x: 585, y: 220 },
  { id: 'out', label: 'COPY_OUT', kind: 'op', pipe: 'MTE3', x: 750, y: 154 },
  { id: 'free0', label: 'FREE b0', kind: 'cache', x: 910, y: 96 },
  { id: 'free1', label: 'FREE b1', kind: 'cache', x: 910, y: 210 },
]

export const edges = [
  ['a0', 'copy'],
  ['a1', 'move'],
  ['copy', 'matmul'],
  ['move', 'matmul'],
  ['matmul', 'spillOut'],
  ['spillOut', 'spillIn'],
  ['spillIn', 'out'],
  ['out', 'free0'],
  ['out', 'free1'],
]

export const schedule: ScheduleStep[] = [
  { nodeId: 'a0', delta: 192, label: 'ALLOC b0' },
  { nodeId: 'a1', delta: 128, label: 'ALLOC b1' },
  { nodeId: 'copy', delta: 0, label: 'COPY_IN' },
  { nodeId: 'move', delta: 0, label: 'MOVE' },
  { nodeId: 'matmul', delta: 0, label: 'MATMUL' },
  { nodeId: 'spillOut', delta: -192, label: 'SPILL_OUT' },
  { nodeId: 'spillIn', delta: 192, label: 'SPILL_IN' },
  { nodeId: 'out', delta: 0, label: 'COPY_OUT' },
  { nodeId: 'free0', delta: -192, label: 'FREE b0' },
  { nodeId: 'free1', delta: -128, label: 'FREE b1' },
]

export const stageOrder = stages.map((stage) => stage.id)
