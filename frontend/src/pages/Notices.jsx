/* 公告列表：读者可查看全部站内公告（置顶不分页，按时间倒序） */
import { useEffect, useState } from 'react'
import { apiNotices } from '../api'

export default function Notices() {
  const [notices, setNotices] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiNotices().then(setNotices).catch(() => setNotices([])).finally(() => setLoading(false))
  }, [])

  const fmtDate = (s) => new Date(s).toLocaleString('zh-CN', {
    year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })

  return (
    <div className="container page-enter notices-page">
      <div className="page-head">
        <h1 className="page-title">公告</h1>
        <span className="page-sub">站内公告与系统通知</span>
      </div>

      {loading ? (
        <div className="empty">加载中…</div>
      ) : notices.length === 0 ? (
        <div className="empty">暂无公告</div>
      ) : (
        notices.map((n) => (
          <article key={n.id} className="notice-item">
            <div className="notice-head">
              <h2 className="notice-title">{n.title}</h2>
              <time className="notice-time">{fmtDate(n.created_at)}</time>
            </div>
            <p className="notice-content">{n.content}</p>
          </article>
        ))
      )}

      <style>{`
        .notices-page { max-width: 720px; }
        .notice-item {
          background: var(--card);
          border: 1px solid var(--hairline);
          border-radius: var(--radius);
          padding: var(--space-4) var(--space-5);
          margin-bottom: var(--space-4);
        }
        .notice-head {
          display: flex;
          align-items: baseline;
          justify-content: space-between;
          gap: var(--space-4);
          padding-bottom: var(--space-3);
          border-bottom: 1px solid var(--hairline);
          margin-bottom: var(--space-3);
        }
        .notice-title {
          font-size: var(--fs-16);
          font-weight: 600;
          color: var(--ink-900);
          letter-spacing: 0.02em;
        }
        .notice-time {
          font-size: var(--fs-12);
          color: var(--ink-300);
          white-space: nowrap;
          font-variant-numeric: tabular-nums;
        }
        .notice-content {
          font-size: var(--fs-14);
          line-height: 1.9;
          color: var(--ink-700);
          white-space: pre-wrap;
        }
      `}</style>
    </div>
  )
}
