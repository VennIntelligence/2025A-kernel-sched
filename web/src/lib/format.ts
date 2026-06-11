export const fmt = (n: number) => n.toLocaleString('en-US')

export const pct = (x: number, digits = 1) => `${(x * 100).toFixed(digits)}%`

/** Compact ratio like "8.5×" / "10×". */
export function ratio(x: number, digits = 1): string {
  const r = Number.isFinite(x) ? x : 0
  const s = r >= 10 ? Math.round(r).toString() : r.toFixed(digits)
  return `${s}×`
}

/** Signed percentage delta of `a` relative to `b`. */
export function deltaPct(a: number, b: number, digits = 1): string {
  if (b === 0) return a === 0 ? '0%' : '—'
  const d = ((a - b) / b) * 100
  const sign = d > 0 ? '+' : ''
  return `${sign}${d.toFixed(digits)}%`
}
