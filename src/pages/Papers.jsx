import { useCallback, useEffect, useState } from 'react'
import { api, DIFFICULTIES, SECTIONS, downloadFile } from '../api.js'
import { Empty, Link, Modal, fmtTime, navigate } from '../ui.jsx'

const DEFAULT_PARAMS = {
  title: '',
  sections: [
    // 默认：基础 12 题全简单
    { section: '基础', count: 12, difficulty: ['简单'], difficultyRatio: { 简单: 1, 中等: 2, 困难: 1 }, categories: [], llm_gen_count: 0 },
    // 默认：应用 10 题 = 中等:困难 按 2:1
    { section: '应用', count: 10, difficulty: ['中等', '困难'], difficultyRatio: { 简单: 1, 中等: 2, 困难: 1 }, categories: [], llm_gen_count: 0 },
  ],
}

function CheckGroup({ options, values, onChange }) {
  return (
    <div className="row" style={{ gap: 2 }}>
      {options.map((opt) => (
        <label key={opt} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, marginRight: 10, cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={values.includes(opt)}
            onChange={(e) =>
              onChange(e.target.checked ? [...values, opt] : values.filter((v) => v !== opt))
            }
          />
          <span className="small">{opt}</span>
        </label>
      ))}
    </div>
  )
}

function GenerateModal({ categories, onClose, onGenerated }) {
  const [params, setParams] = useState(DEFAULT_PARAMS)
  const [freqRatio, setFreqRatio] = useState({ 高频: 7, 中频: 2, 低频: 1 })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const updateSection = (i, patch) => {
    const sections = params.sections.map((s, idx) => (idx === i ? { ...s, ...patch } : s))
    setParams({ ...params, sections })
  }

  const generate = async () => {
    setBusy(true)
    setError('')
    try {
      const body = {
        title: params.title.trim() || undefined,
        frequency_ratio: {
          高频: Number(freqRatio.高频) || 0,
          中频: Number(freqRatio.中频) || 0,
          低频: Number(freqRatio.低频) || 0,
        },
        sections: params.sections.map((s) => ({
          section: s.section,
          count: Number(s.count) || 0,
          difficulty: s.difficulty,
          difficulty_ratio: s.difficulty.length > 1 && s.difficultyRatio
            ? Object.fromEntries(DIFFICULTIES.map((d) => [d, Number(s.difficultyRatio[d]) || 0]))
            : undefined,
          categories: s.categories,
          llm_gen_count: Number(s.llm_gen_count) || 0,
        })),
      }
      const paper = await api.post('/api/papers/generate', body)
      onGenerated(paper)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal title="随机组卷" onClose={onClose}>
      <div className="col">
        <div className="field">
          <label>试卷标题（可选，留空自动生成）</label>
          <input
            className="input" value={params.title}
            onChange={(e) => setParams({ ...params, title: e.target.value })}
            placeholder="如：Python 后端校招面试卷"
          />
        </div>

        {params.sections.map((s, i) => (
          <div className="card" key={s.section} style={{ marginBottom: 0, background: '#f8fafc' }}>
            <div className="row between mb">
              <b>{s.section}部分</b>
              <div className="row">
                <span className="muted">抽题数量</span>
                <input className="input" style={{ width: 72 }} type="number" min="0" max="50"
                  value={s.count} onChange={(e) => updateSection(i, { count: e.target.value })} />
                {s.section === '简历' && (
                  <>
                    <span className="muted" style={{ marginLeft: 12 }}>按简历生成</span>
                    <input className="input" style={{ width: 72 }} type="number" min="0" max="10"
                      value={s.llm_gen_count} onChange={(e) => updateSection(i, { llm_gen_count: e.target.value })} />
                  </>
                )}
              </div>
            </div>
            <div className="row mb" style={{ gap: 8 }}>
              <span className="muted" style={{ width: 36 }}>难度</span>
              <CheckGroup options={DIFFICULTIES} values={s.difficulty}
                onChange={(v) => updateSection(i, { difficulty: v })} />
              <span className="muted">不选 = 任意</span>
            </div>
            {s.difficulty.length > 1 && (
              <div className="row mb" style={{ gap: 8 }}>
                <span className="muted" style={{ width: 36 }}>比例</span>
                {s.difficulty.map((d) => (
                  <span key={d} className="row" style={{ gap: 4 }}>
                    <span className="small">{d}</span>
                    <input className="input" style={{ width: 60 }} type="number" min="0" max="10"
                      value={s.difficultyRatio?.[d] ?? 1}
                      onChange={(e) => updateSection(i, {
                        difficultyRatio: { ...(s.difficultyRatio || {}), [d]: Number(e.target.value) || 0 },
                      })} />
                  </span>
                ))}
                <span className="muted">按比例分配名额，某档不足自动用其他档补足</span>
              </div>
            )}
            <div className="row" style={{ gap: 8 }}>
              <span className="muted" style={{ width: 36 }}>类型</span>
              <CheckGroup options={categories} values={s.categories}
                onChange={(v) => updateSection(i, { categories: v })} />
              <span className="muted">不选 = 任意</span>
            </div>
          </div>
        ))}

        <div className="field">
          <label>频率比例（高 : 中 : 低）</label>
          <div className="row">
            <input className="input" style={{ width: 76 }} type="number" min="0" max="10"
              value={freqRatio.高频} onChange={(e) => setFreqRatio({ ...freqRatio, 高频: e.target.value })} />
            <span className="muted">:</span>
            <input className="input" style={{ width: 76 }} type="number" min="0" max="10"
              value={freqRatio.中频} onChange={(e) => setFreqRatio({ ...freqRatio, 中频: e.target.value })} />
            <span className="muted">:</span>
            <input className="input" style={{ width: 76 }} type="number" min="0" max="10"
              value={freqRatio.低频} onChange={(e) => setFreqRatio({ ...freqRatio, 低频: e.target.value })} />
            <span className="muted">例：7:2:1 时，10 题抽 7 道高频、2 道中频、1 道低频</span>
          </div>
        </div>

        <div className="alert info">
          默认：基础 12 题全简单；应用 10 题 = 中等:困难 按 2:1（纯技术题，不含简历题）。
          需要简历题时，在试卷详情页点「📎 按简历生成新试卷」，按候选人简历派生含简历题的新试卷。
        </div>
        {error && <div className="alert error">{error}</div>}
      </div>
      <div className="modal-footer">
        <button className="btn secondary" onClick={onClose}>取消</button>
        <button className="btn" onClick={generate} disabled={busy}>
          {busy ? '生成中…' : '🎲 生成试卷'}
        </button>
      </div>
    </Modal>
  )
}

export default function Papers() {
  const [papers, setPapers] = useState(null)
  const [categories, setCategories] = useState([])
  const [showGen, setShowGen] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      const data = await api.get('/api/papers')
      setPapers(data.papers)
      setError('')
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => { load() }, [load])
  useEffect(() => {
    api.get('/api/questions/categories').then((d) => setCategories(d.categories)).catch(() => {})
  }, [])

  const remove = async (p) => {
    if (!window.confirm(`确定删除试卷「${p.title}」？`)) return
    await api.del('/api/papers/' + p.id)
    await load()
  }

  return (
    <div>
      <div className="row between">
        <div>
          <h1 className="page-title">试卷管理</h1>
          <p className="page-sub">查看已创建的试卷，或按参数随机生成新试卷</p>
        </div>
        <button className="btn" onClick={() => setShowGen(true)}>🎲 随机组卷</button>
      </div>

      {error && <div className="alert error">{error}</div>}

      <div className="card" style={{ padding: 0 }}>
        {papers === null ? (
          <Empty text="加载中…" />
        ) : papers.length === 0 ? (
          <Empty text="还没有试卷，点击右上角「随机组卷」创建" />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>标题</th><th>题数</th><th>简历题</th><th>创建时间</th><th className="right">操作</th>
              </tr>
            </thead>
            <tbody>
              {papers.map((p) => (
                <tr key={p.id}>
                  <td><Link to={'/papers/' + p.id}><b>{p.title}</b></Link></td>
                  <td>{p.question_count}</td>
                  <td>{p.llm_gen_count || '—'}</td>
                  <td className="muted">{fmtTime(p.created_at)}</td>
                  <td className="right">
                    <button className="btn sm" onClick={() => navigate('/interview/new?paper=' + p.id)}>开始面试</button>{' '}
                    <button className="btn sm secondary" onClick={() => navigate('/papers/' + p.id)}>详情</button>{' '}
                    <button
                      className="btn sm secondary"
                      title="无电脑/麦克风时，打印此表线下手写评分"
                      onClick={() =>
                        downloadFile(`/api/papers/${p.id}/export_sheet`, `线下评分表_${p.title}.pdf`)
                          .catch((e) => setError(e.message))}
                    >🖨 评分表</button>{' '}
                    <button className="btn sm ghost-danger" onClick={() => remove(p)}>删除</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showGen && (
        <GenerateModal
          categories={categories}
          onClose={() => setShowGen(false)}
          onGenerated={(paper) => {
            setShowGen(false)
            navigate('/papers/' + paper.id)
          }}
        />
      )}
    </div>
  )
}
