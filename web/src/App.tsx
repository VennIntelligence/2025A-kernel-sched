import { useEffect, useState } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { TopNav } from './components/TopNav'
import { HomePage } from './pages/HomePage'
import { ProblemPage } from './pages/ProblemPage'
import { MethodPage } from './pages/MethodPage'
import { ResultsPage } from './pages/ResultsPage'
import { copy, type Language } from './lib/i18n'
import './App.css'

const LANG_KEY = 'ks-lang'

function readLang(): Language {
  const stored = typeof localStorage !== 'undefined' ? localStorage.getItem(LANG_KEY) : null
  return stored === 'en' || stored === 'zh' ? stored : 'zh'
}

/** Reset scroll on route change so deep links open at the top. */
function ScrollReset() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

function App() {
  const [language, setLanguage] = useState<Language>(readLang)
  const t = copy[language]

  useEffect(() => {
    document.documentElement.lang = language
    try {
      localStorage.setItem(LANG_KEY, language)
    } catch {
      /* storage unavailable — ignore */
    }
  }, [language])

  return (
    <main className="app-shell">
      <ScrollReset />
      <TopNav
        copy={t.nav}
        language={language}
        onToggleLanguage={() => setLanguage(language === 'zh' ? 'en' : 'zh')}
      />
      <Routes>
        <Route path="/" element={<HomePage copy={t.home} />} />
        <Route path="/problem" element={<ProblemPage copy={t.problem} />} />
        <Route path="/method" element={<MethodPage copy={t.method} />} />
        <Route path="/results" element={<ResultsPage copy={t.results} />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </main>
  )
}

export default App
