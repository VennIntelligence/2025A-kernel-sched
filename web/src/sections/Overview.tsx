import type { Copy } from '../lib/i18n'
import { FigureBlock } from '../components/FigureBlock'

export function Overview({ copy }: { copy: Copy }) {
  return (
    <section className="prose-section" aria-labelledby="abstract-h">
      <div className="abstract-block">
        <h2 id="abstract-h" className="section-title">{copy.abstract.title}</h2>
        <p className="abstract-body">{copy.abstract.body}</p>
      </div>

      <FigureBlock
        src="figures/bridge_conv0.png"
        alt={copy.meta.fig1Label}
        label={copy.meta.fig1Label}
        caption={copy.meta.fig1Caption}
      />
    </section>
  )
}
