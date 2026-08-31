/* 作者写作台：我的作品（含收益）| 发布章节 | 新建作品 | 修改章节 */
import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  apiAuthorStats, apiCategories, apiChapters, apiCreateNovel, apiMyNovels, apiNovelEarnings,
  apiPublishChapter, apiUpdateChapter,
} from '../api'
import { useAuth } from '../stores/AuthContext'

export default function Author() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const [novels, setNovels] = useState([])
  const [earnings, setEarnings] = useState({})   // novel_id -> 收益统计
  const [stats, setStats] = useState(null)       // 写作台概览
  const [categories, setCategories] = useState([])
  const [tab, setTab] = useState('list')
  const [msg, setMsg] = useState('')

  // 发章节表单
  const [novelId, setNovelId] = useState('')
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [price, setPrice] = useState(0)
  const [busy, setBusy] = useState(false)

  // 新建作品表单
  const [newTitle, setNewTitle] = useState('')
  const [newIntro, setNewIntro] = useState('')
  const [newCategory, setNewCategory] = useState('')

  // 修改章节表单
  const [editNovelId, setEditNovelId] = useState('')
  const [chapters, setChapters] = useState([])
  const [editing, setEditing] = useState(null)   // 正在编辑的章节
  const [eTitle, setETitle] = useState('')
  const [eContent, setEContent] = useState('')
  const [ePrice, setEPrice] = useState(0)

  // 可选分类：叶子分类（二级优先，其次一级），来自数据库
  const loadCategories = () =>
    apiCategories().then((cats) => {
      const leaf = cats.filter((c) => !cats.some((x) => x.parent_id === c.id))
      setCategories(leaf.length ? leaf : cats)
    }).catch(() => {})

  const load = useCallback(() => {
    apiMyNovels().then(async (list) => {
      setNovels(list)
      // 并行拉取每本书的收益
      const entries = await Promise.all(
        list.map((n) => apiNovelEarnings(n.id).then((e) => [n.id, e]).catch(() => [n.id, null]))
      )
      setEarnings(Object.fromEntries(entries))
    }).catch(() => {})
    // 概览统计
    apiAuthorStats().then(setStats).catch(() => setStats(null))
  }, [])

  useEffect(() => { load(); loadCategories() }, [load])

  const flash = (m, isErr = false) => { setMsg({ text: m, isErr }); setTimeout(() => setMsg(''), 3500) }

  const createNovel = async () => {
    if (!newTitle.trim()) { flash('请填写书名', true); return }
    setBusy(true)
    try {
      const d = await apiCreateNovel({
        title: newTitle.trim(),
        intro: newIntro.trim() || null,
        category_id: newCategory ? Number(newCategory) : null,
      })
      flash(`作品《${d.title}》创建成功，去发布第一章吧！`)
      setNewTitle(''); setNewIntro(''); setNewCategory('')
      await load()
      setTab('publish')
      setNovelId(String(d.id))
    } catch (e) {
      flash(e.response?.data?.detail || '创建失败', true)
    } finally {
      setBusy(false)
    }
  }

  const publish = async () => {
    if (!novelId || !title.trim() || !content.trim()) {
      flash('请填写完整（选择作品、标题、正文）')
      return
    }
    if (price < 0) {
      flash('价格不能为负', true)
      return
    }
    setBusy(true)
    try {
      const d = await apiPublishChapter(novelId, {
        title: title.trim(),
        content: content.trim(),
        price,
      })
      flash(`发布成功：第 ${d.chapter_no} 章（全书现 ${d.novel_chapter_count} 章 / ${d.novel_word_count} 字）`)
      setTitle(''); setContent(''); setPrice(0)
      load()
    } catch (e) {
      flash(e.response?.data?.detail || '发布失败')
    } finally {
      setBusy(false)
    }
  }

  // ---- 修改章节 ----
  const loadChapters = async (nid) => {
    if (!nid) { setChapters([]); return }
    try {
      setChapters(await apiChapters(Number(nid)))
    } catch { setChapters([]) }
  }

  const startEdit = (c) => {
    setEditing(c)
    setETitle(c.title)
    setEContent('')
    setEPrice(Number(c.price))
    // 拉取正文（免费直读；若是收费章，作者本人免购）
    apiReadForEdit(c.id).then((d) => setEContent(d.content)).catch(() => setEContent(''))
  }

  const cancelEdit = () => {
    setEditing(null); setETitle(''); setEContent(''); setEPrice(0)
  }

  const saveEdit = async () => {
    if (!eTitle.trim()) { flash('标题不能为空', true); return }
    if (ePrice < 0) { flash('价格不能为负', true); return }
    setBusy(true)
    try {
      const d = await apiUpdateChapter(editing.id, {
        title: eTitle.trim(),
        content: eContent || null,
        price: ePrice,
      })
      flash(d.detail || '章节已更新')
      cancelEdit()
      loadChapters(editNovelId)
      load()
    } catch (e) {
      flash(e.response?.data?.detail || '保存失败', true)
    } finally {
      setBusy(false)
    }
  }

  // 作者读取自己章节的正文（免费/收费均可，作者免购）
  const apiReadForEdit = async (chapterId) => {
    const { apiReadChapter } = await import('../api')
    return apiReadChapter(chapterId)
  }

  if (!user) return <div className="container empty">请先<Link to="/login">登录</Link></div>
  if (user.role !== 'author' && user.role !== 'admin') {
    return <div className="container empty">写作台仅对作者开放</div>
  }

  const fmt = (v) => v >= 10000 ? `${(v / 10000).toFixed(1)}万` : String(v)

  return (
    <div className="container page-enter">
      <div className="page-head">
        <h1 className="page-title">写作台</h1>
        <span className="page-sub">发布章节自动更新字数与章数 · 修改章节实时同步</span>
      </div>

      {msg && <div className={`alert ${msg.isErr ? 'alert-error' : 'alert-success'}`}>{msg.text}</div>}

      {/* 写作台概览：作品数 / 点击 / 订阅收入 / 打赏收入 */}
      {stats && (
        <div className="author-stats">
          <div className="author-stat">
            <b>{stats.novel_count}</b>
            <span>作品数</span>
          </div>
          <div className="author-stat">
            <b>{fmt(stats.total_views)}</b>
            <span>总点击</span>
          </div>
          <div className="author-stat">
            <b>{fmt(stats.chapter_revenue)}</b>
            <span>订阅收入（书币）</span>
          </div>
          <div className="author-stat">
            <b>{fmt(stats.reward_revenue)}</b>
            <span>打赏收入（书币）</span>
          </div>
          <div className="author-stat author-stat-total">
            <b>{fmt(stats.total_revenue)}</b>
            <span>合计收入</span>
          </div>
          <div className="author-stat">
            <b>{stats.chapter_count}</b>
            <span>章节总数</span>
          </div>
        </div>
      )}

      <div className="author-tabs">
        <button className={`tab ${tab === 'list' ? 'tab-active' : ''}`} onClick={() => setTab('list')}>
          我的作品（{novels.length}）
        </button>
        <button className={`tab ${tab === 'publish' ? 'tab-active' : ''}`} onClick={() => setTab('publish')}>
          发布章节
        </button>
        <button className={`tab ${tab === 'edit' ? 'tab-active' : ''}`} onClick={() => setTab('edit')}>
          修改章节
        </button>
        <button className={`tab ${tab === 'new' ? 'tab-active' : ''}`} onClick={() => setTab('new')}>
          新建作品
        </button>
      </div>

      {tab === 'list' ? (
        <div className="author-list">
          {novels.length === 0 ? (
            <div className="empty">还没有作品，去「发布章节」开始创作吧</div>
          ) : (
            novels.map((n) => {
              const e = earnings[n.id]
              return (
                <div key={n.id} className="author-item">
                  <div className="author-item-info">
                    <h3 className="author-item-title">{n.title}</h3>
                    <p className="author-item-meta">
                      {n.chapter_count} 章 · {Number(n.word_count / 10000).toFixed(1)} 万字 ·{' '}
                      {n.total_favorites} 收藏 · {n.total_tickets} 月票 · {fmt(n.total_views)} 点击
                    </p>
                    {e && (
                      <p className="author-item-earn">
                        订阅 <b>{fmt(e.chapter_revenue)}</b> 书币 · 打赏 <b>{fmt(e.reward_revenue)}</b> 书币 ·
                        合计 <b className="earn-total">{fmt(e.total_revenue)}</b> 书币
                        <span className="earn-count">（{e.purchase_count} 次订阅 / {e.reward_count} 次打赏）</span>
                      </p>
                    )}
                  </div>
                  <div className="author-item-actions">
                    {n.status === 'banned' && <span className="badge badge-ban">已下架</span>}
                    <button className="btn btn-ghost btn-sm" onClick={() => { setTab('edit'); setEditNovelId(String(n.id)); loadChapters(n.id) }}>
                      管理章节
                    </button>
                    <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/novel/${n.id}`)}
                      disabled={n.status === 'banned'} title={n.status === 'banned' ? '作品已下架，无法访问书页' : ''}>
                      {n.status === 'banned' ? '已下架' : '查看书页'}
                    </button>
                  </div>
                </div>
              )
            })
          )}
          <style>{`
            .author-item {
              display: flex;
              align-items: center;
              justify-content: space-between;
              padding: var(--space-4);
              border-bottom: 1px solid var(--hairline);
              gap: var(--space-4);
            }
            .author-item-title { font-size: var(--fs-16); font-weight: 600; margin-bottom: 4px; }
            .author-item-meta { font-size: var(--fs-12); color: var(--ink-500); }
            .author-item-earn { font-size: var(--fs-13); color: var(--ink-700); margin-top: 6px; }
            .author-item-earn b { font-variant-numeric: tabular-nums; }
            .earn-total { color: var(--accent); }
            .earn-count { font-size: var(--fs-12); color: var(--ink-300); margin-left: var(--space-2); }
            .author-item-actions { display: flex; align-items: center; gap: var(--space-3); flex-shrink: 0; }
            .btn-sm { padding: 5px 12px; font-size: var(--fs-13); }
            .badge-ban { color: var(--danger); border: 1px solid var(--danger); }
          `}</style>
        </div>
      ) : tab === 'publish' ? (
        <div className="publish-box">
          <div className="field-group">
            <label className="label">选择作品</label>
            <select className="field" value={novelId} onChange={(e) => setNovelId(e.target.value)}>
              <option value="">— 选择 —</option>
              {novels.map((n) => (
                <option key={n.id} value={n.id}>{n.title}（{n.chapter_count} 章）</option>
              ))}
            </select>
          </div>
          <div className="field-group">
            <label className="label">章节标题</label>
            <input className="field" value={title} onChange={(e) => setTitle(e.target.value)}
              placeholder="如：第一章 初入宗门" />
          </div>
          <div className="field-group">
            <label className="label">正文（系统自动统计字数）</label>
            <textarea className="field publish-content" rows="10"
              value={content} onChange={(e) => setContent(e.target.value)}
              placeholder="写下本章内容…" />
          </div>
          <div className="publish-opts">
            <div className="field-group publish-price">
              <label className="label">书币价格</label>
              <input className="field" type="number" min="0" step="0.5" value={price}
                onChange={(e) => setPrice(Number(e.target.value) || 0)} />
              <span className="publish-hint">价格大于 0 即为付费章节，0 为免费</span>
            </div>
          </div>
          <button className="btn btn-primary publish-btn" disabled={busy} onClick={publish}>
            {busy ? '发布中…' : '发布章节'}
          </button>
        </div>
      ) : tab === 'edit' ? (
        <div className="publish-box">
          <div className="field-group">
            <label className="label">选择作品</label>
            <select className="field" value={editNovelId}
              onChange={(e) => { setEditNovelId(e.target.value); cancelEdit(); loadChapters(e.target.value) }}>
              <option value="">— 选择 —</option>
              {novels.map((n) => (
                <option key={n.id} value={n.id}>{n.title}（{n.chapter_count} 章）</option>
              ))}
            </select>
          </div>

          {chapters.length === 0 ? (
            <div className="empty">还没有章节可编辑</div>
          ) : (
            <div className="edit-chapter-list">
              {chapters.map((c) => (
                <div key={c.id} className={`edit-row ${editing?.id === c.id ? 'edit-row-active' : ''}`}>
                  <div className="edit-row-info">
                    <span className="edit-row-no">第 {c.chapter_no} 章</span>
                    <span className="edit-row-title">{c.title}</span>
                    <span className="edit-row-meta">
                      {c.word_count} 字 · {Number(c.price) > 0 ? `${c.price} 书币` : c.is_free ? '试读' : '免费'}
                    </span>
                  </div>
                  <button className="btn btn-ghost btn-sm" onClick={() => startEdit(c)}>
                    {editing?.id === c.id ? '收起' : '编辑'}
                  </button>
                </div>
              ))}
            </div>
          )}

          {editing && (
            <div className="edit-box">
              <h3 className="edit-box-title">编辑 第 {editing.chapter_no} 章</h3>
              <div className="field-group">
                <label className="label">章节标题</label>
                <input className="field" value={eTitle} onChange={(e) => setETitle(e.target.value)} />
              </div>
              <div className="field-group">
                <label className="label">正文（不修改则保留原文；保存后字数重算）</label>
                <textarea className="field publish-content" rows="10"
                  value={eContent} onChange={(e) => setEContent(e.target.value)}
                  placeholder="留空表示不修改正文" />
              </div>
              <div className="publish-opts">
                <div className="field-group publish-price">
                  <label className="label">书币价格</label>
                  <input className="field" type="number" min="0" step="0.5" value={ePrice}
                    onChange={(e) => setEPrice(Number(e.target.value) || 0)} />
                </div>
              </div>
              <div className="edit-ops">
                <button className="btn btn-primary" disabled={busy} onClick={saveEdit}>
                  {busy ? '保存中…' : '保存修改'}
                </button>
                <button className="btn btn-ghost" onClick={cancelEdit}>取消</button>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* 新建作品 */
        <div className="publish-box">
          <div className="field-group">
            <label className="label">书名</label>
            <input className="field" value={newTitle} onChange={(e) => setNewTitle(e.target.value)}
              placeholder="如：我的第一本书" />
          </div>
          <div className="field-group">
            <label className="label">作品简介</label>
            <textarea className="field publish-content" rows="4"
              value={newIntro} onChange={(e) => setNewIntro(e.target.value)}
              placeholder="一句话让读者点进来…" />
          </div>
          <div className="publish-opts">
            <div className="field-group publish-price">
              <label className="label">分类</label>
              <select className="field" value={newCategory} onChange={(e) => setNewCategory(e.target.value)}>
                <option value="">未分类</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          </div>
          <button className="btn btn-primary publish-btn" disabled={busy} onClick={createNovel}>
            {busy ? '创建中…' : '创建作品'}
          </button>
        </div>
      )}

      <style>{`
        /* 概览统计条 */
        .author-stats {
          display: grid;
          grid-template-columns: repeat(6, 1fr);
          background: var(--card);
          border: 1px solid var(--hairline);
          border-radius: var(--radius);
          margin-bottom: var(--space-5);
        }
        .author-stat {
          padding: var(--space-4) var(--space-3);
          text-align: center;
          border-left: 1px solid var(--hairline);
        }
        .author-stat:first-child { border-left: none; }
        .author-stat b {
          display: block;
          font-size: var(--fs-22);
          font-weight: 700;
          font-variant-numeric: tabular-nums;
          color: var(--ink-900);
          margin-bottom: 4px;
        }
        .author-stat span {
          font-size: var(--fs-12);
          color: var(--ink-500);
        }
        .author-stat-total b { color: var(--accent); }
        @media (max-width: 768px) {
          .author-stats { grid-template-columns: repeat(3, 1fr); }
          .author-stat { border-left: none; border-top: 1px solid var(--hairline); }
          .author-stat:nth-child(-n+3) { border-top: none; }
          .author-stat:nth-child(3n+2), .author-stat:nth-child(3n+3) { border-left: 1px solid var(--hairline); }
        }
        .author-tabs {
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
        .tab-active {
          color: var(--accent);
          border-bottom-color: var(--accent);
          font-weight: 600;
        }
        .author-list {
          background: var(--card);
          border: 1px solid var(--hairline);
          border-radius: var(--radius-lg);
          overflow: hidden;
        }

        .publish-box {
          max-width: 640px;
          display: flex;
          flex-direction: column;
          gap: var(--space-4);
        }
        .field-group { display: flex; flex-direction: column; gap: 6px; }
        .publish-content { resize: vertical; line-height: 1.8; }
        .publish-opts {
          display: flex;
          align-items: flex-end;
          gap: var(--space-5);
        }
        .publish-price { width: 160px; }
        .publish-hint { font-size: var(--fs-12); color: var(--ink-500); }
        .publish-btn { align-self: flex-start; padding: 10px 32px; }

        /* 修改章节 */
        .edit-chapter-list {
          border: 1px solid var(--hairline);
          border-radius: var(--radius);
          background: var(--card);
          overflow: hidden;
        }
        .edit-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: var(--space-4);
          padding: var(--space-3) var(--space-4);
          border-bottom: 1px solid var(--hairline);
        }
        .edit-row:last-child { border-bottom: none; }
        .edit-row-active { background: var(--accent-weak); }
        .edit-row-info { display: flex; align-items: baseline; gap: var(--space-3); min-width: 0; }
        .edit-row-no { font-size: var(--fs-12); color: var(--ink-500); white-space: nowrap; }
        .edit-row-title { font-size: var(--fs-14); font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .edit-row-meta { font-size: var(--fs-12); color: var(--ink-500); white-space: nowrap; display: flex; gap: 6px; align-items: center; }
        .edit-box {
          border: 1px solid var(--hairline);
          border-radius: var(--radius-lg);
          padding: var(--space-5);
          background: var(--card);
          display: flex;
          flex-direction: column;
          gap: var(--space-4);
        }
        .edit-box-title { font-size: var(--fs-16); font-weight: 600; }
        .edit-ops { display: flex; gap: var(--space-3); }
      `}</style>
    </div>
  )
}
