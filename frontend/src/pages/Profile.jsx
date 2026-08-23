/* 个人中心：克制简约 —— 单卡片 + hairline 分区
   设计依据 novel-reading-ui skill：无 emoji、无花哨图标、文字信息优先 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
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

  useEffect(() => { load() }, [user])

  const doRecharge = async () => {
    setRechargeBusy(true)
    try {
      const d = await apiRecharge(amount)
      setMsg(`充值成功：到账 ${d.coins} 书币，当前余额 ${d.balance_after}`)
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

  const entries = [
    { label: '我的书架', sub: `${shelfCount} 本收藏`, to: '/bookshelf' },
    { label: '阅读历史', sub: `${historyCount} 本在读`, to: '/bookshelf?tab=history' },
    ...(user.role === 'author' ? [{ label: '写作台', sub: `${myNovels.length} 部作品`, to: '/author' }] : []),
    ...(user.role === 'admin' ? [{ label: '管理后台', sub: '用户 · 作品 · 公告 · 统计', to: '/admin' }] : []),
  ]

  return (
    <div className="container profile page-enter">
      <div className="page-head">
        <h1 className="page-title">个人中心</h1>
        <span className="page-sub">@{user.username}</span>
      </div>

      {msg && <div className="alert alert-success">{msg}</div>}

      <div className="p-card">
        {/* 资料区 */}
        <section className="p-sec p-user">
          <div className="p-avatar">{user.nickname?.[0] || '书'}</div>
          <div className="p-user-info">
            <div className="p-name-row">
              <h2 className="p-nickname">{user.nickname}</h2>
              <span className={`badge ${user.role === 'admin' ? 'badge-vip' : user.role === 'author' ? 'badge-finished' : 'badge-serializing'}`}>
                {roleLabel}
              </span>
            </div>
            <p className="p-sub">@{user.username} · 加入于 {user.created_at?.slice(0, 10)}</p>
            {user.email && <p className="p-sub">{user.email}</p>}
          </div>
        </section>

        {/* 钱包区 */}
        <section className="p-sec p-wallet">
          <div className="p-wallet-head">
            <span className="p-sec-title">书币钱包</span>
            <span className="p-wallet-total">累计充值 {wallet ? Number(wallet.total_recharged) : '—'} 书币</span>
          </div>
          <div className="p-balance">
            <span className="p-balance-num">{wallet ? Number(wallet.balance) : '—'}</span>
            <span className="p-balance-unit">书币</span>
          </div>
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
            <span className="p-hint">1 元 = 10 书币</span>
          </div>
        </section>

        {/* 统计区 */}
        <section className="p-sec p-stats">
          <div className="p-stat"><b>{shelfCount}</b><span>收藏</span></div>
          <div className="p-stat"><b>{historyCount}</b><span>在读</span></div>
          <div className="p-stat"><b>{commentCount}</b><span>评论</span></div>
          {user.role === 'author' && <div className="p-stat"><b>{myNovels.length}</b><span>作品</span></div>}
        </section>

        {/* 入口区 */}
        <section className="p-entries">
          {entries.map((e) => (
            <button key={e.label} className="p-entry" onClick={() => navigate(e.to)}>
              <div className="p-entry-text">
                <span className="p-entry-label">{e.label}</span>
                <span className="p-entry-sub">{e.sub}</span>
              </div>
              <span className="p-entry-arrow">→</span>
            </button>
          ))}
        </section>
      </div>

      <style>{`
        /* 单卡片布局 */
        .p-card {
          max-width: 640px;
          background: var(--card);
          border: 1px solid var(--hairline);
          border-radius: var(--radius-lg);
          overflow: hidden;
          margin-bottom: var(--space-8);
        }
        /* hairline 分区 */
        .p-sec {
          padding: var(--space-5) var(--space-6);
          border-bottom: 1px solid var(--hairline);
        }
        .p-sec:last-child { border-bottom: none; }

        /* 资料区 */
        .p-user { display: flex; gap: var(--space-5); align-items: center; }
        .p-avatar {
          width: 56px; height: 56px;
          border-radius: 50%;
          background: var(--accent);
          color: #fff;
          font-family: var(--font-serif);
          font-size: var(--fs-22);
          display: flex; align-items: center; justify-content: center;
          flex-shrink: 0;
        }
        .p-name-row { display: flex; align-items: center; gap: var(--space-3); margin-bottom: 4px; }
        .p-nickname { font-size: var(--fs-22); font-weight: 600; }
        .p-sub { font-size: var(--fs-13); color: var(--ink-500); margin-top: 2px; }

        /* 钱包区 */
        .p-wallet-head {
          display: flex;
          align-items: baseline;
          justify-content: space-between;
          margin-bottom: var(--space-3);
        }
        .p-sec-title { font-size: var(--fs-15); font-weight: 600; color: var(--ink-900); }
        .p-wallet-total { font-size: var(--fs-12); color: var(--ink-300); }
        .p-balance { display: flex; align-items: baseline; gap: 8px; margin-bottom: var(--space-4); }
        .p-balance-num {
          font-size: 36px;
          font-weight: 700;
          font-variant-numeric: tabular-nums;
          letter-spacing: -0.02em;
        }
        .p-balance-unit { font-size: var(--fs-13); color: var(--ink-500); }
        .p-recharge { display: flex; gap: var(--space-2); align-items: center; flex-wrap: wrap; }
        .p-amount { padding: 6px 16px; font-size: var(--fs-13); font-variant-numeric: tabular-nums; }
        .p-amount-on {
          border-color: var(--accent) !important;
          color: var(--accent) !important;
          background: var(--accent-weak) !important;
        }
        .p-hint { font-size: var(--fs-12); color: var(--ink-300); margin-left: var(--space-2); }

        /* 统计区 */
        .p-stats { display: flex; gap: var(--space-7); padding: var(--space-4) var(--space-6); }
        .p-stat { text-align: center; }
        .p-stat b {
          display: block;
          font-size: var(--fs-20);
          font-variant-numeric: tabular-nums;
          color: var(--ink-900);
        }
        .p-stat span { font-size: var(--fs-12); color: var(--ink-500); }

        /* 入口区：纯文字列表行 */
        .p-entries { padding: 0; }
        .p-entry {
          display: flex;
          align-items: center;
          justify-content: space-between;
          width: 100%;
          padding: var(--space-4) var(--space-6);
          border-bottom: 1px solid var(--hairline);
          text-align: left;
          transition: background var(--ease);
        }
        .p-entry:last-child { border-bottom: none; }
        .p-entry:hover { background: #f6f5f1; }
        .p-entry-text { display: flex; flex-direction: column; gap: 2px; }
        .p-entry-label { font-size: var(--fs-15); color: var(--ink-900); }
        .p-entry-sub { font-size: var(--fs-12); color: var(--ink-500); }
        .p-entry-arrow { color: var(--ink-300); font-size: var(--fs-14); transition: transform var(--ease); }
        .p-entry:hover .p-entry-arrow { transform: translateX(3px); color: var(--accent); }

        @media (max-width: 768px) {
          .p-sec { padding: var(--space-4); }
          .p-stats { padding: var(--space-3) var(--space-4); gap: var(--space-5); }
          .p-entry { padding: var(--space-3) var(--space-4); }
        }
      `}</style>
    </div>
  )
}
