// 麦克风录音控制器：采集 → 线性插值重采样至 16kHz → Int16 PCM → WebSocket 发给后端 ASR 中继
import workletSource from './audio-worklet.js?raw'
import { asrWsUrl } from './api.js'

const TARGET_RATE = 16000
const SEND_SAMPLES = 1600 // 100ms 一包

export class MicRecorder {
  constructor({ onPartial, onError } = {}) {
    this.onPartial = onPartial
    this.onError = onError
    this._ws = null
    this._ctx = null
    this._stream = null
    this._node = null
    this._buf = null
    this._bufStart = 0
    this._pos = 0
    this._sendBuf = new Int16Array(SEND_SAMPLES)
    this._sendLen = 0
    this._finalText = ''
    this._error = null
    this._doneResolve = null
  }

  get recording() {
    return Boolean(this._ws)
  }

  async start({ interviewId, itemId }) {
    if (this._ws) throw new Error('已经在录音中')

    // 1. 连接后端中继
    this._ws = new WebSocket(asrWsUrl())
    this._ws.binaryType = 'arraybuffer'
    await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('连接语音识别服务超时')), 8000)
      this._ws.onopen = () => { clearTimeout(timer); resolve() }
      this._ws.onerror = () => { clearTimeout(timer); reject(new Error('无法连接语音识别服务')) }
    })
    this._ws.onmessage = (ev) => this._onMessage(ev)

    // 2. 打开麦克风
    try {
      this._stream = await navigator.mediaDevices.getUserMedia({
        audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      })
    } catch (e) {
      this._cleanup()
      throw new Error('无法访问麦克风：' + (e.message || e.name))
    }

    // 3. 建立采集链（worklet 以 Blob URL 加载，兼容 vite dev 与 file:// 打包场景）
    this._ctx = new AudioContext()
    const srcRate = this._ctx.sampleRate
    if (!MicRecorder._workletUrl) {
      const blob = new Blob([workletSource], { type: 'application/javascript' })
      MicRecorder._workletUrl = URL.createObjectURL(blob)
    }
    await this._ctx.audioWorklet.addModule(MicRecorder._workletUrl)
    this._node = new AudioWorkletNode(this._ctx, 'pcm-collector')
    this._node.port.onmessage = (e) => this._processChunk(e.data, srcRate)
    this._ctx.createMediaStreamSource(this._stream).connect(this._node)
    this._srcRate = srcRate

    // 4. 通知后端开始（后端去连火山 ASR）
    this._ws.send(JSON.stringify({ type: 'start', interview_id: interviewId, item_id: itemId }))
  }

  _onMessage(ev) {
    let msg
    try {
      msg = JSON.parse(ev.data)
    } catch {
      return
    }
    if (msg.type === 'partial') {
      this.onPartial?.(msg.text || '')
    } else if (msg.type === 'final') {
      this._finalText = msg.text || ''
    } else if (msg.type === 'error') {
      this._error = msg.message || '语音识别出错'
      this.onError?.(this._error)
      this._doneResolve?.()
    } else if (msg.type === 'done') {
      this._doneResolve?.()
    }
  }

  // 线性插值重采样：任意输入采样率 → 16kHz
  _processChunk(chunk, srcRate) {
    if (this._buf === null) {
      this._buf = chunk
      this._bufStart = 0
      this._pos = 0
    } else {
      const merged = new Float32Array(this._buf.length + chunk.length)
      merged.set(this._buf)
      merged.set(chunk, this._buf.length)
      this._buf = merged
    }
    const ratio = srcRate / TARGET_RATE
    const bufEnd = this._bufStart + this._buf.length
    const out = []
    while (this._pos + 1 < bufEnd) {
      const i = Math.floor(this._pos) - this._bufStart
      const t = this._pos - Math.floor(this._pos)
      const s0 = this._buf[i]
      const s1 = this._buf[i + 1]
      out.push(s0 + (s1 - s0) * t)
      this._pos += ratio
    }
    // 保留插值所需的前一个样本
    const keepFrom = Math.floor(this._pos) - 1
    this._buf = this._buf.slice(keepFrom - this._bufStart)
    this._bufStart = keepFrom

    for (let k = 0; k < out.length; k++) {
      const v = Math.max(-1, Math.min(1, out[k]))
      this._sendBuf[this._sendLen++] = v < 0 ? v * 0x8000 : v * 0x7fff
      if (this._sendLen === SEND_SAMPLES) {
        this._send()
        this._sendLen = 0
      }
    }
  }

  _send() {
    if (this._ws && this._ws.readyState === WebSocket.OPEN) {
      const payload = this._sendBuf.buffer.slice(0, this._sendLen * 2)
      this._ws.send(payload)
    }
  }

  async stop() {
    if (!this._ws) return { text: this._finalText, error: this._error }
    // 把余量发出去，再通知结束
    if (this._sendLen > 0) this._send()
    try {
      this._ws.send(JSON.stringify({ type: 'stop' }))
    } catch {
      /* ignore */
    }
    await new Promise((resolve) => {
      this._doneResolve = resolve
      setTimeout(resolve, 12000) // 后端最终结果兜底超时
    })
    this._cleanup()
    return { text: this._finalText, error: this._error }
  }

  cancel() {
    this._cleanup()
  }

  _cleanup() {
    try { this._node?.port && (this._node.port.onmessage = null) } catch { /* ignore */ }
    try { this._stream?.getTracks().forEach((t) => t.stop()) } catch { /* ignore */ }
    try { this._ctx?.close() } catch { /* ignore */ }
    try { this._ws?.close() } catch { /* ignore */ }
    this._node = null
    this._stream = null
    this._ctx = null
    this._ws = null
    this._doneResolve = null
  }
}
