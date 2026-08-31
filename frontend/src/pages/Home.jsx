/* 首页：推荐位 | 热门榜 | 分类精选 */
import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { apiCategories, apiNotices, apiNovels, apiTicketRank } from '../api'
import NovelCard, { Cover } from '../components/NovelCard'

export default function Home() {
  const [params] = useSearchParams()
  const q = params.get('q') || ''
  const cat = params.get('cat') || ''

  const [novels, setNovels] = useState([])
  const [rank, setRank] = useState([])
  const [loading, setLoading] = useState(true)
  const [catName, setCatName] = useState('')
  const [notice, setNotice] = useState(null)  // 首页公告条：最新一条

  useEffect(() => {
    // 分类页：解析当前分类名用于标题标识
    if (cat) {
      apiCategories().then((cats) => {
        const c = cats.find((x) => x.id === Number(cat))
        setCatName(c?.name || '')
      }).catch(() => setCatName(''))
    } else {
      setCatName('')
    }
  }, [cat])

  useEffect(() => {
    setLoading(true)
    const paramsObj = { sort: 'hot', page_size: 20 }
    if (q) paramsObj.keyword = q
    if (cat) paramsObj.category_id = cat
    apiNovels(paramsObj)
      .then((d) => setNovels(d.items))
      .catch(() => setNovels([]))   // 请求失败视为空，避免 unhandled rejection
      .finally(() => setLoading(false))
    if (!q && !cat) {
      apiTicketRank(5).then(setRank).catch(() => setRank([]))
      // 最新公告（读者端公告入口）
      apiNotices().then((list) => setNotice(list[0] || null)).catch(() => setNotice(null))
    }
  }, [q, cat])

  const featured = novels[0]
  // 列表区域：推荐位占用第一本；分类/搜索页则展示全部（否则 1 本书时整页空白）
  const listItems = q || cat ? novels : novels.slice(1)

  return (
    <div className="container page-enter">
      {q && (
        <div className="page-head">
          <h1 className="page-title">“{q}” 的搜索结果</h1>
          <span className="page-sub">{novels.length} 本</span>
        </div>
      )}

      {cat && catName && (
        <div className="page-head">
          <h1 className="page-title">{catName}</h1>
          <span className="page-sub">{novels.length} 本作品</span>
        </div>
      )}

      {/* 首页公告条：读者进入首页即可看到最新公告 */}
      {notice && !q && !cat && (
        <Link to="/notices" className="notice-bar">
          <span className="notice-bar-tag">公告</span>
          <span className="notice-bar-title">{notice.title}</span>
          <span className="notice-bar-desc">{notice.content}</span>
          <span className="notice-bar-more">查看全部</span>
        </Link>
      )}

      {/* 推荐位：第一本 */}
      {!q && !cat && featured && (
        <section className="featured">
          <Link to={`/novel/${featured.id}`} className="featured-inner">
            <div className="featured-cover-wrap">
              <Cover title={featured.title} categoryId={featured.category_id} size="lg" />
            </div>
            <div className="featured-body">
              <p className="featured-eyebrow">本周推荐</p>
              <h1 className="featured-title">{featured.title}</h1>
              <p className="featured-meta">
                {featured.author?.nickname} · {featured.chapter_count} 章 ·{' '}
                {Number(featured.word_count / 10000).toFixed(1)} 万字
              </p>
              <p className="featured-intro">{featured.intro}</p>
              <span className="btn btn-primary">开始阅读 →</span>
            </div>
          </Link>
        </section>
      )}

      <div className="home-cols">
        {/* 主列表 */}
        <div className="home-main">
          {loading ? (
            <LoadingList />
          ) : novels.length === 0 ? (
            <div className="empty">
              没有找到相关作品，<Link to="/">看看全部热门</Link>
            </div>
          ) : listItems.length > 0 ? (
            <div className="list-block">
              <h2 className="block-title">{q ? '搜索结果' : '热门作品'}</h2>
              {listItems.map((n) => <NovelCard key={n.id} novel={n} />)}
            </div>
          ) : null}
        </div>

        {/* 月票榜 */}
        {!q && !cat && (
          <aside className="home-side">
            <div className="list-block">
              <h2 className="block-title">月票榜</h2>
              {rank.map((r) => (
                <Link key={r.novel_id} to={`/novel/${r.novel_id}`} className="rank-item">
                  <span className={`rank-no rank-no-${r.rank <= 3 ? 'top' : ''}`}>{r.rank}</span>
                  <span className="rank-title">{r.title}</span>
                  <span className="rank-count">{r.ticket_count} 票</span>
                </Link>
              ))}
            </div>
          </aside>
        )}
      </div>

      <style>{`
        .featured {
          margin: var(--space-5) 0;
          background: var(--card);
          border: 1px solid var(--hairline);
          border-radius: var(--radius-lg);
          overflow: hidden;
        }
        .featured-inner {
          display: flex;
          gap: var(--space-6);
          padding: var(--space-6);
        }
        .featured-cover-wrap {
          width: 180px;
          flex-shrink: 0;
        }
        .featured-eyebrow {
          font-size: var(--fs-12);
          color: var(--accent);
          letter-spacing: 0.2em;
          margin-bottom: var(--space-2);
        }
        .featured-title {
          font-family: var(--font-serif);
          font-size: var(--fs-28);
          margin-bottom: var(--space-3);
        }
        .featured-meta {
          font-size: var(--fs-14);
          color: var(--ink-500);
          margin-bottom: var(--space-3);
        }
        .featured-intro {
          font-size: var(--fs-14);
          color: var(--ink-700);
          line-height: 1.8;
          display: -webkit-box;
          -webkit-line-clamp: 3;
          -webkit-box-orient: vertical;
          overflow: hidden;
          margin-bottom: var(--space-5);
          max-width: 560px;
        }
        .home-cols {
          display: grid;
          grid-template-columns: 1fr 280px;
          gap: var(--space-6);
          align-items: start;
          margin-bottom: var(--space-8);
        }
        .list-block {
          background: var(--card);
          border: 1px solid var(--hairline);
          border-radius: var(--radius-lg);
          padding: var(--space-4) var(--space-5);
          margin-bottom: var(--space-5);
        }
        .block-title {
          font-size: var(--fs-18);
          font-weight: 600;
          padding-bottom: var(--space-3);
          border-bottom: 1px solid var(--hairline);
          margin-bottom: var(--space-3);
          letter-spacing: 0.03em;
        }
        .rank-item {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          padding: 9px 0;
          border-bottom: 1px solid var(--hairline);
          font-size: var(--fs-14);
        }
        .rank-item:last-child { border-bottom: none; }
        .rank-no {
          font-family: var(--font-serif);
          font-weight: 700;
          color: var(--ink-300);
          width: 20px;
          font-variant-numeric: tabular-nums;
        }
        .rank-no-top { color: var(--gold); }
        .rank-title {
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
          color: var(--ink-700);
        }
        .rank-title:hover { color: var(--accent); }
        .rank-count {
          font-size: var(--fs-12);
          color: var(--ink-300);
          font-variant-numeric: tabular-nums;
        }
        .notice-bar {
          display: flex;
          align-items: center;
          gap: var(--space-3);
          margin: var(--space-5) 0 0;
          padding: 10px var(--space-4);
          background: var(--card);
          border: 1px solid var(--hairline);
          border-radius: var(--radius);
          color: var(--ink-700);
          transition: border-color var(--ease);
        }
        .notice-bar:hover { border-color: var(--accent); }
        .notice-bar-tag {
          flex-shrink: 0;
          font-size: var(--fs-12);
          color: var(--accent-text);
          background: var(--accent-weak);
          border-radius: 3px;
          padding: 1px 8px;
        }
        .notice-bar-title {
          flex-shrink: 0;
          font-weight: 600;
          font-size: var(--fs-14);
          color: var(--ink-900);
          max-width: 220px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .notice-bar-desc {
          flex: 1;
          min-width: 0;
          font-size: var(--fs-13);
          color: var(--ink-500);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .notice-bar-more {
          flex-shrink: 0;
          font-size: var(--fs-12);
          color: var(--accent);
        }
        @media (max-width: 768px) {
          .featured-inner { flex-direction: row; padding: var(--space-4); gap: var(--space-4); }
          .featured-cover-wrap { width: 110px; }
          .home-cols { grid-template-columns: 1fr; }
          .home-side { display: none; }
          .featured-intro { -webkit-line-clamp: 2; }
        }
      `}</style>
    </div>
  )
}

/* 复用 NovelCard 的封面 */

function LoadingList() {
  return (
    <div className="list-block">
      <h2 className="block-title">热门作品</h2>
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="skeleton-row">
          <div className="skeleton" style={{ width: 96, height: 128 }} />
          <div style={{ flex: 1 }}>
            <div className="skeleton" style={{ height: 18, width: '40%', marginBottom: 10 }} />
            <div className="skeleton" style={{ height: 14, width: '70%', marginBottom: 8 }} />
            <div className="skeleton" style={{ height: 14, width: '90%' }} />
          </div>
          <style>{`
            .skeleton-row {
              display: flex;
              gap: var(--space-4);
              padding: var(--space-4) 0;
              border-bottom: 1px solid var(--hairline);
            }
          `}</style>
        </div>
      ))}
    </div>
  )
}
