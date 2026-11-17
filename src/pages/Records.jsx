import { useCallback, useEffect, useState } from 'react'
import { api } from '../api.js'
import { Empty, Link, fmtTime } from '../ui.jsx'

const STATUS = {
  ongoing: { text: '进行中', badge: 'blue' },
  finished: { text: '已完成', badge: 'green' },
  scoring: { text: '已完成', badge: 'green' },
  scored: { text: '已完成', badge: 'green' },
  score_error: { text: '已完成', badge: 'green' },
}

export default function Records() {
  const [rows, setRows] = useState(null)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      const data = await api.get('/api/interviews')
      setRows(data.interviews)
      setError('')
    } catch (e) {
      setError(e.message)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const remove = async (r) => {
    if (!window.confirm(`确定删除「${r.candidate_name}」的面试记录？（录音文件保留）`)) return
    await api.del('/api/interviews/' + r.id)
    await load()
  }

  return (
    <div>
      <h1 className="page-title">面试记录</h1>
      <p className="page-sub">历史面试与面试报告</p>
      {error && <div className="alert error">{error}</div>}

      <div className="card" style={{ padding: 0 }}>
        {rows === null ? (
          <Empty text="加载中…" />
        ) : rows.length === 0 ? (
          <Empty text="暂无面试记录，从试卷页「开始面试」创建" />
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>候选人</th><th>试卷</th><th>状态</th><th>已答/不会/未问</th><th>面试时间</th><th className="right">操作</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const st = STATUS[r.status] || { text: r.status, badge: 'gray' }
                return (
                  <tr key={r.id}>
                    <td><b>{r.candidate_name}</b></td>
                    <td>{r.paper_title}</td>
                    <td><span className={'badge ' + st.badge}>{st.text}</span></td>
                    <td className="muted">{r.answered} / {r.unknown} / {r.total_items - r.answered - r.unknown}</td>
                    <td className="muted">{fmtTime(r.created_at)}</td>
                    <td className="right">
                      {r.status === 'ongoing' ? (
                        <Link to={'/interview/run/' + r.id} className="btn sm">继续面试</Link>
                      ) : (
                        <Link to={'/interview/report/' + r.id} className="btn sm secondary">报告</Link>
                      )}{' '}
                      <button className="btn sm ghost-danger" onClick={() => remove(r)}>删除</button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
