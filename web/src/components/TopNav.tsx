import type { PageId } from '../lib/i18n'

type TopNavCopy = {
  brand: string
  home: string
  problem: string
  language: string
}

export function TopNav({
  copy,
  page,
  onNavigate,
  onToggleLanguage,
}: {
  copy: TopNavCopy
  page: PageId
  onNavigate: (page: PageId) => void
  onToggleLanguage: () => void
}) {
  return (
    <nav className="topbar" aria-label="Site navigation">
      <button className="brand" type="button" onClick={() => onNavigate('home')}>
        {copy.brand}
      </button>
      <div className="nav-actions">
        <div className="nav-links">
          <button className={page === 'home' ? 'active' : ''} type="button" onClick={() => onNavigate('home')}>
            {copy.home}
          </button>
          <button
            className={page === 'problem' ? 'active' : ''}
            type="button"
            onClick={() => onNavigate('problem')}
          >
            {copy.problem}
          </button>
        </div>
        <button className="language-toggle" type="button" onClick={onToggleLanguage}>
          {copy.language}
        </button>
      </div>
    </nav>
  )
}
