import { MethodPipeline } from '../components/method/MethodPipeline'
import { OrderVsVictim } from '../components/method/OrderVsVictim'
import { PhiResidency } from '../components/method/PhiResidency'
import { CleanDirtyCost } from '../components/method/CleanDirtyCost'
import type { Copy } from '../lib/i18n'

export function MethodPage({ copy }: { copy: Copy['method'] }) {
  return (
    <div className="problem-view">
      <header className="page-hero">
        <p className="eyebrow">{copy.eyebrow}</p>
        <h1>{copy.title}</h1>
        <p className="hero-lead">{copy.lead}</p>
      </header>

      <MethodPipeline copy={copy.pipeline} />
      <OrderVsVictim copy={copy.orderVictim} />
      <PhiResidency copy={copy.residency} />
      <CleanDirtyCost copy={copy.cleanDirty} />
    </div>
  )
}
