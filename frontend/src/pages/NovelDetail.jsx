/* 小说详情：信息区 | 操作区 | Tab（简介/目录/评论/评分） */
import { useCallback, useEffect, useState } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import {
  apiAddFavorite, apiBookshelf, apiChapters, apiCommentReplies, apiComments, apiDeleteComment,
  apiDeleteReview, apiHistory, apiLikeComment, apiNovel, apiPostComment, apiPostReview,
  apiRemoveFavorite, apiReviews, apiReward, apiRewards, apiVoteTicket, apiWallet,
} from '../api'
import { useAuth } from '../stores/AuthContext'
import { Cover, StatusBadge } from '../components/NovelCard'
import ChapterList from '../components/ChapterList'

export default function NovelDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()

  const [novel, setNovel] = useState(null)
  const [chapters, setChapters] = useState([])
  const [comments, setComments] = useState([])
  const [reviews, setReviews] = useState([])
  const [rewards, setRewards] = useState([])
  const [favorited, setFavorited] = useState(false)
  const [wallet, setWallet] = useState(null)
  const [tab, setTab] = useState('intro')
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState('')

  // 评论表单
  const [commentText, setCommentText] = useState('')
  // 楼中楼：parentId 非空 = 回复目标；repliesMap[评论id] = 子评论数组
  const [replyTo, setReplyTo] = useState(null)
  const [replyText, setReplyText] = useState('')
  const [repliesOpen, setRepliesOpen] = useState({})
  const [repliesMap, setRepliesMap] = useState({})
  // 评分表单
  const [rating, setRating] = useState(0)
  const [reviewText, setReviewText] = useState('')
  // 打赏表单
  const [rewardOpen, setRewardOpen] = useState(false)
  const [rewardAmount, setRewardAmount] = useState(10)
  // 月票：每个账号每书一票，投过后本地禁用按钮
  const [voted, setVoted] = useState(false)
  // 续读：当前用户对该书的最近阅读章节（无则第一章）
  const [resumeChapterId, setResumeChapterId] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [n, ch, cm, rv, rw] = await Promise.all([
        apiNovel(id), apiChapters(id), apiComments(id), apiReviews(id), apiRewards(id),
      ])
      setNovel(n); setChapters(ch); setComments(cm); setReviews(rv); setRewards(rw)
      if (user) {
        const [shelf, w, hist] = await Promise.all([
          apiBookshelf().catch(() => ({ items: [] })),
          apiWallet().catch(() => null),
          apiHistory().catch(() => ({ items: [] })),
        ])
        setFavorited(shelf.items.some((i) => i.novel.id === Number(id)))
        setWallet(w)
        const rec = hist.items.find((i) => i.novel.id === Number(id))
        setResumeChapterId(rec?.chapter_id ?? null)
      }
    } catch (e) {
      setMsg(e.response?.data?.detail || '加载失败')
    } finally {
      setLoading(false)
    }
  }, [id, user])

  useEffect(() => { load() }, [load])

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500) }

  const toggleFavorite = async () => {
    try {
      if (favorited) { await apiRemoveFavorite(id); setFavorited(false); flash('已移出书架') }
      else { await apiAddFavorite(id); setFavorited(true); flash('已加入书架') }
      load()
    } catch (e) { flash(e.response?.data?.detail || '操作失败') }
  }

  const submitComment = async () => {
    if (!commentText.trim()) return
    try {
      await apiPostComment(id, { content: commentText.trim() })
      setCommentText('')
      flash('评论已发布')
      setComments(await apiComments(id))
    } catch (e) { flash(e.response?.data?.detail || '发布失败') }
  }

  const like = async (cid) => {
    try {
      const r = await apiLikeComment(cid)
      // 单人单赞（toggle）：用响应直接更新，避免整页刷新
      setComments((list) => list.map((c) => (c.id === cid ? { ...c, liked: r.liked, likes: r.likes } : c)))
    } catch (e) {
      if (e.response?.status === 401) flash('请先登录') 
    }
  }

  // ---- 楼中楼 ----
  const toggleReplies = async (cid) => {
    const open = !repliesOpen[cid]
    setRepliesOpen((m) => ({ ...m, [cid]: open }))
    if (open && !repliesMap[cid]) {
      try {
        const list = await apiCommentReplies(cid)
        setRepliesMap((m) => ({ ...m, [cid]: list }))
      } catch { /* 忽略 */ }
    }
  }

  const submitReply = async (cid) => {
    if (!replyText.trim()) return
    try {
      await apiPostComment(id, { content: replyText.trim(), parent_id: cid })
      setReplyText('')
      setReplyTo(null)
      const list = await apiCommentReplies(cid)
      setRepliesMap((m) => ({ ...m, [cid]: list }))
      setRepliesOpen((m) => ({ ...m, [cid]: true }))
    } catch (e) { flash(e.response?.data?.detail || '回复失败') }
  }

  const removeComment = async (cid) => {
    if (!window.confirm('确定删除这条评论？')) return
    try {
      await apiDeleteComment(cid)
      flash('评论已删除')
      setComments(await apiComments(id))
    } catch (e) { flash(e.response?.data?.detail || '删除失败') }
  }

  const submitReview = async () => {
    if (!rating) { flash('请选择评分'); return }
    try {
      await apiPostReview(id, { rating, content: reviewText.trim() || null })
      flash('评分已提交')
      setRating(0); setReviewText('')
      setReviews(await apiReviews(id))
      load()
    } catch (e) { flash(e.response?.data?.detail || '提交失败') }
  }

  const removeReview = async (rid) => {
    if (!window.confirm('确定删除这条评分？删除后作品均分将重新计算')) return
    try {
      await apiDeleteReview(id, rid)
      flash('评分已删除')
      setReviews(await apiReviews(id))
      load()
    } catch (e) { flash(e.response?.data?.detail || '删除失败') }
  }

  const submitReward = async () => {
    try {
      await apiReward(id, rewardAmount, '')
      flash(`已打赏 ${rewardAmount} 书币，感谢支持！`)
      setRewardOpen(false)
      setWallet(await apiWallet())
      setRewards(await apiRewards(id))
    } catch (e) { flash(e.response?.data?.detail || '打赏失败') }
  }

  const vote = async () => {
    if (voted) return
    try {
      await apiVoteTicket(id, 'monthly')
      setVoted(true)
      flash('月票已投出')
      load()
    } catch (e) {
      // 后端语义：每人每书每类一票；已投过则确认禁用按钮
      if (e.response?.status === 409) {
        setVoted(true)
        flash('该书您已投过月票')
      } else {
        flash(e.response?.data?.detail || '投票失败')
      }
    }
  }

  if (loading) return <div className="container"><div className="skeleton" style={{ height: 260, marginTop: 24 }} /></div>
  if (!novel) return <div className="container empty">作品不存在或已下架</div>

  // 开始阅读：有阅读记录则续读该章，否则从第一章开始
  const startChapterId = chapters.length
    ? (resumeChapterId && chapters.some((c) => c.id === resumeChapterId) ? resumeChapterId : chapters[0].id)
    : null

  return (
    <div className="container detail page-enter">
      {msg && <div className="alert alert-success">{msg}</div>}

      {/* 信息区 */}
      <section className="detail-head">
        <Cover title={novel.title} categoryId={novel.category_id} size="lg" className="detail-cover" />
        <div className="detail-info">
          <h1 className="detail-title">{novel.title}</h1>
          <p className="detail-meta">
            <span>{novel.author?.nickname}</span>
            <span className="dot">·</span>
            <span>{novel.category?.name || '未分类'}</span>
            <span className="dot">·</span>
            <StatusBadge status={novel.status} />
          </p>
          <p className="detail-stats">
            <span><b>{Number(novel.score) > 0 ? Number(novel.score).toFixed(1) : '—'}</b> 评分</span>
            <span><b>{novel.word_count > 10000 ? `${Number(novel.word_count / 10000).toFixed(1)}万` : novel.word_count}</b> 字数</span>
            <span><b>{novel.total_favorites}</b> 收藏</span>
            <span><b>{novel.total_tickets}</b> 月票</span>
            <span><b>{novel.total_views}</b> 点击</span>
          </p>
          <p className="detail-tags">
            <StatusBadge status={novel.status} />
          </p>
          <div className="detail-actions">
            {startChapterId && (
              <button className="btn btn-primary" onClick={() => navigate(`/reader/${startChapterId}`)}>
                {resumeChapterId ? '继续阅读' : '开始阅读'}
              </button>
            )}
            <button className={`btn ${favorited ? 'btn-primary' : 'btn-ghost'}`} onClick={toggleFavorite}>
              {favorited ? '✓ 已在书架' : '加入书架'}
            </button>
            <button className="btn btn-ghost" onClick={() => setRewardOpen(!rewardOpen)}>打赏</button>
            <button className="btn btn-ghost" onClick={vote} disabled={voted}>
              {voted ? '已投月票' : '投月票'}
            </button>
          </div>
          {rewardOpen && (
            <div className="reward-box">
              <p className="detail-note">
                当前余额：<b>{wallet ? Number(wallet.balance) : '登录可见'} 书币</b>
              </p>
              <div className="reward-row">
                {[5, 10, 50, 100].map((v) => (
                  <button key={v} className={`btn btn-ghost ${rewardAmount === v ? 'reward-active' : ''}`}
                    onClick={() => setRewardAmount(v)}>{v}</button>
                ))}
                <button className="btn btn-primary" onClick={submitReward}>确认打赏</button>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Tab */}
      <section className="detail-tabs">
        <button className={`tab ${tab === 'intro' ? 'tab-active' : ''}`} onClick={() => setTab('intro')}>简介</button>
        <button className={`tab ${tab === 'chapters' ? 'tab-active' : ''}`} onClick={() => setTab('chapters')}>
          目录（{chapters.length}）
        </button>
        <button className={`tab ${tab === 'comments' ? 'tab-active' : ''}`} onClick={() => setTab('comments')}>
          评论（{comments.length}）
        </button>
        <button className={`tab ${tab === 'reviews' ? 'tab-active' : ''}`} onClick={() => setTab('reviews')}>
          评分（{reviews.length}）
        </button>
        <button className={`tab ${tab === 'rewards' ? 'tab-active' : ''}`} onClick={() => setTab('rewards')}>
          打赏记录
        </button>
      </section>

      <section className="detail-body">
        {tab === 'intro' && (
          <div className="intro-box">
            <h3 className="intro-title">作品简介</h3>
            <p className="intro-text">{novel.intro || '作者很懒，还没写简介。'}</p>
          </div>
        )}

        {tab === 'chapters' && (
          chapters.length ? <ChapterList chapters={chapters} />
            : <div className="empty">还没有章节</div>
        )}

        {tab === 'comments' && (
          <div>
            {user ? (
              <div className="comment-form">
                <textarea className="field" rows="3" placeholder="写下你的评论（书评）…"
                  value={commentText} onChange={(e) => setCommentText(e.target.value)} />
                <button className="btn btn-primary" onClick={submitComment}>发布评论</button>
              </div>
            ) : (
              <div className="empty"><Link to="/login">登录后参与评论</Link></div>
            )}
            {comments.map((c) => (
              <div key={c.id} className="comment-item">
                <div className="comment-head">
                  <Link to={`/users/${c.user_id}`} className="comment-user">{c.user?.nickname}</Link>
                  <span className="comment-time">{new Date(c.created_at).toLocaleDateString()}</span>
                </div>
                <p className="comment-content">{c.content}</p>
                <div className="comment-ops">
                  <button className={`comment-like ${c.liked ? 'comment-like-on' : ''}`} onClick={() => like(c.id)}>
                    {c.liked ? '已赞' : '赞'} {c.likes}
                  </button>
                  <button className="comment-like" onClick={() => { setReplyTo(replyTo === c.id ? null : c.id); setReplyText('') }}>
                    {replyTo === c.id ? '取消回复' : '回复'}
                  </button>
                  <button className="comment-like" onClick={() => toggleReplies(c.id)}>
                    {repliesOpen[c.id] ? '收起回复' : '展开回复'}
                  </button>
                  {user && (user.role === 'admin' || user.id === c.user_id) && (
                    <button className="comment-like comment-del" onClick={() => removeComment(c.id)}>删除</button>
                  )}
                </div>

                {replyTo === c.id && (
                  <div className="reply-form">
                    <input className="field" placeholder={`回复 @${c.user?.nickname}`}
                      value={replyText} onChange={(e) => setReplyText(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && submitReply(c.id)} autoFocus />
                    <button className="btn btn-primary btn-sm" onClick={() => submitReply(c.id)}>回复</button>
                  </div>
                )}

                {repliesOpen[c.id] !== undefined && (
                  <div className="reply-list">
                    {(repliesMap[c.id] || []).map((r) => (
                      <div key={r.id} className="reply-item">
                        <Link to={`/users/${r.user_id}`} className="reply-user">{r.user?.nickname}</Link>
                        <span className="reply-text">{r.content}</span>
                        {(user?.role === 'admin' || user?.id === r.user_id) && (
                          <button className="comment-like comment-del" onClick={() => removeComment(r.id)}>删除</button>
                        )}
                      </div>
                    ))}
                    {!(repliesMap[c.id] || []).length && <div className="reply-empty">还没有回复</div>}
                  </div>
                )}
              </div>
            ))}
            {!comments.length && <div className="empty">还没有评论，来抢沙发</div>}
          </div>
        )}

        {tab === 'reviews' && (
          <div>
            {user ? (
              <div className="review-form">
                <div className="stars">
                  {[1, 2, 3, 4, 5].map((v) => (
                    <button key={v} className={`star ${v <= rating ? 'star-on' : ''}`} onClick={() => setRating(v)}>★</button>
                  ))}
                  <span className="review-hint">{rating ? `${rating} 分` : '点击星星评分'}</span>
                </div>
                <textarea className="field" rows="2" placeholder="说说这本书（可选）"
                  value={reviewText} onChange={(e) => setReviewText(e.target.value)} />
                <button className="btn btn-primary" onClick={submitReview}>提交评分</button>
              </div>
            ) : (
              <div className="empty"><Link to="/login">登录后评分</Link></div>
            )}
            {reviews.map((r) => (
              <div key={r.id} className="comment-item">
                <div className="comment-head">
                  <Link to={`/users/${r.user_id}`} className="comment-user">{r.user?.nickname}</Link>
                  <span className="stars-inline">{'★'.repeat(r.rating)}{'☆'.repeat(5 - r.rating)}</span>
                  {(user && (user.id === r.user_id || user.role === 'admin')) && (
                    <span className="comment-del" onClick={() => removeReview(r.id)}>删除</span>
                  )}
                </div>
                {r.content && <p className="comment-content">{r.content}</p>}
              </div>
            ))}
          </div>
        )}

        {tab === 'rewards' && (
          <div>
            {rewards.length ? rewards.map((r) => (
              <div key={r.id} className="comment-item">
                <div className="comment-head">
                  <Link to={`/users/${r.user_id}`} className="comment-user">{r.user?.nickname}</Link>
                  <span className="reward-amount">打赏 {Number(r.amount)} 书币</span>
                  <span className="comment-time">{new Date(r.created_at).toLocaleDateString()}</span>
                </div>
                {r.message && <p className="comment-content">{r.message}</p>}
              </div>
            )) : <div className="empty">暂无打赏记录</div>}
          </div>
        )}
      </section>

      <style>{`
        .detail-head {
          display: flex;
          gap: var(--space-6);
          padding: var(--space-6) 0;
          border-bottom: 1px solid var(--hairline);
        }
        .detail-cover { width: 180px; }
        .detail-info { flex: 1; min-width: 0; }
        .detail-title {
          font-family: var(--font-serif);
          font-size: var(--fs-28);
          margin-bottom: var(--space-3);
        }
        .detail-meta {
          font-size: var(--fs-14);
          color: var(--ink-500);
          margin-bottom: var(--space-4);
          display: flex;
          align-items: center;
          gap: var(--space-2);
        }
        .dot { color: var(--ink-300); }
        .detail-stats {
          display: flex;
          gap: var(--space-5);
          margin-bottom: var(--space-4);
          font-size: var(--fs-12);
          color: var(--ink-500);
        }
        .detail-stats b {
          display: block;
          font-size: var(--fs-16);
          color: var(--ink-900);
          font-variant-numeric: tabular-nums;
        }
        .detail-tags { margin-bottom: var(--space-5); }
        .detail-actions {
          display: flex;
          gap: var(--space-3);
          flex-wrap: wrap;
        }
        .detail-note { font-size: var(--fs-14); color: var(--ink-700); margin-bottom: var(--space-3); }
        .reward-box {
          margin-top: var(--space-4);
          padding: var(--space-4);
          border: 1px solid var(--hairline);
          border-radius: var(--radius);
          background: var(--card);
          max-width: 420px;
        }
        .reward-row { display: flex; gap: var(--space-2); align-items: center; flex-wrap: wrap; }
        .reward-active { border-color: var(--accent) !important; color: var(--accent) !important; }

        .detail-tabs {
          display: flex;
          gap: var(--space-5);
          border-bottom: 1px solid var(--hairline);
          margin: var(--space-4) 0;
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
        .detail-body { padding-bottom: var(--space-8); min-height: 300px; }

        .intro-box { max-width: 720px; }
        .intro-title {
          font-size: var(--fs-16);
          font-weight: 600;
          margin-bottom: var(--space-3);
        }
        .intro-text {
          font-size: var(--fs-15);
          line-height: 1.9;
          color: var(--ink-700);
          text-align: justify;
        }

        .comment-form, .review-form {
          display: flex;
          flex-direction: column;
          gap: var(--space-3);
          margin-bottom: var(--space-5);
          max-width: 620px;
        }
        .comment-form .btn, .review-form .btn { align-self: flex-end; }
        .comment-item {
          padding: var(--space-4) 0;
          border-bottom: 1px solid var(--hairline);
          max-width: 620px;
        }
        .comment-head {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          margin-bottom: 6px;
        }
        .comment-user { font-size: var(--fs-14); font-weight: 600; color: var(--accent-text); text-decoration: none; }
        .comment-user:hover { text-decoration: underline; }
        .comment-time { font-size: var(--fs-12); color: var(--ink-300); margin-left: auto; }
        .comment-content {
          font-size: var(--fs-14);
          line-height: 1.8;
          color: var(--ink-700);
        }
        .comment-like {
          margin-top: 6px;
          font-size: var(--fs-12);
          color: var(--ink-500);
          transition: color var(--ease);
        }
        .comment-like:hover { color: var(--accent); }
        .comment-like-on { color: var(--accent); }
        .comment-ops {
          display: flex;
          gap: var(--space-4);
          align-items: center;
        }
        .comment-del:hover { color: var(--danger); }
        .reply-form {
          display: flex;
          gap: var(--space-2);
          margin: var(--space-3) 0 0 var(--space-5);
          max-width: 480px;
        }
        .reply-list {
          margin: var(--space-3) 0 0 var(--space-5);
          padding-left: var(--space-3);
          border-left: 2px solid var(--hairline);
          display: flex;
          flex-direction: column;
          gap: var(--space-2);
        }
        .reply-item {
          display: flex;
          align-items: baseline;
          gap: var(--space-2);
          font-size: var(--fs-13);
        }
        .reply-user { color: var(--accent-text); font-weight: 600; white-space: nowrap; text-decoration: none; }
        .reply-user:hover { text-decoration: underline; }
        .reply-text { color: var(--ink-700); flex: 1; }
        .reply-empty { font-size: var(--fs-12); color: var(--ink-300); padding: 4px 0; }
        .stars { display: flex; align-items: center; gap: 2px; }
        .star {
          font-size: var(--fs-22);
          color: var(--ink-300);
          transition: color var(--ease), transform var(--ease);
        }
        .star:hover { transform: scale(1.15); }
        .star-on { color: var(--gold); }
        .stars-inline { color: var(--gold); font-size: var(--fs-12); }
        .review-hint { font-size: var(--fs-12); color: var(--ink-500); margin-left: var(--space-2); }
        .reward-amount { font-size: var(--fs-13); color: var(--gold); font-weight: 600; }

        @media (max-width: 768px) {
          .detail-head { gap: var(--space-4); padding: var(--space-4) 0; }
          .detail-cover { width: 108px; }
          .detail-title { font-size: var(--fs-22); }
          .detail-stats { gap: var(--space-3); flex-wrap: wrap; }
          .detail-tabs { gap: var(--space-4); overflow-x: auto; }
          .tab { font-size: var(--fs-14); white-space: nowrap; }
        }
      `}</style>
    </div>
  )
}
