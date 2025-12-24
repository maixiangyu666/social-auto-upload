import { http } from '@/utils/request'

// 分组管理相关API
export const groupApi = {
  // 获取分组列表
  getGroups() {
    return http.get('/api/groups')
  },

  // 获取分组详情
  getGroupDetail(id) {
    return http.get(`/api/groups/${id}`)
  },

  // 创建分组
  createGroup(data) {
    return http.post('/api/groups', data)
  },

  // 更新分组
  updateGroup(id, data) {
    return http.put(`/api/groups/${id}`, data)
  },

  // 删除分组
  deleteGroup(id) {
    return http.delete(`/api/groups/${id}`)
  },

  // 批量分配账号到分组
  batchAssignAccounts(accountIds, groupId) {
    return http.post('/api/accounts/batch-assign-group', {
      account_ids: accountIds,
      group_id: groupId
    })
  }
}

