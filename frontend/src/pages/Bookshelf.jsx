/* 书架：收藏 + 阅读历史 两个 Tab */
import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { apiBookshelf, apiHistory, apiRemoveFavorite } from '../api'
import NovelCard from '../components/NovelCard'

export default function Bookshelf() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const [tab, setTab] = useState(params.get('tab') === 'history' ? 'history' : 'shelf')
  const [shelf, setShelf] = useState([])
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState('')

  const load = () => {
    setLoading(true)
    Promise.all([apiBookshelf(), apiHistory()])
      .then(([s, h]) => { setShelf(s.items); setHistory(h.items) })
      .catch(() => setMsg('加载失败，请稍后重试'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const remove = async (id) => {
    try {
      await apiRemoveFavorite(id)
      setMsg('')
      load()
    } catch (e) {
      setMsg(e.response?.data?.detail || '移出书架失败')
    }
  }

  const list = tab === 'shelf' ? shelf : history

  return (
    <div className="container page-enter">
      <div className="page-head">
        <h1 className="page-title">我的书架</h1>
        <span className="page-sub">{shelf.length} 本收藏 · {history.length} 本在读</span>
      </div>

      {msg && <div className="alert alert-error">{msg}</div>}

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
          <Link to="/">→ 去逛逛</Link>
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
              {tab === 'history' && item.chapter_id && (
                <button className="btn btn-primary shelf-continue"
                  onClick={() => navigate(`/reader/${item.chapter_id}`)}>
                  续读
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
        .shelf-remove,
        .shelf-continue {
          position: absolute;
          right: 16px;
          top: 50%;
          transform: translateY(-50%);
          padding: 4px 12px;
          font-size: var(--fs-12);
          z-index: 2;
        }
        @media (max-width: 768px) {
          .shelf-remove, .shelf-continue { display: none; }
        }
      `}</style>
    </div>
  )
}
