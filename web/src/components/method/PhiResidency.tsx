import { useState } from 'react'
import { FigureCard } from '../viz/FigureCard'
import { Segmented, type SegOption } from '../viz/Segmented'
import {
  RESIDENCY_BASELINE,
  RESIDENCY_CAPACITY,
  RESIDENCY_ID_RAW,
  RESIDENCY_PEAK,
  type ResidencyPoint,
} from '../../data/residency'
import { fmt } from '../../lib/format'
import type { ResidencyCopy } from '../../lib/i18n'

const W = 920
const H = 320
const PAD = { l: 56, r: 18, t: 18, b: 28 }
const PLOT_W = W - PAD.l - PAD.r
const PLOT_H = H - PAD.t - PAD.b
const BASE_Y = PAD.t + PLOT_H

const MAX_Y = Math.ceil((RESIDENCY_PEAK.idRaw * 1.06) / 1024) * 1024

type Series = 'idRaw' | 'baseline'

const xOf = (i: number, n: number) => PAD.l + (i / (n - 1)) * PLOT_W
const yOf = (v: number) => PAD.t + (1 - v / MAX_Y) * PLOT_H

function areaPath(points: ResidencyPoint[], top: (p: ResidencyPoint) => number): string {
  const n = points.length
  const head = `M ${xOf(0, n).toFixed(1)} ${BASE_Y.toFixed(1)}`
  const line = points.map((p, i) => `L ${xOf(i, n).toFixed(1)} ${yOf(top(p)).toFixed(1)}`).join(' ')
  return `${head} ${line} L ${xOf(n - 1, n).toFixed(1)} ${BASE_Y.toFixed(1)} Z`
}

function phiArea(points: ResidencyPoint[]): number {
  return points.reduce((acc, p) => acc + Math.max(0, p.clean + p.dirty - RESIDENCY_CAPACITY), 0)
}

export function PhiResidency({ copy }: { copy: ResidencyCopy }) {
  const [series, setSeries] = useState<Series>('idRaw')
  const points = series === 'idRaw' ? RESIDENCY_ID_RAW : RESIDENCY_BASELINE

  const options: SegOption<Series>[] = [
    { id: 'idRaw', label: copy.idRaw },
    { id: 'baseline', label: copy.baseline },
  ]

  const cleanArea = areaPath(points, (p) => p.clean)
  const totalArea = areaPath(points, (p) => p.clean + p.dirty)

  const peakIdx = points.reduce((best, p, i) => (p.clean + p.dirty > points[best].clean + points[best].dirty ? i : best), 0)
  const peakPt = points[peakIdx]
  const peakTotal = peakPt.clean + peakPt.dirty
  const cleanAtPeak = series === 'idRaw' ? RESIDENCY_PEAK.idRawCleanAtPeak : RESIDENCY_PEAK.baselineCleanAtPeak
  const capY = yOf(RESIDENCY_CAPACITY)
  const phi = phiArea(points)

  return (
    <FigureCard
      kicker={copy.kicker}
      title={copy.title}
      caption={copy.caption}
      note={copy.surrogateNote}
      action={<Segmented options={options} value={series} onChange={setSeries} ariaLabel={copy.title} size="sm" />}
    >
      <div className="phi-figure">
        <svg className="phi-svg" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={copy.title}>
          <defs>
            <clipPath id="phi-overflow">
              <rect x={PAD.l} y={PAD.t} width={PLOT_W} height={Math.max(0, capY - PAD.t)} />
            </clipPath>
            <pattern id="phi-hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
              <line x1="0" y1="0" x2="0" y2="7" stroke="#cf4f3e" strokeWidth="1.4" opacity="0.5" />
            </pattern>
          </defs>

          {/* baseline axis */}
          <line className="phi-axis" x1={PAD.l} y1={BASE_Y} x2={PAD.l + PLOT_W} y2={BASE_Y} />
          <line className="phi-axis" x1={PAD.l} y1={PAD.t} x2={PAD.l} y2={BASE_Y} />

          {/* stacked residency areas */}
          <path className="phi-dirty" d={totalArea} />
          <path className="phi-clean" d={cleanArea} />

          {/* overflow integral Φ — total area clipped above the capacity line */}
          <path d={totalArea} fill="url(#phi-hatch)" clipPath="url(#phi-overflow)" />

          {/* capacity line */}
          <line className="phi-cap" x1={PAD.l} y1={capY} x2={PAD.l + PLOT_W} y2={capY} />
          <text className="phi-cap-label" x={PAD.l + PLOT_W} y={capY - 6} textAnchor="end">
            {copy.capacity}
          </text>

          {/* peak marker */}
          <line className="phi-peak-line" x1={xOf(peakIdx, points.length)} y1={yOf(peakTotal)} x2={xOf(peakIdx, points.length)} y2={BASE_Y} />
          <circle className="phi-peak-dot" cx={xOf(peakIdx, points.length)} cy={yOf(peakTotal)} r="4" />

          {/* y ticks */}
          <text className="phi-tick" x={PAD.l - 8} y={yOf(0) + 4} textAnchor="end">0</text>
          <text className="phi-tick" x={PAD.l - 8} y={capY + 4} textAnchor="end">{fmt(RESIDENCY_CAPACITY)}</text>
          <text className="phi-tick" x={PAD.l - 8} y={yOf(MAX_Y) + 10} textAnchor="end">{fmt(MAX_Y)}</text>
        </svg>

        <ul className="phi-legend" aria-hidden="true">
          <li className="lg-clean">{copy.clean}</li>
          <li className="lg-dirty">{copy.dirty}</li>
          <li className="lg-phi">{copy.phi}</li>
        </ul>

        <div className="phi-stats">
          <div className="phi-stat">
            <span className="phi-stat-value">{fmt(cleanAtPeak)}</span>
            <span className="phi-stat-label">{copy.cleanAtPeak}</span>
          </div>
          <div className="phi-stat">
            <span className="phi-stat-value">{fmt(phi)}</span>
            <span className="phi-stat-label">{copy.phi}</span>
          </div>
        </div>
      </div>
    </FigureCard>
  )
}
