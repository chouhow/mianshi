// 极简 hash 路由 + 通用小组件
import { useEffect, useState } from 'react'

export function parseRoute() {
  const raw = (window.location.hash || '#/questions').replace(/^#/, '')
  const [path, queryStr] = raw.split('?')
  const query = Object.fromEntries(new URLSearchParams(queryStr || ''))
  return { path, parts: path.split('/').filter(Boolean), query }
}

export function useRoute() {
  const [route, setRoute] = useState(parseRoute)
  useEffect(() => {
    const onChange = () => setRoute(parseRoute())
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])
  return route
}

export function navigate(to) {
  window.location.hash = to
}

export function Link({ to, children, className = '' }) {
  return (
    <a
      href={'#' + to}
      className={className}
      onClick={(e) => {
        e.preventDefault()
        navigate(to)
      }}
    >
      {children}
    </a>
  )
}

export function Modal({ title, children, onClose, width }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose?.()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])
  return (
    <div className="modal-overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose?.()}>
      <div className="modal" style={width ? { width } : undefined}>
        {title && <h3>{title}</h3>}
        {children}
      </div>
    </div>
  )
}

export function Spinner({ dark }) {
  return <span className={'spinner' + (dark ? ' dark' : '')} />
}

export function Empty({ text = '暂无数据' }) {
  return <div className="empty">{text}</div>
}

export function fmtTime(iso) {
  if (!iso) return '-'
  return iso.replace('T', ' ')
}
