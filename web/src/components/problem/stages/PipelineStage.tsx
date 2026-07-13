import { NODES_19, PIPES, PIPE_COLOR, TIMELINE, type Pipe } from '../problemData'

const VIEW = { w: 960, h: 470 }
const PX0 = 88
const PX1 = 930
const T_MAX = 1800
const LANE_Y: Record<Pipe, number> = { MTE2: 120, CUBE: 204, MTE3: 288 }
const LANE_H = 42

const x = (t: number) => PX0 + (t / T_MAX) * (PX1 - PX0)

const STEP_OF = new Map(NODES_19.map((node, index) => [node.id, index + 1]))

type Arrow = { from: string; to: string; kind: 'data' | 'reuse' | 'spill' }

/** Dependency arrows worth drawing (the rest would be visual noise). */
const ARROWS: Arrow[] = [
  { from: 'CI_X1', to: 'MM1', kind: 'data' },
  { from: 'CI_W', to: 'MM1', kind: 'data' },
  { from: 'MM1', to: 'CO_Y1', kind: 'data' },
  { from: 'CO_Y1', to: 'CI_X2', kind: 'reuse' },
  { from: 'SO_b0', to: 'SI_b0', kind: 'spill' },
  { from: 'SI_b0', to: 'MM2', kind: 'spill' },
  { from: 'CI_X2', to: 'MM2', kind: 'data' },
  { from: 'MM2', to: 'CO_Y2', kind: 'data' },
]

function arrowPath(x0: number, y0: number, x1: number, y1: number): string {
  if (Math.abs(x1 - x0) < 8) {
    const bend = 24
    return `M ${x0} ${y0} C ${x0 + bend} ${y0}, ${x1 + bend} ${y1}, ${x1 + 2} ${y1}`
  }
  const bulge = Math.max(18, Math.min(70, (x1 - x0) * 0.5))
  return `M ${x0} ${y0} C ${x0 + bulge} ${y0}, ${x1 - bulge} ${y1}, ${x1 - 2} ${y1}`
}

/**
 * Stage 5 — Problem 3. Same-pipe nodes run serially in schedule order,
 * different pipes overlap; spill + address-reuse dependencies (dashed)
 * push MATMUL₂ late and set the makespan T = max E(v).
 */
export function PipelineStage({ step }: { step: number }) {
  const bars = TIMELINE.bars.map((bar) => ({ ...bar, step: STEP_OF.get(bar.id)! }))
  const revealed = bars.filter((bar) => bar.step <= step)
  const tNow = revealed.length > 0 ? Math.max(...revealed.map((bar) => bar.end)) : 0
  const complete = step >= NODES_19.length

  const barById = new Map(bars.map((bar) => [bar.id, bar]))

  return (
    <svg
      className="stage-svg chart-svg"
      viewBox={`0 0 ${VIEW.w} ${VIEW.h}`}
      role="img"
      aria-label="Pipelined execution Gantt chart"
    >
      <defs>
        <marker id="gantt-arrow" markerWidth="7" markerHeight="7" refX="5.4" refY="3" orient="auto">
          <path d="M0,0.5 L5.6,3 L0,5.5" fill="none" stroke="#8f99a6" strokeWidth="1.2" />
        </marker>
        <marker id="gantt-arrow-warn" markerWidth="7" markerHeight="7" refX="5.4" refY="3" orient="auto">
          <path d="M0,0.5 L5.6,3 L0,5.5" fill="none" stroke="#D55E00" strokeWidth="1.2" />
        </marker>
      </defs>

      {/* lane backgrounds + labels */}
      {PIPES.map((pipe, index) => (
        <g key={pipe}>
          {index % 2 === 1 && (
            <rect x={PX0 - 62} y={LANE_Y[pipe] - LANE_H / 2 - 10} width={PX1 - PX0 + 62} height={LANE_H + 20} fill="#f6f7f9" />
          )}
          <rect x={PX0 - 58} y={LANE_Y[pipe] - 5} width="10" height="10" rx="2" fill={PIPE_COLOR[pipe]} />
          <text className="lane-name" x={PX0 - 42} y={LANE_Y[pipe] + 4}>
            {pipe}
          </text>
          <line className="lane-rail" x1={PX0} x2={PX1} y1={LANE_Y[pipe]} y2={LANE_Y[pipe]} />
        </g>
      ))}

      {/* time grid */}
      {Array.from({ length: T_MAX / 200 + 1 }, (_, i) => i * 200).map((t) => (
        <g key={t}>
          <line className="grid-line" x1={x(t)} x2={x(t)} y1={LANE_Y.MTE2 - LANE_H / 2 - 14} y2={LANE_Y.MTE3 + LANE_H / 2 + 14} />
          <text className="tick-label" x={x(t)} y={LANE_Y.MTE3 + LANE_H / 2 + 32} textAnchor="middle">
            {t}
          </text>
        </g>
      ))}

      {/* dependency arrows */}
      {ARROWS.map((arrow) => {
        const from = barById.get(arrow.from)!
        const to = barById.get(arrow.to)!
        if (to.step > step) return null
        return (
          <path
            key={`${arrow.from}-${arrow.to}`}
            className={`dep-arrow dep-${arrow.kind}`}
            d={arrowPath(x(from.end), LANE_Y[from.pipe], x(to.start), LANE_Y[to.pipe])}
            markerEnd={`url(#${arrow.kind === 'spill' ? 'gantt-arrow-warn' : 'gantt-arrow'})`}
          />
        )
      })}

      {/* bars */}
      {bars.map((bar) => {
        const w = x(bar.end) - x(bar.start)
        const visible = bar.step <= step
        const active = bar.step === step
        const color = bar.kind === 'spill' ? '#D55E00' : PIPE_COLOR[bar.pipe]
        const top = LANE_Y[bar.pipe] - LANE_H / 2

        if (w < 3) {
          /* zero-cycle SPILL_OUT: render as a diamond event marker */
          return (
            <g key={bar.id} className={`gantt-event ${visible ? 'is-visible' : ''} ${active ? 'is-active' : ''}`}>
              <path
                d={`M ${x(bar.start)} ${LANE_Y[bar.pipe] - 9} l 7 9 l -7 9 l -7 -9 Z`}
                fill="#fff"
                stroke={color}
                strokeWidth="1.8"
              />
              <text className="bar-label-out" x={x(bar.start)} y={top + LANE_H + 16} textAnchor="middle">
                {bar.label} · 0c
              </text>
            </g>
          )
        }

        const cycles = bar.end - bar.start
        const inside = w >= 78
        const withCycles = w >= 110
        return (
          <g key={bar.id} className={`gantt-bar ${visible ? 'is-visible' : ''} ${active ? 'is-active' : ''}`}>
            <rect
              x={x(bar.start)}
              y={top}
              width={w}
              height={LANE_H}
              rx="5"
              fill={color}
              fillOpacity={bar.kind === 'spill' ? 0.28 : 0.16}
              stroke={color}
              strokeWidth="1.6"
            />
            {inside ? (
              <text
                className="bar-label"
                x={x(bar.start) + w / 2}
                y={withCycles ? LANE_Y[bar.pipe] - 2 : LANE_Y[bar.pipe] + 3.5}
                textAnchor="middle"
              >
                {bar.label}
              </text>
            ) : (
              <text className="bar-label-out" x={x(bar.start) + w / 2} y={top - 8} textAnchor="middle">
                {bar.label}
              </text>
            )}
            {withCycles && (
              <text className="bar-cycles" x={x(bar.start) + w / 2} y={LANE_Y[bar.pipe] + 13} textAnchor="middle">
                {bar.start} → {bar.end} · {cycles}c
              </text>
            )}
          </g>
        )
      })}

      {/* now / makespan marker */}
      {tNow > 0 && (
        <g className={`makespan ${complete ? 'is-final' : ''}`}>
          <line x1={x(tNow)} x2={x(tNow)} y1={LANE_Y.MTE2 - LANE_H / 2 - 22} y2={LANE_Y.MTE3 + LANE_H / 2 + 14} />
          <text x={x(tNow)} y={LANE_Y.MTE2 - LANE_H / 2 - 30} textAnchor={x(tNow) > 700 ? 'end' : 'middle'}>
            {complete ? `T = max E(v) = ${TIMELINE.makespan}` : `t = ${tNow}`}
          </text>
        </g>
      )}

      <text className="axis-title" x={(PX0 + PX1) / 2} y={LANE_Y.MTE3 + LANE_H / 2 + 56} textAnchor="middle">
        time (cycles)
      </text>

      <text className="svg-footnote" x={PX0 - 62} y={VIEW.h - 12}>
        solid arrow = data dependency · dashed = address-reuse / spill dependency · orange = spill traffic
      </text>
    </svg>
  )
}
