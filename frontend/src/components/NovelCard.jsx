/* 小说卡片：CSS 生成封面（封面是页面里唯一的彩色来源） */

// 封面底色板：按分类取色，全部用低饱和深色调
const COVER_PALETTE = [
  '#2f5d8c', '#4a6b5a', '#7a5c4e', '#5c5570', '#6b6b52',
  '#3d6b6b', '#7a4e5e', '#4e5a7a', '#6b4e3d', '#3d6b5c',
]

export function Cover({ title, categoryId, size = 'md', className = '' }) {
  const color = COVER_PALETTE[(categoryId || 1) % COVER_PALETTE.length]
  return (
    <div
      className={`cover cover-${size} ${className}`}
      style={{ background: color }}
      aria-label={title}
    >
      <span className="cover-title">{title}</span>
      <span className="cover-corner" />
      <style>{`
        .cover {
          position: relative;
          border-radius: var(--radius);
          overflow: hidden;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: var(--shadow-soft);
          flex-shrink: 0;
        }
        .cover-title {
          color: rgba(255, 255, 255, 0.92);
          font-family: var(--font-serif);
          font-weight: 600;
          letter-spacing: 0.08em;
          text-align: center;
          padding: 0 10px;
          line-height: 1.5;
          display: -webkit-box;
          -webkit-line-clamp: 3;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
        .cover-corner {
          position: absolute;
          right: -6px;
          bottom: -6px;
          width: 22px;
          height: 22px;
          background: rgba(255, 255, 255, 0.14);
          transform: rotate(45deg);
          border-radius: 3px;
        }
        .cover-lg {
          width: 100%;
          aspect-ratio: 3 / 4;
          font-size: var(--fs-18);
        }
        .cover-md {
          width: 96px;
          aspect-ratio: 3 / 4;
          font-size: var(--fs-14);
        }
        .cover-sm {
          width: 64px;
          aspect-ratio: 3 / 4;
          font-size: var(--fs-12);
        }
      `}</style>
    </div>
  )
}

/* 状态徽标：连载中 / 已完结 */
export function StatusBadge({ status }) {
  return (
    <span className={`badge ${status === 'finished' ? 'badge-finished' : 'badge-serializing'}`}>
      {status === 'finished' ? '完结' : '连载'}
    </span>
  )
}

/* 横向卡片：详情/书架复用 */
export default function NovelCard({ novel, rank }) {
  return (
    <div className="card">
      {rank !== undefined && <span className="card-rank">{rank}</span>}
      <a href={`/novel/${novel.id}`} className="card-main">
        <Cover title={novel.title} categoryId={novel.category_id} size="md" />
        <div className="card-body">
          <h3 className="card-title">{novel.title}</h3>
          <p className="card-meta">
            <span>{novel.author?.nickname || '佚名'}</span>
            <span className="dot">·</span>
            <span>{novel.chapter_count} 章</span>
            <span className="dot">·</span>
            <span>{Number(novel.word_count / 10000).toFixed(1)} 万字</span>
          </p>
          <p className="card-intro">{novel.intro}</p>
          <p className="card-tags">
            {novel.is_vip && <span className="badge badge-vip">VIP</span>}
            <StatusBadge status={novel.status} />
            {Number(novel.score) > 0 && (
              <span className="card-score">★ {Number(novel.score).toFixed(1)}</span>
            )}
          </p>
        </div>
      </a>
      <style>{`
        .card {
          position: relative;
          padding: var(--space-4);
          background: var(--card);
          border-bottom: 1px solid var(--hairline);
          transition: background var(--ease);
        }
        .card:hover {
          background: #f6f5f1;
        }
        .card-main {
          display: flex;
          gap: var(--space-4);
        }
        .card-rank {
          position: absolute;
          left: -4px;
          top: var(--space-4);
          font-family: var(--font-serif);
          font-size: var(--fs-22);
          font-weight: 700;
          color: var(--ink-300);
          font-variant-numeric: tabular-nums;
        }
        .card-body {
          flex: 1;
          min-width: 0;
        }
        .card-title {
          font-size: var(--fs-18);
          font-weight: 600;
          margin-bottom: 4px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .card-meta {
          font-size: var(--fs-12);
          color: var(--ink-500);
          margin-bottom: 6px;
        }
        .dot {
          margin: 0 6px;
          color: var(--ink-300);
        }
        .card-intro {
          font-size: var(--fs-14);
          color: var(--ink-700);
          line-height: 1.6;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
          margin-bottom: 8px;
        }
        .card-tags {
          display: flex;
          align-items: center;
          gap: var(--space-2);
        }
        .card-score {
          font-size: var(--fs-12);
          color: var(--gold);
          margin-left: auto;
        }
      `}</style>
    </div>
  )
}
