import { useSearchParams } from 'react-router-dom'
import { FigureCard } from '../viz/FigureCard'
import { CASES, FAMILY_COLOR, HEADLINE, HEADLINE_STATS, type HeadlineRow, type ProblemId } from '../../data/headline'
import { deltaPct, fmt } from '../../lib/format'
import type { ResultsCopy } from '../../lib/i18n'

const CASE_LABEL: Record<string, string> = {
  Conv_Case0: 'Conv_Case0',
  Conv_Case1: 'Conv_Case1',
  FlashAttention_Case0: 'FlashAttention_Case0',
  FlashAttention_Case1: 'FlashAttention_Case1',
  Matmul_Case0: 'Matmul_Case0',
  Matmul_Case1: 'Matmul_Case1',
}

const PROBLEMS: ProblemId[] = [1, 2, 3]

function rowFor(caseId: string, problem: ProblemId): HeadlineRow {
  return HEADLINE.find((r) => r.case === caseId && r.problem === problem)!
}

/** Primary metric per subproblem (all lower-is-better). */
function metric(row: HeadlineRow): { label: string; ours: number; base: number } {
  if (row.problem === 1) return { label: 'max_L1', ours: row.ours.maxL1, base: row.base.maxL1 }
  if (row.problem === 2) return { label: 'extra', ours: row.ours.extra, base: row.base.extra }
  return { label: 'time', ours: row.ours.time, base: row.base.time }
}

function CompareBar({ label, ours, base, win }: { label: string; ours: number; base: number; win: boolean }) {
  const max = Math.max(ours, base, 1)
  return (
    <div className="cmp-metric">
      <div className="cmp-metric-head">
        <span className="cmp-metric-name">{label}</span>
        <span className={`cmp-delta ${win ? 'is-win' : 'is-loss'}`}>{deltaPct(ours, base)}</span>
      </div>
      <div className="cmp-bar">
        <span className="cmp-bar-tag">ours</span>
        <span className="cmp-track">
          <span className={`cmp-fill ${win ? 'is-win' : 'is-loss'}`} style={{ width: `${(ours / max) * 100}%` }} />
        </span>
        <span className="cmp-num">{fmt(ours)}</span>
      </div>
      <div className="cmp-bar">
        <span className="cmp-bar-tag">base</span>
        <span className="cmp-track">
          <span className="cmp-fill is-base" style={{ width: `${(base / max) * 100}%` }} />
        </span>
        <span className="cmp-num">{fmt(base)}</span>
      </div>
    </div>
  )
}

export function WinLossWall({ copy }: { copy: ResultsCopy['wall'] }) {
  const [params, setParams] = useSearchParams()
  const paramCase = params.get('case')
  const selected = paramCase && CASES.includes(paramCase) ? paramCase : CASES[0]

  const select = (caseId: string) => {
    const next = new URLSearchParams(params)
    next.set('case', caseId)
    setParams(next, { replace: true })
  }

  return (
    <FigureCard
      kicker={copy.kicker}
      title={copy.title}
      caption={copy.caption}
      action={
        <div className="wall-legend">
          <span className="lg-win">{copy.legendWin}</span>
          <span className="lg-loss">{copy.legendLoss}</span>
        </div>
      }
    >
      <div className="wall">
        <div className="wall-grid" role="grid" aria-label={copy.title}>
          <div className="wall-line wall-headrow" role="row">
            <span className="wall-corner" role="columnheader" />
            {PROBLEMS.map((p) => (
              <span key={p} className="wall-colhead" role="columnheader">
                P{p}
              </span>
            ))}
          </div>

          {CASES.map((caseId) => (
            <div className="wall-line" role="row" key={caseId}>
              <button
                type="button"
                className={`wall-rowhead${caseId === selected ? ' is-active' : ''}`}
                onClick={() => select(caseId)}
              >
                <span className="wall-dot" style={{ background: FAMILY_COLOR[rowFor(caseId, 1).family] }} />
                {CASE_LABEL[caseId]}
              </button>
              {PROBLEMS.map((p) => {
                const row = rowFor(caseId, p)
                const win = row.result === 'WIN'
                return (
                  <button
                    key={p}
                    type="button"
                    role="gridcell"
                    aria-selected={caseId === selected}
                    className={`wall-cell ${win ? 'is-win' : 'is-loss'}${caseId === selected ? ' is-active' : ''}`}
                    onClick={() => select(caseId)}
                    title={`${caseId} · P${p} · ${row.result}`}
                  >
                    {win ? 'W' : 'L'}
                  </button>
                )
              })}
            </div>
          ))}
        </div>

        <div className="wall-stats">
          <span><strong>{HEADLINE_STATS.wins}</strong> {copy.legendWin}</span>
          <span><strong>{HEADLINE_STATS.losses}</strong> {copy.legendLoss}</span>
          <span><strong>{HEADLINE_STATS.valid}/{HEADLINE_STATS.total}</strong> valid</span>
        </div>

        <div className="wall-detail">
          <p className="wall-detail-head">
            <span className="wall-detail-name">{selected}</span>
            <span className="wall-detail-hint">{copy.pickHint}</span>
          </p>
          <div className="cmp-grid">
            {PROBLEMS.map((p) => {
              const row = rowFor(selected, p)
              const m = metric(row)
              const colLabel = p === 1 ? copy.metricPeak : p === 2 ? copy.metricExtra : copy.metricTime
              return <CompareBar key={p} label={colLabel} ours={m.ours} base={m.base} win={row.result === 'WIN'} />
            })}
          </div>
        </div>
      </div>
    </FigureCard>
  )
}
