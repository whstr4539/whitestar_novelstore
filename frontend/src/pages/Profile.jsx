/* 个人中心：资料编辑 | 可点击统计（收藏/在读/评论）| 评论历史 | 角色入口
   设计依据 novel-reading-ui skill：单卡片、hairline 分区、无 emoji */
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  apiBookshelf, apiCancelOrder, apiHistory, apiMyComments, apiMyNovels, apiOrderStatus, apiPayOrder, apiRecharge, apiUpdateProfile, apiWallet,
} from '../api'
import { useAuth } from '../stores/AuthContext'

const RECHARGE_OPTIONS = [6, 30, 50, 100] // 元，汇率 1元=10书币

export default function Profile() {
  const { user, updateUser } = useAuth()
  const navigate = useNavigate()

  const [wallet, setWallet] = useState(null)
  const [shelfCount, setShelfCount] = useState(0)
  const [historyCount, setHistoryCount] = useState(0)
  const [myComments, setMyComments] = useState([])
  const [myNovels, setMyNovels] = useState([])
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState('')

  const [amount, setAmount] = useState(RECHARGE_OPTIONS[1])
  const [rechargeBusy, setRechargeBusy] = useState(false)

  // 评论历史展开
  const [showComments, setShowComments] = useState(false)

  // 编辑资料
  const [editing, setEditing] = useState(false)
  const [editForm, setEditForm] = useState({ nickname: '', email: '' })
  const [saveBusy, setSaveBusy] = useState(false)

  // 模拟支付（三步：下单 → 收银台 → 支付确认）
  const [cashier, setCashier] = useState(null)   // { order_no, amount, coins, pay_url }
  const [paying, setPaying] = useState(false)    // 等待“第三方”处理中
  const [payResult, setPayResult] = useState(null) // { status, balance_after, coins }
  // 支付轮询代次：每开新单/关闭/卸载递增，旧轮询据此停止，避免覆盖新订单
  const payGenRef = useRef(0)

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
      setMyComments(c); setMyNovels(n)
    }).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [user])

  // 卸载时使支付轮询失效，避免卸载后 setState
  useEffect(() => () => { payGenRef.current++ }, [])

  const flash = (m, isErr = false) => {
    setMsg({ text: m, isErr })
    setTimeout(() => setMsg(''), 3000)
  }

  const doRecharge = async () => {
    setRechargeBusy(true)
    try {
      const d = await apiRecharge(amount)      // 第一步：下单（仅创建待支付订单）
      setCashier(d)                            // 进入模拟收银台
    } catch (e) {
      flash(e.response?.data?.detail || '下单失败', true)
    } finally {
      setRechargeBusy(false)
    }
  }

  // 收银台：确认支付（渠道受理，前端轮询订单状态直到回调结果）
  const confirmPay = async () => {
    setPaying(true)
    setPayResult(null)
    const gen = ++payGenRef.current
    try {
      await apiPayOrder(cashier.order_no)          // 受理：立即返回 processing
      // 轮询订单状态（渠道 3 秒后回调，轮询直到终态）
      const poll = async (tries) => {
        if (gen !== payGenRef.current) return       // 已开新单/关闭/卸载，停止旧轮询
        if (tries <= 0) {
          setPayResult({ status: 'failed', detail: '支付结果确认超时，请稍后在充值记录中查看' })
          setPaying(false)
          return
        }
        const d = await apiOrderStatus(cashier.order_no)
        if (d.status === 'success' || d.status === 'failed' || d.status === 'cancelled') {
          if (gen !== payGenRef.current) return
          setPayResult(d)
          setWallet(await apiWallet())
          setPaying(false)
          return
        }
        setTimeout(() => poll(tries - 1), 1200)    // pending：1.2s 间隔继续轮询
      }
      poll(15)                                      // 最多等 18 秒（> 3 秒渠道耗时）
    } catch (e) {
      if (gen !== payGenRef.current) return
      setPayResult({ status: 'failed', detail: e.response?.data?.detail || '支付受理失败' })
      setPaying(false)
    }
  }

  // 收银台：取消支付（即时关单，不走渠道）
  const cancelPay = async () => {
    setPaying(true)
    try {
      const d = await apiCancelOrder(cashier.order_no)
      setPayResult(d)
    } catch {
      setPayResult({ status: 'cancelled' })
    } finally {
      setPaying(false)
    }
  }

  const closeCashier = () => {
    payGenRef.current++                // 使进行中的轮询失效，避免关闭后仍 setState
    setCashier(null)
    setPayResult(null)
    setPaying(false)
  }

  const startEdit = () => {
    setEditForm({ nickname: user.nickname, email: user.email || '' })
    setEditing(true)
  }

  const saveProfile = async () => {
    if (!editForm.nickname.trim()) { flash('昵称不能为空', true); return }
    setSaveBusy(true)
    try {
      const u = await apiUpdateProfile({
        nickname: editForm.nickname.trim(),
        email: editForm.email.trim() || null,
      })
      updateUser(u)
      setEditing(false)
      flash('资料已保存')
    } catch (e) {
      flash(e.response?.data?.detail || '保存失败', true)
    } finally {
      setSaveBusy(false)
    }
  }

  if (!user) return <div className="container empty">请先<Link to="/login">登录</Link></div>

  const roleLabel = user.role === 'admin' ? '管理员' : user.role === 'author' ? '签约作者' : '读者'

  const entries = [
    ...(user.role === 'author' ? [{ label: '写作台', sub: `${myNovels.length} 部作品`, to: '/author' }] : []),
    ...(user.role === 'admin' ? [{ label: '管理后台', sub: '用户 · 作品 · 公告 · 统计', to: '/admin' }] : []),
  ]

  return (
    <div className="container profile page-enter">
      <div className="page-head">
        <h1 className="page-title">个人中心</h1>
      </div>

      {msg && <div className={`alert ${msg.isErr ? 'alert-error' : 'alert-success'}`}>{msg.text}</div>}

      <div className="p-card">
        {/* 资料区 */}
        <section className="p-sec p-user">
          <div className="p-avatar">{user.nickname?.[0] || '书'}</div>
          <div className="p-user-info">
            {editing ? (
              <div className="p-edit">
                <div className="p-edit-row">
                  <label className="label p-edit-label">昵称</label>
                  <input className="field" value={editForm.nickname}
                    onChange={(e) => setEditForm({ ...editForm, nickname: e.target.value })} />
                </div>
                <div className="p-edit-row">
                  <label className="label p-edit-label">邮箱</label>
                  <input className="field" type="email" placeholder="选填"
                    value={editForm.email}
                    onChange={(e) => setEditForm({ ...editForm, email: e.target.value })} />
                </div>
                <div className="p-edit-actions">
                  <button className="btn btn-primary" disabled={saveBusy} onClick={saveProfile}>
                    {saveBusy ? '保存中…' : '保存'}
                  </button>
                  <button className="btn btn-ghost" onClick={() => setEditing(false)}>取消</button>
                </div>
              </div>
            ) : (
              <>
                <div className="p-name-row">
                  <h2 className="p-nickname">{user.nickname}</h2>
                  <span className={`badge ${user.role === 'admin' ? 'badge-vip' : user.role === 'author' ? 'badge-finished' : 'badge-serializing'}`}>
                    {roleLabel}
                  </span>
                  <button className="p-edit-btn" onClick={startEdit}>编辑</button>
                </div>
                <p className="p-sub">@{user.username} · 加入于 {user.created_at?.slice(0, 10)}</p>
                {user.email && <p className="p-sub">{user.email}</p>}
              </>
            )}
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
              {rechargeBusy ? '下单中…' : '充值'}
            </button>
            <span className="p-hint">1 元 = 10 书币 · 模拟支付</span>
          </div>
          <Link to="/bills" className="p-bills-link">
            <span>账单</span>
            <span className="p-bills-arrow">查看 →</span>
          </Link>
        </section>

        {/* 模拟收银台弹层：下单后进入，支付 3 秒回调 */}
        {cashier && (
          <div className="cashier-mask" onClick={closeCashier}>
            <div className="cashier" onClick={(e) => e.stopPropagation()}>
              {!payResult ? (
                <>
                  <h3 className="cashier-title">确认支付</h3>
                  <p className="cashier-order">订单号 {cashier.order_no}</p>
                  <p className="cashier-amount">¥{Number(cashier.amount)} <span className="cashier-coins">= {Number(cashier.coins)} 书币</span></p>
                  <p className="cashier-channel">收款方：星辰书城 · 模拟支付宝收银台</p>
                  {paying ? (
                    <div className="cashier-waiting">
                      <span className="cashier-spinner" />
                      正在连接支付渠道，请稍候（模拟 3 秒）…
                    </div>
                  ) : (
                    <div className="cashier-ops">
                      <button className="btn btn-primary" onClick={confirmPay}>确认支付</button>
                      <button className="btn btn-ghost" onClick={cancelPay}>取消</button>
                    </div>
                  )}
                </>
              ) : (
                <>
                  {payResult.status === 'success' ? (
                    <>
                      <p className="cashier-result cashier-result-ok">支付成功</p>
                      <p className="cashier-detail">到账 {Number(payResult.coins)} 书币，当前余额 {Number(payResult.balance_after)} 书币</p>
                    </>
                  ) : payResult.status === 'failed' ? (
                    <>
                      <p className="cashier-result cashier-result-fail">支付失败</p>
                      <p className="cashier-detail">{payResult.detail || '渠道未完成扣款，请重试'}</p>
                    </>
                  ) : (
                    <>
                      <p className="cashier-result">已取消支付</p>
                      <p className="cashier-detail">订单已关闭，未产生扣款</p>
                    </>
                  )}
                  <div className="cashier-ops">
                    <button className="btn btn-primary" onClick={closeCashier}>完成</button>
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {/* 统计区：可点击跳转 */}
        <section className="p-sec p-stats">
          <button className="p-stat" onClick={() => navigate('/bookshelf')} title="查看我的书架">
            <b>{shelfCount}</b><span>收藏</span>
          </button>
          <button className="p-stat" onClick={() => navigate('/bookshelf?tab=history')} title="查看阅读历史">
            <b>{historyCount}</b><span>在读</span>
          </button>
          <button className={`p-stat ${showComments ? 'p-stat-on' : ''}`}
            onClick={() => setShowComments(!showComments)} title="查看我的评论">
            <b>{myComments.length}</b><span>评论</span>
          </button>
          {user.role === 'author' && (
            <button className="p-stat" onClick={() => navigate('/author')} title="进入写作台">
              <b>{myNovels.length}</b><span>作品</span>
            </button>
          )}
        </section>

        {/* 评论历史（点击"评论"展开） */}
        {showComments && (
          <section className="p-comments">
            {myComments.length === 0 ? (
              <div className="empty">还没有发表过评论</div>
            ) : (
              myComments.map((c) => (
                <Link key={c.id} className="p-comment" to={`/novel/${c.novel_id}`}>
                  <div className="p-comment-head">
                    <span className="p-comment-novel">{c.novel_title}</span>
                    {c.chapter_title && <span className="p-comment-chapter">{c.chapter_title}</span>}
                    <span className="p-comment-time">{new Date(c.created_at).toLocaleDateString()}</span>
                  </div>
                  <p className="p-comment-content">{c.content}</p>
                </Link>
              ))
            )}
          </section>
        )}

        {/* 角色入口 */}
        {entries.length > 0 && (
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
        )}
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
        .p-edit-btn {
          font-size: var(--fs-12);
          color: var(--ink-500);
          border: 1px solid var(--hairline);
          border-radius: 12px;
          padding: 2px 10px;
          transition: border-color var(--ease), color var(--ease);
        }
        .p-edit-btn:hover { border-color: var(--accent); color: var(--accent); }

        /* 编辑表单 */
        .p-edit { display: flex; flex-direction: column; gap: var(--space-3); width: 100%; max-width: 360px; }
        .p-edit-row { display: flex; align-items: center; gap: var(--space-3); }
        .p-edit-label { margin: 0; width: 40px; flex-shrink: 0; }
        .p-edit-actions { display: flex; gap: var(--space-2); }

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
        /* 账单入口 */
        .p-bills-link {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          margin-top: var(--space-4);
          padding-top: var(--space-3);
          border-top: 1px solid var(--hairline);
          font-size: var(--fs-14);
          font-weight: 500;
          color: var(--ink-900);
          transition: color var(--ease);
        }
        .p-bills-link:hover { color: var(--accent); }
        .p-bills-sub { font-size: var(--fs-12); font-weight: 400; color: var(--ink-500); }
        .p-bills-arrow { margin-left: auto; font-size: var(--fs-12); font-weight: 400; color: var(--accent); }
        /* 模拟收银台弹层 */
        .cashier-mask {
          position: fixed;
          inset: 0;
          z-index: 100;
          background: rgba(38, 38, 42, 0.45);
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .cashier {
          width: 360px;
          max-width: calc(100vw - 48px);
          background: var(--paper);
          border-radius: var(--radius-lg);
          padding: var(--space-6);
          box-shadow: var(--shadow-soft), 0 12px 40px rgba(38, 38, 42, 0.18);
          text-align: center;
        }
        .cashier-title { font-size: var(--fs-18); font-weight: 600; margin-bottom: var(--space-3); }
        .cashier-order { font-size: var(--fs-12); color: var(--ink-500); font-variant-numeric: tabular-nums; }
        .cashier-amount {
          font-size: var(--fs-28); font-weight: 700;
          margin: var(--space-4) 0 var(--space-2);
          font-variant-numeric: tabular-nums;
        }
        .cashier-coins { font-size: var(--fs-14); font-weight: 400; color: var(--ink-500); }
        .cashier-channel { font-size: var(--fs-12); color: var(--ink-500); margin-bottom: var(--space-5); }
        .cashier-waiting {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-2);
          font-size: var(--fs-13);
          color: var(--ink-500);
          padding: var(--space-4) 0;
        }
        .cashier-spinner {
          width: 14px; height: 14px;
          border: 2px solid var(--hairline);
          border-top-color: var(--accent);
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .cashier-ops { display: flex; gap: var(--space-3); justify-content: center; }
        .cashier-ops .btn { min-width: 120px; }
        .cashier-result { font-size: var(--fs-18); font-weight: 600; margin-bottom: var(--space-2); }
        .cashier-result-ok { color: var(--success); }
        .cashier-result-fail { color: var(--danger); }
        .cashier-detail { font-size: var(--fs-13); color: var(--ink-500); margin-bottom: var(--space-5); }

        /* 统计区：整体可点击 */
        .p-stats { display: flex; gap: var(--space-7); padding: var(--space-4) var(--space-6); }
        .p-stat {
          text-align: center;
          padding: var(--space-2) var(--space-3);
          border-radius: var(--radius);
          transition: background var(--ease);
        }
        .p-stat:hover { background: #f0efea; }
        .p-stat b {
          display: block;
          font-size: var(--fs-20);
          font-variant-numeric: tabular-nums;
          color: var(--ink-900);
        }
        .p-stat span { font-size: var(--fs-12); color: var(--ink-500); }
        .p-stat-on { background: var(--accent-weak); }
        .p-stat-on span { color: var(--accent-text); }

        /* 评论历史 */
        .p-comments { border-bottom: 1px solid var(--hairline); }
        .p-comment {
          display: block;
          padding: var(--space-4) var(--space-6);
          border-bottom: 1px solid var(--hairline);
          transition: background var(--ease);
        }
        .p-comment:last-child { border-bottom: none; }
        .p-comment:hover { background: #f6f5f1; }
        .p-comment-head { display: flex; align-items: baseline; gap: var(--space-3); margin-bottom: 4px; }
        .p-comment-novel { font-size: var(--fs-13); font-weight: 600; color: var(--accent-text); }
        .p-comment-chapter { font-size: var(--fs-12); color: var(--ink-500); }
        .p-comment-time { font-size: var(--fs-12); color: var(--ink-300); margin-left: auto; }
        .p-comment-content {
          font-size: var(--fs-14);
          color: var(--ink-700);
          line-height: 1.7;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

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
          .p-comment { padding: var(--space-3) var(--space-4); }
        }
      `}</style>
    </div>
  )
}
