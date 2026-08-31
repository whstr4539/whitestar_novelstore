/* 管理后台（仅管理员）：概览 | 用户 | 作品 | 公告 */
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  apiAdminComments, apiAdminNovels, apiAdminSetNovelStatus, apiAdminSetUserStatus, apiAdminStats,
  apiAdminUsers, apiCreateNotice, apiDeleteComment, apiDeleteNotice, apiNotices,
} from '../api'
import { useAuth } from '../stores/AuthContext'

export default function Admin() {
  const { user } = useAuth()
  const [tab, setTab] = useState('stats')
  const [msg, setMsg] = useState('')

  const flash = (m, isErr = false) => {
    setMsg({ text: m, isErr })
    setTimeout(() => setMsg(''), 3000)
  }

  if (!user || user.role !== 'admin') {
    return (
      <div className="container empty">
        无权访问管理后台
        {!user && <span>，<Link to="/login">先登录</Link></span>}
      </div>
    )
  }

  return (
    <div className="container page-enter">
      <div className="page-head">
        <h1 className="page-title">管理后台</h1>
        <span className="page-sub">平台运营控制台</span>
      </div>

      {msg && <div className={`alert ${msg.isErr ? 'alert-error' : 'alert-success'}`}>{msg.text}</div>}

      <div className="admin-tabs">
        {[['stats', '概览'], ['users', '用户管理'], ['novels', '作品管理'], ['comments', '评论管理'], ['notices', '公告管理']].map(([k, label]) => (
          <button key={k} className={`tab ${tab === k ? 'tab-active' : ''}`} onClick={() => setTab(k)}>{label}</button>
        ))}
      </div>

      {tab === 'stats' && <StatsTab />}
      {tab === 'users' && <UsersTab flash={flash} />}
      {tab === 'novels' && <NovelsTab flash={flash} />}
      {tab === 'comments' && <CommentsTab flash={flash} />}
      {tab === 'notices' && <NoticesTab flash={flash} />}

      <style>{`
        .admin-tabs {
          display: flex;
          gap: var(--space-5);
          border-bottom: 1px solid var(--hairline);
          margin-bottom: var(--space-4);
        }
        .tab {
          padding: 12px 2px;
          font-size: var(--fs-15);
          color: var(--ink-500);
          border-bottom: 2px solid transparent;
          margin-bottom: -1px;
          transition: color var(--ease), border-color var(--ease);
        }
        .tab-active { color: var(--accent); border-bottom-color: var(--accent); font-weight: 600; }
        .admin-table-wrap {
          background: var(--card);
          border: 1px solid var(--hairline);
          border-radius: var(--radius-lg);
          overflow-x: auto;
        }
        .admin-table { width: 100%; border-collapse: collapse; font-size: var(--fs-14); min-width: 640px; }
        .admin-table th {
          text-align: left;
          padding: 12px 16px;
          font-size: var(--fs-12);
          color: var(--ink-500);
          font-weight: 500;
          border-bottom: 1px solid var(--hairline);
          white-space: nowrap;
        }
        .admin-table td {
          padding: 12px 16px;
          border-bottom: 1px solid var(--hairline);
          color: var(--ink-700);
          white-space: nowrap;
        }
        .admin-table tr:last-child td { border-bottom: none; }
        .admin-table tr:hover td { background: #faf9f6; }
        .admin-search {
          display: flex;
          gap: var(--space-3);
          margin-bottom: var(--space-4);
          max-width: 480px;
        }
        .admin-search .field { flex: 1; }
        .op-btn { font-size: var(--fs-13); padding: 4px 12px; border-radius: 4px; }
        .op-ban { color: var(--danger); border: 1px solid var(--hairline); }
        .op-ban:hover { border-color: var(--danger); }
        .op-ok { color: var(--success); border: 1px solid var(--hairline); }
        .op-ok:hover { border-color: var(--success); }
        .st-banned { color: var(--danger); }
        .st-serializing { color: var(--accent); }
        .st-finished { color: var(--success); }
      `}</style>
    </div>
  )
}

/* ---------- 概览 ---------- */
function StatsTab() {
  const [stats, setStats] = useState(null)
  useEffect(() => { apiAdminStats().then(setStats).catch(() => {}) }, [])

  const cards = stats ? [
    ['注册用户', stats.user_count, '人'],
    ['签约作者', stats.author_count, '人'],
    ['作品总数', stats.novel_count, '本'],
    ['章节总数', stats.chapter_count, '章'],
    ['累计点击', stats.total_views, '次'],
    ['订阅收入', stats.total_revenue, '书币'],
    ['充值总额', stats.total_recharges, '元'],
  ] : []

  return (
    <div>
      {!stats ? (
        <div className="skeleton" style={{ height: 160 }} />
      ) : (
        <div className="stats-grid">
          {cards.map(([label, value, unit]) => (
            <div key={label} className="stat-card">
              <span className="stat-label">{label}</span>
              <span className="stat-value">{value} <small>{unit}</small></span>
            </div>
          ))}
          <style>{`
            .stats-grid {
              display: grid;
              grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
              gap: var(--space-4);
            }
            .stat-card {
              background: var(--card);
              border: 1px solid var(--hairline);
              border-radius: var(--radius-lg);
              padding: var(--space-5);
            }
            .stat-label { display: block; font-size: var(--fs-13); color: var(--ink-500); margin-bottom: var(--space-2); }
            .stat-value { font-size: 28px; font-weight: 700; font-variant-numeric: tabular-nums; }
            .stat-value small { font-size: var(--fs-13); font-weight: 400; color: var(--ink-500); }
          `}</style>
        </div>
      )}
    </div>
  )
}

/* ---------- 用户管理 ---------- */
function UsersTab({ flash }) {
  const [users, setUsers] = useState([])
  const [total, setTotal] = useState(0)
  const [keyword, setKeyword] = useState('')
  const [page, setPage] = useState(1)

  const load = (kw = keyword, pg = page) => {
    apiAdminUsers({ keyword: kw || undefined, page: pg, page_size: 10 })
      .then((d) => { setUsers(d.items); setTotal(d.total) })
      .catch(() => {})
  }
  useEffect(() => { load() }, []) // eslint-disable-line

  const toggleBan = async (u) => {
    try {
      const d = await apiAdminSetUserStatus(u.id, u.status === 1 ? 0 : 1)
      flash(d.detail)
      load()
    } catch (e) { flash(e.response?.data?.detail || '操作失败', true) }
  }

  return (
    <div>
      <div className="admin-search">
        <input className="field" placeholder="搜索用户名 / 昵称"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (setPage(1), load(keyword, 1))} />
        <button className="btn btn-ghost" onClick={() => (setPage(1), load(keyword, 1))}>搜索</button>
      </div>

      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr><th>ID</th><th>用户名</th><th>昵称</th><th>角色</th><th>状态</th><th>注册时间</th><th>操作</th></tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.id}</td>
                <td>{u.username}</td>
                <td>{u.nickname}</td>
                <td>{u.role === 'admin' ? '管理员' : u.role === 'author' ? '作者' : '读者'}</td>
                <td className={u.status === 1 ? 'st-serializing' : 'st-banned'}>
                  {u.status === 1 ? '正常' : '已封禁'}
                </td>
                <td>{u.created_at?.slice(0, 10)}</td>
                <td>
                  <button className={`btn op-btn ${u.status === 1 ? 'op-ban' : 'op-ok'}`}
                    onClick={() => toggleBan(u)}>
                    {u.status === 1 ? '封禁' : '解封'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination page={page} total={total} pageSize={10}
        onChange={(p) => (setPage(p), load(keyword, p))} />
    </div>
  )
}

/* ---------- 作品管理 ---------- */
function NovelsTab({ flash }) {
  const [novels, setNovels] = useState([])
  const [total, setTotal] = useState(0)
  const [keyword, setKeyword] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [page, setPage] = useState(1)

  const load = (kw = keyword, st = statusFilter, pg = page) => {
    apiAdminNovels({
      keyword: kw || undefined, status: st || undefined, page: pg, page_size: 10,
    }).then((d) => { setNovels(d.items); setTotal(d.total) }).catch(() => {})
  }
  useEffect(() => { load() }, []) // eslint-disable-line

  const setStatus = async (n, s) => {
    try {
      const d = await apiAdminSetNovelStatus(n.id, s)
      flash(d.detail)
      load()
    } catch (e) { flash(e.response?.data?.detail || '操作失败', true) }
  }

  return (
    <div>
      <div className="admin-search">
        <input className="field" placeholder="搜索书名"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (setPage(1), load(keyword, statusFilter, 1))} />
        <select className="field" style={{ maxWidth: 130 }}
          value={statusFilter} onChange={(e) => (setStatusFilter(e.target.value), setPage(1), load(keyword, e.target.value, 1))}>
          <option value="">全部状态</option>
          <option value="serializing">连载中</option>
          <option value="finished">已完结</option>
          <option value="banned">已下架</option>
        </select>
        <button className="btn btn-ghost" onClick={() => (setPage(1), load(keyword, statusFilter, 1))}>搜索</button>
      </div>

      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr><th>ID</th><th>书名</th><th>作者</th><th>状态</th><th>章数</th><th>字数</th><th>收藏</th><th>月票</th><th>操作</th></tr>
          </thead>
          <tbody>
            {novels.map((n) => (
              <tr key={n.id}>
                <td>{n.id}</td>
                <td><Link to={`/novel/${n.id}`} style={{ color: 'var(--accent)' }}>{n.title}</Link></td>
                <td>{n.author?.nickname}</td>
                <td className={`st-${n.status}`}>
                  {n.status === 'serializing' ? '连载中' : n.status === 'finished' ? '已完结' : '已下架'}
                </td>
                <td>{n.chapter_count}</td>
                <td>{Number(n.word_count / 10000).toFixed(1)}万</td>
                <td>{n.total_favorites}</td>
                <td>{n.total_tickets}</td>
                <td>
                  {n.status !== 'banned' ? (
                    <button className="btn op-btn op-ban" onClick={() => setStatus(n, 'banned')}>下架</button>
                  ) : (
                    <button className="btn op-btn op-ok" onClick={() => setStatus(n, 'serializing')}>恢复</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Pagination page={page} total={total} pageSize={10}
        onChange={(p) => (setPage(p), load(keyword, statusFilter, p))} />
    </div>
  )
}

/* ---------- 评论管理 ---------- */
function CommentsTab({ flash }) {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [keyword, setKeyword] = useState('')
  const [page, setPage] = useState(1)

  const load = (kw = keyword, pg = page) => {
    apiAdminComments({ keyword: kw || undefined, page: pg, page_size: 10 })
      .then((d) => { setItems(d.items); setTotal(d.total) })
      .catch(() => {})
  }
  useEffect(() => { load() }, []) // eslint-disable-line

  const remove = async (c) => {
    if (!window.confirm(`删除 ${c.user?.nickname} 的这条评论？\n“${c.content.slice(0, 30)}…”`)) return
    try {
      await apiDeleteComment(c.id)
      flash('评论已删除')
      load(keyword, page)
    } catch (e) {
      flash(e.response?.data?.detail || '删除失败', true)
    }
  }

  return (
    <div>
      <div className="admin-search">
        <input className="field" placeholder="搜索评论内容"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && (setPage(1), load(keyword, 1))} />
        <button className="btn btn-ghost" onClick={() => (setPage(1), load(keyword, 1))}>搜索</button>
      </div>

      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr><th>ID</th><th>用户</th><th>类型</th><th>内容</th><th>点赞</th><th>时间</th><th>操作</th></tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={c.id}>
                <td>{c.id}</td>
                <td>{c.user?.nickname}</td>
                <td>
                  {c.parent_id ? '回复' : c.chapter_id ? '本章说' : '书评'}
                </td>
                <td style={{ maxWidth: 420, whiteSpace: 'normal' }}>{c.content}</td>
                <td>{c.likes}</td>
                <td>{c.created_at?.slice(0, 10)}</td>
                <td>
                  <button className="btn op-btn op-ban" onClick={() => remove(c)}>删除</button>
                </td>
              </tr>
            ))}
            {!items.length && (
              <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--ink-300)', padding: 24 }}>暂无评论</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <Pagination page={page} total={total} pageSize={10}
        onChange={(p) => (setPage(p), load(keyword, p))} />
    </div>
  )
}

/* ---------- 公告管理 ---------- */
function NoticesTab({ flash }) {
  const [notices, setNotices] = useState([])
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')

  const load = () => apiNotices().then(setNotices).catch(() => {})
  useEffect(() => { load() }, [])

  const publish = async () => {
    if (!title.trim() || !content.trim()) { flash('标题和内容不能为空', true); return }
    try {
      await apiCreateNotice({ title: title.trim(), content: content.trim() })
      flash('公告已发布')
      setTitle(''); setContent('')
      load()
    } catch (e) { flash(e.response?.data?.detail || '发布失败', true) }
  }

  const remove = async (id) => {
    try {
      await apiDeleteNotice(id)
      flash('已删除')
      load()
    } catch (e) { flash(e.response?.data?.detail || '删除失败', true) }
  }

  return (
    <div>
      <div className="notice-form">
        <input className="field" placeholder="公告标题"
          value={title} onChange={(e) => setTitle(e.target.value)} />
        <textarea className="field" rows="3" placeholder="公告内容"
          value={content} onChange={(e) => setContent(e.target.value)} />
        <button className="btn btn-primary" style={{ alignSelf: 'flex-start' }} onClick={publish}>发布公告</button>
      </div>

      <div className="admin-table-wrap" style={{ marginTop: 16 }}>
        <table className="admin-table">
          <thead>
            <tr><th>ID</th><th>标题</th><th>发布时间</th><th>操作</th></tr>
          </thead>
          <tbody>
            {notices.map((n) => (
              <tr key={n.id}>
                <td>{n.id}</td>
                <td style={{ maxWidth: 320, whiteSpace: 'normal' }}>{n.title}</td>
                <td>{new Date(n.created_at).toLocaleString()}</td>
                <td>
                  <button className="btn op-btn op-ban" onClick={() => remove(n.id)}>删除</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <style>{`
        .notice-form {
          display: flex;
          flex-direction: column;
          gap: var(--space-3);
          max-width: 560px;
        }
      `}</style>
    </div>
  )
}

/* 分页 */
function Pagination({ page, total, pageSize, onChange }) {
  const pages = Math.max(1, Math.ceil(total / pageSize))
  if (pages <= 1) return null
  return (
    <div className="pagination">
      <button className="btn btn-ghost" disabled={page <= 1} onClick={() => onChange(page - 1)}>上一页</button>
      <span className="pagination-info">{page} / {pages}（共 {total} 条）</span>
      <button className="btn btn-ghost" disabled={page >= pages} onClick={() => onChange(page + 1)}>下一页</button>
      <style>{`
        .pagination {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-4);
          margin: var(--space-5) 0;
        }
        .pagination-info { font-size: var(--fs-13); color: var(--ink-500); }
      `}</style>
    </div>
  )
}
