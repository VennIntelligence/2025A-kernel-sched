import type { Language, PageId } from '../lib/i18n'

type TopNavCopy = {
  brand: string
  home: string
  problem: string
}

export function TopNav({
  copy,
  language,
  page,
  onNavigate,
  onToggleLanguage,
}: {
  copy: TopNavCopy
  language: Language
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
        <div className="nav-end">
          <button
            className={`language-switch ${language === 'en' ? 'en' : 'zh'}`}
            type="button"
            onClick={onToggleLanguage}
            aria-label="Toggle language"
          >
            <div className="switch-thumb" />
            <span>中</span>
            <span>EN</span>
          </button>
        </div>
      </div>
    </nav>
  )
}
