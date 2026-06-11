import { Link, NavLink } from 'react-router-dom'
import { BrandGlyph } from './icons'
import type { Language } from '../lib/i18n'

type TopNavCopy = {
  brand: string
  home: string
  problem: string
  method: string
  results: string
}

const navClass = ({ isActive }: { isActive: boolean }) => (isActive ? 'is-active' : '')

export function TopNav({
  copy,
  language,
  onToggleLanguage,
}: {
  copy: TopNavCopy
  language: Language
  onToggleLanguage: () => void
}) {
  return (
    <nav className="topbar" aria-label="Site navigation">
      <div className="topbar-inner">
        <Link className="brand" to="/">
          <BrandGlyph size={19} />
          <span className="brand-name">{copy.brand}</span>
        </Link>

        <div className="nav-links">
          <NavLink to="/" end className={navClass}>
            {copy.home}
          </NavLink>
          <NavLink to="/problem" className={navClass}>
            {copy.problem}
          </NavLink>
          <NavLink to="/method" className={navClass}>
            {copy.method}
          </NavLink>
          <NavLink to="/results" className={navClass}>
            {copy.results}
          </NavLink>
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
