// 后端 API 客户端（直连本地 Python 服务；Electron 与浏览器开发模式均可用）
const BASE =
  window.localStorage.getItem('api_base') ||
  import.meta.env.VITE_API_BASE ||
  'http://127.0.0.1:18742'

export const API_BASE = BASE

async function request(method, path, body) {
  const opts = { method, headers: {} }
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  }
  let res
  try {
    res = await fetch(BASE + path, opts)
  } catch (e) {
    throw new Error('无法连接后端服务，请确认 Python 后端已启动（' + e.message + '）')
  }
  let data = null
  try {
    data = await res.json()
  } catch {
    /* 无 body */
  }
  if (!res.ok) {
    const detail = data && (typeof data.detail === 'string' ? data.detail : data.error || data.detail?.[0]?.msg)
    throw new Error(detail || `请求失败（HTTP ${res.status}）`)
  }
  return data
}

export const api = {
  get: (p) => request('GET', p),
  post: (p, body) => request('POST', p, body),
  put: (p, body) => request('PUT', p, body),
  del: (p) => request('DELETE', p),
}

export function asrWsUrl() {
  return BASE.replace(/^http/, 'ws') + '/ws/asr'
}

// ---------- 领域常量 ----------
export const SECTIONS = ['基础', '应用', '简历']
export const DIFFICULTIES = ['简单', '中等', '困难']
export const FREQUENCIES = ['高频', '中频', '低频']
export const FREQ_BADGE = { 高频: 'red', 中频: 'orange', 低频: 'gray' }
export const SECTION_FULL = { 基础: 40, 应用: 30, 简历: 30 }

export const STATE_TEXT = {
  pending: '未问',
  answered: '已回答',
  unknown: '不会',
  unasked: '未问',
}
export const STATE_BADGE = {
  pending: 'gray',
  answered: 'green',
  unknown: 'red',
  unasked: 'gray',
}
