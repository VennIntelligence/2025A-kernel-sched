import { BrandGlyph } from './icons'
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
      <div className="topbar-inner">
        <button className="brand" type="button" onClick={() => onNavigate('home')}>
          <BrandGlyph size={19} />
          <span className="brand-name">{copy.brand}</span>
        </button>

        <div className="nav-links" role="tablist">
          <button
            type="button"
            className={page === 'home' ? 'is-active' : ''}
            aria-current={page === 'home' ? 'page' : undefined}
            onClick={() => onNavigate('home')}
          >
            {copy.home}
          </button>
          <button
            type="button"
            className={page === 'problem' ? 'is-active' : ''}
            aria-current={page === 'problem' ? 'page' : undefined}
            onClick={() => onNavigate('problem')}
          >
            {copy.problem}
          </button>
        </div>

        <button
          className={`language-switch lang-${language}`}
          type="button"
          onClick={onToggleLanguage}
          aria-label="Toggle language"
        >
          <span className="switch-thumb" aria-hidden="true" />
          <span className={language === 'zh' ? 'is-on' : ''}>中</span>
          <span className={language === 'en' ? 'is-on' : ''}>EN</span>
        </button>
      </div>
    </nav>
  )
}
