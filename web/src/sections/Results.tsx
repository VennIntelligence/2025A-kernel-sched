import { FigureBlock } from '../components/FigureBlock'
import { BenchmarkTable, P2ResultsTable, P3ResultsTable, ResearchEvidenceTable } from '../components/ResultTables'
import type { Copy } from '../lib/i18n'

export function Results({ copy }: { copy: Copy['results'] }) {
  return (
    <section className="prose-section" id="results" aria-labelledby="results-h">
      <div className="section-head">
        <p className="eyebrow">{copy.eyebrow}</p>
        <h2 id="results-h" className="section-title">{copy.title}</h2>
        <p className="section-lead">{copy.lead}</p>
      </div>

      <FigureBlock
        src="figures/headline_reductions.png"
        alt={copy.headlineLabel}
        label={copy.headlineLabel}
        caption={copy.headlineCaption}
      />

      <figure className="table-figure">
        <figcaption className="table-title">
          {copy.mainTitle}
          <span className="table-hint">{copy.lowerBetter} ↓</span>
        </figcaption>
        <P2ResultsTable copy={copy} />
        <p className="figure-block-caption">{copy.mainCaption}</p>
      </figure>

      <figure className="table-figure">
        <figcaption className="table-title">{copy.p3Title}</figcaption>
        <P3ResultsTable copy={copy} />
        <p className="figure-block-caption">{copy.p3Caption}</p>
      </figure>

      <figure className="table-figure">
        <figcaption className="table-title">{copy.evidenceTitle}</figcaption>
        <ResearchEvidenceTable copy={copy} />
        <p className="figure-block-caption">{copy.evidenceCaption}</p>
      </figure>

      <div className="subblock">
        <h3 className="subhead">{copy.accountingTitle}</h3>
        <p className="section-lead">{copy.accountingBody}</p>
      </div>

      <FigureBlock
        src="figures/vd_plane.png"
        alt={copy.accountingLabel}
        label={copy.accountingLabel}
        caption={copy.accountingCaption}
        maxWidth={680}
      />

      <div className="callout">
        <h3>{copy.robustnessTitle}</h3>
        <p>{copy.robustnessBody}</p>
      </div>

      <figure className="table-figure">
        <figcaption className="table-title">{copy.benchTitle}</figcaption>
        <BenchmarkTable copy={copy} />
        <p className="figure-block-caption">{copy.benchCaption}</p>
      </figure>

      <p className="cap-note">
        <strong>{copy.capTitle}.</strong> {copy.capBody}
      </p>
    </section>
  )
}
