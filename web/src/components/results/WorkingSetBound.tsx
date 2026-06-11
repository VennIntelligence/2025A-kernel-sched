import { FigureCard } from '../viz/FigureCard'
import { WORKING_SET } from '../../data/workingSet'
import { ratio as fmtRatio } from '../../lib/format'
import type { ResultsCopy } from '../../lib/i18n'

const CASE_SHORT: Record<string, string> = {
  Conv_Case0: 'Conv 0',
  Conv_Case1: 'Conv 1',
  FlashAttention_Case0: 'FA 0',
  FlashAttention_Case1: 'FA 1',
  Matmul_Case0: 'MM 0',
  Matmul_Case1: 'MM 1',
}

// The binding caches (L1 / UB) carry the capacity story; L0* sit far below 1.
const ROWS = WORKING_SET.filter((r) => r.cache === 'L1' || r.cache === 'UB')
  .slice()
  .sort((a, b) => b.ratio - a.ratio)

const MAX_RATIO = Math.max(...ROWS.map((r) => r.ratio), 1)
const CAP_FRAC = (1 / MAX_RATIO) * 100

export function WorkingSetBound({ copy }: { copy: ResultsCopy['workingSet'] }) {
  return (
    <FigureCard
      kicker={copy.kicker}
      title={copy.title}
      caption={copy.caption}
      note={copy.note}
      action={
        <div className="ws-legend">
          <span className="lg-bound">{copy.capacityBound}</span>
          <span className="lg-reach">{copy.orderReachable}</span>
        </div>
      }
    >
      <div className="ws">
        <div className="ws-chart">
          {ROWS.map((r) => {
            const bound = r.boundClass === 'capacity_bound'
            return (
              <div className={`ws-row${bound ? ' is-bound' : ''}`} key={`${r.case}-${r.cache}`}>
                <span className="ws-label">
                  {CASE_SHORT[r.case]} · {r.cache}
                </span>
                <span className="ws-track">
                  <span className={`ws-fill${bound ? ' is-bound' : ''}`} style={{ width: `${(r.ratio / MAX_RATIO) * 100}%` }} />
                  <span className="ws-cap-tick" style={{ left: `${CAP_FRAC}%` }} aria-hidden="true" />
                </span>
                <span className="ws-value">{fmtRatio(r.ratio)}</span>
              </div>
            )
          })}
        </div>
        <p className="ws-axis">{copy.ratioAxis} · <span className="ws-axis-cap">— —</span> = 1× capacity</p>
      </div>
    </FigureCard>
  )
}
