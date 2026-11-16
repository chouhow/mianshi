import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, DIFFICULTIES, FREQ_BADGE, FREQUENCIES } from '../api.js'
import { Empty, Modal, fmtTime } from '../ui.jsx'

const EMPTY_FORM = {
  stem: '',
  reference_answer: '',
  scoring_points: '',
  explanation: '',
  category: '',
  difficulty: '中等',
  frequency: '高频',
  scoring_mode: 'points',
}

const DIFF_BADGE = { 简单: 'green', 中等: 'orange', 困难: 'red' }

function QuestionFormModal({ initial, categories, onSave, onClose }) {
  const isEdit = Boolean(initial?.id)
  const [form, setForm] = useState(initial ? {
    stem: initial.stem,
    reference_answer: initial.reference_answer,
    scoring_points: initial.scoring_points || '',
    explanation: initial.explanation || '',
    category: initial.category,
    difficulty: initial.difficulty,
    frequency: initial.frequency || '高频',
    scoring_mode: initial.scoring_mode || 'points',
  } : EMPTY_FORM)
  const [errors, setErrors] = useState({})
  const [saving, setSaving] = useState(false)

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async () => {
    const errs = {}
    if (!form.stem.trim()) errs.stem = '题干不能为空'
    if (!form.reference_answer.trim()) errs.reference_answer = '参考答案不能为空'
    if (!form.category.trim()) errs.category = '类型不能为空（如 Python、数据库）'
    setErrors(errs)
    if (Object.keys(errs).length) return
    setSaving(true)
    try {
      await onSave({
        stem: form.stem.trim(),
        reference_answer: form.reference_answer.trim(),
        scoring_points: form.scoring_points.trim(),
        explanation: form.explanation.trim(),
        category: form.category.trim(),
        difficulty: form.difficulty,
        frequency: form.frequency,
        scoring_mode: form.scoring_mode,
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal title={isEdit ? '编辑题目' : '新建题目'} onClose={onClose}>
      <div className="col">
        <div className="field">
          <label>题干 *</label>
          <textarea className="textarea" rows={3} value={form.stem} onChange={set('stem')} placeholder="例如：请解释 Python 中 GIL 的作用及其影响" />
          {errors.stem && <span className="err">{errors.stem}</span>}
        </div>
        <div className="field">
          <label>参考答案 *</label>
          <textarea className="textarea" rows={4} value={form.reference_answer} onChange={set('reference_answer')} placeholder="评分依据，尽量写清要点" />
          {errors.reference_answer && <span className="err">{errors.reference_answer}</span>}
        </div>
        <div className="field">
          <label>评分标准 / 采分点（推荐填写，评分将严格按点给分）</label>
          <textarea className="textarea" rows={3} value={form.scoring_points} onChange={set('scoring_points')} placeholder={'每行一个采分点及分值，合计 5 分。例如：\n答出列表可变、元组不可变：2分\n答出元组可哈希、可作字典键：1.5分\n答出元组内存更小：1.5分\n\n留空时 LLM 会按参考答案自动归纳采分点'} />
        </div>
        <div className="field">
          <label>题目讲解（可选，支持 Markdown：列表 / 代码 / 表格）</label>
          <textarea className="textarea" rows={2} value={form.explanation} onChange={set('explanation')} placeholder="出题意图、追问方向等，供面试官参考。支持 Markdown，如：&#10;- 要点一&#10;- \`code\` 示例" />
        </div>
        <div className="form-grid">
          <div className="field">
            <label>所属类型 *</label>
            <input className="input" list="category-list" value={form.category} onChange={set('category')} placeholder="如 Python、数据库" />
            <datalist id="category-list">
              {categories.map((c) => <option key={c} value={c} />)}
            </datalist>
            {errors.category && <span className="err">{errors.category}</span>}
          </div>
          <div className="field">
            <label>难易程度 *</label>
            <select className="select" value={form.difficulty} onChange={set('difficulty')}>
              {DIFFICULTIES.map((d) => <option key={d}>{d}</option>)}
            </select>
          </div>
          <div className="field">
            <label>出现频率 *</label>
            <select className="select" value={form.frequency} onChange={set('frequency')}>
              {FREQUENCIES.map((f) => <option key={f}>{f}</option>)}
            </select>
          </div>
          <div className="field span2">
            <label>评分方式 *</label>
            <select className="select" value={form.scoring_mode} onChange={set('scoring_mode')}>
              <option value="points">按点给分（答案确定，严格按采分点）</option>
              <option value="holistic">综合评价（开放型题目，整体质量判断）</option>
            </select>
          </div>
          <div className="field">
            <label></label>
            <span className="muted" style={{ marginTop: 18, display: 'inline-block' }}>所属部分按难度自动归属：简单/中等→基础，困难→应用</span>
          </div>
        </div>
      </div>
      <div className="modal-footer">
        <button className="btn secondary" onClick={onClose}>取消</button>
        <button className="btn" onClick={submit} disabled={saving}>{saving ? '保存中…' : '保存'}</button>
      </div>
    </Modal>
  )
}

export default function Questions() {
  const [questions, setQuestions] = useState(null)
  const [categories, setCategories] = useState([])
  const [filters, setFilters] = useState({ q: '', category: '', difficulty: '', frequency: '' })
  const [editing, setEditing] = useState(null) // null 关闭 / {} 新建 / question 编辑
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      const params = new URLSearchParams()
      Object.entries(filters).forEach(([k, v]) => v && params.set(k, v))
      const data = await api.get('/api/questions?' + params.toString())
      setQuestions(data.questions)
      setError('')
    } catch (e) {
      setError(e.message)
    }
  }, [filters])

  useEffect(() => { load() }, [load])
  useEffect(() => {
    api.get('/api/questions/categories').then((d) => setCategories(d.categories)).catch(() => {})
  }, [questions])

  const stats = useMemo(() => {
    const by = { 高频: 0, 中频: 0, 低频: 0 }
    ;(questions || []).forEach((q) => { by[q.frequency] = (by[q.frequency] || 0) + 1 })
    return by
  }, [questions])

  const save = async (payload) => {
    if (editing?.id) {
      await api.put('/api/questions/' + editing.id, payload)
    } else {
      await api.post('/api/questions', payload)
    }
    setEditing(null)
    await load()
  }

  const remove = async (q) => {
    if (!window.confirm(`确定删除该题目？\n${q.stem.slice(0, 60)}`)) return
    await api.del('/api/questions/' + q.id)
    await load()
  }

  return (
    <div>
      <h1 className="page-title">题库管理</h1>
      <p className="page-sub">
        共 {(questions || []).length} 道题 · 高频 {stats['高频']} / 中频 {stats['中频']} / 低频 {stats['低频']}
      </p>

      {error && <div className="alert error">{error}</div>}

      <div className="card">
        <div className="row">
          <input
            className="input grow" style={{ maxWidth: 320 }}
            placeholder="搜索题干 / 参考答案…"
            value={filters.q}
            onChange={(e) => setFilters({ ...filters, q: e.target.value })}
          />
          <select className="select" value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value })}>
            <option value="">全部类型</option>
            {categories.map((c) => <option key={c}>{c}</option>)}
          </select>
          <select className="select" value={filters.difficulty} onChange={(e) => setFilters({ ...filters, difficulty: e.target.value })}>
            <option value="">全部难度</option>
            {DIFFICULTIES.map((d) => <option key={d}>{d}</option>)}
          </select>
          <select className="select" value={filters.frequency} onChange={(e) => setFilters({ ...filters, frequency: e.target.value })}>
            <option value="">全部频率</option>
            {FREQUENCIES.map((f) => <option key={f}>{f}</option>)}
          </select>
          <div className="grow" />
          <button className="btn" onClick={() => setEditing({})}>＋ 新建题目</button>
        </div>
      </div>

      <div className="card" style={{ padding: 0 }}>
        {questions === null ? (
          <Empty text="加载中…" />
        ) : questions.length === 0 ? (
          <Empty text="题库为空，点击右上角「新建题目」开始添加" />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: '42%' }}>题干</th>
                <th>类型</th>
                <th>难度</th>
                <th>频率</th>
                <th>讲解</th>
                <th>更新时间</th>
                <th className="right">操作</th>
              </tr>
            </thead>
            <tbody>
              {questions.map((q) => (
                <tr key={q.id}>
                  <td>{q.stem.length > 80 ? q.stem.slice(0, 80) + '…' : q.stem}</td>
                  <td><span className="tag">{q.category}</span></td>
                  <td><span className={'badge ' + (DIFF_BADGE[q.difficulty] || 'gray')}>{q.difficulty}</span></td>
                  <td><span className={'badge ' + (FREQ_BADGE[q.frequency] || 'gray')}>{q.frequency || '高频'}</span></td>
                  <td>{q.explanation ? '✅' : '—'}</td>
                  <td className="muted">{fmtTime(q.updated_at)}</td>
                  <td className="right">
                    <button className="btn sm secondary" onClick={() => setEditing(q)}>编辑</button>{' '}
                    <button className="btn sm ghost-danger" onClick={() => remove(q)}>删除</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {editing !== null && (
        <QuestionFormModal
          initial={editing.id ? editing : null}
          categories={categories}
          onSave={save}
          onClose={() => setEditing(null)}
        />
      )}
    </div>
  )
}
