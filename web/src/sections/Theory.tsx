import { FigureBlock } from '../components/FigureBlock'
import type { Copy } from '../lib/i18n'

export function Theory({ copy }: { copy: Copy['theory'] }) {
  return (
    <section className="prose-section" id="theory" aria-labelledby="theory-h">
      <div className="section-head">
        <p className="eyebrow">{copy.eyebrow}</p>
        <h2 id="theory-h" className="section-title">{copy.title}</h2>
        <p className="section-lead">{copy.lead}</p>
      </div>

      <div className="theorem-list">
        {copy.items.map((t) => (
          <article key={t.tag} className="theorem">
            <header>
              <span className="theorem-tag">{t.tag}</span>
              <h3>{t.name}</h3>
            </header>
            <p className="theorem-statement">{t.statement}</p>
            <p className="theorem-note">{t.note}</p>
          </article>
        ))}
      </div>

      <FigureBlock
        src="figures/order_headroom.png"
        alt={copy.wsLabel}
        label={copy.wsLabel}
        caption={copy.wsCaption}
      />
    </section>
  )
}
