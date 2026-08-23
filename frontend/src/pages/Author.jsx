/* 作者写作台：我的作品 | 发布章节 | 新建作品 */
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiCreateNovel, apiMyNovels, apiPublishChapter } from '../api'
import { useAuth } from '../stores/AuthContext'

export default function Author() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const [novels, setNovels] = useState([])
  const [tab, setTab] = useState('list')
  const [msg, setMsg] = useState('')

  // 发章节表单
  const [novelId, setNovelId] = useState('')
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [price, setPrice] = useState(0)
  const [isVip, setIsVip] = useState(false)
  const [busy, setBusy] = useState(false)

  // 新建作品表单
  const [newTitle, setNewTitle] = useState('')
  const [newIntro, setNewIntro] = useState('')
  const [newCategory, setNewCategory] = useState('')
  const [newVip, setNewVip] = useState(false)

  const CATEGORIES = [
    { id: 6, name: '玄幻' }, { id: 7, name: '都市' }, { id: 8, name: '科幻' },
    { id: 4, name: '历史' }, { id: 5, name: '悬疑' },
  ]

  const load = () => apiMyNovels().then(setNovels).catch(() => {})
  useEffect(() => { load() }, [])

  const flash = (m, isErr = false) => { setMsg({ text: m, isErr }); setTimeout(() => setMsg(''), 3500) }

  const createNovel = async () => {
    if (!newTitle.trim()) { flash('请填写书名', true); return }
    setBusy(true)
    try {
      const d = await apiCreateNovel({
        title: newTitle.trim(),
        intro: newIntro.trim() || null,
        category_id: newCategory ? Number(newCategory) : null,
        is_vip: newVip,
      })
      flash(`作品《${d.title}》创建成功，去发布第一章吧！`)
      setNewTitle(''); setNewIntro(''); setNewCategory(''); setNewVip(false)
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
    setBusy(true)
    try {
      const d = await apiPublishChapter(novelId, {
        title: title.trim(),
        content: content.trim(),
        price,
        is_vip: isVip,
      })
      flash(`发布成功：第 ${d.chapter_no} 章（全书现 ${d.novel_chapter_count} 章 / ${d.novel_word_count} 字）`)
      setTitle(''); setContent(''); setPrice(0); setIsVip(false)
    } catch (e) {
      flash(e.response?.data?.detail || '发布失败')
    } finally {
      setBusy(false)
    }
  }

  if (!user) return <div className="container empty">请先<a href="/login">登录</a></div>
  if (user.role !== 'author' && user.role !== 'admin') {
    return <div className="container empty">写作台仅对作者开放</div>
  }

  return (
    <div className="container page-enter">
      <div className="page-head">
        <h1 className="page-title">写作台</h1>
        <span className="page-sub">发布章节后自动更新作品字数与章数</span>
      </div>

      {msg && <div className={`alert ${msg.isErr ? 'alert-error' : 'alert-success'}`}>{msg.text}</div>}

      <div className="author-tabs">
        <button className={`tab ${tab === 'list' ? 'tab-active' : ''}`} onClick={() => setTab('list')}>
          我的作品（{novels.length}）
        </button>
        <button className={`tab ${tab === 'publish' ? 'tab-active' : ''}`} onClick={() => setTab('publish')}>
          发布章节
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
            novels.map((n) => (
              <div key={n.id} className="author-item">
                <div className="author-item-info">
                  <h3 className="author-item-title">{n.title}</h3>
                  <p className="author-item-meta">
                    {n.chapter_count} 章 · {Number(n.word_count / 10000).toFixed(1)} 万字 ·{' '}
                    {n.total_favorites} 收藏 · {n.total_tickets} 月票 · {n.total_views} 点击
                  </p>
                </div>
                <div className="author-item-actions">
                  {n.is_vip && <span className="badge badge-vip">VIP</span>}
                  <button className="btn btn-ghost btn-sm" onClick={() => navigate(`/novel/${n.id}`)}>
                    查看书页
                  </button>
                </div>
              </div>
            ))
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
            .author-item-actions { display: flex; align-items: center; gap: var(--space-3); flex-shrink: 0; }
            .btn-sm { padding: 5px 12px; font-size: var(--fs-13); }
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
            </div>
            <label className="vip-check">
              <input type="checkbox" checked={isVip} onChange={(e) => setIsVip(e.target.checked)} />
              VIP 章节（收费）
            </label>
          </div>
          <button className="btn btn-primary publish-btn" disabled={busy} onClick={publish}>
            {busy ? '发布中…' : '发布章节'}
          </button>
          <style>{`
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
            .vip-check {
              font-size: var(--fs-14);
              color: var(--ink-700);
              display: flex;
              align-items: center;
              gap: 6px;
              padding-bottom: 10px;
            }
            .publish-btn { align-self: flex-start; padding: 10px 32px; }
          `}</style>
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
                {CATEGORIES.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <label className="vip-check">
              <input type="checkbox" checked={newVip} onChange={(e) => setNewVip(e.target.checked)} />
              VIP 作品
            </label>
          </div>
          <button className="btn btn-primary publish-btn" disabled={busy} onClick={createNovel}>
            {busy ? '创建中…' : '创建作品'}
          </button>
        </div>
      )}

      <style>{`
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
      `}</style>
    </div>
  )
}
