import { useCallback, useEffect, useRef, useState } from 'react'
import { api, DIFFICULTIES, SECTIONS, downloadFile } from '../api.js'
import { Empty, Link, Modal, fmtTime, navigate } from '../ui.jsx'
import ResumeDropZone from '../components/ResumeDropZone.jsx'

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

// 按简历生成独立简历试卷（异步流式）：上传简历 → 后台生成（实时显示思考过程与输出）→ 完成自动创建试卷并跳转
function ResumePaperModal({ onClose, onCreated }) {
  const [resumeText, setResumeText] = useState('')
  const [title, setTitle] = useState('')
  const [maxCount, setMaxCount] = useState(10)
  const [taskId, setTaskId] = useState(null)
  const [task, setTask] = useState(null) // {status, reasoning, output, error}
  const [error, setError] = useState('')
  const reasoningRef = useRef(null)
  const outputRef = useRef(null)

  // 轮询后台生成任务（含 LLM 思考过程与输出文本）
  useEffect(() => {
    if (!taskId) return undefined
    const timer = setInterval(async () => {
      try {
        const s = await api.get(`/api/papers/tasks/${taskId}`)
        setTask(s)
        if (s.status === 'done') {
          clearInterval(timer)
          onCreated({ id: s.paper_id, title: s.title })
        } else if (s.status === 'error') {
          clearInterval(timer)
          setError('生成失败：' + (s.error || '未知错误'))
        }
      } catch (e) {
        clearInterval(timer)
        setError(e.message)
      }
    }, 800)
    return () => clearInterval(timer)
  }, [taskId]) // eslint-disable-line react-hooks/exhaustive-deps

  // 流式文本自动滚到底部
  useEffect(() => {
    for (const ref of [reasoningRef, outputRef]) {
      if (ref.current) ref.current.scrollTop = ref.current.scrollHeight
    }
  }, [task?.reasoning, task?.output])

  const start = async () => {
    if (resumeText.trim().length < 10) {
      setError('请先上传简历 PDF 或粘贴简历文本（至少 10 个字）')
      return
    }
    setError('')
    try {
      const d = await api.post('/api/papers/generate_from_resume', {
        resume_text: resumeText.trim(),
        max_count: Number(maxCount) || 10,
        title: title.trim() || undefined,
      })
      setTaskId(d.task_id)
      setTask({ status: 'running' })
    } catch (e) {
      setError(e.message)
    }
  }

  const running = task?.status === 'running'

  return (
    <Modal title="按简历生成试卷" onClose={onClose} width={640}>
      <div className="col">
        {running ? (
          <div className="card center" style={{ marginBottom: 0 }}>
            <div className="card-title">正在生成简历试卷…</div>
            <p className="muted">
              大模型正在根据简历生成个性化题目（含参考答案），
              通常需要 1 分钟左右。完成后会<span style={{ color: '#1d4ed8' }}>自动创建简历试卷</span>并跳转。
            </p>
            <div className="progress-bar" style={{ width: 300, margin: '10px auto' }}>
              <div style={{ width: '100%', animation: 'pulse 1.5s infinite' }} />
            </div>
            {(task.reasoning || task.output) && (
              <div className="llm-live">
                {task.reasoning && (
                  <div className="llm-block">
                    <div className="muted small" style={{ textAlign: 'left', marginBottom: 4 }}>🧠 思考过程</div>
                    <pre ref={reasoningRef} className="llm-reasoning">{task.reasoning}</pre>
                  </div>
                )}
                {task.output && (
                  <div className="llm-block">
                    <div className="muted small" style={{ textAlign: 'left', marginBottom: 4 }}>📄 生成输出</div>
                    <pre ref={outputRef} className="llm-output">{task.output}</pre>
                  </div>
                )}
              </div>
            )}
            <p className="muted small">可以关闭此窗口，生成完成后新试卷会出现在试卷列表中。</p>
          </div>
        ) : (
          <>
            <div className="muted">
              生成一份<span style={{ color: '#1d4ed8' }}>仅含简历题</span>的独立试卷；面试时可与随机卷同时勾选，
              从简历提到的技术中随机抽取最多 6 道题库题（不足 6 道按实际数量），再加入 AI 生成的项目题。两类题在报告中均显示为「简历」。
            </div>
            <ResumeDropZone
              compact
              onParsed={(d) => {
                setResumeText(d.resume_text)
                if (!title && d.candidate_name) setTitle(`简历卷·${d.candidate_name}`)
                setError('')
              }}
            />
            <div className="field">
              <label>或直接粘贴简历文本</label>
              <textarea className="textarea" rows={5} value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                placeholder="拖入 PDF 会自动填入，也可手动粘贴" />
            </div>
            <div className="row">
              <div className="field grow">
                <label>试卷标题（可选）</label>
                <input className="input" value={title} onChange={(e) => setTitle(e.target.value)}
                  placeholder="简历卷·张三" />
              </div>
              <div className="field">
                <label>AI 生成题量上限</label>
                <select className="select" value={maxCount} onChange={(e) => setMaxCount(e.target.value)}>
                  {[3, 4, 5, 6, 8, 10].map((n) => <option key={n} value={n}>{n} 题</option>)}
                </select>
              </div>
            </div>
            <div className="muted small">
              实际题量由模型根据简历内容自行决定（3~上限，每题聚焦一个细节）。
            </div>
            {error && <div className="alert error">{error}</div>}
          </>
        )}
      </div>
      <div className="modal-footer">
        <button className="btn secondary" onClick={onClose}>{running ? '后台运行，关闭窗口' : '取消'}</button>
        {!running && (
          <button className="btn success" onClick={start} disabled={resumeText.trim().length < 10}>
            📄 生成简历试卷（后台自动完成）
          </button>
        )}
      </div>
    </Modal>
  )
}

export default function Papers() {
  const [papers, setPapers] = useState(null)
  const [categories, setCategories] = useState([])
  const [manualTitle, setManualTitle] = useState(null)
  const [creating, setCreating] = useState(false)
  const createManual = async () => {
    setCreating(true)
    try {
      const paper = await api.post('/api/papers', { title: manualTitle.trim() })
      navigate('/questions?paper=' + paper.id)
    } catch (e) {
      setError(e.message)
    } finally {
      setCreating(false)
    }
  }
  const [showGen, setShowGen] = useState(false)
  const [showResume, setShowResume] = useState(false)
  const [error, setError] = useState('')

  const [loadError, setLoadError] = useState('')
  const load = useCallback(async () => {
    try {
      const data = await api.get('/api/papers')
      setPapers(data.papers)
      setLoadError('')
      setError('')
      api.get('/api/questions/categories').then((d) => setCategories(d.categories.filter(c => c !== '算法笔试'))).catch(() => {})
    } catch (e) {
      setLoadError(e.message)
    }
  }, [])

  useEffect(() => { load() }, [load])
  useEffect(() => {
    if (!loadError) return
    let active = true
    let timer
    const retry = async () => {
      await load()
      if (active) timer = setTimeout(retry, 3000)
    }
    timer = setTimeout(retry, 3000)
    return () => { active = false; clearTimeout(timer) }
  }, [loadError, load])

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
          <p className="page-sub">可手动选题、随机抽题或按简历生成试卷，面试时可组合使用</p>
        </div>
        <div className="row">
          <button className="btn" onClick={() => { setManualTitle(''); setError('') }}>＋ 创建空白试卷</button>
          <button className="btn" onClick={() => setShowGen(true)}>🎲 随机组卷</button>
          <button className="btn" onClick={() => setShowResume(true)}>📄 简历生成试卷</button>
        </div>
      </div>

      {loadError && <div className="alert error">{loadError}。正在自动重试。</div>}
      {error && <div className="alert error">{error}</div>}

      <div className="card" style={{ padding: 0 }}>
        {papers === null ? (
          <Empty text={loadError ? "等待试卷服务恢复…" : "加载中…"} />
        ) : papers.length === 0 ? (
          <Empty text="还没有试卷，可先创建空白试卷，再从题库选题" />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>标题</th><th>类型</th><th>题数</th><th>简历题</th><th>创建时间</th><th className="right">操作</th>
              </tr>
            </thead>
            <tbody>
              {papers.map((p) => (
                <tr key={p.id}>
                  <td><Link to={'/papers/' + p.id}><b>{p.title}</b></Link></td>
                  <td>
                    <span className={'badge ' + (p.kind === 'resume' ? 'purple' : 'blue')}>
                      {p.kind === 'manual' ? '自建卷' : p.kind === 'resume' ? '简历卷' : '随机卷'}
                    </span>
                  </td>
                  <td>{p.question_count}</td>
                  <td>{p.resume_question_count || '—'}</td>
                  <td className="muted">{fmtTime(p.created_at)}</td>
                  <td className="right">
                    <button className="btn sm" onClick={() => navigate('/interview/new?paper=' + p.id)}>开始面试</button>{' '}
                    <button className="btn sm secondary" onClick={() => navigate('/papers/' + p.id)}>详情</button>{' '}
                    <button
                      className="btn sm secondary"
                      title="无电脑/麦克风时，打印此表线下记录回答"
                      onClick={() =>
                        downloadFile(`/api/papers/${p.id}/export_sheet`, `线下面试记录表_${p.title}.pdf`)
                          .catch((e) => setError(e.message))}
                    >🖨 面试记录表</button>{' '}
                    <button className="btn sm ghost-danger" onClick={() => remove(p)}>删除</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {manualTitle !== null && (
        <Modal title="创建空白试卷" onClose={() => setManualTitle(null)}>
          <div className="field"><label htmlFor="manual-title">试卷名称</label>
            <input id="manual-title" className="input" autoFocus value={manualTitle} onChange={(e) => setManualTitle(e.target.value)} />
          </div>
          {error && <div className="alert error">{error}</div>}
          <div className="modal-footer">
            <button className="btn secondary" onClick={() => setManualTitle(null)}>取消</button>
            <button className="btn" disabled={creating || !manualTitle.trim()} onClick={createManual}>创建并前往题库</button>
          </div>
        </Modal>
      )}
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

      {showResume && (
        <ResumePaperModal
          onClose={() => setShowResume(false)}
          onCreated={(paper) => {
            setShowResume(false)
            load()
            navigate('/papers/' + paper.id)
          }}
        />
      )}
    </div>
  )
}
