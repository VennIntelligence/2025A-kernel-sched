import type { Copy } from '../lib/i18n'

export function HomePage({
  copy,
  onOpenProblem,
}: {
  copy: Copy['home']
  onOpenProblem: () => void
}) {
  return (
    <section className="home-page">
      <div className="home-hero">
        <p className="eyebrow">{copy.eyebrow}</p>
        <h1>{copy.title}</h1>
        <p className="lead">{copy.lead}</p>
        <button className="primary-action" type="button" onClick={onOpenProblem}>
          {copy.openProblem}
        </button>
      </div>

      <section className="placeholder-panel" aria-label={copy.placeholderTitle}>
        <div>
          <p className="panel-kicker">Coming next</p>
          <h2>{copy.placeholderTitle}</h2>
          <p>{copy.placeholderBody}</p>
        </div>
      </section>

      <section className="summary-band">
        {copy.cards.map((card) => (
          <article key={card.label}>
            <span>{card.label}</span>
            <h2>{card.title}</h2>
            <p>{card.body}</p>
          </article>
        ))}
      </section>
    </section>
  )
}
