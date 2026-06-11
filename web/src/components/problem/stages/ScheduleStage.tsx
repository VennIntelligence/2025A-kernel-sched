import { MAX_VSTAY, NODES_17, UB_CAPACITY, VSTAY_17 } from '../problemData'

const VIEW = { w: 960, h: 470 }
const PX0 = 84
const PX1 = 930
const PY0 = 60
const PY1 = 380
const V_MAX = 1280
const N = NODES_17.length

const x = (k: number) => PX0 + (k / N) * (PX1 - PX0)
const y = (v: number) => PY1 - (v / V_MAX) * (PY1 - PY0)

function stepPath(upTo: number): string {
  let d = `M ${x(0)} ${y(VSTAY_17[0])}`
  for (let k = 1; k <= upTo; k += 1) {
    d += ` H ${x(k)} V ${y(VSTAY_17[k])}`
  }
  return d
}

const PEAK_STEP = VSTAY_17.indexOf(MAX_VSTAY)
const TICKS = [0, 256, 512, 768, 1024, 1280]

/**
 * Stage 2 — Problem 1. V_stay prefix scan over the schedule: ALLOC adds
 * Size, FREE subtracts it, operations contribute 0.
 */
export function ScheduleStage({ step }: { step: number }) {
  const v = VSTAY_17[step]
  const peakSeen = Math.max(...VSTAY_17.slice(0, step + 1))

  return (
    <svg
      className="stage-svg chart-svg"
      viewBox={`0 0 ${VIEW.w} ${VIEW.h}`}
      role="img"
      aria-label="V_stay prefix scan chart"
    >
      {/* horizontal grid + y labels */}
      {TICKS.map((tick) => (
        <g key={tick}>
          <line className="grid-line" x1={PX0} x2={PX1} y1={y(tick)} y2={y(tick)} />
          <text className="tick-label" x={PX0 - 10} y={y(tick) + 3} textAnchor="end">
            {tick}
          </text>
        </g>
      ))}

      {/* x ticks: one per schedule position */}
      {Array.from({ length: N + 1 }, (_, k) => (
        <g key={k}>
          <line className="tick-mark" x1={x(k)} x2={x(k)} y1={PY1} y2={PY1 + 5} />
          <text className="tick-label" x={x(k)} y={PY1 + 18} textAnchor="middle">
            {k}
          </text>
        </g>
      ))}

      {/* capacity line */}
      <line className="capacity-line" x1={PX0} x2={PX1} y1={y(UB_CAPACITY)} y2={y(UB_CAPACITY)} />
      <text className="capacity-label" x={PX1} y={y(UB_CAPACITY) - 7} textAnchor="end">
        UB capacity = {UB_CAPACITY}
      </text>

      {/* future trajectory (ghost) */}
      <path className="vstay-ghost" d={stepPath(N)} />

      {/* revealed prefix */}
      <path className="vstay-area" d={`${stepPath(step)} V ${PY1} H ${x(0)} Z`} />
      <path className="vstay-line" d={stepPath(step)} />

      {/* peak annotation */}
      <g className="peak-marker" opacity={step >= PEAK_STEP ? 1 : 0}>
        <circle cx={x(PEAK_STEP)} cy={y(MAX_VSTAY)} r="4.5" />
        <line
          x1={x(PEAK_STEP)}
          y1={y(MAX_VSTAY) - 6}
          x2={x(PEAK_STEP) - 14}
          y2={y(MAX_VSTAY) - 26}
        />
        <text x={x(PEAK_STEP) - 18} y={y(MAX_VSTAY) - 31} textAnchor="end">
          maxV_stay = {MAX_VSTAY} (= capacity)
        </text>
      </g>

      {/* cursor */}
      <g className="chart-cursor" transform={`translate(${x(step)} 0)`}>
        <line x1="0" x2="0" y1={PY0 - 8} y2={PY1} />
        <circle cx="0" cy={y(v)} r="5" />
        <text
          className="cursor-value"
          x={step > 15 ? -10 : 10}
          y={y(v) - 9}
          textAnchor={step > 15 ? 'end' : 'start'}
        >
          {v}
        </text>
      </g>

      {/* running peak readout */}
      <text className="svg-readout" x={PX0} y={PY0 - 26}>
        V_stay({step}) = {v}
      </text>
      <text className="svg-readout strong" x={PX0 + 190} y={PY0 - 26}>
        peak so far = {peakSeen}
      </text>

      <text className="axis-title" x={(PX0 + PX1) / 2} y={PY1 + 44} textAnchor="middle">
        schedule position
      </text>
      <text
        className="axis-title"
        transform={`translate(26 ${(PY0 + PY1) / 2}) rotate(-90)`}
        textAnchor="middle"
      >
        V_stay (cache units)
      </text>
    </svg>
  )
}
