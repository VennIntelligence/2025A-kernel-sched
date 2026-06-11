import type { SchedNode } from './problemData'

const OP_SHORT: Record<string, string> = {
  SPILL_OUT: 'SP_OUT',
  SPILL_IN: 'SP_IN',
}

/**
 * The schedule order rendered as a row of clickable cells. It is shared by
 * every stage so the reader always sees where the cursor sits in the order.
 */
export function ScheduleStrip({
  nodes,
  step,
  maxStep,
  onSeek,
}: {
  nodes: SchedNode[]
  step: number
  maxStep: number
  onSeek: (step: number) => void
}) {
  return (
    <div className="sched-strip" role="list" aria-label="Schedule order">
      {nodes.map((node, index) => {
        const pos = index + 1
        const state =
          pos > maxStep ? 'locked' : pos === step ? 'active' : pos < step ? 'done' : ''
        return (
          <button
            key={node.id}
            type="button"
            role="listitem"
            className={`strip-cell kind-${node.kind} ${state}`}
            title={`${pos}. ${node.op} ${node.tag}`}
            onClick={() => onSeek(Math.min(pos, maxStep))}
          >
            <span className="cell-idx">{pos}</span>
            <span className="cell-op">{OP_SHORT[node.op] ?? node.op}</span>
            <span className="cell-tag">{node.tag}</span>
          </button>
        )
      })}
    </div>
  )
}
