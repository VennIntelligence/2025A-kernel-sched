import {
  BUFFERS,
  MEM_FAIL_STEP,
  MEM_SEGMENTS_17,
  MEM_SEGMENTS_19,
  NODES_17,
  NODES_19,
  SPILL_IN_STEP,
  SPILL_OUT_STEP,
  UB_CAPACITY,
  type MemSegment,
} from '../problemData'

const VIEW = { w: 960, h: 470 }
const PX0 = 84
const PX1 = 930
const PY0 = 46
const PY1 = 380
const DDR_Y = 416
const DDR_H = 30

const ADDR_TICKS = [0, 256, 512, 768, 1024]

/**
 * Stages 3 & 4 — physical UB address space over schedule position.
 * `mode="plain"` walks the spill-free schedule until placement of X2 fails
 * (fragmentation); `mode="spill"` shows the repaired schedule where W is
 * parked in DDR and reloaded at NewOffset 640.
 */
export function MemoryStage({ step, mode }: { step: number; mode: 'plain' | 'spill' }) {
  const spill = mode === 'spill'
  const N = spill ? NODES_19.length : NODES_17.length
  const segments = spill ? MEM_SEGMENTS_19 : MEM_SEGMENTS_17

  const x = (k: number) => PX0 + (k / N) * (PX1 - PX0)
  const y = (a: number) => PY1 - (a / UB_CAPACITY) * (PY1 - PY0)

  const failed = !spill && step >= MEM_FAIL_STEP

  const renderSegment = (seg: MemSegment, index: number) => {
    if (step < seg.fromStep) return null
    const buf = BUFFERS[seg.buf]
    const x0 = x(seg.fromStep - 1)
    const x1 = x(Math.min(step, seg.toStep - 1))
    const w = Math.max(0, x1 - x0)
    if (w <= 0) return null
    const top = y(seg.offset + buf.size)
    const h = y(seg.offset) - top
    return (
      <g key={`${seg.buf}-${index}`} className="mem-seg">
        <rect x={x0} y={top} width={w} height={h} rx="3" fill={buf.color} fillOpacity="0.16" stroke={buf.color} strokeWidth="1.5" />
        {w > 86 ? (
          <text className="mem-label" x={x0 + w / 2} y={top + h / 2 + 3.5} textAnchor="middle">
            {buf.id} · {buf.tag} · {buf.size}
          </text>
        ) : w > 34 ? (
          <text className="mem-label" x={x0 + w / 2} y={top + h / 2 + 3.5} textAnchor="middle">
            {buf.id}
          </text>
        ) : null}
      </g>
    )
  }

  return (
    <svg
      className="stage-svg chart-svg"
      viewBox={`0 0 ${VIEW.w} ${VIEW.h}`}
      role="img"
      aria-label="UB physical address space over schedule position"
    >
      {/* address grid */}
      {ADDR_TICKS.map((tick) => (
        <g key={tick}>
          <line className="grid-line" x1={PX0} x2={PX1} y1={y(tick)} y2={y(tick)} />
          <text className="tick-label" x={PX0 - 10} y={y(tick) + 3} textAnchor="end">
            {tick}
          </text>
        </g>
      ))}

      {/* x ticks */}
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

      {/* resident segments */}
      {segments.map(renderSegment)}

      {/* fragmentation failure overlay (stage 3 punchline) */}
      {failed && (
        <g className="fail-overlay">
          <rect x={x(MEM_FAIL_STEP - 1)} y={y(384)} width={PX1 - x(MEM_FAIL_STEP - 1)} height={y(0) - y(384)} fill="#009E73" fillOpacity="0.14" />
          <rect x={x(MEM_FAIL_STEP - 1)} y={y(1024)} width={PX1 - x(MEM_FAIL_STEP - 1)} height={y(512) - y(1024)} fill="#009E73" fillOpacity="0.14" />
          <text className="free-label" x={x(MEM_FAIL_STEP - 1) + 10} y={y(192)}>
            free 384
          </text>
          <text className="free-label" x={x(MEM_FAIL_STEP - 1) + 10} y={y(760)}>
            free 512
          </text>

          <rect
            className="ghost-rect"
            x={x(MEM_FAIL_STEP - 1)}
            y={y(640)}
            width={x(MEM_FAIL_STEP + 1.6) - x(MEM_FAIL_STEP - 1)}
            height={y(0) - y(640)}
          />
          <text className="ghost-label" x={x(MEM_FAIL_STEP + 0.3)} y={y(320) + 4} textAnchor="middle">
            ✕
          </text>
          <text className="ghost-sub" x={x(MEM_FAIL_STEP + 0.3)} y={y(320) + 24} textAnchor="middle">
            b3 · X2 · 640
          </text>

          <g className="fail-note">
            <text x={PX1 - 6} y={PY0 + 26} textAnchor="end">
              total free = 384 + 512 = 896 ≥ 640
            </text>
            <text x={PX1 - 6} y={PY0 + 44} textAnchor="end">
              max contiguous = 512 &lt; 640 → must spill W
            </text>
          </g>
        </g>
      )}

      {/* DDR band + relocation connectors */}
      {spill && (
        <g>
          <rect className="ddr-band" x={PX0} y={DDR_Y} width={PX1 - PX0} height={DDR_H} rx="4" />
          <text className="ddr-title" x={PX0 - 10} y={DDR_Y + DDR_H / 2 + 3.5} textAnchor="end">
            DDR
          </text>

          {step >= SPILL_OUT_STEP && (
            <g className="spill-flow">
              <rect
                className="ddr-block"
                x={x(SPILL_OUT_STEP - 1)}
                y={DDR_Y + 4}
                width={x(SPILL_IN_STEP - 1) - x(SPILL_OUT_STEP - 1)}
                height={DDR_H - 8}
                rx="3"
              />
              <text
                className="ddr-block-label"
                x={(x(SPILL_OUT_STEP - 1) + x(SPILL_IN_STEP - 1)) / 2}
                y={DDR_Y + DDR_H / 2 + 3.5}
                textAnchor="middle"
              >
                b0 · W
              </text>
              <path
                className="spill-connector"
                d={`M ${x(SPILL_OUT_STEP - 1)} ${y(384)} C ${x(SPILL_OUT_STEP - 1)} ${y(140)}, ${x(SPILL_OUT_STEP - 1)} ${DDR_Y - 26}, ${x(SPILL_OUT_STEP - 1) + 3} ${DDR_Y - 2}`}
              />
              <text className="spill-tag" x={x(SPILL_OUT_STEP - 1) - 6} y={y(120)} textAnchor="end">
                SPILL_OUT · 0c
              </text>
            </g>
          )}

          {step >= SPILL_IN_STEP && (
            <g className="spill-flow">
              <path
                className="spill-connector"
                d={`M ${x(SPILL_IN_STEP - 1)} ${DDR_Y - 2} C ${x(SPILL_IN_STEP - 1)} ${DDR_Y - 30}, ${x(SPILL_IN_STEP - 1)} ${y(560)}, ${x(SPILL_IN_STEP - 1) + 2} ${y(640) + 2}`}
              />
              <text className="spill-tag" x={x(SPILL_IN_STEP - 1) + 8} y={y(540)}>
                SPILL_IN @ 640 · 406c
              </text>
            </g>
          )}

          {step >= SPILL_IN_STEP && (
            <text className="cost-note" x={PX1 - 6} y={DDR_Y + DDR_H / 2 + 3.5} textAnchor="end">
              extra DDR traffic = Size(W) = 128
            </text>
          )}
        </g>
      )}

      {/* cursor */}
      <g className="chart-cursor" transform={`translate(${x(step)} 0)`}>
        <line x1="0" x2="0" y1={PY0 - 8} y2={PY1} />
      </g>

      <text className="axis-title" x={(PX0 + PX1) / 2} y={spill ? 466 : PY1 + 44} textAnchor="middle">
        schedule position
      </text>
      <text className="axis-title" transform={`translate(26 ${(PY0 + PY1) / 2}) rotate(-90)`} textAnchor="middle">
        UB address
      </text>
    </svg>
  )
}
