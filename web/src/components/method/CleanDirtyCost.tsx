import { useState } from 'react'
import { FigureCard } from '../viz/FigureCard'
import { Segmented, type SegOption } from '../viz/Segmented'
import { SYNTH_ABLATION } from '../../data/cleanDirty'
import { fmt, ratio } from '../../lib/format'
import type { MethodCopy } from '../../lib/i18n'

const ORDERS = Array.from(new Set(SYNTH_ABLATION.map((r) => r.order)))
const orderOptions: SegOption<string>[] = ORDERS.map((o) => ({ id: o, label: o }))

export function CleanDirtyCost({ copy }: { copy: MethodCopy['cleanDirty'] }) {
  const [order, setOrder] = useState('capfit_id')

  const clean = SYNTH_ABLATION.find((r) => r.order === order && r.reserve === 'clean')!
  const dirty = SYNTH_ABLATION.find((r) => r.order === order && r.reserve === 'dirty')!
  const max = Math.max(clean.extra, dirty.extra)
  const sameSpills = clean.spills === dirty.spills
  const gap = dirty.extra / clean.extra

  return (
    <FigureCard
      kicker={copy.kicker}
      title={copy.title}
      caption={copy.caption}
      note={copy.note}
      action={<Segmented options={orderOptions} value={order} onChange={setOrder} ariaLabel={copy.title} size="sm" />}
    >
      <div className="cd">
        <div className="cd-bars">
          <div className="cd-row cd-clean">
            <span className="cd-name">{copy.clean}</span>
            <span className="cd-track">
              <span className="cd-fill" style={{ width: `${(clean.extra / max) * 100}%` }}>
                <span className="cd-val">{fmt(clean.extra)}</span>
              </span>
            </span>
            <span className="cd-spills">{clean.spills} spills</span>
          </div>
          <div className="cd-row cd-dirty">
            <span className="cd-name">{copy.dirty}</span>
            <span className="cd-track">
              <span className="cd-fill" style={{ width: `${(dirty.extra / max) * 100}%` }}>
                <span className="cd-val">{fmt(dirty.extra)}</span>
              </span>
            </span>
            <span className="cd-spills">{dirty.spills} spills</span>
          </div>
        </div>

        <div className="cd-gap" aria-hidden={!sameSpills}>
          <span className="cd-gap-value">{ratio(gap)}</span>
          <span className="cd-gap-label">{copy.perSpill}</span>
        </div>
      </div>
    </FigureCard>
  )
}
