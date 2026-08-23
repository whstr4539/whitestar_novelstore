/* 阅读器：长文排版核心页面
   排版铁律：行高≥1.8 / 行长≤40字 / 首行缩进2em / 字距0.05em / 衬线字体
   交互：点击正文呼出工具栏 / 日夜间模式 / VIP购买无缝续读 / 进度记忆 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { apiChapters, apiPurchaseChapter, apiReadChapter, apiSaveProgress } from '../api'
import { useAuth } from '../stores/AuthContext'

export default function Reader() {
  const { chapterId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()

    const [chapter, setChapter] = useState(null)   // 元信息
  const [content, setContent] = useState('')
  const [novelId, setNovelId] = useState(null)
  const [allChapters, setAllChapters] = useState([])
  const [purchased, setPurchased] = useState(false)
  const [blocked, setBlocked] = useState(false)  // VIP 未购拦截
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [toolbar, setToolbar] = useState(false)
  const [night, setNight] = useState(() => localStorage.getItem('reader-night') === '1')
  const [fontSize, setFontSize] = useState(17)
  const bodyRef = useRef(null)

  const loadChapter = useCallback(async (cid) => {
    setLoading(true); setError(''); setBlocked(false)
    try {
      const d = await apiReadChapter(cid)
      setChapter(d.chapter)
      setContent(d.content)
      setPurchased(d.purchased)
      setNovelId(d.novel_id)
      // 目录
      const chapters = d.novel_id ? await apiChapters(d.novel_id) : []
      setAllChapters(chapters)
      // 上报进度
      if (user && d.novel_id) {
        apiSaveProgress({ novel_id: d.novel_id, chapter_id: Number(cid), progress: 0 }).catch(() => {})
      }
      window.scrollTo(0, 0)
    } catch (e) {
      if (e.response?.status === 402) {
        setBlocked(true)
        const detail = e.response.data?.detail
        if (detail && typeof detail === 'object' && detail.chapter) {
          setChapter(detail.chapter)   // 锁屏页展示章节标题/价格
          setError(detail.message)
        } else {
          setError(typeof detail === 'string' ? detail : '该章节为 VIP 章节')
        }
      } else {
        setError(e.response?.data?.detail || '加载失败')
      }
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    // 恢复滚动位置
    const saved = sessionStorage.getItem(`reader-scroll-${chapterId}`)
    if (saved) {
      setTimeout(() => window.scrollTo(0, Number(saved)), 50)
    }
  }, [chapterId])

  // 记住滚动位置
  const rememberScroll = () => {
    sessionStorage.setItem(`reader-scroll-${chapterId}`, String(window.scrollY))
  }
  useEffect(() => {
    window.addEventListener('scroll', rememberScroll, { passive: true })
    return () => window.removeEventListener('scroll', rememberScroll)
  }, [chapterId])

  // 加载章节 + 目录
  useEffect(() => { loadChapter(chapterId) }, [chapterId, loadChapter])

  const buy = async () => {
    try {
      await apiPurchaseChapter(chapterId)
      setBlocked(false); setPurchased(true)
      loadChapter(chapterId)
    } catch (e) {
      setError(e.response?.data?.detail || '购买失败')
    }
  }

  const idx = allChapters.findIndex((c) => c.id === Number(chapterId))
  const prev = idx > 0 ? allChapters[idx - 1] : null
  const next = idx >= 0 && idx < allChapters.length - 1 ? allChapters[idx + 1] : null

  const go = (cid) => {
    sessionStorage.setItem(`reader-scroll-${chapterId}`, String(window.scrollY))
    navigate(`/reader/${cid}`)
  }

  const toggleNight = () => {
    const v = !night
    setNight(v)
    localStorage.setItem('reader-night', v ? '1' : '0')
  }

  const paragraphs = content.split('\n').filter((p) => p.trim())

  return (
    <div className={`reader ${night ? 'reader-night' : ''}`} onClick={() => setToolbar(!toolbar)}>
      {/* 顶栏 */}
      <header className={`reader-bar reader-top ${toolbar ? 'reader-bar-show' : ''}`}>
        <button className="bar-btn" onClick={(e) => { e.stopPropagation(); navigate(-1) }}>←</button>
        <span className="bar-title">{chapter?.title || '…'}</span>
        <button className="bar-btn" onClick={(e) => { e.stopPropagation(); toggleNight() }}>
          {night ? '☀' : '☾'}
        </button>
      </header>

      {/* 正文 */}
      <main className="reader-body" style={{ fontSize: `${fontSize}px` }}>
        {loading ? (
          <div className="reader-loading">
            <div className="skeleton" style={{ height: 22, width: '40%', margin: '0 auto 32px' }} />
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="skeleton" style={{ height: 16, marginBottom: 18 }} />
            ))}
          </div>
        ) : blocked ? (
          <div className="reader-lock">
            <div className="lock-icon">🔒</div>
            <h2 className="lock-title">{chapter?.title}</h2>
            <p className="lock-price">
              本章为 VIP 章节，需 {chapter ? Number(chapter.price) : '—'} 书币购买
            </p>
            {user ? (
              <>
                <button className="btn btn-primary btn-block" onClick={(e) => { e.stopPropagation(); buy() }}>
                  购买本章
                </button>
                <p className="lock-note">购买后永久可读</p>
              </>
            ) : (
              <button className="btn btn-primary btn-block" onClick={(e) => {
                e.stopPropagation()
                navigate('/login?redirect=' + encodeURIComponent(`/reader/${chapterId}`))
              }}>
                登录后购买
              </button>
            )}
          </div>
        ) : error ? (
          <div className="empty">{error} <a href="/">返回首页</a></div>
        ) : (
          <article className="reader-article" ref={bodyRef}>
            <h1 className="article-title">{chapter?.title}</h1>
            <p className="article-meta">
              第 {chapter?.chapter_no} 章 · {chapter?.word_count} 字
              {purchased && <span className="article-purchased">✓ 已订阅</span>}
            </p>
            <div className="article-content">
              {paragraphs.map((p, i) => (
                <p key={i}>{p}</p>
              ))}
            </div>

            {/* 章末导航 */}
            <div className="article-end">
              {prev ? (
                <button className="btn btn-ghost" onClick={() => go(prev.id)}>← 上一章</button>
              ) : <span />}
              <button className="btn btn-ghost" onClick={() => navigate(`/novel/${novelId || ''}`)}>目录</button>
              {next ? (
                <button className="btn btn-primary" onClick={() => go(next.id)}>下一章 →</button>
              ) : (
                <button className="btn btn-primary" onClick={() => navigate(`/novel/${novelId || ''}`)}>
                  已读完 · 返回书页
                </button>
              )}
            </div>
          </article>
        )}
      </main>

      /* 底栏 */
      <footer className={`reader-bar reader-bottom ${toolbar ? 'reader-bar-show' : ''}`}>
        <button className="bar-btn" onClick={(e) => { e.stopPropagation(); if (prev) go(prev.id) }} disabled={!prev}>上一章</button>
        <div className="bar-progress">
          {allChapters.length > 0 && idx >= 0 && (
            <span className="bar-progress-text">
              第 {chapter?.chapter_no} / {allChapters.length} 章
            </span>
          )}
        </div>
        <button className="bar-btn" onClick={(e) => { e.stopPropagation(); if (next) go(next.id) }} disabled={!next}>下一章</button>
        <div className="bar-font">
          <button className="bar-btn" onClick={(e) => { e.stopPropagation(); setFontSize((s) => Math.min(20, s + 1)) }}>A+</button>
          <button className="bar-btn" onClick={(e) => { e.stopPropagation(); setFontSize((s) => Math.max(15, s - 1)) }}>A-</button>
        </div>
      </footer>

      <style>{`
        .reader {
          min-height: 100vh;
          background: var(--reader-bg);
          color: var(--reader-text);
          transition: background 0.25s ease, color 0.25s ease;
        }
        /* 阅读模式：日间/夜间 由 --reader-* 变量驱动 */

        .reader-bar {
          position: fixed;
          left: 0;
          right: 0;
          z-index: 60;
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: 0 var(--space-4);
          background: var(--reader-bg);
          border-color: var(--reader-hairline);
          opacity: 0;
          transform: translateY(0);
          pointer-events: none;
          transition: opacity 0.22s ease;
        }
        .reader-top { top: 0; height: 48px; border-bottom: 1px solid var(--reader-hairline); }
        .reader-bottom { bottom: 0; height: 52px; border-top: 1px solid var(--reader-hairline); }
        .reader-bar-show { opacity: 1; pointer-events: auto; }

        .bar-btn {
          font-size: var(--fs-14);
          color: var(--reader-text);
          padding: 6px 10px;
          border-radius: var(--radius);
          transition: background var(--ease);
          white-space: nowrap;
        }
        .bar-btn:hover { background: color-mix(in srgb, var(--reader-text) 8%, transparent); }
        .bar-btn:disabled { opacity: 0.35; cursor: not-allowed; }
        .bar-title {
          flex: 1;
          text-align: center;
          font-size: var(--fs-14);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .bar-progress { flex: 1; text-align: center; }
        .bar-progress-text { font-size: var(--fs-12); opacity: 0.6; }
        .bar-font { display: flex; }

        /* 正文排版（核心规范） */
        .reader-body {
          max-width: var(--content-max);
          margin: 0 auto;
          padding: 72px var(--space-5) 90px;
          min-height: 100vh;
        }
        .reader-article { cursor: default; }
        .article-title {
          font-family: var(--font-serif);
          font-size: 21px;
          font-weight: 600;
          text-align: center;
          letter-spacing: 0.06em;
          margin-bottom: var(--space-2);
        }
        .article-meta {
          text-align: center;
          font-size: 12px;
          opacity: 0.45;
          margin-bottom: 40px;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-2);
        }
        .article-purchased { color: var(--success); opacity: 1; }

        .article-content {
          font-family: var(--font-serif);
          font-size: 1em;          /* 由页面级 fontSize 控制 */
          line-height: 1.9;         /* ≥1.8 铁律 */
          letter-spacing: 0.05em;   /* 中文略加字距 */
          text-align: justify;      /* 两端对齐 */
          word-break: break-word;
        }
        .article-content p {
          text-indent: 2em;         /* 首行缩进 2 字符 */
          margin-bottom: 1em;       /* 段间距 */
        }

        .article-end {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: var(--space-3);
          margin-top: 56px;
          padding-top: var(--space-5);
          border-top: 1px solid var(--reader-hairline);
        }

        /* VIP 拦截 */
        .reader-lock {
          max-width: 360px;
          margin: 80px auto;
          text-align: center;
          padding: var(--space-6);
          border: 1px solid var(--reader-hairline);
          border-radius: var(--radius-lg);
        }
        .lock-icon { font-size: 40px; margin-bottom: var(--space-4); }
        .lock-title { font-size: var(--fs-18); margin-bottom: var(--space-2); font-weight: 600; }
        .lock-price { font-size: var(--fs-14); opacity: 0.7; margin-bottom: var(--space-5); }
        .lock-note { font-size: var(--fs-12); opacity: 0.5; margin-top: var(--space-3); }
        .lock-error { opacity: 1; color: var(--danger); }

        .reader-loading { padding-top: 60px; }

        @media (max-width: 768px) {
          .reader-body { padding: 64px var(--space-4) 84px; }
          .bar-font { display: none; }
        }
      `}</style>
    </div>
  )
}
