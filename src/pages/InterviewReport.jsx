import { useEffect, useState } from 'react'
import { api, downloadFile } from '../api.js'
import { Link, fmtTime } from '../ui.jsx'

export default function InterviewReport({ interviewId }) {
  const [interview, setInterview] = useState(null)
  const [error, setError] = useState('')
  const [questions, setQuestions] = useState([])
  const [selected, setSelected] = useState('')
  const [saving, setSaving] = useState(false)
  useEffect(() => {
    api.get('/api/questions?category=算法笔试').then(d => setQuestions(d.questions)).catch(e => setError(e.message))
  }, [])
  useEffect(() => {
    api.get('/api/interviews/' + interviewId).then(setInterview).catch((e) => setError(e.message))
  }, [interviewId])
  if (!interview) return <div>{error || '加载中…'}</div>
  const results = interview.written_results || {}
  async function record(id, passed) {
    setSaving(true)
    setError('')
    const path = `/api/interviews/${interview.id}/written/${encodeURIComponent(id)}`
    try {
      setInterview(passed === null ? await api.del(path) : await api.put(path, { passed }))
      setSelected('')
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }
  return (
    <div>
      <div className="row between mb">
        <div>
          <h1 className="page-title">面试报告 · {interview.candidate_name}</h1>
          <p className="page-sub">{interview.paper_title} · {fmtTime(interview.created_at)}</p>
        </div>
        <div className="row">
          <button className="btn secondary" onClick={() => downloadFile(`/api/interviews/${interview.id}/export_pdf`,
            `面试报告_${interview.candidate_name}.pdf`).catch((e) => setError(e.message))}>导出 PDF</button>
          <Link to="/records" className="btn secondary">返回记录</Link>
        </div>
      </div>
      {error && <div className="alert error">{error}</div>}
      <table className="table">
        <thead><tr><th>#</th><th>题目</th><th>难度</th><th>类型</th></tr></thead>
        <tbody>{interview.items.map((it, i) => (
          <tr key={it.id}><td>{i + 1}</td><td>{it.stem}</td><td>{it.difficulty || '—'}</td><td>{it.category || '—'}</td></tr>
        ))}</tbody>
      </table>
      <h2>算法笔试</h2>
      {Object.keys(results).length === 0 ? <p>未登记</p> : (
        <table className="table">
          <thead><tr><th>机测题目</th><th>结果</th><th>操作</th></tr></thead>
          <tbody>{Object.entries(results).map(([id, result]) => (
            <tr key={id}><td>{result.title}</td><td>{result.passed ? '通过' : '未通过'}</td><td>
              <button className="btn sm secondary" disabled={saving} onClick={() => record(id, !result.passed)}>
                改为{result.passed ? '未通过' : '通过'}
              </button>{' '}
              <button className="btn sm secondary" disabled={saving} onClick={() => record(id, null)}>移除</button>
            </td></tr>
          ))}</tbody>
        </table>
      )}
      <div className="row">
        <select className="select" aria-label="独立机测题目" value={selected} disabled={saving} onChange={e => setSelected(e.target.value)}>
          <option value="">选择机测题目</option>
          {questions.filter(q => !results[q.id]).map(q => <option key={q.id} value={q.id}>{q.stem.split('\n')[0]}</option>)}
        </select>
        <button className="btn" disabled={!selected || saving} onClick={() => record(selected, true)}>登记通过</button>
        <button className="btn secondary" disabled={!selected || saving} onClick={() => record(selected, false)}>登记未通过</button>
      </div>
    </div>
  )
}
