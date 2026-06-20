import { useEffect, useState } from 'react'
import { BrandGlyph } from './icons'
import type { Copy, Language } from '../lib/i18n'

type NavCopy = Copy['nav']

const SECTIONS: Array<{ id: string; key: keyof Omit<NavCopy, 'brand'> }> = [
  { id: 'overview', key: 'overview' },
  { id: 'problem', key: 'problem' },
  { id: 'method', key: 'method' },
  { id: 'results', key: 'results' },
]

/** Smoothly scroll to a section, accounting for the sticky bar height. */
function scrollToId(id: string) {
  const el = document.getElementById(id)
  if (!el) return
  const top = el.getBoundingClientRect().top + window.scrollY - 64
  window.scrollTo({ top, behavior: 'smooth' })
}

export function TopNav({
  copy,
  language,
  onToggleLanguage,
}: {
  copy: NavCopy
  language: Language
  onToggleLanguage: () => void
}) {
  const [active, setActive] = useState('overview')

  useEffect(() => {
    const targets = SECTIONS.map((s) => document.getElementById(s.id)).filter(
      (el): el is HTMLElement => el != null,
    )
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)
        if (visible[0]) setActive(visible[0].target.id)
      },
      { rootMargin: '-45% 0px -45% 0px', threshold: [0, 0.25, 0.5, 1] },
    )
    targets.forEach((el) => observer.observe(el))
    return () => observer.disconnect()
  }, [])

  return (
    <nav className="topbar" aria-label="Site navigation">
      <div className="topbar-inner">
        <button
          className="brand"
          type="button"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        >
          <BrandGlyph size={18} />
          <span className="brand-name">{copy.brand}</span>
        </button>

        <div className="nav-links">
          {SECTIONS.map((s) => (
            <button
              key={s.id}
              type="button"
              className={active === s.id ? 'is-active' : ''}
              onClick={() => scrollToId(s.id)}
            >
              {copy[s.key]}
            </button>
          ))}
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
