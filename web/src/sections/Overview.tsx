import type { Copy } from '../lib/i18n'

export function Overview({ copy }: { copy: Copy }) {
  return (
    <section className="prose-section" aria-labelledby="abstract-h">
      <div className="abstract-block">
        <h2 id="abstract-h" className="section-title">{copy.abstract.title}</h2>
        <p className="abstract-body">{copy.abstract.body}</p>

        <ul className="highlight-row" aria-label={copy.highlights.title}>
          {copy.highlights.items.map((it) => (
            <li key={it.value}>
              <span className="highlight-value">{it.value}</span>
              <span className="highlight-label">{it.label}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="contrib-block">
        <h2 className="section-title">{copy.contributions.title}</h2>
        <p className="section-lead">{copy.contributions.lead}</p>
        <ol className="contrib-list">
          {copy.contributions.items.map((c) => (
            <li key={c.tag} className="contrib-item">
              <span className="contrib-tag">{c.tag}</span>
              <div>
                <h3>{c.name}</h3>
                <p>{c.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}
