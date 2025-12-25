import { http } from '@/utils/request'

// 任务管理相关API
export const taskApi = {
  // 获取任务详情
  getTask(taskId) {
    return http.get(`/getTask/${taskId}`)
  },

  // 查询任务列表
  listTasks(params = {}) {
    return http.get('/listTasks', params)
  },

  // 取消任务
  cancelTask(taskId) {
    return http.post(`/cancelTask/${taskId}`)
  },

  // 重试任务
  retryTask(taskId) {
    return http.post(`/retryTask/${taskId}`)
  },

  // 删除任务（软删除）
  deleteTask(taskId) {
    // 后端兼容 DELETE/POST，这里用 DELETE
    return http.delete(`/deleteTask/${taskId}`)
  }
}

