import { useState } from 'react'
import { FigureCard } from '../viz/FigureCard'
import { Segmented, type SegOption } from '../viz/Segmented'
import { ORDER_VICTIM, VICTIMS } from '../../data/orderVictim'
import { fmt, pct, ratio } from '../../lib/format'
import type { MethodCopy } from '../../lib/i18n'

const CASE_LABEL: Record<string, string> = {
  Conv_Case0: 'Conv 0',
  Conv_Case1: 'Conv 1',
  FlashAttention_Case0: 'FA 0',
  FlashAttention_Case1: 'FA 1',
  Matmul_Case0: 'MM 0',
  Matmul_Case1: 'MM 1',
}

const caseOptions: SegOption<string>[] = ORDER_VICTIM.map((c) => ({ id: c.case, label: CASE_LABEL[c.case] ?? c.case }))
const victimOptions: SegOption<string>[] = VICTIMS.map((v) => ({ id: v, label: v }))

export function OrderVsVictim({ copy }: { copy: MethodCopy['orderVictim'] }) {
  const [caseId, setCaseId] = useState(ORDER_VICTIM[0].case)
  const [victim, setVictim] = useState(VICTIMS[0])

  const block = ORDER_VICTIM.find((c) => c.case === caseId) ?? ORDER_VICTIM[0]
  const orders = block.orders

  const extraFor = (o: (typeof orders)[number]) =>
    o.byVictim.find((v) => v.victim === victim)?.extra ?? o.extraMin

  const maxExtra = Math.max(...orders.flatMap((o) => o.byVictim.map((v) => v.extra)))
  const selected = orders.map(extraFor)
  const swing = Math.max(...selected) / Math.min(...selected)
  const maxCv = Math.max(...orders.map((o) => o.cv))
  const bestExtra = Math.min(...selected)

  return (
    <FigureCard
      kicker={copy.kicker}
      title={copy.title}
      caption={copy.caption}
      note={copy.note}
      action={
        <div className="ovv-controls">
          <span className="ctrl-label">{copy.caseLabel}</span>
          <Segmented options={caseOptions} value={caseId} onChange={setCaseId} ariaLabel={copy.caseLabel} size="sm" />
        </div>
      }
    >
      <div className="ovv">
        <div className="ovv-victim">
          <span className="ctrl-label">{copy.victimLabel}</span>
          <Segmented options={victimOptions} value={victim} onChange={setVictim} ariaLabel={copy.victimLabel} size="sm" />
        </div>

        <div className="ovv-bars" role="img" aria-label={`${copy.extraLabel} — ${CASE_LABEL[caseId]}`}>
          {orders.map((o) => {
            const value = extraFor(o)
            const isBest = value === bestExtra
            const bandLeft = (o.extraMin / maxExtra) * 100
            const bandWidth = ((o.extraMax - o.extraMin) / maxExtra) * 100
            return (
              <div className={`ovv-row${o.order === 'baseline' ? ' is-baseline' : ''}`} key={o.order}>
                <span className="ovv-order">{o.order}</span>
                <span className="ovv-track">
                  <span
                    className="ovv-band"
                    style={{ left: `${bandLeft}%`, width: `${Math.max(bandWidth, 0.4)}%` }}
                    aria-hidden="true"
                  />
                  <span
                    className={`ovv-fill${isBest ? ' is-best' : ''}`}
                    style={{ width: `${(value / maxExtra) * 100}%` }}
                  />
                </span>
                <span className="ovv-value">{fmt(value)}</span>
                <span className="ovv-cv" title={copy.cvLabel}>
                  CV {pct(o.cv, 1)}
                </span>
              </div>
            )
          })}
        </div>

        <div className="ovv-summary">
          <div className="ovv-stat">
            <span className="ovv-stat-value">{ratio(swing)}</span>
            <span className="ovv-stat-label">{copy.swingLabel}</span>
          </div>
          <div className="ovv-stat">
            <span className="ovv-stat-value">≤ {pct(maxCv, 1)}</span>
            <span className="ovv-stat-label">{copy.cvLabel}</span>
          </div>
        </div>
      </div>
    </FigureCard>
  )
}
