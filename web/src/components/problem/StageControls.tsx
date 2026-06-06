import { schedule, stages, type StageId } from './problemData'

export function StageControls({
  stage,
  step,
  cursorLabel,
  onStageChange,
  onStepChange,
}: {
  stage: StageId
  step: number
  cursorLabel: string
  onStageChange: (stage: StageId) => void
  onStepChange: (step: number) => void
}) {
  return (
    <div className="controls">
      <div className="stage-tabs" role="tablist" aria-label="Animation stages">
        {stages.map((item) => (
          <button
            key={item.id}
            className={item.id === stage ? 'active' : ''}
            type="button"
            role="tab"
            aria-selected={item.id === stage}
            onClick={() => onStageChange(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>
      <label className="step-control">
        <span>{cursorLabel}</span>
        <input
          type="range"
          min="0"
          max={schedule.length - 1}
          value={step}
          onChange={(event) => onStepChange(Number(event.target.value))}
        />
      </label>
    </div>
  )
}
