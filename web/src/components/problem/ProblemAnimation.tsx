import { DagStage } from './stages/DagStage'
import { MemoryStage } from './stages/MemoryStage'
import { PipelineStage } from './stages/PipelineStage'
import { ScheduleStage } from './stages/ScheduleStage'
import { ScheduleStrip } from './ScheduleStrip'
import {
  BUFFERS,
  MEM_FAIL_STEP,
  TIMELINE,
  VSTAY_17,
  stageMaxStep,
  stageNodes,
  type SchedNode,
  type StageId,
} from './problemData'

function nodeName(node: SchedNode): string {
  if (node.kind === 'cache') {
    const sign = node.delta > 0 ? '+' : ''
    return `${node.op} ${node.buf} (${sign}${node.delta})`
  }
  return `${node.op} ${node.tag}`
}

function rangeOf(buf: NonNullable<SchedNode['buf']>, reload = false): string {
  const info = BUFFERS[buf]
  const offset = reload && info.reloadOffset !== undefined ? info.reloadOffset : info.offset
  return `[${offset}, ${offset + info.size})`
}

function statusText(stage: StageId, step: number): string {
  const nodes = stageNodes(stage)
  if (step === 0) return 'ready'
  const node = nodes[step - 1]

  switch (stage) {
    case 'dag':
      return node.kind === 'op'
        ? `${nodeName(node)} @ ${node.pipe} · ${node.cycles}c`
        : nodeName(node)

    case 'schedule': {
      const peak = Math.max(...VSTAY_17.slice(0, step + 1))
      return `${nodeName(node)} · V_stay = ${VSTAY_17[step]} · peak = ${peak}`
    }

    case 'memory': {
      if (step >= MEM_FAIL_STEP) {
        return 'ALLOC b3 (640): max contiguous free = 512 < 640 → must spill'
      }
      if (node.op === 'ALLOC') return `place ${node.buf} @ ${rangeOf(node.buf!)}`
      if (node.op === 'FREE') return `release ${node.buf} ${rangeOf(node.buf!)}`
      return `${nodeName(node)} · residency unchanged`
    }

    case 'spill': {
      if (node.op === 'SPILL_OUT') return 'SPILL_OUT b0 → DDR · 0 cycles (COPY_IN origin)'
      if (node.op === 'SPILL_IN') return `SPILL_IN b0 @ ${rangeOf('b0', true)} · +128 DDR traffic`
      if (node.op === 'ALLOC' && node.buf === 'b3') return 'place b3 @ [0, 640) — fits after spill'
      if (node.op === 'ALLOC') return `place ${node.buf} @ ${rangeOf(node.buf!)}`
      if (node.op === 'FREE') return `release ${node.buf} ${rangeOf(node.buf!, node.buf === 'b0')}`
      return `${nodeName(node)} · residency unchanged`
    }

    case 'pipeline': {
      const timing = TIMELINE.timing.get(node.id)!
      const base =
        node.kind === 'cache'
          ? `${nodeName(node)} · 0-cycle event · E = ${timing.end}`
          : `${nodeName(node)} @ ${node.pipe} · S ${timing.start} → E ${timing.end}`
      return step === nodes.length ? `${base} · T = ${TIMELINE.makespan}` : base
    }
  }
}

export function ProblemAnimation({
  stage,
  step,
  legend,
  onSeek,
}: {
  stage: StageId
  step: number
  legend: { cache: string; op: string; spill: string }
  onSeek: (step: number) => void
}) {
  const nodes = stageNodes(stage)
  const maxStep = stageMaxStep(stage)
  const showSpillLegend = stage === 'spill' || stage === 'pipeline'

  return (
    <div className="problem-animation">
      <ScheduleStrip nodes={nodes} step={step} maxStep={maxStep} onSeek={onSeek} />

      <div className="stage-canvas" key={stage}>
        {stage === 'dag' && <DagStage step={step} />}
        {stage === 'schedule' && <ScheduleStage step={step} />}
        {stage === 'memory' && <MemoryStage step={step} mode="plain" />}
        {stage === 'spill' && <MemoryStage step={step} mode="spill" />}
        {stage === 'pipeline' && <PipelineStage step={step} />}
      </div>

      <div className="figure-footer">
        <p className="figure-status">
          <span className="status-step">
            {step}/{maxStep}
          </span>
          {statusText(stage, step)}
        </p>
        <ul className="figure-legend" aria-hidden="true">
          <li className="legend-cache">{legend.cache}</li>
          <li className="legend-op">{legend.op}</li>
          {showSpillLegend && <li className="legend-spill">{legend.spill}</li>}
        </ul>
      </div>
    </div>
  )
}
