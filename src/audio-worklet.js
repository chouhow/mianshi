// AudioWorklet 采集处理器：聚合 128 采样量子，约 4096 采样（~85ms@48k）回传一次 Float32
class PcmCollector extends AudioWorkletProcessor {
  constructor() {
    super()
    this._chunks = []
    this._len = 0
  }

  process(inputs) {
    const ch = inputs[0] && inputs[0][0]
    if (ch) {
      this._chunks.push(new Float32Array(ch))
      this._len += ch.length
      if (this._len >= 4096) {
        const out = new Float32Array(this._len)
        let off = 0
        for (const c of this._chunks) {
          out.set(c, off)
          off += c.length
        }
        this._chunks = []
        this._len = 0
        this.port.postMessage(out, [out.buffer])
      }
    }
    return true
  }
}

registerProcessor('pcm-collector', PcmCollector)
