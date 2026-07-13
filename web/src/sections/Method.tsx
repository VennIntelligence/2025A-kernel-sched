import { FigureBlock } from '../components/FigureBlock'
import type { Copy } from '../lib/i18n'

export function Method({ copy }: { copy: Copy['method'] }) {
  return (
    <section className="prose-section" id="method" aria-labelledby="method-h">
      <div className="section-head">
        <p className="eyebrow">{copy.eyebrow}</p>
        <h2 id="method-h" className="section-title">{copy.title}</h2>
        <p className="section-lead">{copy.lead}</p>
      </div>

      <h3 className="subhead">{copy.stagesTitle}</h3>
      <ol className="stage-flow">
        {copy.stages.map((s) => (
          <li key={s.n} className="stage-step">
            <span className="stage-num">{s.n}</span>
            <h4>{s.title}</h4>
            <p>{s.body}</p>
          </li>
        ))}
      </ol>

      <FigureBlock
        src="figures/frontier_mechanism.png"
        alt={copy.pipelineLabel}
        label={copy.pipelineLabel}
        caption={copy.pipelineCaption}
      />

    </section>
  )
}
