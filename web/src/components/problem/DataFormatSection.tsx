import { useState } from 'react'
import type { DataSectionCopy } from '../../lib/i18n'

/* Language-neutral facts (numbers / identifiers identical across languages). */

type BenchRow = {
  task: string
  nodes: number
  edges: number
  bufs: number
  ops: number
  family: 'matmul' | 'fa' | 'conv'
}

const BENCH_ROWS: BenchRow[] = [
  { task: 'Matmul_Case0', nodes: 4160, edges: 7104, bufs: 1216, ops: 1728, family: 'matmul' },
  { task: 'Matmul_Case1', nodes: 30976, edges: 55040, bufs: 8960, ops: 13056, family: 'matmul' },
  { task: 'FlashAttention_Case0', nodes: 1716, edges: 2712, bufs: 572, ops: 572, family: 'fa' },
  { task: 'FlashAttention_Case1', nodes: 6952, edges: 11184, bufs: 2328, ops: 2296, family: 'fa' },
  { task: 'Conv_Case0', nodes: 2580, edges: 3869, bufs: 831, ops: 918, family: 'conv' },
  { task: 'Conv_Case1', nodes: 36086, edges: 85653, bufs: 12013, ops: 12060, family: 'conv' },
]

const FAMILY_COLOR: Record<BenchRow['family'], string> = {
  matmul: '#0072b2',
  fa: '#cc79a7',
  conv: '#e69f00',
}

const CAPACITIES = [
  { name: 'L1', cap: 4096 },
  { name: 'UB', cap: 1024 },
  { name: 'L0C', cap: 512 },
  { name: 'L0A', cap: 256 },
  { name: 'L0B', cap: 256 },
]

const ENUMS = {
  op: [
    'ALLOC', 'FREE', 'COPY_IN', 'COPY_OUT', 'COPY', 'MOVE', 'MATMUL', 'CONV',
    'CONV_ADD', 'ADD', 'SUB', 'MUL', 'MAX', 'EXP', 'REC', 'ROWMAX', 'ROWSUM',
    'COMPACT', 'D2S',
  ],
  pipe: ['MTE1', 'MTE2', 'MTE3', 'FIXP', 'CUBE', 'VECTOR'],
  type: ['L1', 'UB', 'L0A', 'L0B', 'L0C'],
}

const MAX_NODES = Math.max(...BENCH_ROWS.map((r) => r.nodes))
const MAX_CAP = Math.max(...CAPACITIES.map((c) => c.cap))

const fmt = (n: number) => n.toLocaleString('en-US')

function FieldTable({ rows }: { rows: DataSectionCopy['cacheFields'] }) {
  return (
    <dl className="field-list">
      {rows.map((row) => (
        <div key={row.name} className="field-row">
          <dt className="field-name">{row.name}</dt>
          <dd className="field-type">{row.type}</dd>
          <dd className="field-desc">{row.desc}</dd>
        </div>
      ))}
    </dl>
  )
}

export function DataFormatSection({ copy }: { copy: DataSectionCopy }) {
  const [nodeKind, setNodeKind] = useState<'cache' | 'op'>('cache')
  const fields = nodeKind === 'cache' ? copy.cacheFields : copy.opFields
  const example = nodeKind === 'cache' ? copy.cacheExample : copy.opExample

  return (
    <section className="data-section" id="data">
      <div className="data-head">
        <p className="data-eyebrow">{copy.eyebrow}</p>
        <h2>{copy.title}</h2>
        <p className="data-lead">{copy.lead}</p>
      </div>

      {/* Input / output data structures */}
      <div className="data-io">
        <article className="data-panel">
          <header className="panel-head">
            <span className="panel-dot in" aria-hidden="true" />
            <h3>{copy.inputTitle}</h3>
          </header>
          <p className="panel-lead">{copy.inputLead}</p>

          <div className="node-toggle" role="tablist" aria-label={copy.inputTitle}>
            <button
              type="button"
              role="tab"
              aria-selected={nodeKind === 'cache'}
              className={nodeKind === 'cache' ? 'is-active' : ''}
              onClick={() => setNodeKind('cache')}
            >
              {copy.nodeToggle.cache}
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={nodeKind === 'op'}
              className={nodeKind === 'op' ? 'is-active' : ''}
              onClick={() => setNodeKind('op')}
            >
              {copy.nodeToggle.op}
            </button>
          </div>

          <FieldTable rows={fields} />
          <pre className="json-example">{example}</pre>

          <div className="edges-note">
            <span className="edges-label">{copy.edgesTitle}</span>
            <code className="edges-type">{copy.edgesType}</code>
            <span className="edges-desc">{copy.edgesDesc}</span>
          </div>
        </article>

        <article className="data-panel">
          <header className="panel-head">
            <span className="panel-dot out" aria-hidden="true" />
            <h3>{copy.outputTitle}</h3>
          </header>
          <p className="panel-lead">{copy.outputLead}</p>

          <pre className="dir-tree">{`Attachment.rar
├── Problem1/  <task>_schedule.txt
├── Problem2/  schedule · memory · spill
└── Problem3/  schedule · memory · spill`}</pre>

          <ul className="file-list">
            {copy.files.map((file) => (
              <li key={file.name}>
                <code className="file-name">{file.name}</code>
                <code className="file-format">{file.format}</code>
                <span className="file-desc">{file.desc}</span>
              </li>
            ))}
          </ul>
        </article>
      </div>

      {/* Benchmark scale + hardware capacity */}
      <div className="data-metrics">
        <article className="data-panel">
          <header className="panel-head">
            <h3>{copy.benchTitle}</h3>
          </header>
          <p className="panel-lead">{copy.benchLead}</p>

          <div className="bench-table" role="table" aria-label={copy.benchTitle}>
            <div className="bench-row bench-header" role="row">
              <span role="columnheader">{copy.benchCols.task}</span>
              <span role="columnheader">{copy.benchCols.nodes}</span>
              <span role="columnheader">{copy.benchCols.edges}</span>
              <span role="columnheader">{copy.benchCols.bufs}</span>
              <span role="columnheader">{copy.benchCols.ops}</span>
            </div>
            {BENCH_ROWS.map((row) => (
              <div className="bench-row" role="row" key={row.task}>
                <span className="bench-task" role="cell">
                  <span
                    className="bench-bar"
                    style={{
                      width: `${(row.nodes / MAX_NODES) * 100}%`,
                      background: FAMILY_COLOR[row.family],
                    }}
                  />
                  <span className="bench-task-name">{row.task}</span>
                </span>
                <span className="bench-num" role="cell">{fmt(row.nodes)}</span>
                <span className="bench-num" role="cell">{fmt(row.edges)}</span>
                <span className="bench-num" role="cell">{fmt(row.bufs)}</span>
                <span className="bench-num" role="cell">{fmt(row.ops)}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="data-panel">
          <header className="panel-head">
            <h3>{copy.capTitle}</h3>
          </header>
          <p className="panel-lead">{copy.capLead}</p>

          <ul className="cap-list">
            {CAPACITIES.map((cache) => (
              <li key={cache.name} className="cap-row">
                <span className="cap-name">{cache.name}</span>
                <span className="cap-track">
                  <span className="cap-fill" style={{ width: `${(cache.cap / MAX_CAP) * 100}%` }} />
                </span>
                <span className="cap-value">{fmt(cache.cap)}</span>
              </li>
            ))}
          </ul>
        </article>
      </div>

      {/* Enums */}
      <article className="data-panel enum-panel">
        <header className="panel-head">
          <h3>{copy.enumTitle}</h3>
        </header>
        <p className="panel-lead">{copy.enumLead}</p>

        <div className="enum-groups">
          <div className="enum-group">
            <span className="enum-label">{copy.enumGroups.op}</span>
            <div className="chip-row">
              {ENUMS.op.map((v) => (
                <code key={v} className="chip">{v}</code>
              ))}
            </div>
          </div>
          <div className="enum-group">
            <span className="enum-label">{copy.enumGroups.pipe}</span>
            <div className="chip-row">
              {ENUMS.pipe.map((v) => (
                <code key={v} className="chip chip-pipe">{v}</code>
              ))}
            </div>
          </div>
          <div className="enum-group">
            <span className="enum-label">{copy.enumGroups.type}</span>
            <div className="chip-row">
              {ENUMS.type.map((v) => (
                <code key={v} className="chip chip-type">{v}</code>
              ))}
            </div>
          </div>
        </div>
      </article>
    </section>
  )
}
