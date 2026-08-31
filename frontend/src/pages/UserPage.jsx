/* 用户公开主页：头像 | 基本信息 | 创作统计
   从评论/评分/打赏的用户昵称点入，无需登录即可查看 */
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { apiUserProfile } from '../api'

export default function UserPage() {
  const { userId } = useParams()
  const [u, setU] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    apiUserProfile(userId)
      .then(setU)
      .catch(() => setU(null))
      .finally(() => setLoading(false))
  }, [userId])

  if (loading) return <div className="container page-enter"><div className="empty">加载中…</div></div>
  if (!u) return <div className="container page-enter"><div className="empty">用户不存在或已被封禁</div></div>

  const roleName = { admin: '管理员', author: '作者', reader: '读者' }[u.role] || '读者'

  return (
    <div className="container page-enter user-page">
      <div className="user-card">
        <div className="user-card-head">
          <div className="user-avatar">
            {u.avatar ? <img src={u.avatar} alt="头像" /> : (u.nickname || u.username).slice(0, 1)}
          </div>
          <div className="user-card-info">
            <h1 className="user-name">{u.nickname || u.username}</h1>
            <p className="user-meta">
              <span className={`badge badge-role badge-${u.role}`}>{roleName}</span>
              <span className="user-meta-item">@{u.username}</span>
              {u.created_at && (
                <span className="user-meta-item">注册于 {new Date(u.created_at).toLocaleDateString()}</span>
              )}
            </p>
          </div>
        </div>

        <div className="user-stats">
          <div className="user-stat">
            <b>{u.novel_count ?? 0}</b>
            <span>创作作品</span>
          </div>
          <div className="user-stat">
            <b>{u.author_total_views ?? 0}</b>
            <span>作品总点击</span>
          </div>
        </div>
      </div>

      <style>{`
        .user-page { max-width: 720px; }
        .user-card {
          background: var(--card);
          border: 1px solid var(--hairline);
          border-radius: var(--radius);
          padding: var(--space-6);
        }
        .user-card-head { display: flex; gap: var(--space-5); align-items: center; }
        .user-avatar {
          width: 72px; height: 72px; border-radius: 50%;
          background: var(--accent-weak);
          color: var(--accent);
          font-size: var(--fs-28); font-weight: 600;
          display: flex; align-items: center; justify-content: center;
          overflow: hidden; flex-shrink: 0;
        }
        .user-avatar img { width: 100%; height: 100%; object-fit: cover; }
        .user-name { font-family: var(--font-serif); font-size: var(--fs-22); margin-bottom: var(--space-2); }
        .user-meta { display: flex; align-items: center; gap: var(--space-3); flex-wrap: wrap; }
        .user-meta-item { font-size: var(--fs-12); color: var(--ink-500); }
        .badge-role { font-size: var(--fs-12); }
        .badge-admin { color: var(--danger); border: 1px solid var(--danger); }
        .badge-author { color: var(--accent); border: 1px solid var(--accent); }
        .badge-reader { color: var(--ink-500); border: 1px solid var(--ink-300); }
        .user-stats {
          display: flex; gap: var(--space-6);
          margin-top: var(--space-5); padding-top: var(--space-5);
          border-top: 1px solid var(--hairline);
        }
        .user-stat { display: flex; flex-direction: column; gap: 2px; }
        .user-stat b { font-size: var(--fs-20); font-variant-numeric: tabular-nums; }
        .user-stat span { font-size: var(--fs-12); color: var(--ink-500); }
      `}</style>
    </div>
  )
}
