import { useEffect, useState } from 'react'
import { api } from '../api.js'


// 密钥输入框：默认掩码显示，可切换明文
function KeyInput({ value, onChange, placeholder }) {
  const [show, setShow] = useState(false)
  return (
    <div className="row" style={{ gap: 6 }}>
      <input
        className="input grow"
        type={show ? 'text' : 'password'}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        autoComplete="new-password"
      />
      <button type="button" className="btn sm secondary" onClick={() => setShow(!show)}>
        {show ? '隐藏' : '显示'}
      </button>
    </div>
  )
}

export default function Settings() {
  const [cfg, setCfg] = useState(null)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [testing, setTesting] = useState('')

  useEffect(() => {
    api.get('/api/settings').then(setCfg).catch((e) => setMessage(e.message))
  }, [])

  if (!cfg) return <div className="empty">{message || '加载中…'}</div>

  const setAsr = (k) => (e) => setCfg({ ...cfg, asr: { ...cfg.asr, [k]: e.target.value } })
  const setArk = (k) => (e) => setCfg({ ...cfg, ark: { ...cfg.ark, [k]: e.target.value } })

  const save = async () => {
    setSaving(true)
    setMessage('')
    try {
      const saved = await api.put('/api/settings', {
        python_cmd: cfg.python_cmd,
        asr: cfg.asr,
        ark: cfg.ark,
        judge_mode: cfg.judge_mode,
        llm_mock: cfg.llm_mock,
      })
      if (saved.error) throw new Error(saved.error)
      setCfg(saved)
      setMessage('已保存')
    } catch (e) {
      setMessage('保存失败：' + e.message)
    } finally {
      setSaving(false)
      setTimeout(() => setMessage((m) => (m === '已保存' ? '' : m)), 2000)
    }
  }

  const testArk = async () => {
    setTesting('ark')
    try {
      // 先保存当前编辑中的配置再测试
      const saved = await api.put('/api/settings', { ark: cfg.ark, llm_mock: cfg.llm_mock })
      setCfg(saved)
      const r = await api.post('/api/settings/test_ark')
      setMessage(r.ok ? '✅ ' + r.message : '❌ ' + r.message)
    } catch (e) {
      setMessage('❌ ' + e.message)
    } finally {
      setTesting('')
    }
  }

  const testAsr = async () => {
    setTesting('asr')
    try {
      const saved = await api.put('/api/settings', { asr: cfg.asr })
      setCfg(saved)
      const r = await api.post('/api/settings/test_asr')
      setMessage(r.ok ? '✅ ' + r.message : '❌ ' + r.message)
    } catch (e) {
      setMessage('❌ ' + e.message)
    } finally {
      setTesting('')
    }
  }

  return (
    <div>
      <h1 className="page-title">系统设置</h1>
      <p className="page-sub">
        凭据可写入项目根目录 <code className="inline">.env</code>（模板见 .env.example），此处留空时自动读取；
        在此页面填写并保存的值优先生效
      </p>
      {message && <div className={message.startsWith('✅') ? 'alert info' : 'alert error'}>{message}</div>}

      <div className="settings-grid">
        <div className="card">
          <div className="card-title">🎙️ 语音识别（火山引擎流式 ASR）</div>
          <div className="col">
            <div className="field">
              <label>App ID（旧版控制台）</label>
              <input className="input" value={cfg.asr.app_id} onChange={setAsr('app_id')} placeholder="控制台应用 ID" />
            </div>
            <div className="field">
              <label>Access Token（旧版控制台，与 AppID 搭配）</label>
              <KeyInput value={cfg.asr.access_token} onChange={setAsr('access_token')} />
            </div>
            <div className="field">
              <label>API Key（新版控制台，二选一即可）</label>
              <KeyInput value={cfg.asr.api_key} onChange={setAsr('api_key')} />
            </div>
            <div className="field">
              <label>Resource ID</label>
              <input className="input" value={cfg.asr.resource_id} onChange={setAsr('resource_id')} />
            </div>
            <div className="kv-hint">
              豆包语音大模型控制台获取；<code className="inline">volc.bigasr.sauc.duration</code> 为时长版资源 ID。
            </div>
            <button className="btn secondary" onClick={testAsr} disabled={testing === 'asr'}>
              {testing === 'asr' ? '测试中…' : '测试 ASR 连接'}
            </button>
          </div>
        </div>

        <div className="card">
          <div className="card-title">🤖 大模型（火山方舟）</div>
          <div className="col">
            <div className="field">
              <label>API Key *</label>
              <KeyInput value={cfg.ark.api_key} onChange={setArk('api_key')} placeholder="方舟 API Key" />
            </div>
            <div className="field">
              <label>模型 ID / Endpoint</label>
              <input className="input" value={cfg.ark.model} onChange={setArk('model')} placeholder="如 doubao-seed-1-6-250615 或 ep-2024xxxx" />
            </div>
            <div className="field">
              <label>Base URL</label>
              <input className="input" value={cfg.ark.base_url} onChange={setArk('base_url')} />
            </div>
            <div className="kv-hint">
              在方舟控制台「在线推理 / API Key 管理」创建；模型需先开通推理接入点。
            </div>
            <button className="btn secondary" onClick={testArk} disabled={testing === 'ark'}>
              {testing === 'ark' ? '测试中…' : '测试方舟连接'}
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">评分与其他</div>
        <div className="form-grid">
          <div className="field">
            <label>评分模式</label>
            <select className="select" value={cfg.judge_mode} onChange={(e) => setCfg({ ...cfg, judge_mode: e.target.value })}>
              <option value="per_question">逐题评判（默认，进度可见、可中断恢复）</option>
              <option value="whole_paper">整卷评判（一次提交全部问答）</option>
            </select>
            <span className="muted">两种模式的准确性可比对测试后自行选择</span>
          </div>
          <div className="field">
            <label>Mock 模式（无密钥联调）</label>
            <label className="row" style={{ gap: 6 }}>
              <input type="checkbox" checked={cfg.llm_mock} onChange={(e) => setCfg({ ...cfg, llm_mock: e.target.checked })} />
              <span className="small">LLM 调用返回模拟评分（按回答长度），不请求方舟</span>
            </label>
          </div>
          <div className="field">
            <label>Python 命令（Electron 启动后端用，留空自动检测）</label>
            <input className="input" value={cfg.python_cmd} onChange={(e) => setCfg({ ...cfg, python_cmd: e.target.value })} placeholder="默认 python；也可填 venv 绝对路径" />
          </div>
        </div>
      </div>

      <button className="btn" onClick={save} disabled={saving}>{saving ? '保存中…' : '💾 保存设置'}</button>
    </div>
  )
}
