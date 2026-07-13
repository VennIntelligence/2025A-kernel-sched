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

    </section>
  )
}
