import { http } from '@/utils/request'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5409'

export const loginApi = {
  /**
   * SSE 登录（扫码/手动）
   * 后端会推送：
   * - {"event":"session","session_id":"..."}
   * - {"event":"qrcode","img":"..."}
   * - {"event":"manual_required","session_id":"..."}
   * - {"event":"success"...} / {"event":"error"...}
   */
  loginWithSSE(platformType, accountName) {
    const url = `${apiBaseUrl}/login?type=${encodeURIComponent(platformType)}&id=${encodeURIComponent(accountName)}`
    return new EventSource(url)
  },

  /** 手动登录确认（百家号/TikTok） */
  confirmManual(sessionId) {
    return http.post('/api/accounts/login/confirm', { session_id: sessionId })
  },

  /** REST 登录（可选：配合轮询） */
  loginWithREST(platformType, accountName, accountId) {
    return http.post('/api/accounts/login', {
      platform_type: platformType,
      account_name: accountName,
      account_id: accountId
    })
  },

  getLoginStatus(sessionId) {
    return http.get(`/api/accounts/login/status/${encodeURIComponent(sessionId)}`)
  },

  /** 刷新Cookie（复用登录流程） */
  refreshCookieWithLogin(accountId) {
    return http.post(`/api/accounts/${encodeURIComponent(accountId)}/refresh-cookie-with-login`)
  },

  /** Bilibili Cookie 上传（新增账号或更新账号） */
  uploadCookie({ file, platformType, accountId, accountName }) {
    const form = new FormData()
    form.append('file', file)
    form.append('platform', String(platformType))
    if (accountId) form.append('id', String(accountId))
    if (accountName) form.append('account_name', String(accountName))
    return http.upload('/uploadCookie', form)
  }
}


