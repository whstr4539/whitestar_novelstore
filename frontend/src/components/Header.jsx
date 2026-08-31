/* 顶部导航：Logo | 分类 | 搜索 | 书架 | 登录态 */
import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { apiCategories } from '../api'
import { useAuth } from '../stores/AuthContext'

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const cat = params.get('cat') || ''
  const [keyword, setKeyword] = useState('')
  // 顶级分类（parent_id 为 null），来自数据库，避免硬编码错位
  const [topCategories, setTopCategories] = useState([])

  useEffect(() => {
    apiCategories()
      .then((cats) => setTopCategories(cats.filter((c) => c.parent_id === null)))
      .catch(() => {})
  }, [])

  const submitSearch = (e) => {
    e.preventDefault()
    navigate(keyword ? `/?q=${encodeURIComponent(keyword)}` : '/')
  }

  return (
    <header className="header">
      <div className="container header-inner">
        <Link to="/" className="logo">
          <span className="logo-mark">星</span>
          星辰书城
        </Link>

        <nav className="nav">
          {topCategories.map((c) => (
            <Link
              key={c.id}
              to={`/?cat=${c.id}`}
              className={`nav-link ${cat === String(c.id) ? 'nav-link-active' : ''}`}
              aria-current={cat === String(c.id) ? 'page' : undefined}
            >
              {c.name}
            </Link>
          ))}
        </nav>

        <form className="search" onSubmit={submitSearch}>
          <input
            className="field search-input"
            placeholder="搜索书名 / 简介"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
          />
        </form>

        <div className="header-right">
          {user ? (
            <>
              <Link to="/bookshelf" className="nav-link">书架</Link>
              <Link to="/profile" className="user-chip" title="个人中心">
                {user.nickname}
                <span className="user-role">
                  {user.role === 'author' ? '作者' : user.role === 'admin' ? '管理' : ''}
                </span>
              </Link>
              {user.role === 'author' && (
                <Link to="/author" className="nav-link">写作台</Link>
              )}
              {user.role === 'admin' && (
                <Link to="/admin" className="nav-link">管理台</Link>
              )}
              <button className="nav-link logout" onClick={() => { logout(); navigate('/') }}>
                退出
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="nav-link">登录</Link>
              <Link to="/register" className="btn btn-primary btn-sm">注册</Link>
            </>
          )}
        </div>
      </div>

      <style>{`
        .header {
          position: sticky;
          top: 0;
          z-index: 50;
          background: var(--paper);
          border-bottom: 1px solid var(--hairline);
        }
        .header-inner {
          display: flex;
          align-items: center;
          gap: var(--space-5);
          height: 56px;
        }
        .logo {
          display: flex;
          align-items: center;
          gap: var(--space-2);
          font-weight: 600;
          font-size: var(--fs-18);
          letter-spacing: 0.04em;
          white-space: nowrap;
        }
        .logo-mark {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 28px;
          height: 28px;
          border-radius: 6px;
          background: var(--accent);
          color: #fff;
          font-size: var(--fs-14);
        }
        .nav {
          display: flex;
          gap: var(--space-4);
        }
        .nav-link {
          font-size: var(--fs-14);
          color: var(--ink-700);
          transition: color var(--ease);
          white-space: nowrap;
        }
        .nav-link:hover {
          color: var(--accent);
        }
        .nav-link-active {
          color: var(--accent);
          font-weight: 600;
          box-shadow: 0 2px 0 0 var(--accent);
        }
        .search {
          flex: 1;
          max-width: 320px;
          margin-left: auto;
        }
        .search-input {
          padding: 7px 14px;
          font-size: var(--fs-14);
        }
        .header-right {
          display: flex;
          align-items: center;
          gap: var(--space-4);
        }
        .user-chip {
          font-size: var(--fs-14);
          color: var(--ink-900);
          white-space: nowrap;
          padding: 5px 10px;
          border-radius: 16px;
          border: 1px solid var(--hairline);
          transition: border-color var(--ease), color var(--ease);
        }
        .user-chip:hover {
          border-color: var(--accent);
          color: var(--accent);
        }
        .user-role {
          font-size: var(--fs-12);
          color: var(--accent);
          margin-left: 4px;
        }
        .logout {
          color: var(--ink-500);
        }
        .btn-sm {
          padding: 6px 14px;
          font-size: var(--fs-14);
        }
        @media (max-width: 768px) {
          .header-inner { gap: var(--space-3); }
          .nav { display: none; }
          .search { max-width: 160px; }
          .header-right .nav-link:not(:last-child) { display: none; }
        }
      `}</style>
    </header>
  )
}
