// 简历 PDF 拖拽上传区（共享组件）：解析后回调姓名与简历全文
import { useRef, useState } from 'react'
import { API_BASE } from '../api.js'

export default function ResumeDropZone({ onParsed, compact }) {
  const [dragOver, setDragOver] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const inputRef = useRef(null)

  const handleFile = async (file) => {
    if (!file || busy) return
    if (!/\.pdf$/i.test(file.name || '')) {
      setError('只支持 PDF 文件')
      return
    }
    setBusy(true)
    setError('')
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await fetch(API_BASE + '/api/llm/parse_resume_pdf', { method: 'POST', body: fd })
      let data = null
      try {
        data = await res.json()
      } catch {
        /* ignore */
      }
      if (!res.ok || data?.error) throw new Error(data?.error || data?.detail || `上传失败（HTTP ${res.status}）`)
      onParsed(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div
      className={'dropzone' + (dragOver ? ' drag-over' : '') + (busy ? ' busy' : '')}
      style={compact ? { padding: '16px 12px' } : undefined}
      onClick={() => !busy && inputRef.current?.click()}
      onDragOver={(e) => {
        e.preventDefault()
        setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragOver(false)
        handleFile(e.dataTransfer.files?.[0])
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        hidden
        onChange={(e) => {
          handleFile(e.target.files?.[0])
          e.target.value = ''
        }}
      />
      {busy ? (
        <div className="center">
          <span className="spinner dark" style={{ marginRight: 8 }} />
          正在解析 PDF（提取文本 + 识别姓名）…
        </div>
      ) : (
        <div className="center">
          <div style={{ fontSize: compact ? 22 : 28, marginBottom: 6 }}>📄</div>
          <div><b>拖拽简历 PDF 到这里</b>，或点击选择文件</div>
          {!compact && <div className="muted mt">自动提取简历全文与候选人姓名</div>}
        </div>
      )}
      {error && <div className="alert error" style={{ marginTop: 10, marginBottom: 0 }}>{error}</div>}
    </div>
  )
}
