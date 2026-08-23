/* 章节目录列表：付费章带锁标识，点击进入阅读 */
export default function ChapterList({ chapters, novelId }) {
  return (
    <div className="clist">
      {chapters.map((c) => {
        const payable = (c.is_vip || Number(c.price) > 0) && !c.is_free
        return (
          <a key={c.id} href={`/reader/${c.id}`} className="clist-item">
            <span className="clist-title">{c.title}</span>
            <span className="clist-side">
              {payable ? (
                <>
                  <span className="badge badge-vip">VIP {Number(c.price)}书币</span>
                </>
              ) : (
                <span className="badge badge-free">免费</span>
              )}
              <span className="clist-wc">{c.word_count} 字</span>
            </span>
            <style>{`
              .clist-item {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 10px 4px;
                border-bottom: 1px solid var(--hairline);
                font-size: var(--fs-14);
                color: var(--ink-700);
                transition: color var(--ease), padding-left var(--ease);
              }
              .clist-item:hover {
                color: var(--accent);
                padding-left: 10px;
              }
              .clist-title {
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
              }
              .clist-side {
                display: flex;
                align-items: center;
                gap: var(--space-2);
                flex-shrink: 0;
              }
              .clist-wc {
                font-size: var(--fs-12);
                color: var(--ink-300);
                font-variant-numeric: tabular-nums;
              }
            `}</style>
          </a>
        )
      })}
      <style>{`
        .clist { padding: 0 var(--space-2); }
      `}</style>
    </div>
  )
}
