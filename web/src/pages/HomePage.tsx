import type { Copy } from '../lib/i18n'

export function HomePage({
  copy,
  onOpenProblem,
}: {
  copy: Copy['home']
  onOpenProblem: () => void
}) {
  return (
    <section className="paper-page">
      <header className="paper-hero">
        <h1>{copy.title}</h1>
        <p className="paper-subtitle">{copy.subtitle}</p>
        <div className="authors">
          {copy.authors.map((author) => (
            <span key={author}>{author}</span>
          ))}
        </div>
        <div className="affiliations">
          {copy.affiliations.map((affiliation) => (
            <span key={affiliation}>{affiliation}</span>
          ))}
        </div>
        <div className="paper-links" aria-label="Project links">
          {copy.links.map((link) => (
            <button key={link.label} type="button">
              {link.label}
            </button>
          ))}
        </div>
      </header>

      <section className="teaser-panel" aria-label={copy.teaserTitle}>
        <div className="teaser-visual">
          <span>Schedule</span>
          <span>Cache</span>
          <span>Spill</span>
          <span>Pipeline</span>
        </div>
        <p>{copy.teaserBody}</p>
      </section>

      <section className="paper-section">
        <h2>{copy.abstractTitle}</h2>
        <p>{copy.abstract}</p>
      </section>

      <section className="paper-section">
        <h2>{copy.animationTitle}</h2>
        <p>{copy.animationBody}</p>
        <button className="minimal-action" type="button" onClick={onOpenProblem}>
          <span>{copy.openProblem}</span>
          <svg className="action-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </button>
      </section>

      <section className="paper-section">
        <h2>{copy.bibtexTitle}</h2>
        <pre>{copy.bibtex}</pre>
      </section>
    </section>
  )
}
