/* 登录态：token + user 持久化到 localStorage */
import { createContext, useContext, useEffect, useState } from 'react'
import { apiMe } from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('user'))
    } catch {
      return null
    }
  })
  const [loading, setLoading] = useState(false)

  // 刷新页面时用 token 恢复用户信息
  useEffect(() => {
    if (!user && localStorage.getItem('token')) {
      setLoading(true)
      apiMe()
        .then((u) => {
          setUser(u)
          localStorage.setItem('user', JSON.stringify(u))
        })
        .catch(() => {
          localStorage.removeItem('token')
          localStorage.removeItem('user')
        })
        .finally(() => setLoading(false))
    }
  }, [])

  const login = (token, u) => {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(u))
    setUser(u)
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
