import { P2_RESULTS, P3_RESULTS } from '../data/paperTables'
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
