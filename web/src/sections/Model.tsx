import { FigureBlock } from '../components/FigureBlock'
import type { Copy } from '../lib/i18n'

export function Model({ copy }: { copy: Copy['model'] }) {
  return (
    <section className="prose-section" id="model" aria-labelledby="model-h">
      <div className="section-head">
        <p className="eyebrow">{copy.eyebrow}</p>
        <h2 id="model-h" className="section-title">{copy.title}</h2>
        <p className="section-lead">{copy.lead}</p>
      </div>

      <div className="model-grid">
        <FigureBlock
          src="figures/e1_dag_example.png"
          alt={copy.figLabel}
          label={copy.figLabel}
          caption={copy.figCaption}
        />

        <div className="cleandirty">
          <div className="cd-card cd-backed">
            <span className="cd-dot" aria-hidden="true" />
            <h3>{copy.backed.term}</h3>
            <p>{copy.backed.body}</p>
          </div>
          <div className="cd-card cd-unbacked">
            <span className="cd-dot" aria-hidden="true" />
            <h3>{copy.unbacked.term}</h3>
            <p>{copy.unbacked.body}</p>
          </div>
          <aside className="cd-aside">
            <h3>{copy.asideTitle}</h3>
            <p>{copy.asideBody}</p>
          </aside>
        </div>
      </div>

      <h3 className="subhead">{copy.viewsTitle}</h3>
      <div className="views-grid">
        {copy.views.map((v) => (
          <article key={v.tag} className="view-card">
            <span className="view-tag">{v.tag}</span>
            <h4>{v.title}</h4>
            <code className="view-formula">{v.formula}</code>
            <p>{v.body}</p>
          </article>
        ))}
      </div>
    </section>
  )
}
