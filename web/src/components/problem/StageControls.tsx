import {
  PauseIcon,
  PlayIcon,
  RestartIcon,
  StepBackIcon,
  StepForwardIcon,
} from '../icons'
import { stages, type StageId } from './problemData'

export type ControlsCopy = {
  play: string
  pause: string
  restart: string
  prevStep: string
  nextStep: string
}

export function StageControls({
  stage,
  step,
  maxStep,
  playing,
  tabs,
  copy,
  onStageChange,
  onSeek,
  onTogglePlay,
  onRestart,
}: {
  stage: StageId
  step: number
  maxStep: number
  playing: boolean
  tabs: string[]
  copy: ControlsCopy
  onStageChange: (stage: StageId) => void
  onSeek: (step: number) => void
  onTogglePlay: () => void
  onRestart: () => void
}) {
  const progress = maxStep > 0 ? (step / maxStep) * 100 : 0

  return (
    <div className="viz-controls">
      <div className="stage-tabs" role="tablist" aria-label="Animation stages">
        {stages.map((item, index) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={item.id === stage}
            className={item.id === stage ? 'is-active' : ''}
            onClick={() => onStageChange(item.id)}
          >
            <span className="tab-num">{index + 1}</span>
            <span className="tab-label">{tabs[index]}</span>
          </button>
        ))}
      </div>

      <div className="transport">
        <div className="transport-buttons">
          <button type="button" className="t-btn" onClick={onRestart} title={copy.restart} aria-label={copy.restart}>
            <RestartIcon size={15} />
          </button>
          <button
            type="button"
            className="t-btn"
            onClick={() => onSeek(Math.max(0, step - 1))}
            title={copy.prevStep}
            aria-label={copy.prevStep}
          >
            <StepBackIcon size={15} />
          </button>
          <button
            type="button"
            className="t-btn t-play"
            onClick={onTogglePlay}
            title={playing ? copy.pause : copy.play}
            aria-label={playing ? copy.pause : copy.play}
          >
            {playing ? <PauseIcon size={16} /> : <PlayIcon size={16} />}
          </button>
          <button
            type="button"
            className="t-btn"
            onClick={() => onSeek(Math.min(maxStep, step + 1))}
            title={copy.nextStep}
            aria-label={copy.nextStep}
          >
            <StepForwardIcon size={15} />
          </button>
        </div>

        <input
          className="step-slider"
          type="range"
          min="0"
          max={maxStep}
          value={step}
          style={{ ['--progress' as string]: `${progress}%` }}
          onChange={(event) => onSeek(Number(event.target.value))}
          aria-label="Schedule cursor"
        />

        <span className="step-readout">
          {step} / {maxStep}
        </span>
      </div>
    </div>
  )
}
