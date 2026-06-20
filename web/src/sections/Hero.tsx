import { CodeIcon, DataIcon, PaperIcon, ResultsIcon } from '../components/icons'
import { FigureBlock } from '../components/FigureBlock'
import type { Copy, LinkKind } from '../lib/i18n'

const LINK_ICON: Record<LinkKind, typeof PaperIcon> = {
  paper: PaperIcon,
  code: CodeIcon,
  data: DataIcon,
  results: ResultsIcon,
}

export function Hero({ copy }: { copy: Copy }) {
  const m = copy.meta
  return (
    <header className="hero" id="overview">
      <p className="venue">{m.venue}</p>
      <h1 className="paper-title">{m.title}</h1>

      <p className="byline">
        {m.authors.map((a, i) => (
          <span key={a.email}>
            {a.name}
            {i < m.authors.length - 1 ? <span className="byline-sep">·</span> : null}
          </span>
        ))}
      </p>
      <p className="byline-emails">
        {m.authors.map((a, i) => (
          <span key={a.email}>
            <a href={`mailto:${a.email}`}>{a.email}</a>
            {i < m.authors.length - 1 ? <span className="byline-sep">·</span> : null}
          </span>
        ))}
      </p>
      <p className="affiliation">{m.affiliation}</p>

      <nav className="resource-links" aria-label="Resources">
        {m.links.map((link) => {
          const Icon = LINK_ICON[link.kind]
          return (
            <a key={link.label} href={link.href} target="_blank" rel="noreferrer" className="resource-link">
              <Icon size={15} />
              <span>{link.label}</span>
            </a>
          )
        })}
      </nav>

      <div className="hero-figures">
        <FigureBlock src="figures/concept.png" alt={m.fig1Label} label={m.fig1Label} caption={m.fig1Caption} />
        <FigureBlock src="figures/pipeline.png" alt={m.fig2Label} label={m.fig2Label} caption={m.fig2Caption} />
      </div>
    </header>
  )
}
