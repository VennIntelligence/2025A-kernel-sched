import { BENCHMARK, P2_RESULTS, P3_RESULTS, RESEARCH_EVIDENCE } from '../data/paperTables'
import type { Copy } from '../lib/i18n'

const group = (n: number) => n.toLocaleString('en-US')

export function P2ResultsTable({ copy }: { copy: Copy['results'] }) {
  const c = copy.mainCols
  return (
    <div className="table-scroll">
      <table className="data-table results-table">
        <thead>
          <tr>
            <th scope="col" className="ta-left">{c.instance}</th>
            <th scope="col">{c.official}</th>
            <th scope="col" className="col-ours">{c.scalable}</th>
            <th scope="col">{c.outcome}</th>
          </tr>
        </thead>
        <tbody>
          {P2_RESULTS.map((row) => (
            <tr key={row.instance}>
              <th scope="row" className="ta-left">{row.instance}</th>
              <td>{group(row.official)}</td>
              <td className={`col-ours ${row.outcome === 'win' ? 'is-best' : ''}`.trim()}>{group(row.scalable)}</td>
              <td className={row.outcome === 'win' ? 'status-win' : 'status-tie'}>
                {row.outcome === 'win' ? copy.win : copy.tie}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function ResearchEvidenceTable({ copy }: { copy: Copy['results'] }) {
  const c = copy.evidenceCols
  return (
    <div className="table-scroll">
      <table className="data-table evidence-table">
        <thead>
          <tr>
            <th scope="col" className="ta-left">{c.instance}</th>
            <th scope="col">{c.repair}</th>
            <th scope="col">{c.exact}</th>
            <th scope="col" className="ta-left">{c.status}</th>
          </tr>
        </thead>
        <tbody>
          {RESEARCH_EVIDENCE.map((row) => (
            <tr key={row.instance}>
              <th scope="row" className="ta-left">{row.instance}</th>
              <td>{row.repair === 'probe' ? copy.evidenceStatus.probe : row.repair === null ? '—' : group(row.repair)}</td>
              <td>{row.exact === null ? '—' : group(row.exact)}</td>
              <td className="ta-left">{copy.evidenceStatus[row.status]}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function P3ResultsTable({ copy }: { copy: Copy['results'] }) {
  const c = copy.p3Cols
  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col" className="ta-left">{c.instance}</th>
            <th scope="col">{c.official}</th>
            <th scope="col">{c.scalable}</th>
            <th scope="col">{c.outcome}</th>
          </tr>
        </thead>
        <tbody>
          {P3_RESULTS.map((row) => (
            <tr key={row.instance}>
              <th scope="row" className="ta-left">{row.instance}</th>
              <td>{group(row.official)}</td>
              <td className={row.outcome === 'win' ? 'is-best' : ''}>{group(row.scalable)}</td>
              <td className={row.outcome === 'win' ? 'status-win' : 'status-loss'}>
                {row.outcome === 'win' ? copy.win : copy.loss}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function BenchmarkTable({ copy }: { copy: Copy['results'] }) {
  const c = copy.benchCols
  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col" className="ta-left">{c.instance}</th>
            <th scope="col" className="ta-left">{c.opType}</th>
            <th scope="col">{c.nodes}</th>
            <th scope="col">{c.edges}</th>
            <th scope="col">{c.buffers}</th>
          </tr>
        </thead>
        <tbody>
          {BENCHMARK.map((row) => (
            <tr key={row.instance}>
              <th scope="row" className="ta-left">{row.instance}</th>
              <td className="ta-left">{row.opType}</td>
              <td>{group(row.nodes)}</td>
              <td>{group(row.edges)}</td>
              <td>{group(row.buffers)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
