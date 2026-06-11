import { WinLossWall } from '../components/results/WinLossWall'
import { PortfolioTrajectory } from '../components/results/PortfolioTrajectory'
import { WorkingSetBound } from '../components/results/WorkingSetBound'
import type { Copy } from '../lib/i18n'

export function ResultsPage({ copy }: { copy: Copy['results'] }) {
  return (
    <div className="problem-view">
      <header className="page-hero">
        <p className="eyebrow">{copy.eyebrow}</p>
        <h1>{copy.title}</h1>
        <p className="hero-lead">{copy.lead}</p>
      </header>

      <WinLossWall copy={copy.wall} />
      <PortfolioTrajectory copy={copy.portfolio} />
      <WorkingSetBound copy={copy.workingSet} />
    </div>
  )
}
