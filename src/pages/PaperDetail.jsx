import { useCallback, useEffect, useState } from 'react'
import { api, DIFFICULTIES, FREQ_BADGE, SECTIONS, downloadFile } from '../api.js'
import { Empty, Modal, navigate } from '../ui.jsx'

const SECTION_BADGE = { 基础: 'blue', 应用: 'purple', 简历: 'gray' }
const DIFF_BADGE = { 简单: 'green', 中等: 'orange', 困难: 'red' }

function AddQuestionModal({ section, onAdd, onClose }) {
  const [questions, setQuestions] = useState(null)
  const [filters, setFilters] = useState({ q: '', difficulty: '' })

  useEffect(() => {
    const params = new URLSearchParams({ section })
    if (filters.q) params.set('q', filters.q)
    if (filters.difficulty) params.set('difficulty', filters.difficulty)
    api.get('/api/questions?' + params.toString())
      .then((d) => setQuestions(d.questions))
      .catch((e) => setQuestions({ error: e.message }))
  }, [section, filters])

  return (
    <Modal title={`从题库添加${section}部分题目`} onClose={onClose}>
      <div className="row mb">
        <input className="input grow" placeholder="搜索题干…" value={filters.q}
          onChange={(e) => setFilters({ ...filters, q: e.target.value })} />
        <select className="select" value={filters.difficulty} onChange={(e) => setFilters({ ...filters, difficulty: e.target.value })}>
          <option value="">全部难度</option>
          {DIFFICULTIES.map((d) => <option key={d}>{d}</option>)}
        </select>
      </div>
      <div style={{ maxHeight: 380, overflowY: 'auto' }}>
        {questions === null ? (
          <Empty text="加载中…" />
        ) : questions.error ? (
          <div className="alert error">{questions.error}</div>
        ) : questions.length === 0 ? (
          <Empty text={`题库中没有${section}部分的题目`} />
        ) : (
          <table className="table">
            <tbody>
              {questions.map((q) => (
                <tr key={q.id}>
                  <td>{q.stem.length > 70 ? q.stem.slice(0, 70) + '…' : q.stem}</td>
                  <td><span className="tag">{q.category}</span></td>
                  <td><span className={'badge ' + (DIFF_BADGE[q.difficulty] || 'gray')}>{q.difficulty}</span></td>
                  <td className="right">
                    <button className="btn sm" onClick={() => onAdd(q)}>添加</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </Modal>
  )
}

export default function PaperDetail({ paperId }) {
  const [paper, setPaper] = useState(null)
  const [error, setError] = useState('')
  const [addFor, setAddFor] = useState(null)
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    try {
      setPaper(await api.get('/api/papers/' + paperId))
      setError('')
    } catch (e) {
      setError(e.message)
    }
  }, [paperId])

  useEffect(() => { load() }, [load])

  if (error) return <div className="alert error">{error}</div>
  if (!paper) return <Empty text="加载中…" />

  const persistSections = async (sectionsMap) => {
    setSaving(true)
    try {
      setPaper(await api.put('/api/papers/' + paperId, { sections: sectionsMap }))
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  const removeQuestion = async (section, qid) => {
    const sec = paper.sections.find((s) => s.section === section)
    await persistSections({ [section]: sec.question_ids.filter((id) => id !== qid) })
  }

  const addQuestion = async (section, q) => {
    const sec = paper.sections.find((s) => s.section === section)
    await persistSections({ [section]: [...sec.question_ids, q.id] })
    setAddFor(null)
  }

  const missing = paper.resolved?.missing_ids?.length

  return (
    <div>
      <div className="row between mb">
        <div>
          <h1 className="page-title">{paper.title}</h1>
          <p className="page-sub">
            创建于 {paper.created_at?.replace('T', ' ')} · 共 {' '}
            {paper.sections.reduce((n, s) => n + s.question_ids.length, 0)} 道题库题
            {paper.sections.reduce((n, s) => n + (s.embedded_questions?.length || 0), 0) > 0 && ` + ${paper.sections.reduce((n, s) => n + (s.embedded_questions?.length || 0), 0)} 道简历题`}
          </p>
        </div>
        <div className="row">
          <span className={'badge ' + (paper.kind === 'resume' ? 'purple' : 'blue')} style={{ alignSelf: 'center' }}>
            {paper.kind === 'resume' ? '简历卷' : '随机卷'}
          </span>
          <button
            className="btn secondary"
            title="无电脑/麦克风时，打印此表线下手写评分"
            onClick={() =>
              downloadFile(`/api/papers/${paper.id}/export_sheet`, `线下评分表_${paper.title}.pdf`)
                .catch((e) => setError(e.message))}
          >
            🖨 线下评分表
          </button>
          <button className="btn success" onClick={() => navigate('/interview/new?paper=' + paper.id)}>
            🎤 开始面试
          </button>
        </div>
      </div>

      {paper.warnings?.length > 0 && (
        <div className="alert warn">{paper.warnings.map((w, i) => <div key={i}>{w}</div>)}</div>
      )}
      {missing > 0 && (
        <div className="alert warn">有 {missing} 道题目已从题库删除，试卷中已自动忽略。</div>
      )}
      {saving && <div className="alert info">保存中…</div>}

      {SECTIONS.filter((s) => paper.sections.some((x) => x.section === s)).map((section) => {
        const sec = paper.sections.find((s) => s.section === section)
        const questions = paper.resolved.sections.find((s) => s.section === section)?.questions || []
        return (
          <div className="card" key={section}>
            <div className="row between mb">
              <div className="row">
                <span className={'badge ' + SECTION_BADGE[section]}>{section}部分</span>
                <span className="muted">{sec.question_ids.length} 题</span>
                {sec.llm_gen_count > 0 && (
                  <span className="badge purple">面试时按简历生成 {sec.llm_gen_count} 题</span>
                )}
              </div>
              <button className="btn sm secondary" onClick={() => setAddFor(section)}>＋ 从题库添加</button>
            </div>
            {questions.length === 0 ? (
              <Empty text="该部分暂无题目" />
            ) : (
              <table className="table">
                <tbody>
                  {questions.map((q, i) => (
                    <tr key={q.id || 'emb-' + i}>
                      <td style={{ width: 30 }} className="muted">{i + 1}</td>
                      <td>
                        {q.embedded && <span className="badge purple" style={{ marginRight: 6 }}>按简历生成</span>}
                        {q.stem}
                      </td>
                      <td><span className="tag">{q.category}</span></td>
                      <td><span className={'badge ' + (DIFF_BADGE[q.difficulty] || 'gray')}>{q.difficulty}</span>{q.frequency ? <span className={'badge ' + (FREQ_BADGE[q.frequency] || 'gray')} style={{ marginLeft: 6 }}>{q.frequency}</span> : null}</td>
                      <td className="right">
                        {q.id
                          ? <button className="btn sm ghost-danger" onClick={() => removeQuestion(section, q.id)}>移除</button>
                          : <span className="muted small">固化题</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )
      })}

      {addFor && (
        <AddQuestionModal
          section={addFor}
          onAdd={(q) => addQuestion(addFor, q)}
          onClose={() => setAddFor(null)}
        />
      )}
    </div>
  )
}
