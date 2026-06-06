import { useState } from 'react'
import { TopNav } from './components/TopNav'
import { HomePage } from './pages/HomePage'
import { ProblemPage } from './pages/ProblemPage'
import { copy, type Language, type PageId } from './lib/i18n'
import './App.css'

function App() {
  const [language, setLanguage] = useState<Language>('zh')
  const [page, setPage] = useState<PageId>('home')
  const t = copy[language]

  return (
    <main className="app-shell">
      <TopNav
        copy={t.nav}
        page={page}
        onNavigate={setPage}
        onToggleLanguage={() => setLanguage(language === 'zh' ? 'en' : 'zh')}
      />
      {page === 'home' ? (
        <HomePage copy={t.home} onOpenProblem={() => setPage('problem')} />
      ) : (
        <ProblemPage copy={t.problem} />
      )}
    </main>
  )
}

export default App
