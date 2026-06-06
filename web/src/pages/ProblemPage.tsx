import { useState } from 'react'
import { ProblemAnimation } from '../components/problem/ProblemAnimation'
import { StageControls } from '../components/problem/StageControls'
import { stageOrder, type StageId } from '../components/problem/problemData'
import type { Copy } from '../lib/i18n'

export function ProblemPage({ copy }: { copy: Copy['problem'] }) {
  const [stage, setStage] = useState<StageId>('dag')
  const [step, setStep] = useState(4)
  const currentStageIndex = stageOrder.indexOf(stage)
  const activeStage = copy.stages[currentStageIndex]

  const goToNextStage = () => {
    const nextStage = stageOrder[(currentStageIndex + 1) % stageOrder.length]
    setStage(nextStage)
    setStep(nextStage === 'schedule' ? 5 : 4)
  }

  return (
    <>
      <section className="problem-layout">
        <div className="problem-copy">
          <p className="eyebrow">{copy.eyebrow}</p>
          <h1>{copy.title}</h1>
          <p className="lead">{copy.lead}</p>
        </div>

        <section className="visualizer" aria-label="Kernel scheduling animation">
          <div className="visualizer-header">
            <div>
              <p className="panel-kicker">{copy.animationStage}</p>
              <h2>{activeStage.title}</h2>
            </div>
            <button className="icon-button" type="button" onClick={goToNextStage} aria-label={copy.nextStage}>
              <span aria-hidden="true">→</span>
            </button>
          </div>
          <ProblemAnimation stage={stage} step={step} title={activeStage.title} />
          <StageControls
            stage={stage}
            step={step}
            cursorLabel={copy.scheduleCursor}
            onStageChange={setStage}
            onStepChange={setStep}
          />
          <p className="stage-detail">{activeStage.detail}</p>
        </section>
      </section>

      <section className="summary-band" id="problems">
        {copy.problems.map((problem) => (
          <article key={problem.label}>
            <span>{problem.label}</span>
            <h2>{problem.title}</h2>
            <p>{problem.body}</p>
          </article>
        ))}
      </section>

      <section className="export-note">
        <div>
          <p className="panel-kicker">{copy.exportTitle}</p>
          <h2>{copy.exportBody}</h2>
        </div>
        <code>cd web && npm run build</code>
      </section>
    </>
  )
}
