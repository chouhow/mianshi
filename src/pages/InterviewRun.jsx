import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { api, FREQ_BADGE, SECTIONS, STATE_BADGE, STATE_TEXT } from '../api.js'
import { navigate, Markdown } from '../ui.jsx'
import { MicRecorder } from '../audio.js'

const DIFF_BADGE = { 简单: 'green', 中等: 'orange', 困难: 'red' }
const SECTION_BADGE = { 基础: 'blue', 应用: 'purple', 简历: 'gray' }

export default function InterviewRun({ interviewId }) {
  const [interview, setInterview] = useState(null)
  const [activeId, setActiveId] = useState(null)
  const [answerDraft, setAnswerDraft] = useState('')
  const [liveText, setLiveText] = useState('')
  const [recording, setRecording] = useState(false)
  const [asrError, setAsrError] = useState('')
  const [error, setError] = useState('')
  const [showRef, setShowRef] = useState(false)
  const recorderRef = useRef(null)
  const liveBoxRef = useRef(null)

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

  useEffect(() => { load() }, [load])

  const items = interview?.items || []
  const active = useMemo(
    () => items.find((it) => it.id === activeId) || items.find((it) => it.state === 'pending') || items[0] || null,
    [items, activeId],
  )

  // 切题时同步答案草稿
  useEffect(() => {
    setAnswerDraft(active?.answer_text || '')
    setLiveText('')
    setAsrError('')
    setShowRef(false)
  }, [active?.id])

  // 录音中自动滚动转写框
  useEffect(() => {
    if (liveBoxRef.current) liveBoxRef.current.scrollTop = liveBoxRef.current.scrollHeight
  }, [liveText])

  if (error) return <div className="alert error">{error}</div>
  if (!interview) return <div className="empty">加载中…</div>
  if (interview.status !== 'ongoing') {
    return (
      <div>
        <div className="alert info">该面试已结束。</div>
        <button className="btn" onClick={() => navigate('/interview/report/' + interview.id)}>查看报告</button>
      </div>
    )
  }

  const grouped = SECTIONS.map((s) => ({ section: s, items: items.filter((it) => it.section === s) }))
    .filter((g) => g.items.length > 0)

  const stats = {
    answered: items.filter((it) => it.state === 'answered').length,
    unknown: items.filter((it) => it.state === 'unknown').length,
    pending: items.filter((it) => it.state === 'pending').length,
  }

  const startRecord = async () => {
    if (!active) return
    setAsrError('')
    setLiveText('')
    const rec = new MicRecorder({
      onPartial: (t) => setLiveText(t),
      onError: (m) => setAsrError(m),
    })
    recorderRef.current = rec
    try {
      await rec.start({ interviewId: interview.id, itemId: active.id })
      setRecording(true)
    } catch (e) {
      setAsrError(e.message)
      rec.cancel()
      recorderRef.current = null
    }
  }

  const stopRecord = async () => {
    const rec = recorderRef.current
    if (!rec) return
    setRecording(false)
    const { text, error: asrErr } = await rec.stop()
    recorderRef.current = null
    if (asrErr) setAsrError(asrErr)
    if (text) {
      setAnswerDraft((prev) => (prev.trim() ? prev.trim() + '\n' + text : text))
      setLiveText(text)
    }
  }

  const saveAnswer = async (state) => {
    if (!active) return
    if (state === 'answered' && !answerDraft.trim()) {
      setError('回答内容为空')
      setTimeout(() => setError(''), 2000)
      return
    }
    try {
      if (state === 'answered') {
        await api.put(`/api/interviews/${interview.id}/items/${active.id}`, {
          answer_text: answerDraft,
          state: 'answered',
        })
      } else {
        if (!window.confirm('确定标记为「不会」？该题将计 0 分。')) return
        await api.put(`/api/interviews/${interview.id}/items/${active.id}`, { state: 'unknown' })
      }
      setError('')
      const iv = await load()
      // 自动跳到下一道未问的题
      const next = iv?.items.find((it) => it.state === 'pending')
      if (next) setActiveId(next.id)
    } catch (e) {
      setError(e.message)
    }
  }

  const resetItem = async () => {
    if (!active || recording) return
    try {
      await api.put(`/api/interviews/${interview.id}/items/${active.id}`, { state: 'pending' })
      await load()
    } catch (e) {
      setError(e.message)
    }
  }

  const finish = async () => {
    if (recording) await stopRecord()
    const unasked = interview.items.filter((it) => it.state === 'pending').length
    const msg = unasked > 0
      ? `还有 ${unasked} 道题未问，结束面试后这些题不计入评分。确定结束？`
      : '确定结束面试并进入评分？'
    if (!window.confirm(msg)) return
    try {
      await api.post(`/api/interviews/${interview.id}/finish`)
      navigate('/interview/report/' + interview.id)
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div>
      <div className="row between mb">
        <div>
          <h1 className="page-title">面试进行中 · {interview.candidate_name}</h1>
          <p className="page-sub">
            试卷：{interview.paper_title} · 已答 {stats.answered} / 不会 {stats.unknown} / 未问 {stats.pending}
          </p>
        </div>
        <button className="btn danger" onClick={finish}>🏁 结束面试</button>
      </div>
      {error && <div className="alert error">{error}</div>}

      <div className="interview-layout">
        {/* 左：题目列表 */}
        <div className="card q-list" style={{ padding: 12 }}>
          {grouped.map((g) => (
            <div key={g.section}>
              <div className="q-group-title">
                <span className={'badge ' + SECTION_BADGE[g.section]}>{g.section}</span>
              </div>
              {g.items.map((it) => {
                const globalIdx = items.indexOf(it) + 1
                return (
                  <div
                    key={it.id}
                    className={'q-item' + (active?.id === it.id ? ' active' : '')}
                    onClick={() => !recording && setActiveId(it.id)}
                    style={recording ? { opacity: 0.6 } : undefined}
                  >
                    <span className="no">{globalIdx}</span>
                    <span className="stem">{it.stem.length > 44 ? it.stem.slice(0, 44) + '…' : it.stem}</span>
                    <span className={'badge ' + STATE_BADGE[it.state] + ' q-state'}>{STATE_TEXT[it.state]}</span>
                  </div>
                )
              })}
            </div>
          ))}
        </div>

        {/* 右：当前题目 */}
        {active && (
          <div className="card">
            <div className="row mb">
              <span className={'badge ' + SECTION_BADGE[active.section]}>{active.section}</span>
              <span className="tag">{active.category}</span>
              <span className={'badge ' + (DIFF_BADGE[active.difficulty] || 'gray')}>{active.difficulty}</span>
              {active.frequency && <span className={'badge ' + (FREQ_BADGE[active.frequency] || 'gray')}>{active.frequency}</span>}
              {(active.source === 'llm' || active.source === 'resume') && <span className="badge purple">简历题</span>}
              <span className={'badge ' + STATE_BADGE[active.state]}>{STATE_TEXT[active.state]}</span>
            </div>

            <div className="stem-big mb">{active.stem}</div>

            <div className="mb">
              <button className="btn sm secondary" onClick={() => setShowRef(!showRef)}>
                {showRef ? '收起' : '📖 评分标准与参考答案'}
              </button>
            </div>
            {showRef && (
              <div className="ref-answer mb">
                {active.scoring_points && (
                  <>
                    <div className="muted mb"><b>评分标准（采分点）</b></div>
                    <Markdown text={active.scoring_points} />
                  </>
                )}
                <div className="muted mb mt"><b>参考答案</b></div>
                <Markdown text={active.reference_answer} />
                {active.explanation && (
                  <>
                    <div className="muted mt mb"><b>题目讲解</b></div>
                    <Markdown text={active.explanation} />
                  </>
                )}
              </div>
            )}

            {/* 录音控制 */}
            <div className="row mb">
              {!recording ? (
                <button className="btn" onClick={startRecord}>🎙️ 开始录音</button>
              ) : (
                <button className="btn recording" onClick={stopRecord}><span className="rec-dot" />录音中，点击结束</button>
              )}
              <span className="muted">语音实时转写（火山引擎 ASR），识别文本自动填入回答，可手动修改</span>
            </div>
            {asrError && <div className="alert error">{asrError}</div>}

            {(recording || liveText) && (
              <div className="live-box mb">
                {recording && !liveText && <span className="placeholder">请开始说话…</span>}
                {liveText}
              </div>
            )}

            <div className="field mb">
              <label>回答内容（可编辑）</label>
              <textarea className="textarea" rows={6} value={answerDraft}
                onChange={(e) => setAnswerDraft(e.target.value)}
                placeholder="录音转写会填入这里，也可以直接打字补充" />
            </div>

            <div className="row">
              <button className="btn success" onClick={() => saveAnswer('answered')}>✔ 保存回答</button>
              <button className="btn danger" onClick={() => saveAnswer('unknown')} disabled={recording}>
                ✖ 不会（计 0 分）
              </button>
              {active.state !== 'pending' && (
                <button className="btn secondary" onClick={resetItem} disabled={recording}>重新作答</button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
