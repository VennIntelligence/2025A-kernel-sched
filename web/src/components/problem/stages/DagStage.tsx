import { DAG_POS, DAG_VIEW, EDGES_17, NODES_17, dagSubLabel } from '../problemData'

const BOX_W = 104
const BOX_H = 36
const HALF_W = BOX_W / 2

function edgePath(from: string, to: string): string {
  const s = DAG_POS[from]
  const t = DAG_POS[to]
  const x0 = s.x + HALF_W
  const x1 = t.x - HALF_W - 7
  const dx = Math.max(26, Math.min(110, (x1 - x0) * 0.55))
  return `M ${x0} ${s.y} C ${x0 + dx} ${s.y}, ${x1 - dx} ${t.y}, ${x1} ${t.y}`
}

/**
 * Stage 1 — the computation DAG. Stepping the cursor walks the chosen
 * topological order; executed nodes receive their schedule-position badge.
 */
export function DagStage({ step }: { step: number }) {
  const orderOf = new Map(NODES_17.map((node, index) => [node.id, index + 1]))
  const activeId = step > 0 ? NODES_17[step - 1].id : null

  return (
    <svg
      className="stage-svg dag-svg"
      viewBox={`0 0 ${DAG_VIEW.w} ${DAG_VIEW.h}`}
      role="img"
      aria-label="Computation DAG with topological order"
    >
      <defs>
        <marker id="dag-arrow" markerWidth="7" markerHeight="7" refX="5.6" refY="3" orient="auto">
          <path d="M0,0.4 L6,3 L0,5.6" fill="none" stroke="#c6ccd4" strokeWidth="1.3" />
        </marker>
        <marker id="dag-arrow-done" markerWidth="7" markerHeight="7" refX="5.6" refY="3" orient="auto">
          <path d="M0,0.4 L6,3 L0,5.6" fill="none" stroke="#9aa3ae" strokeWidth="1.3" />
        </marker>
        <marker id="dag-arrow-active" markerWidth="7" markerHeight="7" refX="5.6" refY="3" orient="auto">
          <path d="M0,0.4 L6,3 L0,5.6" fill="none" stroke="#21509f" strokeWidth="1.4" />
        </marker>
      </defs>

      {EDGES_17.map(({ from, to }) => {
        const executed = orderOf.get(from)! <= step && orderOf.get(to)! <= step
        const active = from === activeId || to === activeId
        const marker = active ? 'dag-arrow-active' : executed ? 'dag-arrow-done' : 'dag-arrow'
        return (
          <path
            key={`${from}-${to}`}
            className={`dag-edge ${active ? 'is-active' : executed ? 'is-done' : ''}`}
            d={edgePath(from, to)}
            markerEnd={`url(#${marker})`}
          />
        )
      })}

      {NODES_17.map((node) => {
        const pos = DAG_POS[node.id]
        const order = orderOf.get(node.id)!
        const executed = order <= step
        const active = node.id === activeId
        return (
          <g
            key={node.id}
            className={`dag-node kind-${node.kind} ${executed ? 'is-done' : ''} ${active ? 'is-active' : ''}`}
            transform={`translate(${pos.x} ${pos.y})`}
          >
            <rect className="dag-box" x={-HALF_W} y={-BOX_H / 2} width={BOX_W} height={BOX_H} rx="7" />
            <text className="dag-op" y="-2.5">
              {node.op}
            </text>
            <text className={`dag-sub ${node.pipe ? `pipe-${node.pipe}` : ''}`} y="11.5">
              {node.kind === 'op' ? `${dagSubLabel(node)} · ${node.pipe}` : dagSubLabel(node)}
            </text>
            <g className="dag-badge" opacity={executed ? 1 : 0}>
              <circle cx={HALF_W - 8} cy={-BOX_H / 2} r="8.5" />
              <text x={HALF_W - 8} y={-BOX_H / 2 + 3}>
                {order}
              </text>
            </g>
          </g>
        )
      })}

      <text className="svg-footnote" x="16" y={DAG_VIEW.h - 12}>
        edges = data dependency · badge = position in chosen topological order
      </text>
    </svg>
  )
}
