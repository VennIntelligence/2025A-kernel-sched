// Exact figures transcribed from the conference paper (paper/src/*_conf).
// Single source of truth for the results tables — labels live in i18n, numbers here.
// Do not edit without updating paper/src and results/paper/*.csv in lockstep.

/** P2 spill traffic E(S) under a shared spill engine (Table: main-results). */
export type MainResultRow = {
  instance: string
  cpList: number
  pressure: number
  gHsu: number
  cpFree: number
  ours: number
}

export const MAIN_RESULTS: MainResultRow[] = [
  { instance: 'Conv_0', cpList: 694506, pressure: 207932, gHsu: 210844, cpFree: 212956, ours: 88044 },
  { instance: 'Conv_1', cpList: 1695264, pressure: 1048524, gHsu: 1053484, cpFree: 73348, ours: 72520 },
  { instance: 'FA_0', cpList: 211784, pressure: 101356, gHsu: 90092, cpFree: 3904, ours: 3904 },
  { instance: 'FA_1', cpList: 965944, pressure: 445876, gHsu: 418228, cpFree: 33152, ours: 32920 },
  { instance: 'Matmul_0', cpList: 823168, pressure: 296064, gHsu: 298240, cpFree: 34944, ours: 34688 },
  { instance: 'Matmul_1', cpList: 6506240, pressure: 2556928, gHsu: 2560640, cpFree: 460800, ours: 460800 },
]

/** Benchmark instances (Table: benchmark). */
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

/** Solver wall-clock runtime, seconds, median of three repetitions (Table: runtime). */
export type RuntimeRow = { instance: string; p1: number; p2: number; p3: number }

export const RUNTIME: RuntimeRow[] = [
  { instance: 'Conv_0', p1: 0.009, p2: 0.391, p3: 0.683 },
  { instance: 'Conv_1', p1: 0.189, p2: 57.971, p3: 73.141 },
  { instance: 'FA_0', p1: 0.006, p2: 0.22, p3: 0.328 },
  { instance: 'FA_1', p1: 0.027, p2: 2.723, p3: 3.356 },
  { instance: 'Matmul_0', p1: 0.014, p2: 0.701, p3: 1.137 },
  { instance: 'Matmul_1', p1: 0.126, p2: 19.402, p3: 32.328 },
]

/** On-chip cache capacities (abstract units). */
export const CAPACITIES: { name: string; value: number }[] = [
  { name: 'L1', value: 4096 },
  { name: 'UB', value: 1024 },
  { name: 'L0A', value: 256 },
  { name: 'L0B', value: 256 },
  { name: 'L0C', value: 512 },
]
