// Public production numbers and bounded research evidence.
// Sources:
//   results/autoresearch_v2/round11_audited_p2.json
//   results/autoresearch_v2/round6_formal_p3.json
//   results/autoresearch_v2/agent_cost_order/final_summary.json
//   results/autoresearch_v2/agent_direct/

export type P2ResultRow = {
  instance: string
  official: number
  scalable: number
  outcome: 'win' | 'tie'
}

export const P2_RESULTS: P2ResultRow[] = [
  { instance: 'Conv_0', official: 73500, scalable: 66828, outcome: 'win' },
  { instance: 'Conv_1', official: 73240, scalable: 72734, outcome: 'win' },
  { instance: 'FA_0', official: 3692, scalable: 3584, outcome: 'win' },
  { instance: 'FA_1', official: 32840, scalable: 32512, outcome: 'win' },
  { instance: 'Matmul_0', official: 34944, scalable: 34688, outcome: 'win' },
  { instance: 'Matmul_1', official: 460800, scalable: 460800, outcome: 'tie' },
]

export type ResearchEvidenceRow = {
  instance: string
  repair: number | 'probe' | null
  exact: number | null
  status: 'certificate' | 'timeout' | 'feasibleFa1' | 'feasibleMm0' | 'notRun'
}

export const RESEARCH_EVIDENCE: ResearchEvidenceRow[] = [
  { instance: 'Conv_0 / frontier', repair: 65532, exact: 57408, status: 'certificate' },
  { instance: 'Conv_0 / P1', repair: null, exact: 81504, status: 'certificate' },
  { instance: 'Conv_1', repair: 70940, exact: null, status: 'timeout' },
  { instance: 'FA_0', repair: 'probe', exact: 3584, status: 'certificate' },
  { instance: 'FA_1', repair: 'probe', exact: 32512, status: 'feasibleFa1' },
  { instance: 'Matmul_0', repair: null, exact: 34816, status: 'feasibleMm0' },
  { instance: 'Matmul_1', repair: null, exact: null, status: 'notRun' },
]

export type P3ResultRow = {
  instance: string
  official: number
  scalable: number
  outcome: 'win' | 'loss'
}

export const P3_RESULTS: P3ResultRow[] = [
  { instance: 'Conv_0', official: 535312, scalable: 515634, outcome: 'win' },
  { instance: 'Conv_1', official: 1073322, scalable: 1118687, outcome: 'loss' },
  { instance: 'FA_0', official: 46761, scalable: 36344, outcome: 'win' },
  { instance: 'FA_1', official: 193059, scalable: 152364, outcome: 'win' },
  { instance: 'Matmul_0', official: 194331, scalable: 186820, outcome: 'win' },
  { instance: 'Matmul_1', official: 1800218, scalable: 1771383, outcome: 'win' },
]

export type BenchRow = {
  instance: string
  opType: string
  nodes: number
  edges: number
  buffers: number
}

export const BENCHMARK: BenchRow[] = [
  { instance: 'Conv_0', opType: 'Conv', nodes: 2580, edges: 3869, buffers: 831 },
  { instance: 'Conv_1', opType: 'Conv', nodes: 36086, edges: 85653, buffers: 12013 },
  { instance: 'FA_0', opType: 'FA', nodes: 1716, edges: 2712, buffers: 572 },
  { instance: 'FA_1', opType: 'FA', nodes: 6952, edges: 11184, buffers: 2328 },
  { instance: 'Matmul_0', opType: 'Matmul', nodes: 4160, edges: 7104, buffers: 1216 },
  { instance: 'Matmul_1', opType: 'Matmul', nodes: 30976, edges: 55040, buffers: 8960 },
]

export const CAPACITIES: { name: string; value: number }[] = [
  { name: 'L1', value: 4096 },
  { name: 'UB', value: 1024 },
  { name: 'L0A', value: 256 },
  { name: 'L0B', value: 256 },
  { name: 'L0C', value: 512 },
]
