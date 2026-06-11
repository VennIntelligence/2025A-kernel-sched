import { Fragment } from 'react'
import { ArrowRightIcon } from '../icons'
import type { MethodCopy } from '../../lib/i18n'

export function MethodPipeline({ copy }: { copy: MethodCopy['pipeline'] }) {
  return (
    <section className="figure-card method-pipeline-card">
      <div className="figure-head">
        <div className="figure-head-text">
          <p className="figure-kicker">{copy.kicker}</p>
          <h2>{copy.title}</h2>
        </div>
      </div>

      <ol className="method-pipeline" aria-label={copy.title}>
        {copy.steps.map((step, index) => (
          <Fragment key={step}>
            <li className="pipe-step">
              <span className="pipe-num">{index + 1}</span>
              <span className="pipe-text">{step}</span>
            </li>
            {index < copy.steps.length - 1 && (
              <li className="pipe-arrow" aria-hidden="true">
                <ArrowRightIcon size={16} />
              </li>
            )}
          </Fragment>
        ))}
      </ol>

      <p className="figure-caption">{copy.caption}</p>
    </section>
  )
}
