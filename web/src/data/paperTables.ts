// Public production numbers and bounded research evidence.
// Sources:
//   results/autoresearch_v2/round11_audited_p2.json
//   results/autoresearch_v2/round6_formal_p3.json

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
