import { useEffect, useMemo, useState } from 'react'
import { FigureCard } from '../viz/FigureCard'
import { Transport } from '../Transport'
import { PORTFOLIO, PORTFOLIO_DENOM } from '../../data/portfolio'
import type { ResultsCopy } from '../../lib/i18n'

const TICK_MS = 950
const W = 760
const H = 260
const PAD = { l: 44, r: 20, t: 20, b: 40 }
const PLOT_W = W - PAD.l - PAD.r
const PLOT_H = H - PAD.t - PAD.b
const BASE_Y = PAD.t + PLOT_H
const N = PORTFOLIO.length

const xOf = (i: number) => PAD.l + (N === 1 ? 0 : (i / (N - 1)) * PLOT_W)
const yOf = (wins: number) => PAD.t + (1 - wins / PORTFOLIO_DENOM) * PLOT_H

export function PortfolioTrajectory({ copy }: { copy: ResultsCopy['portfolio'] }) {
  const prefersReducedMotion = useMemo(
    () => window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false,
    [],
  )
  const maxStep = N - 1
  const [step, setStep] = useState(maxStep)
  const [playing, setPlaying] = useState(false)

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
    setPlaying(!prefersReducedMotion)
  }

  const current = PORTFOLIO[step]
  const shown = PORTFOLIO.slice(0, step + 1)
  const linePath = shown.map((p, i) => `${i === 0 ? 'M' : 'L'} ${xOf(i).toFixed(1)} ${yOf(p.wins).toFixed(1)}`).join(' ')

  return (
    <FigureCard kicker={copy.kicker} title={copy.title} caption={copy.caption}>
      <div className="pf">
        <div className="pf-readout">
          <div className="pf-big">
            <span className="pf-big-value">{current.wins}<span className="pf-big-denom"> / {PORTFOLIO_DENOM}</span></span>
            <span className="pf-big-label">{copy.wins}</span>
          </div>
          <div className="pf-iter">
            <span className="pf-iter-name">{current.iter}</span>
            <span className="pf-iter-desc">{current.desc}</span>
            <span className="pf-iter-wl">
              {current.wins} {copy.wins} · {current.losses} {copy.losses}
            </span>
          </div>
        </div>

        <svg className="pf-svg" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={copy.title}>
          {[0, 6, 12, 18].map((g) => (
            <g key={g}>
              <line className="pf-grid" x1={PAD.l} y1={yOf(g)} x2={PAD.l + PLOT_W} y2={yOf(g)} />
              <text className="pf-tick" x={PAD.l - 8} y={yOf(g) + 4} textAnchor="end">{g}</text>
            </g>
          ))}

          <path className="pf-line" d={linePath} />

          {PORTFOLIO.map((p, i) => {
            const active = i <= step
            return (
              <g key={p.iter} className={active ? 'pf-pt-on' : 'pf-pt-off'}>
                <circle className="pf-dot" cx={xOf(i)} cy={yOf(p.wins)} r={i === step ? 6 : 4} />
                {active && (
                  <text className="pf-dot-label" x={xOf(i)} y={yOf(p.wins) - 12} textAnchor="middle">
                    {p.wins}
                  </text>
                )}
                <text className="pf-x" x={xOf(i)} y={BASE_Y + 20} textAnchor="middle">
                  {p.iter.replace('iter', '')}
                </text>
              </g>
            )
          })}
        </svg>

        <Transport
          step={step}
          maxStep={maxStep}
          playing={playing}
          copy={copy.controls}
          onSeek={seek}
          onTogglePlay={togglePlay}
          onRestart={restart}
          sliderLabel={copy.iterLabel}
        />
      </div>
    </FigureCard>
  )
}
