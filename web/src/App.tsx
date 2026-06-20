import { useEffect, useState } from 'react'
import { TopNav } from './components/TopNav'
import { Hero } from './sections/Hero'
import { Overview } from './sections/Overview'
import { Problem } from './sections/Problem'
import { Model } from './sections/Model'
import { Method } from './sections/Method'
import { Theory } from './sections/Theory'
import { Results } from './sections/Results'
import { Closing, SiteFooter } from './sections/Closing'
import { copy, type Language } from './lib/i18n'
import './App.css'

const LANG_KEY = 'ks-lang'

function readLang(): Language {
  const stored = typeof localStorage !== 'undefined' ? localStorage.getItem(LANG_KEY) : null
  return stored === 'en' || stored === 'zh' ? stored : 'zh'
}

function App() {
  const [language, setLanguage] = useState<Language>(readLang)
  const t = copy[language]

  useEffect(() => {
    document.documentElement.lang = language
    document.title = t.meta.title
    try {
      localStorage.setItem(LANG_KEY, language)
    } catch {
      /* storage unavailable — ignore */
    }
  }, [language, t.meta.title])

  return (
    <div className="app-shell">
      <TopNav
        copy={t.nav}
        language={language}
        onToggleLanguage={() => setLanguage(language === 'zh' ? 'en' : 'zh')}
      />
      <main className="paper">
        <Hero copy={t} />
        <Overview copy={t} />
        <Problem copy={t.problem} />
        <Model copy={t.model} />
        <Method copy={t.method} />
        <Theory copy={t.theory} />
        <Results copy={t.results} />
        <Closing copy={t} />
      </main>
      <SiteFooter copy={t} />
    </div>
  )
}

export default App
