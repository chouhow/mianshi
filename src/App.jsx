import { useEffect } from 'react'
import { Link, useRoute } from './ui.jsx'
import Questions from './pages/Questions.jsx'
import Papers from './pages/Papers.jsx'
import PaperDetail from './pages/PaperDetail.jsx'
import InterviewSetup from './pages/InterviewSetup.jsx'
import InterviewRun from './pages/InterviewRun.jsx'
import InterviewReport from './pages/InterviewReport.jsx'
import Records from './pages/Records.jsx'
import Settings from './pages/Settings.jsx'

const NAV = [
  { to: '/questions', icon: '📚', text: '题库管理' },
  { to: '/papers', icon: '📄', text: '试卷管理' },
  { to: '/records', icon: '🗂️', text: '面试记录' },
  { to: '/settings', icon: '⚙️', text: '系统设置' },
]

function Switch({ route }) {
  const [seg0, seg1, seg2] = route.parts
  switch (seg0) {
    case 'questions':
      return <Questions />
    case 'papers':
      return seg1 ? <PaperDetail paperId={seg1} /> : <Papers />
    case 'records':
      return <Records />
    case 'settings':
      return <Settings />
    case 'interview':
      if (seg1 === 'new') return <InterviewSetup paperId={route.query.paper} />
      if (seg1 === 'run') return <InterviewRun interviewId={seg2} />
      if (seg1 === 'report') return <InterviewReport interviewId={seg2} />
      return null
    default:
      return <Questions />
  }
}

export default function App() {
  const route = useRoute()
  const active = '/' + (route.parts[0] || 'questions')

  // 阻止把文件拖到非拖放区时浏览器/Electron 直接打开文件导致页面被替换
  useEffect(() => {
    const prevent = (e) => e.preventDefault()
    document.addEventListener('dragover', prevent)
    document.addEventListener('drop', prevent)
    return () => {
      document.removeEventListener('dragover', prevent)
      document.removeEventListener('drop', prevent)
    }
  }, [])
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <span className="icon">🎤</span> 技术面试系统
        </div>
        {NAV.map((n) => (
          <Link key={n.to} to={n.to} className={'nav-item' + (active === n.to ? ' active' : '')}>
            <span>{n.icon}</span> {n.text}
          </Link>
        ))}
        <div className="footer">本地存储 · 火山引擎 ASR / 方舟</div>
      </aside>
      <main className="content">
        <div className="page">
          <Switch route={route} />
        </div>
      </main>
    </div>
  )
}
