import { useMemo } from 'react'
import { edges, graphNodes, schedule, type StageId } from './problemData'

export function ProblemAnimation({ stage, step, title }: { stage: StageId; step: number; title: string }) {
  const positions = useMemo(() => new Map(graphNodes.map((node) => [node.id, node])), [])
  const visibleStep = Math.min(step, schedule.length - 1)
  const activeNodeId = schedule[visibleStep].nodeId
  const residency = schedule.slice(0, visibleStep + 1).reduce((total, item) => total + item.delta, 0)
  const peakResidency = schedule
    .slice(0, visibleStep + 1)
    .reduce(
      (acc, item) => {
        const next = acc.current + item.delta
        return { current: next, peak: Math.max(acc.peak, next) }
      },
      { current: 0, peak: 0 },
    ).peak

  return (
    <svg className="problem-svg" viewBox="0 0 1000 620" role="img" aria-label="Kernel scheduling visual model">
      <defs>
        <marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">
          <path d="M0,0 L0,6 L9,3 z" fill="#6f7785" />
        </marker>
      </defs>

      <rect className="svg-bg" x="0" y="0" width="1000" height="620" rx="18" />
      <text className="svg-title" x="36" y="46">
        {title}
      </text>

      {edges.map(([from, to]) => {
        const start = positions.get(from)!
        const end = positions.get(to)!
        const active = from === activeNodeId || to === activeNodeId
        return (
          <line
            key={`${from}-${to}`}
            className={active ? 'edge active' : 'edge'}
            x1={start.x + 54}
            y1={start.y}
            x2={end.x - 54}
            y2={end.y}
            markerEnd="url(#arrow)"
          />
        )
      })}

      {graphNodes.map((node) => (
        <g key={node.id} className={`node ${node.kind} ${node.id === activeNodeId ? 'active' : ''}`}>
          <rect x={node.x - 58} y={node.y - 25} width="116" height="50" rx="8" />
          <text x={node.x} y={node.y + 5}>
            {node.label}
          </text>
          {node.pipe && (
            <text className="pipe-label" x={node.x} y={node.y + 40}>
              {node.pipe}
            </text>
          )}
        </g>
      ))}

      <ScheduleStrip activeIndex={visibleStep} />

      {(stage === 'schedule' || stage === 'memory' || stage === 'spill') && (
        <ResidencyPanel residency={residency} peakResidency={peakResidency} />
      )}

      {(stage === 'memory' || stage === 'spill') && <MemoryPanel spill={stage === 'spill'} />}

      {stage === 'pipeline' && <PipelinePanel />}
    </svg>
  )
}

function ScheduleStrip({ activeIndex }: { activeIndex: number }) {
  return (
    <g transform="translate(42 326)">
      <text className="section-label" x="0" y="0">
        schedule order
      </text>
      {schedule.map((item, index) => (
        <g key={item.nodeId} transform={`translate(${index * 91} 18)`}>
          <rect className={index <= activeIndex ? 'schedule-cell seen' : 'schedule-cell'} width="78" height="48" rx="7" />
          <text className="schedule-index" x="8" y="17">
            {index + 1}
          </text>
          <text className="schedule-text" x="39" y="33">
            {item.label}
          </text>
        </g>
      ))}
    </g>
  )
}

function ResidencyPanel({ residency, peakResidency }: { residency: number; peakResidency: number }) {
  const height = Math.min(160, residency * 0.42)
  const peakHeight = Math.min(160, peakResidency * 0.42)

  return (
    <g transform="translate(42 430)">
      <text className="section-label" x="0" y="0">
        V_stay prefix scan
      </text>
      <rect className="meter-shell" x="0" y="26" width="260" height="172" rx="10" />
      <rect className="meter-fill" x="28" y={188 - height} width="70" height={height} rx="6" />
      <line className="peak-line" x1="18" x2="230" y1={188 - peakHeight} y2={188 - peakHeight} />
      <text className="metric-text" x="122" y="82">
        current {residency}
      </text>
      <text className="metric-text strong" x="122" y="112">
        maxV_stay {peakResidency}
      </text>
    </g>
  )
}

function MemoryPanel({ spill }: { spill: boolean }) {
  return (
    <g transform="translate(348 430)">
      <text className="section-label" x="0" y="0">
        UB physical cache [0, 1023]
      </text>
      <rect className="cache-track" x="0" y="38" width="430" height="44" rx="8" />
      <rect className={spill ? 'cache-block spilled' : 'cache-block'} x="24" y="46" width="118" height="28" rx="6" />
      <text className="cache-label" x="83" y="65">
        b0 [0,191]
      </text>
      <rect className="cache-block secondary" x="170" y="46" width="82" height="28" rx="6" />
      <text className="cache-label" x="211" y="65">
        b1
      </text>
      {spill && (
        <>
          <path className="spill-path" d="M98 94 C150 130, 210 130, 265 94" />
          <rect className="ddr-block" x="274" y="108" width="108" height="36" rx="8" />
          <text className="cache-label" x="328" y="131">
            DDR copy
          </text>
          <rect className="cache-block reloaded" x="292" y="46" width="118" height="28" rx="6" />
          <text className="cache-label" x="351" y="65">
            b0 NewOffset
          </text>
        </>
      )}
    </g>
  )
}

function PipelinePanel() {
  const lanes = [
    { pipe: 'MTE2', ops: [{ x: 92, w: 118, label: 'COPY_IN' }, { x: 400, w: 128, label: 'SPILL_IN' }] },
    { pipe: 'MTE3', ops: [{ x: 280, w: 110, label: 'SPILL_OUT' }, { x: 500, w: 118, label: 'COPY_OUT' }] },
    { pipe: 'CUBE', ops: [{ x: 230, w: 160, label: 'MATMUL' }] },
    { pipe: 'MTE1', ops: [{ x: 94, w: 105, label: 'MOVE' }] },
  ]

  return (
    <g transform="translate(348 420)">
      <text className="section-label" x="0" y="0">
        pipelined execution time
      </text>
      {lanes.map((lane, laneIndex) => (
        <g key={lane.pipe} transform={`translate(0 ${28 + laneIndex * 44})`}>
          <text className="lane-label" x="0" y="25">
            {lane.pipe}
          </text>
          <line className="lane-line" x1="62" y1="20" x2="620" y2="20" />
          {lane.ops.map((op) => (
            <g key={`${lane.pipe}-${op.label}`}>
              <rect className="op-bar" x={op.x} y="6" width={op.w} height="28" rx="7" />
              <text className="bar-label" x={op.x + op.w / 2} y="25">
                {op.label}
              </text>
            </g>
          ))}
        </g>
      ))}
      <text className="metric-text strong" x="540" y="76">
        T = max E(v)
      </text>
    </g>
  )
}
