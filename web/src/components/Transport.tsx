import { PauseIcon, PlayIcon, RestartIcon, StepBackIcon, StepForwardIcon } from './icons'

export type TransportCopy = {
  play: string
  pause: string
  restart: string
  prevStep: string
  nextStep: string
}

/**
 * Shared play / step / scrub control. Reused by the problem-page stage figure
 * and the results-page portfolio trajectory so both share one interaction model.
 */
export function Transport({
  step,
  maxStep,
  playing,
  copy,
  onSeek,
  onTogglePlay,
  onRestart,
  sliderLabel = 'Cursor',
}: {
  step: number
  maxStep: number
  playing: boolean
  copy: TransportCopy
  onSeek: (step: number) => void
  onTogglePlay: () => void
  onRestart: () => void
  sliderLabel?: string
}) {
  const progress = maxStep > 0 ? (step / maxStep) * 100 : 0

  return (
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
        aria-label={sliderLabel}
      />

      <span className="step-readout">
        {step} / {maxStep}
      </span>
    </div>
  )
}
