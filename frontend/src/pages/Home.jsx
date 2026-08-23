/* 首页：推荐位 | 热门榜 | 分类精选 */
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { apiNovels, apiTicketRank } from '../api'
import NovelCard, { Cover } from '../components/NovelCard'

export default function Home() {
  const [params] = useSearchParams()
  const q = params.get('q') || ''
  const cat = params.get('cat') || ''

  const [novels, setNovels] = useState([])
  const [rank, setRank] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    const paramsObj = { sort: 'hot', page_size: 20 }
    if (q) paramsObj.keyword = q
    if (cat) paramsObj.category_id = cat
    apiNovels(paramsObj)
      .then((d) => setNovels(d.items))
      .finally(() => setLoading(false))
    if (!q && !cat) {
      apiTicketRank(5).then(setRank).catch(() => setRank([]))
    }
  }, [q, cat])

  const featured = novels[0]
  const rest = novels.slice(1)

  return (
    <div className="container page-enter">
      {q && (
        <div className="page-head">
          <h1 className="page-title">“{q}” 的搜索结果</h1>
          <span className="page-sub">{novels.length} 本</span>
        </div>
      )}

      {/* 推荐位：第一本 */}
      {!q && !cat && featured && (
        <section className="featured">
          <a href={`/novel/${featured.id}`} className="featured-inner">
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
          </a>
        </section>
      )}

      <div className="home-cols">
        {/* 主列表 */}
        <div className="home-main">
          {loading ? (
            <LoadingList />
          ) : novels.length === 0 ? (
            <div className="empty">
              没有找到相关作品，<a href="/">看看全部热门</a>
            </div>
          ) : (
            <div className="list-block">
              <h2 className="block-title">{q ? '搜索结果' : '热门作品'}</h2>
              {rest.length ? rest.map((n, i) => <NovelCard key={n.id} novel={n} />) : <NovelCard novel={featured} />}
            </div>
          )}
        </div>

        {/* 月票榜 */}
        {!q && !cat && (
          <aside className="home-side">
            <div className="list-block">
              <h2 className="block-title">月票榜</h2>
              {rank.map((r) => (
                <a key={r.novel_id} href={`/novel/${r.novel_id}`} className="rank-item">
                  <span className={`rank-no rank-no-${r.rank <= 3 ? 'top' : ''}`}>{r.rank}</span>
                  <span className="rank-title">{r.title}</span>
                  <span className="rank-count">{r.ticket_count} 票</span>
                </a>
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
