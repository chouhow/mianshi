import { useCallback, useEffect, useRef, useState } from 'react'
import { api, API_BASE, STATE_BADGE, STATE_TEXT } from '../api.js'
import { Link, Markdown, fmtTime } from '../ui.jsx'

const SECTION_BADGE = { 基础: 'blue', 应用: 'purple', 简历: 'gray' }

function ScoreHero({ scores }) {
  const cards = [
    { label: '总分', value: scores.total, full: 100, total: true },
    { label: '基础部分', value: scores.basic, full: 40 },
    { label: '应用部分', value: scores.applied, full: 30 },
    { label: '简历 · 题目', value: scores.resume_q, full: 15 },
    { label: '简历 · 熟悉度', value: scores.resume_familiar, full: 15 },
  ]
  return (
    <div className="score-hero">
      {cards.map((c) => (
        <div key={c.label} className={'score-card' + (c.total ? ' total' : '')}>
          <div className="label">{c.label}</div>
          <div className="value">{c.value} <small>/ {c.full}</small></div>
        </div>
      ))}
    </div>
  )
}

export default function InterviewReport({ interviewId }) {
  const [interview, setInterview] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [exported, setExported] = useState('')

  const load = useCallback(async () => {
    try {
      const iv = await api.get('/api/interviews/' + interviewId)
      setInterview(iv)
      return iv
    } catch (e) {
      setError(e.message)
      return null
    }
  }, [interviewId])

  const startScore = async () => {
    setBusy(true)
    try {
      await api.post(`/api/interviews/${interviewId}/score`)
      setInterview(await load())
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  // 初次加载
  useEffect(() => {
    load()
  }, [load])

  // 评分中：每 1.5s 轮询进度；状态一变（完成/失败）即停止并自动切到结果视图
  useEffect(() => {
    if (interview?.status !== 'scoring') return
    const timer = setInterval(() => {
      load()
    }, 1500)
    return () => clearInterval(timer)
  }, [interview?.status, load])

  // 结束面试进入报告页后自动开始评分（仅触发一次，失败可手动重试）
  const autoStarted = useRef(false)
  useEffect(() => {
    if (interview?.status === 'finished' && !autoStarted.current) {
      autoStarted.current = true
      startScore()
    }
  }, [interview?.status]) // eslint-disable-line react-hooks/exhaustive-deps

  if (error) return <div className="alert error">{error}</div>
  if (!interview) return <div className="empty">加载中…</div>

  const items = interview.items || []
  const counted = items.filter((it) => it.state === 'answered' || it.state === 'unknown')
  const scoredCount = counted.filter((it) => it.score !== null && it.score !== undefined).length

  // 状态分支：待评分 / 评分中 / 评分失败 / 已完成
  if (interview.status !== 'scored') {
    return (
      <div style={{ maxWidth: 720, margin: '0 auto' }}>
        <div className="row between mb">
          <div>
            <h1 className="page-title">{interview.candidate_name} · 评分</h1>
            <p className="page-sub">
              试卷：{interview.paper_title} · 已答 {counted.filter((i) => i.state === 'answered').length} 题 / 不会 {' '}
              {counted.filter((i) => i.state === 'unknown').length} 题 / 未问 {items.length - counted.length} 题（不计分）
            </p>
          </div>
          <Link to="/records" className="btn secondary">返回记录</Link>
        </div>

        {interview.status === 'scoring' && (
          <div className="card">
            <div className="card-title">LLM 评分中…（{scoredCount}/{counted.length} 题）</div>
            <div className="progress-bar"><div style={{ width: `${counted.length ? (scoredCount / counted.length) * 100 : 0}%` }} /></div>
            <div className="muted mt">评分模式：{interview.judge_mode === 'whole_paper' ? '整卷评判' : '逐题评判'} · 期间请勿关闭页面</div>
          </div>
        )}

        {interview.status === 'finished' && (
          <div className="card center">
            <div className="card-title">面试已结束，等待评分</div>
            <button className="btn success" onClick={startScore} disabled={busy}>
              {busy ? '提交中…' : '🧮 开始 LLM 评分'}
            </button>
          </div>
        )}

        {interview.status === 'score_error' && (
          <div>
            <div className="alert error">评分失败：{interview.score_error}</div>
            <button className="btn" onClick={startScore} disabled={busy}>重试评分</button>
          </div>
        )}

        {interview.status === 'ongoing' && (
          <div className="card center">
            <div className="card-title">面试尚未结束</div>
            <Link to={'/interview/run/' + interview.id} className="btn">继续面试</Link>
          </div>
        )}
      </div>
    )
  }

  const sections = ['基础', '应用', '简历'].filter((s) => items.some((it) => it.section === s))

  const doExport = async () => {
    setBusy(true)
    try {
      const res = await fetch(`${API_BASE}/api/interviews/${interviewId}/export_pdf`)
      if (!res.ok) {
        let msg = `导出失败（HTTP ${res.status}）`
        try {
          const d = await res.json()
          msg = typeof d.detail === 'string' ? d.detail : msg
        } catch { /* ignore */ }
        throw new Error(msg)
      }
      const blob = await res.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `面试报告_${interview.candidate_name}.pdf`
      a.click()
      URL.revokeObjectURL(a.href)
      setExported('已导出 PDF')
      setTimeout(() => setExported(''), 2000)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <div className="row between mb">
        <div>
          <h1 className="page-title">面试报告 · {interview.candidate_name}</h1>
          <p className="page-sub">
            试卷：{interview.paper_title} · 面试时间 {fmtTime(interview.created_at)} · 评分于 {fmtTime(interview.scored_at)} · {' '}
            {interview.judge_mode === 'whole_paper' ? '整卷评判' : '逐题评判'}
          </p>
        </div>
        <div className="row">
          {exported && <span className="muted">{exported}</span>}
          <button className="btn secondary" onClick={doExport} disabled={busy}>⬇ 导出 PDF</button>
          <Link to="/records" className="btn secondary">返回记录</Link>
        </div>
      </div>

      <div className="mb"><ScoreHero scores={interview.scores} /></div>

      {sections.map((section) => {
        const secItems = items.filter((it) => it.section === section)
        const answered = secItems.filter((it) => it.state === 'answered').length
        const unknown = secItems.filter((it) => it.state === 'unknown').length
        const unasked = secItems.length - answered - unknown
        return (
          <div className="card" key={section} style={{ padding: 0 }}>
            <div className="row between" style={{ padding: '14px 16px 4px' }}>
              <div className="row">
                <span className={'badge ' + SECTION_BADGE[section]}>{section}部分</span>
                <span className="muted">已答 {answered} · 不会 {unknown} · 未问 {unasked}（不计分）</span>
              </div>
            </div>
            <table className="table">
              <thead>
                <tr>
                  <th style={{ width: 34 }}>#</th>
                  <th style={{ width: '36%' }}>题目</th>
                  <th style={{ width: 90 }}>状态</th>
                  <th style={{ width: 80 }}>得分</th>
                  <th>评语</th>
                </tr>
              </thead>
              <tbody>
                {secItems.map((it, i) => (
                  <tr key={it.id}>
                    <td className="muted">{i + 1}</td>
                    <td>
                      <div>{it.stem}</div>
                      {it.scoring_points && (
                        <div className="muted mt">采分点：{it.scoring_points.length > 100 ? it.scoring_points.slice(0, 100) + '…' : it.scoring_points.replace(/\n/g, '；')}</div>
                      )}
                      {it.state === 'answered' && (
                        <div className="muted mt">回答：{(it.answer_text || '').slice(0, 120)}{(it.answer_text || '').length > 120 ? '…' : ''}</div>
                      )}
                    </td>
                    <td><span className={'badge ' + STATE_BADGE[it.state]}>{STATE_TEXT[it.state]}</span></td>
                    <td><b>{it.score ?? '—'}</b>{it.score != null && <span className="muted"> / 5</span>}</td>
                    <td className="small">{it.comment || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )
      })}

      {interview.resume_comment && (
        <div className="card">
          <div className="card-title">简历熟悉度评价（{interview.scores.resume_familiar} / 15）</div>
          <Markdown text={interview.resume_comment} />
        </div>
      )}

      <div className="card">
        <div className="card-title">整体评价</div>
        <Markdown text={interview.overall_comment || '（未生成，可重新评分补全）'} />
      </div>
    </div>
  )
}
