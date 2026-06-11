import { useEffect, useMemo, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ProblemAnimation } from '../components/problem/ProblemAnimation'
import { StageControls } from '../components/problem/StageControls'
import { stageMaxStep, stageOrder, type StageId } from '../components/problem/problemData'
import { ArrowRightIcon, ChevronDownIcon } from '../components/icons'
import type { Copy } from '../lib/i18n'
import problemDocRaw from '../assets/problem.md?raw'

const TICK_MS = 900

export function ProblemPage({ copy }: { copy: Copy['problem'] }) {
  const prefersReducedMotion = useMemo(
    () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false,
    [],
  )

  const [stage, setStage] = useState<StageId>('dag')
  const [step, setStep] = useState(0)
  const [playing, setPlaying] = useState(!prefersReducedMotion)
  const [showDoc, setShowDoc] = useState(false)

  const stageIndex = stageOrder.indexOf(stage)
  const maxStep = stageMaxStep(stage)
  const stageCopy = copy.stages[stageIndex]

  useEffect(() => {
    if (!playing) return
    const timer = window.setInterval(() => {
      setStep((current) => {
        if (current >= maxStep) {
          setPlaying(false)
          return current
        }
        return current + 1
      })
    }, TICK_MS)
    return () => window.clearInterval(timer)
  }, [playing, maxStep])

  const selectStage = (next: StageId) => {
    setStage(next)
    setStep(0)
    setPlaying(!prefersReducedMotion)
  }

  const seek = (next: number) => {
    setStep(Math.max(0, Math.min(maxStep, next)))
    setPlaying(false)
  }

  const togglePlay = () => {
    if (!playing && step >= maxStep) setStep(0)
    setPlaying(!playing)
  }

  const restart = () => {
    setStep(0)
    setPlaying(true)
  }

  const goToNextStage = () => {
    selectStage(stageOrder[(stageIndex + 1) % stageOrder.length])
  }

  return (
    <>
      <header className="page-hero">
        <p className="eyebrow">{copy.eyebrow}</p>
        <h1>{copy.title}</h1>
        <p className="hero-lead">{copy.lead}</p>
      </header>

      <section className="figure-card" aria-label="Kernel scheduling interactive figure">
        <div className="figure-head">
          <div className="figure-head-text">
            <p className="figure-kicker">
              {copy.figureKicker} · {copy.stageWord} {stageIndex + 1} / {stageOrder.length}
            </p>
            <h2>{stageCopy.title}</h2>
          </div>
          <button type="button" className="btn-ghost next-stage" onClick={goToNextStage}>
            <span>{copy.nextStage}</span>
            <ArrowRightIcon size={15} />
          </button>
        </div>

        <ProblemAnimation stage={stage} step={step} legend={copy.legend} onSeek={seek} />

        <StageControls
          stage={stage}
          step={step}
          maxStep={maxStep}
          playing={playing}
          tabs={copy.stages.map((s) => s.tab)}
          copy={copy.controls}
          onStageChange={selectStage}
          onSeek={seek}
          onTogglePlay={togglePlay}
          onRestart={restart}
        />

        <p className="figure-caption">{stageCopy.detail}</p>
      </section>

      <section className="problem-grid" id="problems">
        {copy.problems.map((problem) => (
          <article key={problem.label} className="problem-card">
            <p className="card-label">{problem.label}</p>
            <h3>{problem.title}</h3>
            <code className="card-formula">{problem.formula}</code>
            <p className="card-body">{problem.body}</p>
          </article>
        ))}
      </section>

      <section className="doc-section">
        <h2>{copy.dataFormatTitle}</h2>
        <p>{copy.dataFormatBody}</p>
        <button type="button" className="btn-ghost" onClick={() => setShowDoc(!showDoc)} aria-expanded={showDoc}>
          <span>{showDoc ? copy.dataFormatHide : copy.dataFormatLink}</span>
          <ChevronDownIcon size={15} style={{ transform: showDoc ? 'rotate(180deg)' : 'none', transition: 'transform 0.25s ease' }} />
        </button>

        {showDoc && (
          <div className="markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{problemDocRaw}</ReactMarkdown>
          </div>
        )}
      </section>
    </>
  )
}
