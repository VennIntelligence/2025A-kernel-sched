import { Transport, type TransportCopy } from '../Transport'
import { stages, type StageId } from './problemData'

export type ControlsCopy = TransportCopy

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

      <Transport
        step={step}
        maxStep={maxStep}
        playing={playing}
        copy={copy}
        onSeek={onSeek}
        onTogglePlay={onTogglePlay}
        onRestart={onRestart}
        sliderLabel="Schedule cursor"
      />
    </div>
  )
}
