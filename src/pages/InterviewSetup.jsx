import { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import ResumeDropZone from '../components/ResumeDropZone.jsx'
import { navigate } from '../ui.jsx'

export default function InterviewSetup({ paperId }) {
  const [paper, setPaper] = useState(null)
  const [candidateName, setCandidateName] = useState('')
  const [resumeText, setResumeText] = useState('')
  const [genCount, setGenCount] = useState(null) // null=未读试卷
  const [generated, setGenerated] = useState([]) // LLM 生成的简历题（可编辑）
  const [parsedName, setParsedName] = useState('') // PDF 解析识别出的姓名
  const [busy, setBusy] = useState('') // loading | generating | creating
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/api/papers/' + paperId)
      .then((p) => {
        setPaper(p)
        const resumeSec = p.sections.find((s) => s.section === '简历')
        setGenCount(resumeSec?.llm_gen_count || 0)
      })
      .catch((e) => setError(e.message))
  }, [paperId])

  if (error) return <div className="alert error">{error}</div>
  if (!paper) return <div className="empty">加载中…</div>

  const generate = async () => {
    if (resumeText.trim().length < 10) {
      setError('请先粘贴候选人简历（至少 10 个字）')
      return
    }
    setBusy('generating')
    setError('')
    try {
      const data = await api.post('/api/llm/generate_resume_questions', {
        resume_text: resumeText.trim(),
        max_count: 10,
      })
      if (data.error) throw new Error(data.error)
      setGenerated(data.questions)
    } catch (e) {
      setError('生成简历题失败：' + e.message)
    } finally {
      setBusy('')
    }
  }

  const updateGen = (i, patch) => {
    setGenerated(generated.map((q, idx) => (idx === i ? { ...q, ...patch } : q)))
  }

  const start = async () => {
    if (!candidateName.trim()) {
      setError('请填写候选人姓名')
      return
    }
    if (genCount > 0 && generated.length === 0 && resumeText.trim().length >= 10) {
      if (!window.confirm('还没有生成简历题，确定直接开始面试吗？')) return
    }
    setBusy('creating')
    setError('')
    try {
      const iv = await api.post('/api/interviews', {
        paper_id: paper.id,
        candidate_name: candidateName.trim(),
        resume_text: resumeText.trim(),
        extra_questions: generated.map((q) => ({
          ...q,
          category: q.category || '简历',
        })),
      })
      navigate('/interview/run/' + iv.id)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy('')
    }
  }

  return (
    <div style={{ maxWidth: 860, margin: '0 auto' }}>
      <h1 className="page-title">开始面试</h1>
      <p className="page-sub">试卷：{paper.title} · 题库题 {paper.sections.reduce((n, s) => n + s.question_ids.length, 0)} 道</p>
      {error && <div className="alert error">{error}</div>}

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
          <label>候选人简历（PDF 解析后自动填入，也可直接粘贴文本）</label>
          <textarea className="textarea" rows={8} value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            placeholder={'粘贴简历全文或要点，例如：\nxx大学 计算机专业\nA公司 Python后端 2年：负责订单系统，FastAPI + MySQL，做过慢查询优化…'} />
        </div>
      </div>

      {genCount > 0 && (
        <div className="card">
          <div className="row between mb">
            <div>
              <div className="card-title" style={{ marginBottom: 4 }}>简历个性化题目</div>
              <div className="muted">由大模型根据简历内容自行决定题量（3~10 题，每题聚焦一个细节）</div>
            </div>
            <button className="btn" onClick={generate} disabled={busy === 'generating'}>
              {busy === 'generating' ? '生成中…' : '✨ 根据简历生成题目'}
            </button>
          </div>
          {generated.length === 0 ? (
            <div className="empty">尚未生成。粘贴简历后点击上方按钮。</div>
          ) : (
            <div className="col">
              {generated.map((q, i) => (
                <div className="card" key={i} style={{ marginBottom: 0, background: '#f8fafc' }}>
                  <div className="field mb">
                    <label>题干</label>
                    <textarea className="textarea" rows={2} value={q.stem}
                      onChange={(e) => updateGen(i, { stem: e.target.value })} />
                  </div>
                  <div className="field mb">
                    <label>参考答案</label>
                    <textarea className="textarea" rows={2} value={q.reference_answer}
                      onChange={(e) => updateGen(i, { reference_answer: e.target.value })} />
                  </div>
                  <div className="field mb">
                    <label>评分标准（每行一个采分点及分值，合计 5 分）</label>
                    <textarea className="textarea" rows={2} value={q.scoring_points || ''}
                      onChange={(e) => updateGen(i, { scoring_points: e.target.value })} />
                  </div>
                  <div className="row">
                    <div className="field grow">
                      <label>讲解（可选）</label>
                      <input className="input" value={q.explanation || ''}
                        onChange={(e) => updateGen(i, { explanation: e.target.value })} />
                    </div>
                    <div className="field">
                      <label>难度</label>
                      <select className="select" value={q.difficulty || '中等'}
                        onChange={(e) => updateGen(i, { difficulty: e.target.value })}>
                        <option>简单</option><option>中等</option><option>困难</option>
                      </select>
                    </div>
                    <button className="btn sm ghost-danger" style={{ alignSelf: 'flex-end' }}
                      onClick={() => setGenerated(generated.filter((_, idx) => idx !== i))}>
                      移除
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="row">
        <button className="btn secondary" onClick={() => navigate('/papers')}>返回</button>
        <button className="btn success" onClick={start} disabled={busy === 'creating'}>
          {busy === 'creating' ? '创建中…' : '🎤 进入面试'}
        </button>
      </div>
    </div>
  )
}
