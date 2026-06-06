import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ProblemAnimation } from '../components/problem/ProblemAnimation'
import { StageControls } from '../components/problem/StageControls'
import { stageOrder, type StageId } from '../components/problem/problemData'
import type { Copy } from '../lib/i18n'
import problemDocRaw from '../assets/problem.md?raw'

export function ProblemPage({ copy }: { copy: Copy['problem'] }) {
  const [stage, setStage] = useState<StageId>('dag')
  const [step, setStep] = useState(4)
  const [showDoc, setShowDoc] = useState(false)
  const currentStageIndex = stageOrder.indexOf(stage)
  const activeStage = copy.stages[currentStageIndex]

  const goToNextStage = () => {
    const nextStage = stageOrder[(currentStageIndex + 1) % stageOrder.length]
    setStage(nextStage)
    setStep(nextStage === 'schedule' ? 5 : 4)
  }

  return (
    <>
      <header className="paper-hero problem-hero">
        <p className="eyebrow">{copy.eyebrow}</p>
        <h1>{copy.title}</h1>
        <p className="paper-subtitle">{copy.lead}</p>
      </header>

      <section className="visualizer-container">
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

      <section className="paper-section problem-docs">
        <h2>{copy.dataFormatTitle}</h2>
        <p>{copy.dataFormatBody}</p>
        <button className="minimal-action" type="button" onClick={() => setShowDoc(!showDoc)}>
          <span>{copy.dataFormatLink}</span>
          <svg
            className="action-arrow"
            style={{ transform: showDoc ? 'rotate(90deg)' : 'rotate(0)' }}
            width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
          >
            <line x1="5" y1="12" x2="19" y2="12"></line>
            <polyline points="12 5 19 12 12 19"></polyline>
          </svg>
        </button>
      </section>

      {showDoc && (
        <section className="paper-section markdown-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{problemDocRaw}</ReactMarkdown>
        </section>
      )}
    </>
  )
}
