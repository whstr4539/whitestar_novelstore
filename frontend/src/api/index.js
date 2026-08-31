/* 后端接口函数：与 FastAPI 路由一一对应 */
import client from './client'

// ---------- 认证 ----------
export const apiLogin = (username, password) =>
  client.post('/auth/login', { username, password }).then((r) => r.data)

export const apiRegister = (data) =>
  client.post('/auth/register', data).then((r) => r.data)

export const apiMe = () => client.get('/auth/me').then((r) => r.data)

// ---------- 分类 ----------
export const apiCategories = () => client.get('/categories').then((r) => r.data)

// ---------- 小说 ----------
export const apiNovels = (params = {}) =>
  client.get('/novels', { params }).then((r) => r.data)

export const apiNovel = (id) => client.get(`/novels/${id}`).then((r) => r.data)

export const apiChapters = (novelId) =>
  client.get(`/novels/${novelId}/chapters`).then((r) => r.data)

export const apiTicketRank = (limit = 10) =>
  client.get('/novels/tickets/rank', { params: { limit } }).then((r) => r.data)

// ---------- 章节阅读 / 订阅 ----------
export const apiReadChapter = (chapterId) =>
  client.get(`/chapters/${chapterId}`).then((r) => r.data)

export const apiPurchaseChapter = (chapterId) =>
  client.post(`/chapters/${chapterId}/purchase`).then((r) => r.data)

export const apiChapterStatus = (chapterId) =>
  client.get(`/chapters/${chapterId}/status`).then((r) => r.data)

// ---------- 书架 / 进度 ----------
export const apiBookshelf = () => client.get('/bookshelf').then((r) => r.data)

export const apiAddFavorite = (novelId) =>
  client.post(`/bookshelf/${novelId}`).then((r) => r.data)

export const apiRemoveFavorite = (novelId) =>
  client.delete(`/bookshelf/${novelId}`).then((r) => r.data)

export const apiHistory = () =>
  client.get('/bookshelf/history/list').then((r) => r.data)

export const apiSaveProgress = (data) =>
  client.put('/bookshelf/progress', data).then((r) => r.data)

// ---------- 钱包 ----------
export const apiWallet = () => client.get('/wallet').then((r) => r.data)

export const apiRecharge = (amount) =>
  client.post('/wallet/recharge', { amount, payment_method: 'mock' }).then((r) => r.data)

export const apiPayOrder = (orderNo) =>
  client.post(`/wallet/pay/${orderNo}`, {}).then((r) => r.data)

export const apiCancelOrder = (orderNo) =>
  client.post(`/wallet/pay/${orderNo}/cancel`, {}).then((r) => r.data)

export const apiOrderStatus = (orderNo) =>
  client.get(`/wallet/order/${orderNo}`).then((r) => r.data)

export const apiBills = () => client.get('/wallet/bills').then((r) => r.data)

// ---------- 评论 ----------
export const apiComments = (novelId, chapterId) =>
  client.get(`/novels/${novelId}/comments`, {
    params: chapterId ? { chapter_id: chapterId } : {},
  }).then((r) => r.data)

export const apiPostComment = (novelId, data) =>
  client.post(`/novels/${novelId}/comments`, data).then((r) => r.data)

export const apiDeleteComment = (commentId) =>
  client.delete(`/comments/${commentId}`).then((r) => r.data)

export const apiCommentReplies = (commentId) =>
  client.get(`/comments/${commentId}/replies`).then((r) => r.data)

export const apiLikeComment = (commentId) =>
  client.post(`/comments/${commentId}/like`).then((r) => r.data)

// ---------- 评分 ----------
export const apiReviews = (novelId) =>
  client.get(`/novels/${novelId}/reviews`).then((r) => r.data)

export const apiPostReview = (novelId, data) =>
  client.post(`/novels/${novelId}/reviews`, data).then((r) => r.data)

export const apiDeleteReview = (novelId, reviewId) =>
  client.delete(`/novels/${novelId}/reviews/${reviewId}`).then((r) => r.data)

// ---------- 月票 / 打赏 ----------
export const apiVoteTicket = (novelId, ticketType) =>
  client.post(`/novels/${novelId}/tickets`, { ticket_type: ticketType }).then((r) => r.data)

export const apiRewards = (novelId) =>
  client.get(`/novels/${novelId}/rewards`).then((r) => r.data)

export const apiReward = (novelId, amount, message) =>
  client.post(`/novels/${novelId}/rewards`, { amount, message }).then((r) => r.data)

// ---------- 作者后台 ----------
export const apiMyNovels = () => client.get('/author/my-novels').then((r) => r.data)

export const apiAuthorStats = () => client.get('/author/stats').then((r) => r.data)

export const apiCreateNovel = (data) =>
  client.post('/author/novels', data).then((r) => r.data)

export const apiPublishChapter = (novelId, data) =>
  client.post(`/author/novels/${novelId}/chapters`, data).then((r) => r.data)

export const apiUpdateChapter = (chapterId, data) =>
  client.put(`/author/chapters/${chapterId}`, data).then((r) => r.data)

export const apiNovelEarnings = (novelId) =>
  client.get(`/author/novels/${novelId}/earnings`).then((r) => r.data)

// ---------- 公告 ----------
export const apiNotices = () => client.get('/notices').then((r) => r.data)

// ---------- 用户公开主页 ----------
export const apiUserProfile = (userId) =>
  client.get(`/users/${userId}`).then((r) => r.data)

export const apiUpdateProfile = (data) =>
  client.put('/users/me', data).then((r) => r.data)

// ---------- 我的评论 ----------
export const apiMyComments = () => client.get('/comments/me').then((r) => r.data)

// ---------- 管理后台 ----------
export const apiAdminStats = () => client.get('/admin/stats').then((r) => r.data)

export const apiAdminUsers = (params = {}) =>
  client.get('/admin/users', { params }).then((r) => r.data)

export const apiAdminSetUserStatus = (userId, status) =>
  client.put(`/admin/users/${userId}/status`, { status }).then((r) => r.data)

export const apiAdminNovels = (params = {}) =>
  client.get('/admin/novels', { params }).then((r) => r.data)

export const apiAdminComments = (params = {}) =>
  client.get('/admin/comments', { params }).then((r) => r.data)

export const apiAdminSetNovelStatus = (novelId, status) =>
  client.put(`/admin/novels/${novelId}/status`, { status }).then((r) => r.data)

export const apiCreateNotice = (data) =>
  client.post('/notices', data).then((r) => r.data)

export const apiDeleteNotice = (noticeId) =>
  client.delete(`/notices/${noticeId}`).then((r) => r.data)
