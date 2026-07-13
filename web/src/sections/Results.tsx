import { FigureBlock } from '../components/FigureBlock'
import { P2ResultsTable, P3ResultsTable } from '../components/ResultTables'
import type { Copy } from '../lib/i18n'

export function Results({ copy }: { copy: Copy }) {
  const results = copy.results
  return (
    <section className="prose-section" id="results" aria-labelledby="results-h">
      <div className="section-head">
        <p className="eyebrow">{results.eyebrow}</p>
        <h2 id="results-h" className="section-title">{results.title}</h2>
        <p className="section-lead">{results.lead}</p>
      </div>

      <FigureBlock
        src="figures/headline_reductions.png"
        alt={results.headlineLabel}
        label={results.headlineLabel}
        caption={results.headlineCaption}
      />

      <div className="table-pair results-pair">
        <figure className="table-figure">
          <figcaption className="table-title">{results.mainTitle}</figcaption>
          <P2ResultsTable copy={results} />
          <p className="figure-block-caption">{results.mainCaption}</p>
        </figure>

        <figure className="table-figure">
          <figcaption className="table-title">{results.p3Title}</figcaption>
          <P3ResultsTable copy={results} />
          <p className="figure-block-caption">{results.p3Caption}</p>
        </figure>
      </div>

      <FigureBlock
        src="figures/order_headroom.png"
        alt={copy.theory.wsLabel}
        label={copy.theory.wsLabel}
        caption={copy.theory.wsCaption}
      />
    </section>
  )
}
