import { FigureBlock } from '../components/FigureBlock'
import { BenchmarkTable, MainResultsTable, RuntimeTable } from '../components/ResultTables'
import type { Copy } from '../lib/i18n'

export function Results({ copy }: { copy: Copy['results'] }) {
  return (
    <section className="prose-section" id="results" aria-labelledby="results-h">
      <div className="section-head">
        <p className="eyebrow">{copy.eyebrow}</p>
        <h2 id="results-h" className="section-title">{copy.title}</h2>
        <p className="section-lead">{copy.lead}</p>
      </div>

      {/* Main result: P2 spill traffic table + baseline figure */}
      <figure className="table-figure">
        <figcaption className="table-title">
          {copy.mainTitle}
          <span className="table-hint">{copy.lowerBetter} ↓</span>
        </figcaption>
        <MainResultsTable copy={copy} />
        <p className="figure-block-caption">{copy.mainCaption}</p>
      </figure>

      <FigureBlock
        src="figures/baselines.webp"
        alt={copy.baselinesLabel}
        label={copy.baselinesLabel}
        caption={copy.baselinesCaption}
      />

      {/* Applicability */}
      <div className="subblock">
        <h3 className="subhead">{copy.applicTitle}</h3>
        <p className="section-lead">{copy.applicBody}</p>
        <FigureBlock
          src="figures/applicability.webp"
          alt={copy.applicLabel}
          label={copy.applicLabel}
          caption={copy.applicCaption}
        />
      </div>

      {/* Controlled ablation */}
      <div className="callout">
        <h3>{copy.ablationTitle}</h3>
        <p>{copy.ablationBody}</p>
        <div className="metric-pair">
          <div className="metric metric-clean">
            <span className="metric-value">1,536</span>
            <span className="metric-label">clean reserve · extra</span>
          </div>
          <div className="metric-eq">= 2×</div>
          <div className="metric metric-dirty">
            <span className="metric-value">3,072</span>
            <span className="metric-label">dirty reserve · extra</span>
          </div>
        </div>
      </div>

      {/* Benchmark + runtime tables */}
      <div className="table-pair">
        <figure className="table-figure">
          <figcaption className="table-title">{copy.benchTitle}</figcaption>
          <BenchmarkTable copy={copy} />
          <p className="figure-block-caption">{copy.benchCaption}</p>
        </figure>

        <figure className="table-figure">
          <figcaption className="table-title">{copy.runtimeTitle}</figcaption>
          <RuntimeTable copy={copy} />
          <p className="figure-block-caption">{copy.runtimeCaption}</p>
        </figure>
      </div>

      <p className="cap-note">
        <strong>{copy.capTitle}.</strong> {copy.capBody}
      </p>
    </section>
  )
}
