import { useEffect, useState } from 'react'
import { api } from '../api.js'
import ResumeDropZone from '../components/ResumeDropZone.jsx'
import { navigate } from '../ui.jsx'

const KIND_TEXT = { bank: '随机卷', resume: '简历卷' }

export default function InterviewSetup({ paperId }) {
  const [papers, setPapers] = useState(null)
  const [selected, setSelected] = useState(paperId ? [paperId] : [])
  const [candidateName, setCandidateName] = useState('')
  const [resumeText, setResumeText] = useState('')
  const [parsedName, setParsedName] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/api/papers')
      .then((d) => setPapers(d.papers))
      .catch((e) => setError(e.message))
  }, [])

  const toggle = (id) =>
    setSelected(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id])

  // 合计题数（题库题 + 内嵌简历题）
  const totalQuestions = (papers || [])
    .filter((p) => selected.includes(p.id))
    .reduce((n, p) => n + (p.question_count || 0) + (p.resume_question_count || 0), 0)

  const start = async () => {
    if (!candidateName.trim()) {
      setError('请填写候选人姓名')
      return
    }
    if (selected.length === 0) {
      setError('请至少勾选一份试卷（随机卷 + 简历卷可同时勾选）')
      return
    }
    setBusy(true)
    setError('')
    try {
      const iv = await api.post('/api/interviews', {
        paper_ids: selected,
        candidate_name: candidateName.trim(),
        resume_text: resumeText.trim(),
      })
      navigate('/interview/run/' + iv.id)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  const group = (kind) => (papers || []).filter((p) => (p.kind || 'bank') === kind)

  const renderRow = (p) => (
    <label key={p.id} className="paper-check">
      <input
        type="checkbox"
        checked={selected.includes(p.id)}
        onChange={() => toggle(p.id)}
      />
      <span className="grow">
        <b>{p.title}</b>
        <span className="muted small" style={{ marginLeft: 8 }}>
          {p.question_count || 0} 道题库题
          {p.resume_question_count > 0 && ` + ${p.resume_question_count} 道简历题`}
        </span>
      </span>
    </label>
  )

  return (
    <div style={{ maxWidth: 860, margin: '0 auto' }}>
      <h1 className="page-title">开始面试</h1>
      <p className="page-sub">
        勾选本次面试使用的试卷（随机卷 + 简历卷可组合），结束后报告按 基础 / 应用 / 简历 自动汇总
      </p>
      {error && <div className="alert error">{error}</div>}

      <div className="card">
        <div className="card-title">选择试卷（可多选）</div>
        {papers === null ? (
          <div className="empty">加载中…</div>
        ) : (
          <div className="col">
            {group('bank').length > 0 && (
              <>
                <div className="muted small">🎲 随机卷（基础 + 应用，题库抽题）</div>
                {group('bank').map(renderRow)}
              </>
            )}
            {group('resume').length > 0 && (
              <>
                <div className="muted small" style={{ marginTop: 10 }}>📄 简历卷（按候选人简历生成）</div>
                {group('resume').map(renderRow)}
              </>
            )}
            {papers.length === 0 && (
              <div className="empty">
                还没有试卷，先到「试卷管理」随机组卷或按简历生成
                <div style={{ marginTop: 8 }}>
                  <button className="btn sm secondary" onClick={() => navigate('/papers')}>前往试卷管理</button>
                </div>
              </div>
            )}
            {selected.length > 0 && (
              <div className="muted mt">已选 {selected.length} 份卷 · 合计 {totalQuestions} 道题</div>
            )}
          </div>
        )}
      </div>

      <div className="card">
        <div className="card-title">候选人简历（PDF）</div>
        <ResumeDropZone
          onParsed={(d) => {
            if (d.candidate_name) {
              setCandidateName(d.candidate_name)
              setParsedName(d.candidate_name)
            } else {
              setParsedName('')
            }
            setResumeText(d.resume_text)
            setError('')
          }}
        />
        {resumeText && (
          <div className="muted mt">
            已解析简历 {resumeText.length} 字{parsedName ? ` · 识别姓名：${parsedName}（自动填入）` : ''}
          </div>
        )}
      </div>

      <div className="card">
        <div className="field mb">
          <label>候选人姓名 *</label>
          <input className="input" style={{ maxWidth: 280 }} value={candidateName}
            onChange={(e) => setCandidateName(e.target.value)} placeholder="如：李四" />
        </div>
        <div className="field">
          <label>候选人简历（用于简历熟悉度评价；PDF 解析后自动填入，也可直接粘贴文本）</label>
          <textarea className="textarea" rows={8} value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            placeholder={'粘贴简历全文或要点，例如：\nxx大学 计算机专业\nA公司 Python后端 2年：负责订单系统，FastAPI + MySQL，做过慢查询优化…'} />
        </div>
      </div>

      <div className="row">
        <button className="btn secondary" onClick={() => navigate('/papers')}>返回</button>
        <button className="btn success" onClick={start} disabled={busy || selected.length === 0}>
          {busy ? '创建中…' : '🎤 进入面试'}
        </button>
      </div>
    </div>
  )
}
