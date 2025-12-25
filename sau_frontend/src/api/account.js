import { http } from '@/utils/request'

// 账号管理相关API
export const accountApi = {
  // 获取账号列表（支持筛选）
  getAccounts(filters = {}) {
    return http.get('/api/accounts', filters)
  },

  // 获取账号详情
  getAccountDetail(id) {
    return http.get(`/api/accounts/${id}`)
  },

  // 创建账号
  createAccount(data) {
    return http.post('/api/accounts', data)
  },

  // 更新账号
  updateAccount(id, data) {
    return http.put(`/api/accounts/${id}`, data)
  },

  // 删除账号
  deleteAccount(id) {
    return http.delete(`/api/accounts/${id}`)
  },

  // 批量删除账号
  batchDeleteAccounts(accountIds) {
    return http.post('/api/accounts/batch-delete', { account_ids: accountIds })
  },

  // 批量验证Cookie
  batchVerifyAccounts(accountIds) {
    return http.post('/api/accounts/batch-verify', { account_ids: accountIds })
  },

  // 刷新Cookie
  refreshCookie(id, { mode = 'background' } = {}) {
    // mode: background | login
    const qs = mode ? `?mode=${encodeURIComponent(mode)}` : ''
    return http.post(`/api/accounts/${id}/refresh-cookie${qs}`)
  },

  // 批量刷新Cookie
  batchRefreshCookies(accountIds) {
    return http.post('/api/accounts/batch-refresh-cookie', { account_ids: accountIds })
  },

  // 获取账号统计
  getAccountStatistics(id) {
    return http.get(`/api/accounts/${id}/statistics`)
  },

  // 更新账号分组
  updateAccountGroup(accountId, groupId) {
    return http.put(`/api/accounts/${accountId}`, { group_id: groupId })
  },

  // 获取 Cookie 刷新/验证日志（分页）
  getCookieRefreshLogs(accountId, params = {}) {
    return http.get(`/api/accounts/${accountId}/cookie-refresh-logs`, params)
  }
}
