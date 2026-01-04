import { http } from '@/utils/request'

// 代理管理相关API
export const proxyApi = {
  // 获取代理列表（支持筛选和分页）
  getProxies(filters = {}) {
    return http.get('/api/proxies', filters)
  },

  // 获取代理详情
  getProxyDetail(id) {
    return http.get(`/api/proxies/${id}`)
  },

  // 创建代理
  createProxy(data) {
    return http.post('/api/proxies', data)
  },

  // 更新代理
  updateProxy(id, data) {
    return http.put(`/api/proxies/${id}`, data)
  },

  // 删除代理
  deleteProxy(id) {
    return http.delete(`/api/proxies/${id}`)
  },

  // 批量删除代理
  batchDeleteProxies(proxyIds) {
    return http.post('/api/proxies/batch-delete', { proxy_ids: proxyIds })
  },

  // 获取代理简单列表（用于下拉选择）
  getProxiesSimple() {
    return http.get('/api/proxies/simple')
  }
}
