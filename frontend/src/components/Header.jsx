/* 顶部导航：Logo | 分类 | 搜索 | 书架 | 登录态 */
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../stores/AuthContext'

const CATEGORIES = [
  { id: 6, name: '玄幻' },
  { id: 7, name: '都市' },
  { id: 8, name: '科幻' },
]

export default function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [keyword, setKeyword] = useState('')

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
          {CATEGORIES.map((c) => (
            <Link key={c.id} to={`/?cat=${c.id}`} className="nav-link">
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
              <span className="user-chip">
                {user.nickname}
                <span className="user-role">
                  {user.role === 'author' ? '作者' : user.role === 'admin' ? '管理' : ''}
                </span>
              </span>
              {user.role === 'author' && (
                <Link to="/author" className="nav-link">写作台</Link>
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
