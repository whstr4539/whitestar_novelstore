/* 应用入口：路由 + 布局 */
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider, useAuth } from './stores/AuthContext'
import Header from './components/Header'
import Home from './pages/Home'
import NovelDetail from './pages/NovelDetail'
import Reader from './pages/Reader'
import Bookshelf from './pages/Bookshelf'
import AuthPage from './pages/Auth'
import Author from './pages/Author'
import Profile from './pages/Profile'
import Admin from './pages/Admin'
import UserPage from './pages/UserPage'
import Notices from './pages/Notices'
import Bills from './pages/Bills'

/* 阅读页不显示站点导航（沉浸式） */
function Layout() {
  const location = useLocation()
  const isReader = location.pathname.startsWith('/reader')
  return (
    <>
      {!isReader && <Header />}
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/novel/:id" element={<NovelDetail />} />
        <Route path="/reader/:chapterId" element={<Reader />} />
        <Route path="/bookshelf" element={<RequireAuth><Bookshelf /></RequireAuth>} />
        <Route path="/profile" element={<RequireAuth><Profile /></RequireAuth>} />
        <Route path="/admin" element={<RequireAuth><Admin /></RequireAuth>} />
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/register" element={<AuthPage mode="register" />} />
        <Route path="/users/:userId" element={<UserPage />} />
        <Route path="/notices" element={<Notices />} />
        <Route path="/bills" element={<RequireAuth><Bills /></RequireAuth>} />
        <Route path="/author" element={<Author />} />
      </Routes>
    </>
  )
}

/* 未登录跳转登录页 */
function RequireAuth({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()
  if (loading) return null
  if (!user) {
    return <NavigateToLogin from={location.pathname} />
  }
  return children
}

function NavigateToLogin({ from }) {
  return <Navigate to={`/login?redirect=${encodeURIComponent(from)}`} replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Layout />
      </AuthProvider>
    </BrowserRouter>
  )
}
