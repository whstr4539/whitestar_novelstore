/* 书架：收藏 + 阅读历史 两个 Tab */
import { useEffect, useState } from 'react'
import { apiBookshelf, apiHistory, apiRemoveFavorite } from '../api'
import NovelCard from '../components/NovelCard'

export default function Bookshelf() {
  const [tab, setTab] = useState('shelf')
  const [shelf, setShelf] = useState([])
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    Promise.all([apiBookshelf(), apiHistory()])
      .then(([s, h]) => { setShelf(s.items); setHistory(h.items) })
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const remove = async (id) => {
    await apiRemoveFavorite(id)
    load()
  }

  const list = tab === 'shelf' ? shelf : history

  return (
    <div className="container page-enter">
      <div className="page-head">
        <h1 className="page-title">我的书架</h1>
        <span className="page-sub">{shelf.length} 本收藏 · {history.length} 本在读</span>
      </div>

      <div className="shelf-tabs">
        <button className={`tab ${tab === 'shelf' ? 'tab-active' : ''}`} onClick={() => setTab('shelf')}>
          收藏（{shelf.length}）
        </button>
        <button className={`tab ${tab === 'history' ? 'tab-active' : ''}`} onClick={() => setTab('history')}>
          阅读历史（{history.length}）
        </button>
      </div>

      {loading ? (
        <div className="skeleton" style={{ height: 200, marginTop: 16 }} />
      ) : list.length === 0 ? (
        <div className="empty">
          {tab === 'shelf' ? '书架空空如也，去发现好书 ' : '还没有阅读记录 '}
          <a href="/">→ 去逛逛</a>
        </div>
      ) : (
        <div className="shelf-list">
          {list.map((item) => (
            <div key={item.novel.id} className="shelf-item">
              <NovelCard novel={item.novel} />
              {tab === 'shelf' && (
                <button className="btn btn-danger-ghost shelf-remove"
                  onClick={() => remove(item.novel.id)}>
                  移出
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      <style>{`
        .shelf-tabs {
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
        .shelf-list {
          background: var(--card);
          border: 1px solid var(--hairline);
          border-radius: var(--radius-lg);
          overflow: hidden;
        }
        .shelf-item {
          position: relative;
        }
        .shelf-remove {
          position: absolute;
          right: 16px;
          top: 50%;
          transform: translateY(-50%);
          padding: 4px 12px;
          font-size: var(--fs-12);
          z-index: 2;
        }
        @media (max-width: 768px) {
          .shelf-remove { display: none; }
        }
      `}</style>
    </div>
  )
}
