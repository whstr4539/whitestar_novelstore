/* 个人中心：资料卡 | 钱包充值 | 数据统计 | 角色入口 */
import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  apiBookshelf, apiHistory, apiMyComments, apiMyNovels, apiRecharge, apiWallet,
} from '../api'
import { useAuth } from '../stores/AuthContext'

const RECHARGE_OPTIONS = [6, 30, 50, 100] // 元，汇率 1元=10书币

export default function Profile() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const [wallet, setWallet] = useState(null)
  const [shelfCount, setShelfCount] = useState(0)
  const [historyCount, setHistoryCount] = useState(0)
  const [commentCount, setCommentCount] = useState(0)
  const [myNovels, setMyNovels] = useState([])
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState('')

  // 充值
  const [amount, setAmount] = useState(RECHARGE_OPTIONS[1])
  const [rechargeBusy, setRechargeBusy] = useState(false)

  const load = () => {
    setLoading(true)
    Promise.all([
      apiWallet().catch(() => null),
      apiBookshelf().catch(() => ({ items: [] })),
      apiHistory().catch(() => ({ items: [] })),
      apiMyComments().catch(() => []),
      user?.role === 'author' ? apiMyNovels().catch(() => []) : Promise.resolve([]),
    ]).then(([w, s, h, c, n]) => {
      setWallet(w); setShelfCount(s.items.length); setHistoryCount(h.items.length)
      setCommentCount(c.length); setMyNovels(n)
    }).finally(() => setLoading(false))
  }

  useEffect(load, [user])

  const doRecharge = async () => {
    setRechargeBusy(true)
    try {
      const d = await apiRecharge(amount)
      setMsg(`充值成功：到账 ${d.coins} 书币（余额 ${d.balance_after}）`)
      setWallet(await apiWallet())
    } catch (e) {
      setMsg(e.response?.data?.detail || '充值失败')
    } finally {
      setRechargeBusy(false)
      setTimeout(() => setMsg(''), 3000)
    }
  }

  if (!user) return <div className="container empty">请先<a href="/login">登录</a></div>

  const roleLabel = user.role === 'admin' ? '管理员' : user.role === 'author' ? '签约作者' : '读者'

  return (
    <div className="container profile page-enter">
      <div className="page-head">
        <h1 className="page-title">个人中心</h1>
        <span className="page-sub">@ {user.username}</span>
      </div>

      {msg && <div className="alert alert-success">{msg}</div>}

      {/* 资料卡 + 钱包 */}
      <div className="profile-grid">
        <section className="p-card p-user">
          <div className="p-avatar">{user.nickname?.[0] || '书'}</div>
          <div className="p-user-info">
            <h2 className="p-nickname">{user.nickname}</h2>
            <p className="p-username">@{user.username}</p>
            <p className="p-meta">
              <span className={`badge ${user.role === 'admin' ? 'badge-vip' : user.role === 'author' ? 'badge-finished' : 'badge-serializing'}`}>
                {roleLabel}
              </span>
              <span className="p-joined">加入于 {user.created_at?.slice(0, 10)}</span>
            </p>
            {user.email && <p className="p-email">📧 {user.email}</p>}
          </div>
        </section>

        <section className="p-card p-wallet">
          <div className="p-wallet-head">
            <h3 className="p-card-title">书币钱包</h3>
            <Link to="/bookshelf" className="p-link">我的书架 →</Link>
          </div>
          <div className="p-balance">
            <span className="p-balance-num">{wallet ? Number(wallet.balance) : '—'}</span>
            <span className="p-balance-unit">书币</span>
          </div>
          <p className="p-wallet-sub">累计充值 {wallet ? Number(wallet.total_recharged) : '—'} 书币 · 1元 = 10书币</p>
          <div className="p-recharge">
            {RECHARGE_OPTIONS.map((v) => (
              <button key={v}
                className={`btn btn-ghost p-amount ${amount === v ? 'p-amount-on' : ''}`}
                onClick={() => setAmount(v)}>
                ¥{v}
              </button>
            ))}
            <button className="btn btn-primary" onClick={doRecharge} disabled={rechargeBusy}>
              {rechargeBusy ? '处理中…' : '充值'}
            </button>
          </div>
        </section>
      </div>

      {/* 数据统计 */}
      <section className="p-card p-stats">
        <div className="p-stat">
          <b>{shelfCount}</b><span>收藏</span>
        </div>
        <div className="p-stat">
          <b>{historyCount}</b><span>在读</span>
        </div>
        <div className="p-stat">
          <b>{commentCount}</b><span>评论</span>
        </div>
        {user.role === 'author' && (
          <div className="p-stat">
            <b>{myNovels.length}</b><span>作品</span>
          </div>
        )}
      </section>

      {/* 角色入口 */}
      <section className="p-card p-entries">
        <button className="p-entry" onClick={() => navigate('/bookshelf')}>
          <span className="p-entry-icon">📚</span>
          <div><h4>我的书架</h4><p>收藏与阅读历史</p></div>
          <span className="p-entry-arrow">→</span>
        </button>
        {user.role === 'author' && (
          <button className="p-entry" onClick={() => navigate('/author')}>
            <span className="p-entry-icon">✍️</span>
            <div><h4>写作台</h4><p>管理作品 · 发布章节</p></div>
            <span className="p-entry-arrow">→</span>
          </button>
        )}
        {user.role === 'admin' && (
          <button className="p-entry" onClick={() => navigate('/admin')}>
            <span className="p-entry-icon">🛠</span>
            <div><h4>管理后台</h4><p>用户 · 作品 · 公告 · 平台统计</p></div>
            <span className="p-entry-arrow">→</span>
          </button>
        )}
      </section>

      <style>{`
        .profile-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: var(--space-4);
        }
        .p-card {
          background: var(--card);
          border: 1px solid var(--hairline);
          border-radius: var(--radius-lg);
          padding: var(--space-5);
          margin-bottom: var(--space-4);
        }
        .p-user { display: flex; gap: var(--space-5); align-items: flex-start; }
        .p-avatar {
          width: 64px; height: 64px;
          border-radius: 50%;
          background: var(--accent);
          color: #fff;
          font-family: var(--font-serif);
          font-size: var(--fs-22);
          display: flex; align-items: center; justify-content: center;
          flex-shrink: 0;
        }
        .p-nickname { font-size: var(--fs-22); font-weight: 600; margin-bottom: 2px; }
        .p-username { font-size: var(--fs-14); color: var(--ink-500); margin-bottom: var(--space-2); }
        .p-meta { display: flex; align-items: center; gap: var(--space-3); margin-bottom: 4px; }
        .p-joined { font-size: var(--fs-12); color: var(--ink-300); }
        .p-email { font-size: var(--fs-13); color: var(--ink-500); margin-top: 4px; }

        .p-wallet-head { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: var(--space-3); }
        .p-card-title { font-size: var(--fs-16); font-weight: 600; }
        .p-link { font-size: var(--fs-13); color: var(--accent); }
        .p-balance { display: flex; align-items: baseline; gap: 8px; margin-bottom: 4px; }
        .p-balance-num { font-size: 34px; font-weight: 700; font-variant-numeric: tabular-nums; color: var(--ink-900); }
        .p-balance-unit { font-size: var(--fs-14); color: var(--ink-500); }
        .p-wallet-sub { font-size: var(--fs-12); color: var(--ink-300); margin-bottom: var(--space-4); }
        .p-recharge { display: flex; gap: var(--space-2); align-items: center; flex-wrap: wrap; }
        .p-amount { padding: 6px 14px; font-size: var(--fs-13); }
        .p-amount-on { border-color: var(--accent) !important; color: var(--accent) !important; background: var(--accent-weak) !important; }

        .p-stats { display: flex; gap: var(--space-7); }
        .p-stat { text-align: center; }
        .p-stat b { display: block; font-size: var(--fs-22); font-variant-numeric: tabular-nums; }
        .p-stat span { font-size: var(--fs-12); color: var(--ink-500); }

        .p-entries { display: flex; flex-direction: column; padding: 0; overflow: hidden; }
        .p-entry {
          display: flex; align-items: center; gap: var(--space-4);
          padding: var(--space-4) var(--space-5);
          border-bottom: 1px solid var(--hairline);
          text-align: left;
          transition: background var(--ease);
        }
        .p-entry:last-child { border-bottom: none; }
        .p-entry:hover { background: #f6f5f1; }
        .p-entry-icon { font-size: 22px; }
        .p-entry h4 { font-size: var(--fs-15); margin-bottom: 2px; }
        .p-entry p { font-size: var(--fs-12); color: var(--ink-500); }
        .p-entry-arrow { margin-left: auto; color: var(--ink-300); }

        @media (max-width: 768px) {
          .profile-grid { grid-template-columns: 1fr; }
          .p-stats { gap: var(--space-5); }
        }
      `}</style>
    </div>
  )
}
