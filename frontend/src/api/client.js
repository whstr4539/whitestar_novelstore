/* axios 封装：token 注入、401 统一跳登录 */
import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// 请求拦截：自动带 token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 响应拦截：401 清登录态并跳转
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (!location.pathname.startsWith('/login')) {
        location.href = '/login?redirect=' + encodeURIComponent(location.pathname + location.search)
      }
    }
    return Promise.reject(err)
  }
)

export default client
