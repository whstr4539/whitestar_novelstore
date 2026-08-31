/* 登录 / 注册：同一布局双表单 */
import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { apiLogin, apiRegister } from '../api'
import { useAuth } from '../stores/AuthContext'

export default function AuthPage({ mode }) {
  const isLogin = mode === 'login'
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const { login } = useAuth()

  const [form, setForm] = useState({ username: '', password: '', nickname: '', email: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError('')
    try {
      const d = isLogin
        ? await apiLogin(form.username, form.password)
        : await apiRegister({ username: form.username, password: form.password, nickname: form.nickname, email: form.email || null })
      login(d.access_token, d.user)
      navigate(params.get('redirect') || '/')
    } catch (err) {
      setError(err.response?.data?.detail || '操作失败，请重试')
    } finally {
      setBusy(false)
    }
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  return (
    <div className="auth-wrap page-enter">
      <div className="auth-card">
        <h1 className="auth-title">{isLogin ? '欢迎回来' : '加入星辰书城'}</h1>
        <p className="auth-sub">
          {isLogin ? '登录后同步书架与阅读进度' : '注册自动开通书币钱包，充值畅读付费章节'}
        </p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={submit} className="auth-form">
          <div className="field-group">
            <label className="label">用户名</label>
            <input className="field" value={form.username} onChange={set('username')}
              placeholder="登录名" required minLength={3} />
          </div>
          {!isLogin && (
            <div className="field-group">
              <label className="label">昵称</label>
              <input className="field" value={form.nickname} onChange={set('nickname')}
                placeholder="展示给别人看的名字" required />
            </div>
          )}
          <div className="field-group">
            <label className="label">密码</label>
            <input className="field" type="password" value={form.password} onChange={set('password')}
              placeholder="至少 6 位" required minLength={6} />
          </div>
          {!isLogin && (
            <div className="field-group">
              <label className="label">邮箱（可选）</label>
              <input className="field" type="email" value={form.email} onChange={set('email')}
                placeholder="用于找回密码" />
            </div>
          )}
          <button className="btn btn-primary btn-block auth-submit" disabled={busy}>
            {busy ? '请稍候…' : isLogin ? '登录' : '注册'}
          </button>
        </form>

        <p className="auth-switch">
          {isLogin ? (
            <>还没有账号？<Link to="/register">去注册</Link></>
          ) : (
            <>已有账号？<Link to="/login">去登录</Link></>
          )}
        </p>
      </div>

      <style>{`
        .auth-wrap {
          min-height: calc(100vh - 56px);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: var(--space-6) var(--space-4);
        }
        .auth-card {
          width: 100%;
          max-width: 380px;
          background: var(--card);
          border: 1px solid var(--hairline);
          border-radius: var(--radius-lg);
          padding: var(--space-7) var(--space-6);
        }
        .auth-title {
          font-family: var(--font-serif);
          font-size: var(--fs-22);
          text-align: center;
          margin-bottom: var(--space-2);
        }
        .auth-sub {
          font-size: var(--fs-14);
          color: var(--ink-500);
          text-align: center;
          margin-bottom: var(--space-6);
        }
        .auth-form {
          display: flex;
          flex-direction: column;
          gap: var(--space-4);
        }
        .field-group { display: flex; flex-direction: column; gap: 6px; }
        .auth-submit { margin-top: var(--space-2); padding: 11px; }
        .auth-submit:disabled { opacity: 0.6; cursor: wait; }
        .auth-switch {
          margin-top: var(--space-5);
          text-align: center;
          font-size: var(--fs-14);
          color: var(--ink-500);
        }
        .auth-switch a { color: var(--accent); }
      `}</style>
    </div>
  )
}
