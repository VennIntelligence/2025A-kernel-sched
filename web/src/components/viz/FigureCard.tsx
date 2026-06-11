import type { ReactNode } from 'react'

/** Shared figure shell matching the problem-page figure-card layout. */
export function FigureCard({
  kicker,
  title,
  action,
  caption,
  note,
  children,
}: {
  kicker: string
  title: string
  action?: ReactNode
  caption?: ReactNode
  note?: ReactNode
  children: ReactNode
}) {
  return (
    <section className="figure-card">
      <div className="figure-head">
        <div className="figure-head-text">
          <p className="figure-kicker">{kicker}</p>
          <h2>{title}</h2>
        </div>
        {action}
      </div>

      {children}

      {note && <p className="figure-note">{note}</p>}
      {caption && <p className="figure-caption">{caption}</p>}
    </section>
  )
}
