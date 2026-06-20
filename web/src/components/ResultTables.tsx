import { MAIN_RESULTS, BENCHMARK, RUNTIME } from '../data/paperTables'
import type { Copy } from '../lib/i18n'

const group = (n: number) => n.toLocaleString('en-US')

/** P2 spill traffic — bold the (possibly tied) minimum in each row. */
export function MainResultsTable({ copy }: { copy: Copy['results'] }) {
  const c = copy.mainCols
  return (
    <div className="table-scroll">
      <table className="data-table results-table">
        <thead>
          <tr>
            <th scope="col" className="ta-left">{c.instance}</th>
            <th scope="col">{c.cpList}</th>
            <th scope="col">{c.pressure}</th>
            <th scope="col">{c.gHsu}</th>
            <th scope="col">{c.cpFree}</th>
            <th scope="col" className="col-ours">{c.ours}</th>
          </tr>
        </thead>
        <tbody>
          {MAIN_RESULTS.map((r) => {
            const min = Math.min(r.cpList, r.pressure, r.gHsu, r.cpFree, r.ours)
            const cell = (v: number, ours = false) => (
              <td className={`${v === min ? 'is-best' : ''} ${ours ? 'col-ours' : ''}`.trim()}>{group(v)}</td>
            )
            return (
              <tr key={r.instance}>
                <th scope="row" className="ta-left">{r.instance}</th>
                {cell(r.cpList)}
                {cell(r.pressure)}
                {cell(r.gHsu)}
                {cell(r.cpFree)}
                {cell(r.ours, true)}
              </tr>
            )
          })}
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
          {BENCHMARK.map((r) => (
            <tr key={r.instance}>
              <th scope="row" className="ta-left">{r.instance}</th>
              <td className="ta-left">{r.opType}</td>
              <td>{group(r.nodes)}</td>
              <td>{group(r.edges)}</td>
              <td>{group(r.buffers)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function RuntimeTable({ copy }: { copy: Copy['results'] }) {
  const c = copy.runtimeCols
  return (
    <div className="table-scroll">
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col" className="ta-left">{c.instance}</th>
            <th scope="col">{c.p1}</th>
            <th scope="col">{c.p2}</th>
            <th scope="col">{c.p3}</th>
          </tr>
        </thead>
        <tbody>
          {RUNTIME.map((r) => (
            <tr key={r.instance}>
              <th scope="row" className="ta-left">{r.instance}</th>
              <td>{r.p1.toFixed(3)}</td>
              <td>{r.p2.toFixed(3)}</td>
              <td>{r.p3.toFixed(3)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
