import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRightIcon,
  CheckIcon,
  CodeIcon,
  CopyIcon,
  DataIcon,
  PaperIcon,
  ResultsIcon,
} from '../components/icons'
import type { Copy, LinkKind } from '../lib/i18n'

const LINK_ICON: Record<LinkKind, typeof PaperIcon> = {
  paper: PaperIcon,
  code: CodeIcon,
  data: DataIcon,
  results: ResultsIcon,
}

/** Decorative static teaser: schedule → placement → pipeline. */
function TeaserFigure() {
  return (
    <svg className="teaser-svg" viewBox="0 0 900 210" role="img" aria-hidden="true">
      {/* panel 1 — DAG */}
      <g transform="translate(18 14)">
        <rect className="teaser-frame" width="252" height="158" rx="10" />
        <g className="teaser-dag">
          <path d="M52 44 C 76 44, 76 79, 100 79" />
          <path d="M52 114 C 76 114, 76 79, 100 79" />
          <path d="M148 79 C 166 79, 166 56, 184 56" />
          <path d="M148 79 C 166 79, 166 102, 184 102" />
          <rect x="22" y="32" width="30" height="24" rx="5" className="t-cache" />
          <rect x="22" y="102" width="30" height="24" rx="5" className="t-cache" />
          <rect x="100" y="67" width="48" height="24" rx="5" className="t-op" />
          <rect x="184" y="44" width="30" height="24" rx="5" className="t-op2" />
          <rect x="184" y="90" width="30" height="24" rx="5" className="t-cache" />
        </g>
        <text className="teaser-tag" x="126" y="146" textAnchor="middle">
          topological schedule
        </text>
      </g>

      <g className="teaser-arrow" transform="translate(288 90)">
        <path d="M0 3h22m0 0-7-7m7 7-7 7" />
      </g>

      {/* panel 2 — memory map */}
      <g transform="translate(330 14)">
        <rect className="teaser-frame" width="252" height="158" rx="10" />
        <line className="teaser-cap" x1="18" x2="234" y1="30" y2="30" />
        <rect x="18" y="92" width="120" height="36" rx="4" className="m-b1" />
        <rect x="58" y="56" width="160" height="28" rx="4" className="m-b0" />
        <rect x="98" y="36" width="84" height="16" rx="4" className="m-b2" />
        <rect x="150" y="92" width="84" height="36" rx="4" className="m-b3" />
        <text className="teaser-tag" x="126" y="146" textAnchor="middle">
          physical placement
        </text>
      </g>

      <g className="teaser-arrow" transform="translate(600 90)">
        <path d="M0 3h22m0 0-7-7m7 7-7 7" />
      </g>

      {/* panel 3 — pipeline */}
      <g transform="translate(642 14)">
        <rect className="teaser-frame" width="240" height="158" rx="10" />
        <line className="teaser-rail" x1="18" x2="222" y1="48" y2="48" />
        <line className="teaser-rail" x1="18" x2="222" y1="84" y2="84" />
        <line className="teaser-rail" x1="18" x2="222" y1="120" y2="120" />
        <rect x="18" y="38" width="64" height="20" rx="4" className="p-mte2" />
        <rect x="92" y="38" width="34" height="20" rx="4" className="p-mte2" />
        <rect x="100" y="74" width="76" height="20" rx="4" className="p-cube" />
        <rect x="150" y="110" width="52" height="20" rx="4" className="p-mte3" />
        <text className="teaser-tag" x="120" y="146" textAnchor="middle">
          pipelined execution
        </text>
      </g>
    </svg>
  )
}

export function HomePage({ copy }: { copy: Copy['home'] }) {
  const [copied, setCopied] = useState(false)

  const copyBibtex = async () => {
    try {
      await navigator.clipboard.writeText(copy.bibtex)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2000)
    } catch {
      /* clipboard unavailable (e.g. insecure context) — ignore */
    }
  }

  return (
    <section className="paper-page">
      <header className="page-hero">
        <p className="eyebrow">{copy.eyebrow}</p>
        <h1>{copy.title}</h1>
        <p className="hero-lead">{copy.subtitle}</p>

        <div className="authors">
          {copy.authors.map((author) => (
            <span key={author}>{author}</span>
          ))}
        </div>
        <div className="affiliations">{copy.affiliations.join(' · ')}</div>

        <div className="paper-links" aria-label="Project links">
          {copy.links.map((link) => {
            const Icon = LINK_ICON[link.kind]
            return (
              <button key={link.label} type="button" className="btn-pill">
                <Icon size={15} />
                <span>{link.label}</span>
              </button>
            )
          })}
        </div>
      </header>

      <figure className="teaser-panel">
        <TeaserFigure />
        <figcaption>{copy.teaserCaption}</figcaption>
      </figure>

      <section className="paper-section">
        <h2>{copy.abstractTitle}</h2>
        <p className="abstract-text">{copy.abstract}</p>
      </section>

      <section className="paper-section">
        <h2>{copy.scoresTitle}</h2>
        <div className="score-bar">
          {copy.scores.map((s) => (
            <div key={s.label} className="score-chip">
              <span className="score-value">{s.value}</span>
              <span className="score-label">{s.label}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="paper-section">
        <h2>{copy.contribTitle}</h2>
        <p>{copy.contribLead}</p>
        <div className="contrib-grid">
          {copy.contributions.map((c) => (
            <Link key={c.tag} to="/method" className="contrib-card">
              <span className="contrib-tag">{c.tag}</span>
              <h3>{c.name}</h3>
              <p>{c.body}</p>
              <span className="contrib-go">
                <ArrowRightIcon size={14} />
              </span>
            </Link>
          ))}
        </div>
      </section>

      <section className="paper-section cta-section">
        <h2>{copy.animationTitle}</h2>
        <p>{copy.animationBody}</p>
        <Link className="btn-primary" to="/problem">
          <span>{copy.openProblem}</span>
          <ArrowRightIcon size={16} />
        </Link>
      </section>

      <section className="paper-section">
        <div className="bibtex-head">
          <h2>{copy.bibtexTitle}</h2>
          <button type="button" className="btn-ghost btn-copy" onClick={copyBibtex}>
            {copied ? <CheckIcon size={14} /> : <CopyIcon size={14} />}
            <span>{copied ? copy.copied : copy.copyBibtex}</span>
          </button>
        </div>
        <pre className="bibtex-block">{copy.bibtex}</pre>
      </section>
    </section>
  )
}
